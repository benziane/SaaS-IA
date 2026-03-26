"""
Billing models: Plans and User Quotas for multi-tenancy.
"""

from datetime import UTC, date, datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class PlanName(str, Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class Plan(SQLModel, table=True):
    """Subscription plan with resource limits."""
    __tablename__ = "plans"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: PlanName = Field(unique=True, index=True)
    display_name: str = Field(max_length=50)
    max_transcriptions_month: int = Field(default=10)
    max_audio_minutes_month: int = Field(default=60)
    max_ai_calls_month: int = Field(default=50)
    price_cents: int = Field(default=0)
    stripe_price_id: Optional[str] = Field(default=None, max_length=100)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class UserQuota(SQLModel, table=True):
    """Tracks resource consumption per user per billing period."""
    __tablename__ = "user_quotas"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    plan_id: UUID = Field(foreign_key="plans.id")
    transcriptions_used: int = Field(default=0)
    audio_minutes_used: int = Field(default=0)
    ai_calls_used: int = Field(default=0)
    stripe_customer_id: Optional[str] = Field(default=None, max_length=100)
    stripe_subscription_id: Optional[str] = Field(default=None, max_length=100)
    period_start: date = Field(default_factory=date.today)
    period_end: date
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
