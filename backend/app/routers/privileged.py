from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.orm import Session

from app.core.dependencies import get_client_ip, zone3_privileged
from app.db.session import get_db
from app.models.user import User
from app.schemas.api_key import ApiKeyCreateResponse
from app.services.key_service import revoke_key, rotate_key

router = APIRouter()


@router.post("/{key_id}/rotate", response_model=ApiKeyCreateResponse)
def rotate_api_key(
    key_id: str,
    request: Request,
    x_nonce_token: str = Header(description="Fresh UUID4 nonce — get one by running: python -c \"import uuid; print(uuid.uuid4())\""),
    db: Session = Depends(get_db),
    current_user: User = Depends(zone3_privileged),
):
    """
    Zone 3 — privileged + replay detection.
    Requires JWT + fresh X-Nonce-Token header.
    The new raw key is returned exactly once.
    """
    ip = get_client_ip(request)
    user_agent = request.headers.get("User-Agent", "")
    result = rotate_key(key_id, current_user, db, ip, user_agent)

    api_key = result["api_key"]
    raw_key = result["raw_key"]

    return ApiKeyCreateResponse(
        id=str(api_key.id),
        name=api_key.name,
        prefix=api_key.prefix,
        last_four=api_key.last_four,
        zone=api_key.zone,
        display_key=api_key.display_key,
        is_active=api_key.is_active,
        usage_count=api_key.usage_count,
        created_at=api_key.created_at,
        expires_at=api_key.expires_at,
        raw_key=raw_key,
    )


@router.delete("/{key_id}/revoke", status_code=204)
def revoke_api_key(
    key_id: str,
    request: Request,
    x_nonce_token: str = Header(description="Fresh UUID4 nonce — get one by running: python -c \"import uuid; print(uuid.uuid4())\""),
    db: Session = Depends(get_db),
    current_user: User = Depends(zone3_privileged),
):
    """
    Zone 3 — privileged + replay detection.
    Requires JWT + fresh X-Nonce-Token header.
    Returns 204 No Content on success.
    """
    ip = get_client_ip(request)
    user_agent = request.headers.get("User-Agent", "")
    revoke_key(key_id, current_user, db, ip, user_agent)