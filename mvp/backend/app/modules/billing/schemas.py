"""
Billing schemas for request/response validation.
"""

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class PlanRead(BaseModel):
    """Plan response schema."""
    id: UUID
    name: str
    display_name: str
    max_transcriptions_month: int
    max_audio_minutes_month: int
    max_ai_calls_month: int
    price_cents: int
    is_active: bool

    class Config:
        from_attributes = True


class QuotaRead(BaseModel):
    """User quota response schema with usage and limits."""
    plan: PlanRead
    transcriptions_used: int
    transcriptions_limit: int
    audio_minutes_used: int
    audio_minutes_limit: int
    ai_calls_used: int
    ai_calls_limit: int
    period_start: date
    period_end: date
    usage_percent: float

    class Config:
        from_attributes = True
