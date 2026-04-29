from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.dependencies import get_client_ip, zone1_public, zone2_authenticated
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import login_user, refresh_tokens, register_user

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(
    payload: RegisterRequest,
    request: Request,
    db: Session = Depends(get_db),
    ctx: dict = Depends(zone1_public),
):
    """
    Zone 1 — public.
    Creates a new user account and returns access + refresh tokens.
    """
    return register_user(payload, db, ctx["ip"], ctx["user_agent"])


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
    ctx: dict = Depends(zone1_public),
):
    """
    Zone 1 — public.
    Authenticates a user and returns access + refresh tokens.
    """
    return login_user(payload, db, ctx["ip"], ctx["user_agent"])


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    payload: RefreshRequest,
    db: Session = Depends(get_db),
):
    """
    Zone 1 — public.
    Exchanges a valid refresh token for a new token pair.
    """
    return refresh_tokens(payload.refresh_token, db)


@router.get("/me", response_model=UserResponse)
def me(
    current_user: User = Depends(zone2_authenticated),
):
    """
    Zone 2 — authenticated.
    Returns the profile of the currently authenticated user.
    """
    return current_user