from __future__ import annotations
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import verify_api_key
from app.models.api_key import ApiKey
from app.models.audit_log import AuditLog, EventType


def verify_key_for_zone(
    raw_key: str,
    required_zone: str,
    db: Session,
    ip: str,
    user_agent: str,
) -> ApiKey:
    """
    Verify a raw API key matches an active key in the required zone.
    Increments usage count and writes an audit log on success.
    Raises 401 if invalid, 403 if wrong zone.
    """
    # Find candidate keys by prefix to narrow the search
    if not raw_key or len(raw_key) < 10:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format",
        )

    prefix = raw_key[:8]
    candidates = (
        db.query(ApiKey)
        .filter(ApiKey.prefix == prefix, ApiKey.is_active == True)
        .all()
    )

    matched_key: ApiKey | None = None
    for candidate in candidates:
        if verify_api_key(raw_key, candidate.key_hash):
            matched_key = candidate
            break

    if not matched_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    if matched_key.is_expired:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key has expired",
        )

    # Zone hierarchy check — privileged keys can access lower zones too
    zone_levels = {"public": 1, "authenticated": 2, "privileged": 3}
    if zone_levels[matched_key.zone] < zone_levels[required_zone]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"This endpoint requires a {required_zone} key. Your key is {matched_key.zone}.",
        )

    matched_key.usage_count += 1

    db.add(AuditLog(
        user_id=matched_key.owner_id,
        api_key_id=matched_key.id,
        event_type=EventType.KEY_VERIFIED,
        zone=required_zone,
        ip_address=ip,
        user_agent=user_agent,
        meta={"endpoint_zone": required_zone, "key_zone": matched_key.zone},
    ))
    db.commit()

    return matched_key