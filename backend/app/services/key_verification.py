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
    from fastapi import HTTPException, status

    if not raw_key or len(raw_key) < 10:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format",
        )

    # Extract prefix the same way we stored it
    if '_' in raw_key:
        last_underscore = raw_key.rfind('_')
        prefix = raw_key[:last_underscore + 1]
    else:
        prefix = raw_key[:7]

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