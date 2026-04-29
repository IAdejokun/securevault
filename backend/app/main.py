from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db.init_db import create_tables
from app.db.session import SessionLocal

settings = get_settings()


def _purge_expired_nonces() -> None:
    """
    Delete nonces whose window has passed.
    Called on startup and should be scheduled every 60s in production
    (use APScheduler or a Celery beat task).
    """
    db = SessionLocal()
    try:
        from app.models.nonce import Nonce
        deleted = (
            db.query(Nonce)
            .filter(Nonce.expires_at < datetime.now(timezone.utc))
            .delete(synchronize_session=False)
        )
        db.commit()
        if deleted:
            print(f"[nonce cleanup] Purged {deleted} expired nonces")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    _purge_expired_nonces()  # clean any leftovers from last run
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="SecureVault",
        description="Zero Trust API Key Manager - NIST SP 800-207",
        version="0.1.0",
        lifespan=lifespan,
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None if settings.is_production else "/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    from app.routers import auth, keys, privileged, audit

    app.include_router(auth.router,       prefix="/api/v1/auth",       tags=["auth"])
    app.include_router(keys.router,       prefix="/api/v1/keys",       tags=["keys"])
    app.include_router(privileged.router, prefix="/api/v1/privileged", tags=["privileged"])
    app.include_router(audit.router,      prefix="/api/v1/audit",      tags=["audit"])

    @app.get("/health", tags=["health"])
    def health_check():
        return {"status": "ok", "env": settings.app_env}

    return app


app = create_app()