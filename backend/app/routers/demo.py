from __future__ import annotations
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.orm import Session

from app.core.dependencies import get_client_ip
from app.db.session import get_db
from app.services.key_verification import verify_key_for_zone

router = APIRouter()


def _extract_key(authorization: str | None) -> str:
    """Pull the raw key out of an Authorization: Bearer <key> header."""
    from fastapi import HTTPException, status
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header. Use: Authorization: Bearer YOUR_KEY",
        )
    return authorization.replace("Bearer ", "", 1).strip()


# ── PUBLIC zone — example: weather data, public catalogue, etc. ───────────────
@router.get("/weather")
def public_weather(
    request: Request,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    """
    Example public endpoint — only requires a PUBLIC key.
    Use case: public read-only data anyone with a key can fetch.
    """
    raw_key = _extract_key(authorization)
    verify_key_for_zone(
        raw_key, "public", db,
        get_client_ip(request),
        request.headers.get("User-Agent", ""),
    )
    return {
        "city": "Lagos",
        "temperature_c": 31,
        "condition": "Partly cloudy",
        "humidity_percent": 78,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "zone": "public",
        "message": "✓ Your public key worked. Public endpoints are open data.",
    }


# ── AUTHENTICATED zone — example: user profile, billing, normal app data ──────
@router.get("/profile")
def authenticated_profile(
    request: Request,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    """
    Example authenticated endpoint — requires an AUTHENTICATED key (or higher).
    Use case: user-specific data — orders, settings, billing info.
    """
    raw_key = _extract_key(authorization)
    matched = verify_key_for_zone(
        raw_key, "authenticated", db,
        get_client_ip(request),
        request.headers.get("User-Agent", ""),
    )
    return {
        "owner_email": matched.owner.email,
        "key_name": matched.name,
        "usage_count": matched.usage_count,
        "zone": "authenticated",
        "message": "✓ Your authenticated key worked. This endpoint returned user-specific data.",
    }


# ── PRIVILEGED zone — example: dangerous admin actions ────────────────────────
@router.post("/admin/reset")
def privileged_reset(
    request: Request,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    """
    Example privileged endpoint — requires a PRIVILEGED key.
    Use case: dangerous operations — bulk deletes, factory resets, key rotations.
    """
    raw_key = _extract_key(authorization)
    matched = verify_key_for_zone(
        raw_key, "privileged", db,
        get_client_ip(request),
        request.headers.get("User-Agent", ""),
    )
    return {
        "action": "system_reset_simulated",
        "performed_by": matched.owner.email,
        "performed_at": datetime.now(timezone.utc).isoformat(),
        "zone": "privileged",
        "message": "✓ Your privileged key worked. In a real system, this is where dangerous actions live.",
    }