from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import zone2_authenticated
from app.db.session import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.audit import AuditLogResponse

router = APIRouter()


@router.get("", response_model=list[AuditLogResponse])
def list_audit_logs(
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(zone2_authenticated),
):
    """
    Zone 2 — authenticated.
    Returns paginated audit logs for the current user, newest first.
    """
    logs = (
        db.query(AuditLog)
        .filter(AuditLog.user_id == current_user.id)
        .order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [
        AuditLogResponse(
            id=str(log.id),
            event_type=log.event_type,
            zone=log.zone,
            ip_address=log.ip_address,
            anomaly_score=log.anomaly_score,
            meta=log.meta,
            created_at=log.created_at,
        )
        for log in logs
    ]