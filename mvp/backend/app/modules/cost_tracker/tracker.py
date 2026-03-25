"""
Cost tracking utility - logs every AI call.

Import and call `track_ai_usage()` after each AI provider call.
Also sends events to Langfuse if available (auto-detection + fallback).
"""

import structlog
from typing import Optional
from uuid import UUID

from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.cost_tracking import AIUsageLog
from app.modules.cost_tracker.pricing import estimate_cost_cents

logger = structlog.get_logger()


async def track_ai_usage(
    user_id: UUID,
    provider: str,
    model: str,
    module: str,
    action: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
    latency_ms: int = 0,
    success: bool = True,
    error: str = None,
    session: AsyncSession = None,
    input_text: Optional[str] = None,
    output_text: Optional[str] = None,
) -> None:
    """
    Log an AI usage event.

    Call this after every AI provider interaction to build cost analytics.
    Also sends the event to Langfuse if configured (LLM-specific observability).
    Fails silently to never block the main flow.
    """
    try:
        total_tokens = input_tokens + output_tokens
        cost = estimate_cost_cents(provider, input_tokens, output_tokens)

        log_entry = AIUsageLog(
            user_id=user_id,
            provider=provider,
            model=model,
            module=module,
            action=action,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cost_cents=cost,
            latency_ms=latency_ms,
            success=success,
            error=error[:500] if error else None,
        )

        if session:
            session.add(log_entry)
            await session.commit()
        else:
            from app.database import get_session_context
            async with get_session_context() as s:
                s.add(log_entry)
                await s.commit()

        logger.debug(
            "ai_usage_tracked",
            provider=provider,
            tokens=total_tokens,
            cost_cents=cost,
            latency_ms=latency_ms,
        )

        # Mirror event to Langfuse if available
        try:
            from app.modules.ai_monitoring.service import AIMonitoringService
            AIMonitoringService.send_to_langfuse(
                provider=provider,
                model=model,
                module=module,
                action=action,
                user_id=str(user_id),
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                success=success,
                error=error,
                input_text=input_text,
                output_text=output_text,
            )
        except Exception as langfuse_err:
            logger.debug("langfuse_mirror_skipped", error=str(langfuse_err))

    except Exception as e:
        logger.warning("ai_usage_tracking_failed", error=str(e))
