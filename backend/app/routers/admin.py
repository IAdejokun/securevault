from __future__ import annotations
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.dependencies import admin_required
from app.db.session import get_db
from app.models.api_key import ApiKey
from app.models.audit_log import AuditLog
from app.models.user import User

router = APIRouter()


@router.get("/stats")
def get_system_stats(
    db: Session = Depends(get_db),
    _: User = Depends(admin_required),
):
    """
    System-wide aggregates. The dashboard's KPI strip pulls from here.
    """
    now = datetime.now(timezone.utc)
    last_24h = now - timedelta(hours=24)

    total_users = db.query(func.count(User.id)).scalar()
    total_keys = db.query(func.count(ApiKey.id)).scalar()
    active_keys = db.query(func.count(ApiKey.id)).filter(ApiKey.is_active == True).scalar()

    events_24h = (
        db.query(func.count(AuditLog.id))
        .filter(AuditLog.created_at >= last_24h)
        .scalar()
    )
    replay_attempts = (
        db.query(func.count(AuditLog.id))
        .filter(AuditLog.event_type == "replay.detected")
        .scalar()
    )
    failed_logins_24h = (
        db.query(func.count(AuditLog.id))
        .filter(
            AuditLog.event_type == "auth.login.failure",
            AuditLog.created_at >= last_24h,
        )
        .scalar()
    )

    return {
        "total_users": total_users,
        "total_keys": total_keys,
        "active_keys": active_keys,
        "events_24h": events_24h,
        "replay_attempts": replay_attempts,
        "failed_logins_24h": failed_logins_24h,
    }


@router.get("/events-by-type")
def events_by_type(
    db: Session = Depends(get_db),
    _: User = Depends(admin_required),
):
    """
    Returns counts grouped by event_type for the last 7 days.
    Used to render the events-by-type chart.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    rows = (
        db.query(AuditLog.event_type, func.count(AuditLog.id).label("count"))
        .filter(AuditLog.created_at >= cutoff)
        .group_by(AuditLog.event_type)
        .order_by(func.count(AuditLog.id).desc())
        .all()
    )
    return [{"event_type": r[0], "count": r[1]} for r in rows]


@router.get("/recent-events")
def recent_events(
    limit: int = 50,
    db: Session = Depends(get_db),
    _: User = Depends(admin_required),
):
    """
    Latest events across ALL users — system-wide live feed.
    """
    logs = (
        db.query(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .limit(min(limit, 200))
        .all()
    )
    return [
        {
            "id": str(log.id),
            "event_type": log.event_type,
            "zone": log.zone,
            "ip_address": log.ip_address,
            "user_id": str(log.user_id) if log.user_id else None,
            "anomaly_score": log.anomaly_score,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]