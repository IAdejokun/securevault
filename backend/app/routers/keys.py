from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.dependencies import get_client_ip, zone2_authenticated
from app.db.session import get_db
from app.models.user import User
from app.schemas.api_key import ApiKeyCreateRequest, ApiKeyCreateResponse, ApiKeyResponse
from app.services.key_service import create_key, get_key, list_keys

router = APIRouter()


@router.post("", response_model=ApiKeyCreateResponse, status_code=201)
def create_api_key(
    payload: ApiKeyCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(zone2_authenticated),
):
    """
    Zone 2 — authenticated.
    Create a new API key. The raw key is returned exactly once in this response.
    """
    ip = get_client_ip(request)
    user_agent = request.headers.get("User-Agent", "")
    result = create_key(payload, current_user, db, ip, user_agent)

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


@router.get("", response_model=list[ApiKeyResponse])
def list_api_keys(
    db: Session = Depends(get_db),
    current_user: User = Depends(zone2_authenticated),
):
    """
    Zone 2 — authenticated.
    List all active API keys for the current user.
    """
    keys = list_keys(current_user, db)
    return [
        ApiKeyResponse(
            id=str(k.id),
            name=k.name,
            display_key=k.display_key,
            zone=k.zone,
            is_active=k.is_active,
            usage_count=k.usage_count,
            created_at=k.created_at,
            rotated_at=k.rotated_at,
            expires_at=k.expires_at,
        )
        for k in keys
    ]


@router.get("/{key_id}", response_model=ApiKeyResponse)
def get_api_key(
    key_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(zone2_authenticated),
):
    """
    Zone 2 — authenticated.
    Get a single API key by ID.
    """
    key = get_key(key_id, current_user, db)
    return ApiKeyResponse(
        id=str(key.id),
        name=key.name,
        display_key=key.display_key,
        zone=key.zone,
        is_active=key.is_active,
        usage_count=key.usage_count,
        created_at=key.created_at,
        rotated_at=key.rotated_at,
        expires_at=key.expires_at,
    )