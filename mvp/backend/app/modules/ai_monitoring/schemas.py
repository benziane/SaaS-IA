"""AI Monitoring schemas."""
from pydantic import BaseModel


class MonitoringDashboard(BaseModel):
    period_days: int
    total_calls: int
    success_rate: float
    total_tokens: int
    total_cost_cents: float
    total_cost_usd: float
    avg_latency_ms: int
    providers: list[dict]
    modules: list[dict]
    recent_errors: list[dict]
    daily_trend: list[dict]
