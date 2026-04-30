from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.security import decode_token
from app.db.session import get_db
from app.models.nonce import Nonce
from app.models.user import User
from app.core.security import nonce_expires_at

settings = get_settings()
bearer_scheme = HTTPBearer(auto_error=False)


# ── Helper: extract real IP ───────────────────────────────────────────────────
def get_client_ip(request: Request) -> str:
    """
    Respect X-Forwarded-For when behind Render/Railway's reverse proxy.
    Falls back to direct connection IP.
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# ── Helper: pull user from JWT ────────────────────────────────────────────────
def _get_user_from_token(
    credentials: HTTPAuthorizationCredentials | None,
    db: Session,
) -> User:
    """
    Shared logic used by Zone 2 and Zone 3 gates.
    Decodes the JWT, validates it is an access token, and loads the user.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token type invalid — access token required",
        )

    user_id: str | None = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token subject missing",
        )

    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or deactivated",
        )

    return user


# ══════════════════════════════════════════════════════════════════════════════
# ZONE 1 — Public gate
# No auth required. Applies rate-limiting headers only.
# Endpoints: /auth/register, /auth/login
# ══════════════════════════════════════════════════════════════════════════════
def zone1_public(request: Request) -> dict:
    """
    Zone 1 dependency. Returns request context dict.
    Add rate-limiting middleware here in a future sprint.
    """
    return {
        "zone": "public",
        "ip": get_client_ip(request),
        "user_agent": request.headers.get("User-Agent", ""),
    }


# ══════════════════════════════════════════════════════════════════════════════
# ZONE 2 — Authenticated-secure gate
# Requires valid JWT access token.
# Endpoints: /keys (CRUD), /audit (read logs)
# ══════════════════════════════════════════════════════════════════════════════
def zone2_authenticated(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Zone 2 dependency. Returns the authenticated User ORM object.
    Inject with: current_user: User = Depends(zone2_authenticated)
    """
    return _get_user_from_token(credentials, db)


# ══════════════════════════════════════════════════════════════════════════════
# ZONE 3 — Privileged + replay-detection gate
# Requires valid JWT AND a fresh, unseen nonce in X-Nonce-Token header.
# Endpoints: /privileged (rotate, revoke)
#
# This is the direct implementation of NIST SP 800-207 §3.3:
# "Each request must be independently authenticated and authorised."
# The nonce ensures each privileged action is cryptographically unique.
# ══════════════════════════════════════════════════════════════════════════════
def zone3_privileged(
    request: Request,
    x_nonce_token: str | None = Header(default=None),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Zone 3 dependency. Returns the authenticated User ORM object.
    Raises 400 if nonce header is missing.
    Raises 409 if nonce has been seen before (replay attack).
    Inject with: current_user: User = Depends(zone3_privileged)
    """
    # Step 1: JWT must be valid (same as Zone 2)
    user = _get_user_from_token(credentials, db)

    # Step 2: Nonce header must be present
    if not x_nonce_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Nonce-Token header required for privileged operations",
        )

    # Step 3: Nonce must not have been seen before (replay check)
    existing = db.query(Nonce).filter(Nonce.value == x_nonce_token).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Replay attack detected — nonce already used",
        )

    # Step 4: Store the nonce so future requests with same nonce are rejected
    new_nonce = Nonce(
        value=x_nonce_token,
        expires_at=nonce_expires_at(),
    )
    db.add(new_nonce)
    db.commit()

    return user

def admin_required(
    current_user: User = Depends(zone2_authenticated),
) -> User:
    """
    Admin gate. Builds on zone2 (JWT required) and additionally
    checks the is_admin flag. Returns 403 if the user is not an admin.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user