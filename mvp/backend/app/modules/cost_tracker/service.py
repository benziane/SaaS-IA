"""
Cost tracker service - Analytics, recommendations, alerts, and export.
"""

from datetime import date, datetime, timedelta
from uuid import UUID

import structlog
from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.cost_tracking import AIUsageLog
from app.modules.cost_tracker.pricing import PRICING

logger = structlog.get_logger()


class CostTrackerService:
    """Service for cost analytics and optimization."""

    @staticmethod
    async def get_dashboard(
        user_id: UUID,
        days: int,
        session: AsyncSession,
    ) -> dict:
        """Build cost dashboard with summary, breakdowns, and recommendations."""
        period_start = date.today() - timedelta(days=days)
        period_end = date.today()

        base_filter = [
            AIUsageLog.user_id == user_id,
            AIUsageLog.created_at >= datetime.combine(period_start, datetime.min.time()),
        ]

        # Summary
        summary_result = await session.execute(
            select(
                func.count().label("total_calls"),
                func.coalesce(func.sum(AIUsageLog.total_tokens), 0).label("total_tokens"),
                func.coalesce(func.sum(AIUsageLog.cost_cents), 0).label("total_cost"),
                func.coalesce(func.avg(AIUsageLog.latency_ms), 0).label("avg_latency"),
            ).where(*base_filter)
        )
        summary_row = summary_result.one()

        summary = {
            "total_cost_cents": round(float(summary_row.total_cost), 2),
            "total_tokens": int(summary_row.total_tokens),
            "total_calls": int(summary_row.total_calls),
            "avg_latency_ms": round(float(summary_row.avg_latency), 1),
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
        }

        # By provider
        provider_result = await session.execute(
            select(
                AIUsageLog.provider,
                AIUsageLog.model,
                func.count().label("calls"),
                func.coalesce(func.sum(AIUsageLog.total_tokens), 0).label("tokens"),
                func.coalesce(func.sum(AIUsageLog.cost_cents), 0).label("cost"),
                func.coalesce(func.avg(AIUsageLog.latency_ms), 0).label("latency"),
                func.sum(func.cast(AIUsageLog.success, type_=func.coalesce.type)).label("successes"),
            )
            .where(*base_filter)
            .group_by(AIUsageLog.provider, AIUsageLog.model)
            .order_by(func.sum(AIUsageLog.cost_cents).desc())
        )

        by_provider = []
        for row in provider_result.all():
            total_calls = int(row.calls)
            pricing = PRICING.get(row.provider, {})
            by_provider.append({
                "provider": row.provider,
                "model": row.model or row.provider,
                "total_calls": total_calls,
                "total_tokens": int(row.tokens),
                "total_cost_cents": round(float(row.cost), 2),
                "avg_latency_ms": round(float(row.latency), 1),
                "success_rate": round(float(row.successes or total_calls) / total_calls * 100, 1) if total_calls > 0 else 100.0,
                "label": pricing.get("label", "Unknown"),
            })

        # By module
        module_result = await session.execute(
            select(
                AIUsageLog.module,
                func.count().label("calls"),
                func.coalesce(func.sum(AIUsageLog.total_tokens), 0).label("tokens"),
                func.coalesce(func.sum(AIUsageLog.cost_cents), 0).label("cost"),
            )
            .where(*base_filter)
            .group_by(AIUsageLog.module)
            .order_by(func.sum(AIUsageLog.cost_cents).desc())
        )

        by_module = [
            {
                "module": row.module,
                "total_calls": int(row.calls),
                "total_tokens": int(row.tokens),
                "total_cost_cents": round(float(row.cost), 2),
            }
            for row in module_result.all()
        ]

        # Recent calls
        recent_result = await session.execute(
            select(AIUsageLog)
            .where(*base_filter)
            .order_by(AIUsageLog.created_at.desc())
            .limit(20)
        )
        recent = [
            {
                "provider": r.provider,
                "model": r.model,
                "module": r.module,
                "action": r.action,
                "total_tokens": r.total_tokens,
                "cost_cents": r.cost_cents,
                "latency_ms": r.latency_ms,
                "success": r.success,
                "created_at": r.created_at.isoformat(),
            }
            for r in recent_result.scalars().all()
        ]

        # Recommendations
        recommendations = CostTrackerService._generate_recommendations(
            by_provider, by_module, summary
        )

        return {
            "summary": summary,
            "by_provider": by_provider,
            "by_module": by_module,
            "recommendations": recommendations,
            "recent_calls": recent,
        }

    @staticmethod
    async def get_alerts(
        user_id: UUID,
        session: AsyncSession,
    ) -> list[dict]:
        """
        Get budget alerts based on spending patterns.

        Checks:
        - Daily spending vs 30-day average (alert if >2x)
        - Monthly spending trend (increasing vs decreasing)
        - Most expensive provider with cheaper alternative
        """
        alerts: list[dict] = []
        today_start = datetime.combine(date.today(), datetime.min.time())

        # --- Today's spending ---
        today_result = await session.execute(
            select(
                func.coalesce(func.sum(AIUsageLog.cost_cents), 0).label("cost"),
                func.count().label("calls"),
            ).where(
                AIUsageLog.user_id == user_id,
                AIUsageLog.created_at >= today_start,
            )
        )
        today_row = today_result.one()
        today_cost = float(today_row.cost)
        today_calls = int(today_row.calls)

        # --- 30-day daily average ---
        month_start = today_start - timedelta(days=30)
        month_result = await session.execute(
            select(
                func.coalesce(func.sum(AIUsageLog.cost_cents), 0).label("cost"),
                func.count().label("calls"),
            ).where(
                AIUsageLog.user_id == user_id,
                AIUsageLog.created_at >= month_start,
                AIUsageLog.created_at < today_start,
            )
        )
        month_row = month_result.one()
        month_cost = float(month_row.cost)
        month_calls = int(month_row.calls)
        daily_avg_cost = month_cost / 30 if month_cost > 0 else 0
        daily_avg_calls = month_calls / 30 if month_calls > 0 else 0

        # Alert: daily spending spike
        if daily_avg_cost > 0 and today_cost > daily_avg_cost * 2:
            alerts.append({
                "level": "warning",
                "title": "Daily spending spike",
                "message": (
                    f"Today's spending ({today_cost:.2f} cents) is "
                    f"{today_cost / daily_avg_cost:.1f}x your 30-day daily average "
                    f"({daily_avg_cost:.2f} cents)."
                ),
                "metric": "daily_cost",
                "current_value": round(today_cost, 2),
                "threshold_value": round(daily_avg_cost * 2, 2),
            })

        # Alert: high call volume today
        if daily_avg_calls > 0 and today_calls > daily_avg_calls * 3:
            alerts.append({
                "level": "warning",
                "title": "High call volume",
                "message": (
                    f"Today's AI calls ({today_calls}) are "
                    f"{today_calls / daily_avg_calls:.1f}x your daily average "
                    f"({daily_avg_calls:.0f} calls)."
                ),
                "metric": "daily_calls",
                "current_value": today_calls,
                "threshold_value": round(daily_avg_calls * 3),
            })

        # --- Monthly trend (this week vs last week) ---
        this_week_start = today_start - timedelta(days=7)
        last_week_start = today_start - timedelta(days=14)

        this_week_result = await session.execute(
            select(
                func.coalesce(func.sum(AIUsageLog.cost_cents), 0).label("cost"),
            ).where(
                AIUsageLog.user_id == user_id,
                AIUsageLog.created_at >= this_week_start,
            )
        )
        this_week_cost = float(this_week_result.scalar_one())

        last_week_result = await session.execute(
            select(
                func.coalesce(func.sum(AIUsageLog.cost_cents), 0).label("cost"),
            ).where(
                AIUsageLog.user_id == user_id,
                AIUsageLog.created_at >= last_week_start,
                AIUsageLog.created_at < this_week_start,
            )
        )
        last_week_cost = float(last_week_result.scalar_one())

        if last_week_cost > 0 and this_week_cost > last_week_cost * 1.5:
            pct_increase = ((this_week_cost - last_week_cost) / last_week_cost) * 100
            alerts.append({
                "level": "critical" if pct_increase > 200 else "warning",
                "title": "Weekly spending trend increasing",
                "message": (
                    f"This week's spending ({this_week_cost:.2f} cents) is "
                    f"{pct_increase:.0f}% higher than last week ({last_week_cost:.2f} cents)."
                ),
                "metric": "weekly_trend",
                "current_value": round(this_week_cost, 2),
                "threshold_value": round(last_week_cost, 2),
            })

        # --- Most expensive provider recommendation ---
        provider_result = await session.execute(
            select(
                AIUsageLog.provider,
                func.coalesce(func.sum(AIUsageLog.cost_cents), 0).label("cost"),
                func.count().label("calls"),
            )
            .where(
                AIUsageLog.user_id == user_id,
                AIUsageLog.created_at >= month_start,
            )
            .group_by(AIUsageLog.provider)
            .order_by(func.sum(AIUsageLog.cost_cents).desc())
        )
        provider_rows = provider_result.all()

        if provider_rows:
            top = provider_rows[0]
            top_cost = float(top.cost)
            if top.provider == "claude" and top_cost > 5:
                alerts.append({
                    "level": "info",
                    "title": "Cost optimization available",
                    "message": (
                        f"Claude accounts for {top_cost:.2f} cents in the last 30 days "
                        f"({int(top.calls)} calls). Consider switching non-critical tasks "
                        f"to Gemini (free) or Groq (very cheap) to reduce costs."
                    ),
                    "metric": "provider_optimization",
                    "current_value": round(top_cost, 2),
                    "threshold_value": 0,
                })

        # --- No alerts is good news ---
        if not alerts:
            alerts.append({
                "level": "info",
                "title": "Spending normal",
                "message": "Your AI spending is within normal patterns. No alerts at this time.",
                "metric": "all_clear",
                "current_value": round(today_cost, 2),
                "threshold_value": 0,
            })

        return alerts

    @staticmethod
    async def get_usage_logs(
        user_id: UUID,
        days: int,
        session: AsyncSession,
    ) -> list[AIUsageLog]:
        """Retrieve raw usage logs for export."""
        period_start = datetime.combine(
            date.today() - timedelta(days=days),
            datetime.min.time(),
        )
        result = await session.execute(
            select(AIUsageLog)
            .where(
                AIUsageLog.user_id == user_id,
                AIUsageLog.created_at >= period_start,
            )
            .order_by(AIUsageLog.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    def _generate_recommendations(
        by_provider: list[dict],
        by_module: list[dict],
        summary: dict,
    ) -> list[dict]:
        """Generate cost optimization recommendations."""
        recs = []

        # Check if using expensive providers when cheaper ones available
        claude_usage = next((p for p in by_provider if p["provider"] == "claude"), None)
        gemini_usage = next((p for p in by_provider if p["provider"] == "gemini"), None)

        if claude_usage and claude_usage["total_cost_cents"] > 10:
            savings = claude_usage["total_cost_cents"] * 0.9
            recs.append({
                "type": "switch_provider",
                "message": f"Switch from Claude to Gemini Flash for non-critical tasks. "
                          f"Claude costs {claude_usage['total_cost_cents']:.0f} cents this period. "
                          f"Gemini Flash is free for most use cases.",
                "potential_savings_cents": round(savings, 2),
            })

        groq_usage = next((p for p in by_provider if p["provider"] == "groq"), None)
        if groq_usage and claude_usage:
            if groq_usage["avg_latency_ms"] < claude_usage.get("avg_latency_ms", 9999) * 0.5:
                recs.append({
                    "type": "performance",
                    "message": f"Groq is {claude_usage.get('avg_latency_ms', 0) / max(groq_usage['avg_latency_ms'], 1):.1f}x faster than Claude. "
                              f"Consider Groq for latency-sensitive tasks.",
                    "potential_savings_cents": 0,
                })

        # High volume module
        for mod in by_module:
            if mod["total_calls"] > 50 and mod["total_cost_cents"] > 5:
                recs.append({
                    "type": "caching",
                    "message": f"Module '{mod['module']}' made {mod['total_calls']} calls. "
                              f"Consider caching frequent queries to reduce costs.",
                    "potential_savings_cents": round(mod["total_cost_cents"] * 0.3, 2),
                })

        if not recs:
            recs.append({
                "type": "info",
                "message": "Your AI usage is optimized. No recommendations at this time.",
                "potential_savings_cents": 0,
            })

        return recs
