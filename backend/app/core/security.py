import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt
from passlib.context import CryptContext

from app.config import get_settings

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def generate_raw_key(prefix: str = "sv_live_") -> str:
    return f"{prefix}{secrets.token_hex(20)}"


def hash_api_key(raw_key: str) -> str:
    return pwd_context.hash(raw_key)


def verify_api_key(raw_key: str, stored_hash: str) -> bool:
    return pwd_context.verify(raw_key, stored_hash)


def extract_key_parts(raw_key: str) -> tuple[str, str]:
    """
    Returns (prefix, last_four). Prefix is everything up to and
    including the last underscore. Falls back to first 7 chars
    if there's no underscore.
    """
    if '_' in raw_key:
        last_underscore = raw_key.rfind('_')
        prefix = raw_key[:last_underscore + 1]
    else:
        prefix = raw_key[:7]
    last_four = raw_key[-4:]
    return prefix, last_four


def _build_token(subject: str, token_type: str, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: str) -> str:
    return _build_token(
        subject=user_id,
        token_type="access",
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )


def create_refresh_token(user_id: str) -> str:
    return _build_token(
        subject=user_id,
        token_type="refresh",
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
    )


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )


def generate_nonce() -> str:
    return str(uuid.uuid4())


def nonce_expires_at() -> datetime:
    return datetime.now(timezone.utc) + timedelta(seconds=settings.nonce_window_seconds)