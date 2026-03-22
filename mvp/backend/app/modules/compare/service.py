"""
Compare service - Execute prompts across multiple AI providers in parallel.
"""

import asyncio
import json
import time
from typing import Optional
from uuid import UUID

import structlog
from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.compare import ComparisonResult, ComparisonVote

logger = structlog.get_logger()


class CompareService:
    """Service for multi-model comparison."""

    @staticmethod
    async def _call_provider(provider_name: str, prompt: str) -> dict:
        """Call a single AI provider and return result with timing."""
        from app.ai_assistant.service import AIAssistantService

        start = time.monotonic()
        try:
            result = await AIAssistantService.process_text_with_provider(
                text=prompt,
                task="general",
                provider_name=provider_name,
            )
            elapsed_ms = int((time.monotonic() - start) * 1000)

            return {
                "provider": provider_name,
                "model": result.get("model", provider_name),
                "response": result.get("processed_text", ""),
                "response_time_ms": elapsed_ms,
                "error": None,
            }
        except Exception as e:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            logger.warning(
                "compare_provider_error",
                provider=provider_name,
                error=str(e),
            )
            return {
                "provider": provider_name,
                "model": provider_name,
                "response": "",
                "response_time_ms": elapsed_ms,
                "error": str(e)[:500],
            }

    @staticmethod
    async def run_comparison(
        user_id: UUID,
        prompt: str,
        providers: list[str],
        session: AsyncSession,
    ) -> tuple[ComparisonResult, list[dict]]:
        """
        Execute the same prompt across multiple providers in parallel.

        Returns the persisted ComparisonResult and a list of provider results.
        """
        # Execute all providers in parallel
        tasks = [
            CompareService._call_provider(provider, prompt)
            for provider in providers
        ]
        results = await asyncio.gather(*tasks)

        # Persist comparison
        comparison = ComparisonResult(
            user_id=user_id,
            prompt=prompt[:10000],
            providers_used=",".join(providers),
            results_json=json.dumps(results, ensure_ascii=False),
        )
        session.add(comparison)
        await session.commit()
        await session.refresh(comparison)

        logger.info(
            "comparison_completed",
            comparison_id=str(comparison.id),
            user_id=str(user_id),
            providers=providers,
        )

        return comparison, results

    @staticmethod
    async def record_vote(
        comparison_id: UUID,
        user_id: UUID,
        provider_name: str,
        quality_score: int,
        session: AsyncSession,
    ) -> ComparisonVote:
        """Record a user vote for a provider in a comparison."""
        vote = ComparisonVote(
            comparison_id=comparison_id,
            user_id=user_id,
            provider_name=provider_name,
            quality_score=quality_score,
        )
        session.add(vote)
        await session.commit()
        await session.refresh(vote)

        logger.info(
            "comparison_vote_recorded",
            comparison_id=str(comparison_id),
            provider=provider_name,
            score=quality_score,
        )

        return vote

    @staticmethod
    async def get_stats(session: AsyncSession) -> list[dict]:
        """Get aggregated quality statistics per provider."""
        result = await session.execute(
            select(
                ComparisonVote.provider_name,
                func.count().label("total_votes"),
                func.avg(ComparisonVote.quality_score).label("avg_score"),
            )
            .group_by(ComparisonVote.provider_name)
            .order_by(func.avg(ComparisonVote.quality_score).desc())
        )
        rows = result.all()

        # Count wins (highest score in each comparison)
        stats = []
        for row in rows:
            stats.append({
                "provider": row.provider_name,
                "total_votes": row.total_votes,
                "avg_score": round(float(row.avg_score), 2),
                "win_count": 0,
            })

        return stats
