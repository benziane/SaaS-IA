"""
AI Monitoring Service - LLM observability with Langfuse integration.

Provides quality scoring, latency tracking, cost analytics,
provider comparison, and prompt effectiveness monitoring.

Built on top of the existing cost_tracker (ai_usage_logs table).
Langfuse integration adds LLM-specific observability (traces, generations, scores).
"""

import os
import json
from datetime import UTC, datetime, timedelta
from typing import Any, Optional
from uuid import UUID

import structlog
from sqlalchemy import func, text
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.cost_tracking import AIUsageLog

# Langfuse integration - auto-detection + graceful fallback
try:
    from langfuse import Langfuse
    HAS_LANGFUSE = True
except ImportError:
    HAS_LANGFUSE = False

logger = structlog.get_logger()

# Langfuse client singleton (lazy-loaded)
_langfuse_client: Optional[Any] = None


def _get_langfuse_client():
    """Get or create the Langfuse client singleton.

    Reads LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST from env.
    Returns None if Langfuse is not installed or not configured.
    """
    global _langfuse_client

    if not HAS_LANGFUSE:
        return None

    if _langfuse_client is not None:
        return _langfuse_client

    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY")
    secret_key = os.environ.get("LANGFUSE_SECRET_KEY")
    host = os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com")

    if not public_key or not secret_key:
        logger.debug("langfuse_not_configured", reason="missing LANGFUSE_PUBLIC_KEY or LANGFUSE_SECRET_KEY")
        return None

    try:
        _langfuse_client = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=host,
        )
        logger.info("langfuse_client_initialized", host=host)
        return _langfuse_client
    except Exception as e:
        logger.warning("langfuse_client_init_failed", error=str(e))
        return None


