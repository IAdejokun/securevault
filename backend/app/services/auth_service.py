from __future__ import annotations

from fastapi import HTTPException, status
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.audit_log import AuditLog, EventType
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse


def register_user(
    payload: RegisterRequest,
    db: Session,
    ip: str,
    user_agent: str,
) -> TokenResponse:
    # Check email is not already taken
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    # Create the user
    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.flush()  # gets user.id without committing yet

    # Write audit event
    db.add(AuditLog(
        user_id=user.id,
        event_type=EventType.AUTH_REGISTER,
        zone="public",
        ip_address=ip,
        user_agent=user_agent,
    ))
    db.commit()

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


def login_user(
    payload: LoginRequest,
    db: Session,
    ip: str,
    user_agent: str,
) -> TokenResponse:
    user = db.query(User).filter(User.email == payload.email).first()

    # Deliberately vague error — don't reveal whether email exists
    invalid_credentials = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password",
    )

    if not user or not user.is_active:
        # Still call verify_password with a dummy hash to prevent timing attacks
        verify_password(payload.password, "$2b$12$dummy_hash_to_prevent_timing_attack")
        db.add(AuditLog(
            event_type=EventType.AUTH_LOGIN_FAILURE,
            zone="public",
            ip_address=ip,
            user_agent=user_agent,
            meta={"reason": "user_not_found", "email": payload.email},
        ))
        db.commit()
        raise invalid_credentials

    if not verify_password(payload.password, user.password_hash):
        db.add(AuditLog(
            user_id=user.id,
            event_type=EventType.AUTH_LOGIN_FAILURE,
            zone="public",
            ip_address=ip,
            user_agent=user_agent,
            meta={"reason": "wrong_password"},
        ))
        db.commit()
        raise invalid_credentials

    db.add(AuditLog(
        user_id=user.id,
        event_type=EventType.AUTH_LOGIN_SUCCESS,
        zone="public",
        ip_address=ip,
        user_agent=user_agent,
    ))
    db.commit()

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


def refresh_tokens(
    refresh_token: str,
    db: Session,
) -> TokenResponse:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token",
    )

    try:
        payload = decode_token(refresh_token)
    except JWTError:
        raise credentials_error

    if payload.get("type") != "refresh":
        raise credentials_error

    user_id: str | None = payload.get("sub")
    if not user_id:
        raise credentials_error

    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise credentials_error

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )