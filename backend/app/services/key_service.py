from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import (
    extract_key_parts,
    generate_raw_key,
    hash_api_key,
)
from app.models.api_key import VALID_ZONES, ApiKey
from app.models.audit_log import AuditLog, EventType
from app.models.user import User
from app.schemas.api_key import ApiKeyCreateRequest


def create_key(
    payload: ApiKeyCreateRequest,
    owner: User,
    db: Session,
    ip: str,
    user_agent: str,
) -> dict:
    """
    Generate a new API key for the owner.
    Returns a dict containing the ORM object AND the raw key.
    Raw key is returned to the caller exactly once — never stored.
    """
    if payload.zone not in VALID_ZONES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid zone. Must be one of: {', '.join(VALID_ZONES)}",
        )

    # Determine prefix from zone
    prefix_map = {
        "public":        "sv_pub_",
        "authenticated": "sv_live_",
        "privileged":    "sv_priv",
    }
    prefix = prefix_map[payload.zone]

    raw_key = generate_raw_key(prefix=prefix)
    key_hash = hash_api_key(raw_key)
    key_prefix, last_four = extract_key_parts(raw_key)

    api_key = ApiKey(
        owner_id=owner.id,
        name=payload.name,
        prefix=key_prefix,
        key_hash=key_hash,
        last_four=last_four,
        zone=payload.zone,
        expires_at=payload.expires_at,
    )
    db.add(api_key)
    db.flush()

    db.add(AuditLog(
        user_id=owner.id,
        api_key_id=api_key.id,
        event_type=EventType.KEY_CREATED,
        zone="authenticated",
        ip_address=ip,
        user_agent=user_agent,
        meta={"key_name": payload.name, "zone": payload.zone},
    ))
    db.commit()

    return {"api_key": api_key, "raw_key": raw_key}


def list_keys(owner: User, db: Session) -> list[ApiKey]:
    return (
        db.query(ApiKey)
        .filter(ApiKey.owner_id == owner.id, ApiKey.is_active == True)
        .order_by(ApiKey.created_at.desc())
        .all()
    )


def get_key(key_id: str, owner: User, db: Session) -> ApiKey:
    key = (
        db.query(ApiKey)
        .filter(
            ApiKey.id == key_id,
            ApiKey.owner_id == owner.id,
        )
        .first()
    )
    if not key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )
    return key


def rotate_key(
    key_id: str,
    owner: User,
    db: Session,
    ip: str,
    user_agent: str,
) -> dict:
    """
    Rotate an API key — invalidate the old one, generate a new one
    with the same name and zone. Old key is deactivated, not deleted,
    so the audit trail is preserved.
    """
    old_key = get_key(key_id, owner, db)

    if not old_key.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot rotate an inactive key",
        )

    # Deactivate the old key
    old_key.is_active = False
    old_key.rotated_at = datetime.now(timezone.utc)
    db.flush()

    # Generate replacement with same name and zone
    prefix_map = {
        "public":        "sv_pub_",
        "authenticated": "sv_live_",
        "privileged":    "sv_priv",
    }
    prefix = prefix_map[old_key.zone]
    raw_key = generate_raw_key(prefix=prefix)
    key_hash = hash_api_key(raw_key)
    key_prefix, last_four = extract_key_parts(raw_key)

    new_key = ApiKey(
        owner_id=owner.id,
        name=old_key.name,
        prefix=key_prefix,
        key_hash=key_hash,
        last_four=last_four,
        zone=old_key.zone,
        expires_at=old_key.expires_at,
    )
    db.add(new_key)
    db.flush()

    db.add(AuditLog(
        user_id=owner.id,
        api_key_id=new_key.id,
        event_type=EventType.KEY_ROTATED,
        zone="privileged",
        ip_address=ip,
        user_agent=user_agent,
        meta={
            "old_key_id": str(old_key.id),
            "new_key_id": str(new_key.id),
            "key_name": old_key.name,
        },
    ))
    db.commit()

    return {"api_key": new_key, "raw_key": raw_key}


def revoke_key(
    key_id: str,
    owner: User,
    db: Session,
    ip: str,
    user_agent: str,
) -> None:
    """
    Permanently deactivate an API key.
    The row is kept for audit trail purposes — never hard deleted.
    """
    key = get_key(key_id, owner, db)

    if not key.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Key is already revoked",
        )

    key.is_active = False

    db.add(AuditLog(
        user_id=owner.id,
        api_key_id=key.id,
        event_type=EventType.KEY_REVOKED,
        zone="privileged",
        ip_address=ip,
        user_agent=user_agent,
        meta={"key_name": key.name},
    ))
    db.commit()