class AIMonitoringService:
    """Service for LLM observability and monitoring."""

    @staticmethod
    async def get_dashboard(
        user_id: UUID, session: AsyncSession, days: int = 7,
    ) -> dict:
        """Get comprehensive monitoring dashboard data."""
        since = datetime.now(UTC) - timedelta(days=days)

        # Query 1: Provider breakdown (derives totals + per-provider stats)
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
        total = 0
        success_count = 0
        total_tokens = 0
        total_cost_cents = 0.0
        latency_weighted_sum = 0.0
        for r in provider_stats:
            calls = int(r[1])
            tokens = int(r[2])
            cost = float(r[3])
            avg_lat = float(r[4])
            successes = int(r[5] or 0)
            total += calls
            success_count += successes
            total_tokens += tokens
            total_cost_cents += cost
            latency_weighted_sum += avg_lat * calls
            providers.append({
                "provider": r[0],
                "calls": calls,
                "tokens": tokens,
                "cost_cents": round(cost, 2),
                "avg_latency_ms": round(avg_lat),
                "success_rate": round(successes / max(calls, 1) * 100, 1),
            })
        avg_latency = latency_weighted_sum / max(total, 1)

        # Query 2: Module breakdown (top 10)
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

        # Query 3: Daily trend + recent errors (single raw SQL)
        combined = await session.execute(
            text("""
                WITH trend AS (
                    SELECT DATE(created_at) as day, COUNT(*) as calls,
                           COALESCE(SUM(total_tokens), 0) as tokens,
                           COALESCE(SUM(cost_cents), 0) as cost
                    FROM ai_usage_logs
                    WHERE user_id = :uid AND created_at >= :since
                    GROUP BY DATE(created_at)
                    ORDER BY day
                ),
                errors AS (
                    SELECT provider, module, action, error,
                           to_char(created_at, 'YYYY-MM-DD"T"HH24:MI:SS.US') as created_at_iso
                    FROM ai_usage_logs
                    WHERE user_id = :uid AND success = false AND created_at >= :since
                    ORDER BY created_at DESC
                    LIMIT 10
                )
                SELECT
                    COALESCE((SELECT json_agg(json_build_object(
                        'day', t.day::text,
                        'calls', t.calls,
                        'tokens', t.tokens,
                        'cost_cents', ROUND(t.cost::numeric, 2)
                    )) FROM trend t), '[]'::json) as daily_trend,
                    COALESCE((SELECT json_agg(json_build_object(
                        'provider', e.provider,
                        'module', e.module,
                        'action', e.action,
                        'error', e.error,
                        'created_at', e.created_at_iso
                    )) FROM errors e), '[]'::json) as recent_errors
            """),
            {"uid": str(user_id), "since": since.isoformat()},
        )
        combined_row = combined.one()
        raw_trend = combined_row[0] if combined_row[0] else []
        raw_errors = combined_row[1] if combined_row[1] else []
        if isinstance(raw_trend, str):
            raw_trend = json.loads(raw_trend)
        if isinstance(raw_errors, str):
            raw_errors = json.loads(raw_errors)
        daily_trend = [
            {"day": r["day"], "calls": int(r["calls"]), "tokens": int(r["tokens"]), "cost_cents": float(r["cost_cents"])}
            for r in raw_trend
        ]
        recent_errors = [
            {"provider": r["provider"], "module": r["module"], "action": r["action"], "error": r["error"], "created_at": r["created_at"]}
            for r in raw_errors
        ]

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
        since = datetime.now(UTC) - timedelta(days=days)

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

    # ------------------------------------------------------------------
    # Langfuse integration (LLM-specific observability)
    # All methods are no-ops when Langfuse is not installed or configured.
    # ------------------------------------------------------------------

    @staticmethod
    def create_trace(
        name: str,
        user_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Optional[Any]:
        """Create a Langfuse trace for an end-to-end LLM operation.

        Returns the trace object, or None if Langfuse is unavailable.
        """
        client = _get_langfuse_client()
        if client is None:
            return None

        try:
            trace = client.trace(
                name=name,
                user_id=user_id,
                metadata=metadata or {},
            )
            logger.debug("langfuse_trace_created", name=name, trace_id=trace.id)
            return trace
        except Exception as e:
            logger.warning("langfuse_trace_create_failed", name=name, error=str(e))
            return None

    @staticmethod
    def create_generation(
        trace_id: str,
        name: str,
        model: str,
        input: Optional[Any] = None,
        output: Optional[Any] = None,
        usage: Optional[dict] = None,
        metadata: Optional[dict] = None,
    ) -> Optional[Any]:
        """Create a Langfuse generation (LLM call) within a trace.

        Args:
            trace_id: The parent trace ID.
            name: Name of the generation (e.g. "summarize", "translate").
            model: Model identifier (e.g. "gemini-2.0-flash").
            input: The prompt / input sent to the LLM.
            output: The LLM response.
            usage: Token usage dict with keys: input, output, total, unit.
            metadata: Additional metadata dict.

        Returns the generation object, or None if Langfuse is unavailable.
        """
        client = _get_langfuse_client()
        if client is None:
            return None

        try:
            generation = client.generation(
                trace_id=trace_id,
                name=name,
                model=model,
                input=input,
                output=output,
                usage=usage or {},
                metadata=metadata or {},
            )
            logger.debug(
                "langfuse_generation_created",
                trace_id=trace_id,
                name=name,
                generation_id=generation.id,
            )
            return generation
        except Exception as e:
            logger.warning("langfuse_generation_create_failed", trace_id=trace_id, error=str(e))
            return None

    @staticmethod
    def score_generation(
        trace_id: str,
        generation_id: Optional[str] = None,
        name: str = "quality",
        value: float = 0.0,
        comment: Optional[str] = None,
    ) -> bool:
        """Score a generation or trace for quality tracking.

        Args:
            trace_id: The trace to score.
            generation_id: Optional specific generation to score.
            name: Score name (e.g. "quality", "relevance", "hallucination").
            value: Numeric score value.
            comment: Optional human-readable comment.

        Returns True if the score was recorded, False otherwise.
        """
        client = _get_langfuse_client()
        if client is None:
            return False

        try:
            score_kwargs = {
                "trace_id": trace_id,
                "name": name,
                "value": value,
            }
            if generation_id:
                score_kwargs["observation_id"] = generation_id
            if comment:
                score_kwargs["comment"] = comment

            client.score(**score_kwargs)
            logger.debug(
                "langfuse_score_recorded",
                trace_id=trace_id,
                name=name,
                value=value,
            )
            return True
        except Exception as e:
            logger.warning("langfuse_score_failed", trace_id=trace_id, error=str(e))
            return False

    @staticmethod
    def send_to_langfuse(
        provider: str,
        model: str,
        module: str,
        action: str,
        user_id: Optional[str] = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
        latency_ms: int = 0,
        success: bool = True,
        error: Optional[str] = None,
        input_text: Optional[str] = None,
        output_text: Optional[str] = None,
    ) -> None:
        """Send an AI usage event to Langfuse as a trace + generation.

        Called by track_ai_usage() to mirror events to Langfuse.
        Fails silently to never block the main flow.
        """
        client = _get_langfuse_client()
        if client is None:
            return

        try:
            trace = client.trace(
                name=f"{module}/{action}",
                user_id=user_id,
                metadata={
                    "provider": provider,
                    "model": model,
                    "module": module,
                    "action": action,
                    "success": success,
                },
            )

            usage = {
                "input": input_tokens,
                "output": output_tokens,
                "total": input_tokens + output_tokens,
                "unit": "TOKENS",
            }

            gen_metadata = {"latency_ms": latency_ms}
            if error:
                gen_metadata["error"] = error[:500]

            client.generation(
                trace_id=trace.id,
                name=action,
                model=model,
                input=input_text,
                output=output_text,
                usage=usage,
                metadata=gen_metadata,
                level="ERROR" if not success else "DEFAULT",
                status_message=error[:500] if error else None,
            )

            logger.debug(
                "langfuse_event_sent",
                trace_id=trace.id,
                module=module,
                action=action,
            )
        except Exception as e:
            logger.warning("langfuse_send_failed", error=str(e))

    @staticmethod
    def get_langfuse_dashboard_url() -> Optional[str]:
        """Return the Langfuse dashboard URL for the current project.

        Returns None if Langfuse is not configured.
        """
        if not HAS_LANGFUSE:
            return None

        host = os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com")
        public_key = os.environ.get("LANGFUSE_PUBLIC_KEY")

        if not public_key:
            return None

        return f"{host.rstrip('/')}/dashboard"

    @staticmethod
    def flush() -> bool:
        """Flush the Langfuse client to ensure all events are sent.

        Should be called before application shutdown.
        Returns True if flush succeeded, False otherwise.
        """
        client = _get_langfuse_client()
        if client is None:
            return False

        try:
            client.flush()
            logger.info("langfuse_flushed")
            return True
        except Exception as e:
            logger.warning("langfuse_flush_failed", error=str(e))
            return False

    @staticmethod
    def get_langfuse_status() -> dict:
        """Return Langfuse integration status for health checks."""
        configured = bool(
            os.environ.get("LANGFUSE_PUBLIC_KEY") and os.environ.get("LANGFUSE_SECRET_KEY")
        )
        return {
            "installed": HAS_LANGFUSE,
            "configured": configured,
            "active": HAS_LANGFUSE and configured and _langfuse_client is not None,
            "host": os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com") if configured else None,
        }
