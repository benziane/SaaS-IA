"""
AI Monitoring Service - Langfuse-style LLM observability.

Provides quality scoring, latency tracking, cost analytics,
provider comparison, and prompt effectiveness monitoring.

Built on top of the existing cost_tracker (ai_usage_logs table).
"""

import json
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

import structlog
from sqlalchemy import func, text
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.cost_tracking import AIUsageLog

logger = structlog.get_logger()


class AIMonitoringService:
    """Service for LLM observability and monitoring."""

    @staticmethod
    async def get_dashboard(
        user_id: UUID, session: AsyncSession, days: int = 7,
    ) -> dict:
        """Get comprehensive monitoring dashboard data."""
        since = datetime.utcnow() - timedelta(days=days)

        # Total calls
        total = (await session.execute(
            select(func.count()).select_from(AIUsageLog)
            .where(AIUsageLog.user_id == user_id, AIUsageLog.created_at >= since)
        )).scalar_one()

        # Success rate
        success_count = (await session.execute(
            select(func.count()).select_from(AIUsageLog)
            .where(AIUsageLog.user_id == user_id, AIUsageLog.created_at >= since, AIUsageLog.success == True)
        )).scalar_one()

        # Total tokens & cost
        agg = await session.execute(
            select(
                func.coalesce(func.sum(AIUsageLog.total_tokens), 0),
                func.coalesce(func.sum(AIUsageLog.cost_cents), 0),
                func.coalesce(func.avg(AIUsageLog.latency_ms), 0),
            ).where(AIUsageLog.user_id == user_id, AIUsageLog.created_at >= since)
        )
        row = agg.one()
        total_tokens = int(row[0])
        total_cost_cents = float(row[1])
        avg_latency = float(row[2])

        # Per-provider stats
        provider_stats = await session.execute(
            select(
                AIUsageLog.provider,
                func.count().label("calls"),
                func.coalesce(func.sum(AIUsageLog.total_tokens), 0).label("tokens"),
                func.coalesce(func.sum(AIUsageLog.cost_cents), 0).label("cost"),
                func.coalesce(func.avg(AIUsageLog.latency_ms), 0).label("avg_latency"),
                func.sum(func.cast(AIUsageLog.success, type_=func.count().type)).label("successes"),
            ).where(AIUsageLog.user_id == user_id, AIUsageLog.created_at >= since)
            .group_by(AIUsageLog.provider)
        )
        providers = []
        for r in provider_stats:
            calls = int(r[1])
            providers.append({
                "provider": r[0],
                "calls": calls,
                "tokens": int(r[2]),
                "cost_cents": round(float(r[3]), 2),
                "avg_latency_ms": round(float(r[4])),
                "success_rate": round(int(r[5] or 0) / max(calls, 1) * 100, 1),
            })

        # Per-module stats
        module_stats = await session.execute(
            select(
                AIUsageLog.module,
                func.count().label("calls"),
                func.coalesce(func.sum(AIUsageLog.cost_cents), 0).label("cost"),
            ).where(AIUsageLog.user_id == user_id, AIUsageLog.created_at >= since)
            .group_by(AIUsageLog.module)
            .order_by(func.count().desc())
            .limit(10)
        )
        modules = [{"module": r[0], "calls": int(r[1]), "cost_cents": round(float(r[2]), 2)} for r in module_stats]

        # Recent errors
        errors = await session.execute(
            select(AIUsageLog)
            .where(AIUsageLog.user_id == user_id, AIUsageLog.success == False, AIUsageLog.created_at >= since)
            .order_by(AIUsageLog.created_at.desc())
            .limit(10)
        )
        recent_errors = [
            {"provider": e.provider, "module": e.module, "action": e.action, "error": e.error, "created_at": e.created_at.isoformat()}
            for e in errors.scalars().all()
        ]

        # Daily trend (last N days)
        daily = await session.execute(
            text("""
                SELECT DATE(created_at) as day, COUNT(*) as calls,
                       COALESCE(SUM(total_tokens), 0) as tokens,
                       COALESCE(SUM(cost_cents), 0) as cost
                FROM ai_usage_logs
                WHERE user_id = :uid AND created_at >= :since
                GROUP BY DATE(created_at)
                ORDER BY day
            """),
            {"uid": str(user_id), "since": since.isoformat()},
        )
        daily_trend = [{"day": str(r[0]), "calls": int(r[1]), "tokens": int(r[2]), "cost_cents": round(float(r[3]), 2)} for r in daily]

        return {
            "period_days": days,
            "total_calls": total,
            "success_rate": round(success_count / max(total, 1) * 100, 1),
            "total_tokens": total_tokens,
            "total_cost_cents": round(total_cost_cents, 2),
            "total_cost_usd": round(total_cost_cents / 100, 4),
            "avg_latency_ms": round(avg_latency),
            "providers": providers,
            "modules": modules,
            "recent_errors": recent_errors,
            "daily_trend": daily_trend,
        }

    @staticmethod
    async def get_provider_comparison(
        user_id: UUID, session: AsyncSession, days: int = 30,
    ) -> list[dict]:
        """Compare providers by quality, speed, and cost."""
        since = datetime.utcnow() - timedelta(days=days)

        result = await session.execute(
            select(
                AIUsageLog.provider,
                AIUsageLog.model,
                func.count().label("calls"),
                func.avg(AIUsageLog.latency_ms).label("avg_latency"),
                func.min(AIUsageLog.latency_ms).label("min_latency"),
                func.max(AIUsageLog.latency_ms).label("max_latency"),
                func.sum(AIUsageLog.cost_cents).label("total_cost"),
                func.avg(AIUsageLog.cost_cents).label("avg_cost_per_call"),
                func.avg(AIUsageLog.total_tokens).label("avg_tokens"),
            ).where(AIUsageLog.user_id == user_id, AIUsageLog.created_at >= since)
            .group_by(AIUsageLog.provider, AIUsageLog.model)
            .order_by(func.count().desc())
        )

        return [
            {
                "provider": r[0], "model": r[1], "calls": int(r[2]),
                "avg_latency_ms": round(float(r[3] or 0)),
                "min_latency_ms": int(r[4] or 0),
                "max_latency_ms": int(r[5] or 0),
                "total_cost_cents": round(float(r[6] or 0), 2),
                "avg_cost_per_call": round(float(r[7] or 0), 4),
                "avg_tokens": round(float(r[8] or 0)),
            }
            for r in result
        ]

    @staticmethod
    async def get_recent_traces(
        user_id: UUID, session: AsyncSession,
        module: Optional[str] = None, limit: int = 50,
    ) -> list[dict]:
        """Get recent AI call traces (Langfuse-style)."""
        query = select(AIUsageLog).where(AIUsageLog.user_id == user_id)
        if module:
            query = query.where(AIUsageLog.module == module)
        query = query.order_by(AIUsageLog.created_at.desc()).limit(limit)

        result = await session.execute(query)
        return [
            {
                "id": str(t.id), "provider": t.provider, "model": t.model,
                "module": t.module, "action": t.action,
                "input_tokens": t.input_tokens, "output_tokens": t.output_tokens,
                "total_tokens": t.total_tokens, "cost_cents": round(t.cost_cents, 4),
                "latency_ms": t.latency_ms, "success": t.success, "error": t.error,
                "created_at": t.created_at.isoformat(),
            }
            for t in result.scalars().all()
        ]
