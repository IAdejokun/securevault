import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings

settings = get_settings()

# ── Password hashing ──────────────────────────────────────────────────────────
# bcrypt with 12 rounds — industry default. Never change rounds without
# a migration plan: existing hashes keep their original round count.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── API key generation ────────────────────────────────────────────────────────
# Raw key is shown ONCE at creation, then discarded. Only the hash is stored.
# Format: sv_live_<40 random hex chars>
# e.g.  sv_live_3f8a2c...b4d1

def generate_raw_key(prefix: str = "sv_live_") -> str:
    """Generate a cryptographically secure raw API key."""
    return f"{prefix}{secrets.token_hex(20)}"


def hash_api_key(raw_key: str) -> str:
    """bcrypt-hash the raw key for storage. Same as password hashing."""
    return pwd_context.hash(raw_key)


def verify_api_key(raw_key: str, stored_hash: str) -> bool:
    return pwd_context.verify(raw_key, stored_hash)


def extract_key_parts(raw_key: str) -> tuple[str, str]:
    """
    Returns (prefix, last_four) from a raw key.
    Both are safe to store and display in the UI.
    e.g. "sv_live_3f8a2cb4d1" -> ("sv_live_", "b4d1")
    """
    prefix = raw_key[:8]        # "sv_live_"
    last_four = raw_key[-4:]    # last 4 chars of the random portion
    return prefix, last_four


# ── JWT ───────────────────────────────────────────────────────────────────────
# Two token types:
#   access  — short-lived (30 min), sent on every request in Authorization header
#   refresh — long-lived (7 days), sent only to /auth/refresh, stored in httpOnly cookie

def _build_token(subject: str, token_type: str, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,          # user UUID as string
        "type": token_type,      # "access" or "refresh"
        "iat": now,              # issued at
        "exp": now + expires_delta,
        "jti": str(uuid.uuid4()), # unique token ID — enables per-token revocation later
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
    """
    Decode and validate a JWT. Raises JWTError on any failure:
    - expired token
    - invalid signature
    - malformed token

    The caller decides what HTTP error to raise — this function is pure logic.
    """
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )


# ── Nonce generation + validation ─────────────────────────────────────────────
# Zone 3 replay-attack detection — NIST SP 800-207 §3.3
#
# Flow:
#   1. Client generates a UUID4 nonce and sends it in X-Nonce-Token header
#   2. Zone 3 gate checks the nonce against the nonces table
#   3. If seen before → 409 Conflict (replay detected)
#   4. If new → store it with expires_at = now + NONCE_WINDOW_SECONDS
#   5. Background job purges expired nonces every 60s
#
# Why UUID4 and not a counter?
#   Counters require the client to maintain state. UUID4 is stateless,
#   unpredictable, and collision probability is astronomically low (2^122).

def generate_nonce() -> str:
    """Generate a nonce for the client to send. Used in tests and the Angular interceptor."""
    return str(uuid.uuid4())


def nonce_expires_at() -> datetime:
    """Compute the expiry timestamp for a new nonce."""
    return datetime.now(timezone.utc) + timedelta(seconds=settings.nonce_window_seconds)