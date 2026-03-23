"""
Cost tracker schemas.
"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class UsageLogRead(BaseModel):
    provider: str
    model: str
    module: str
    action: str
    total_tokens: int
    cost_cents: float
    latency_ms: int
    success: bool
    created_at: datetime

    class Config:
        from_attributes = True


class CostSummary(BaseModel):
    total_cost_cents: float
    total_tokens: int
    total_calls: int
    avg_latency_ms: float
    period_start: date
    period_end: date


class ProviderCostBreakdown(BaseModel):
    provider: str
    model: str
    total_calls: int
    total_tokens: int
    total_cost_cents: float
    avg_latency_ms: float
    success_rate: float
    label: str


class ModuleCostBreakdown(BaseModel):
    module: str
    total_calls: int
    total_tokens: int
    total_cost_cents: float


class CostRecommendation(BaseModel):
    type: str
    message: str
    potential_savings_cents: float


class CostAlert(BaseModel):
    level: str = Field(description="Alert level: info, warning, critical")
    title: str
    message: str
    metric: str
    current_value: float
    threshold_value: float


class CostDashboard(BaseModel):
    summary: CostSummary
    by_provider: list[ProviderCostBreakdown]
    by_module: list[ModuleCostBreakdown]
    recommendations: list[CostRecommendation]
    recent_calls: list[UsageLogRead]
