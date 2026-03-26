"""
Audit module schemas.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AuditEntryRead(BaseModel):
    id: UUID
    tenant_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    details_json: Optional[str] = None
    old_value_json: Optional[str] = None
    new_value_json: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    record_hash: str
    previous_hash: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AuditQueryResponse(BaseModel):
    entries: list[AuditEntryRead]
    total: int
    limit: int
    offset: int


class AuditVerifyResponse(BaseModel):
    verified: int
    valid: bool
    first_broken_at: Optional[str] = None
    details: str


class AuditActionCount(BaseModel):
    action: str
    count: int


class AuditResourceCount(BaseModel):
    resource_type: str
    count: int


class AuditUserCount(BaseModel):
    user_id: str
    count: int


class AuditDayCount(BaseModel):
    date: Optional[str] = None
    count: int


class AuditStatsResponse(BaseModel):
    total_events: int
    period_days: int
    by_action: list[AuditActionCount]
    by_resource: list[AuditResourceCount]
    by_user: list[AuditUserCount]
    by_day: list[AuditDayCount]
