from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.api_key import ApiKey
    from app.models.audit_log import AuditLog

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship


from app.db.base import Base


class EventType:
    AUTH_REGISTER      = "auth.register"
    AUTH_LOGIN_SUCCESS = "auth.login.success"
    AUTH_LOGIN_FAILURE = "auth.login.failure"
    AUTH_TOKEN_REFRESH = "auth.token.refresh"
    KEY_CREATED        = "key.created"
    KEY_ROTATED        = "key.rotated"
    KEY_REVOKED        = "key.revoked"
    KEY_EXPIRED        = "key.expired"
    ZONE_REJECTED      = "zone.rejected"
    REPLAY_DETECTED    = "replay.detected"
    ANOMALY_FLAGGED    = "anomaly.flagged"
    KEY_VERIFIED       = "key.verified"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )
    api_key_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("api_keys.id"), nullable=True, index=True
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    zone: Mapped[str] = mapped_column(String(20), nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    meta: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    anomaly_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    user: Mapped[Optional["User"]] = relationship("User", back_populates="audit_logs")
    api_key: Mapped[Optional["ApiKey"]] = relationship(
        "ApiKey", back_populates="audit_logs"
    )

    def __repr__(self) -> str:
        return f"<AuditLog event={self.event_type} zone={self.zone}>"