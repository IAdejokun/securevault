from __future__ import annotations
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: str
    event_type: str
    zone: str
    ip_address: Optional[str]
    anomaly_score: Optional[int]
    meta: Optional[dict[str, Any]]
    created_at: datetime

    model_config = {"from_attributes": True}