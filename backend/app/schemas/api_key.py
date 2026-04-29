from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


class ApiKeyCreateRequest(BaseModel):
    name: str
    zone: str = "authenticated"
    expires_at: Optional[datetime] = None


class ApiKeyCreateResponse(BaseModel):
    id: str
    name: str
    prefix: str
    last_four: str
    zone: str
    display_key: str
    is_active: bool
    usage_count: int
    created_at: datetime
    expires_at: Optional[datetime]
    raw_key: str  # shown ONCE — never returned again after this

    model_config = {"from_attributes": True}

    @field_validator("id", mode="before")
    @classmethod
    def coerce_id(cls, v) -> str:
        return str(v)


class ApiKeyResponse(BaseModel):
    id: str
    name: str
    display_key: str
    zone: str
    is_active: bool
    usage_count: int
    created_at: datetime
    rotated_at: Optional[datetime]
    expires_at: Optional[datetime]

    model_config = {"from_attributes": True}

    @field_validator("id", mode="before")
    @classmethod
    def coerce_id(cls, v) -> str:
        return str(v)