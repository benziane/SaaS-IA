"""
Compare API routes - Multi-model comparison with voting.
"""

import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth import get_current_user
from app.modules.auth_guards.middleware import require_verified_email
from app.database import get_session
from app.models.user import User
from app.models.compare import ComparisonResult
from app.modules.compare.schemas import (
    CompareRequest,
    CompareResponse,
    ProviderResult,
    ProviderStats,
    VoteRequest,
    VoteResponse,
)
from app.modules.compare.service import CompareService
from app.modules.billing.service import BillingService
from app.modules.billing.middleware import require_ai_call_quota
from app.rate_limit import limiter

router = APIRouter()


@router.post("/run", response_model=CompareResponse)
@limiter.limit("5/minute")
async def run_comparison(
    request: Request,
    body: CompareRequest,
    current_user: User = Depends(require_ai_call_quota),
    session: AsyncSession = Depends(get_session),
):
    """
    Run the same prompt across multiple AI providers in parallel.

    Returns results from each provider with response times.
    Consumes AI call quota for each provider used.

    Rate limit: 5 requests/minute
    """
    comparison, results = await CompareService.run_comparison(
        user_id=current_user.id,
        prompt=body.prompt,
        providers=body.providers,
        session=session,
    )

    # Consume quota for each provider call
    await BillingService.consume_quota(
        current_user.id, "ai_call", len(body.providers), session
    )

    return CompareResponse(
        id=comparison.id,
        prompt=comparison.prompt,
        results=[ProviderResult(**r) for r in results],
        created_at=comparison.created_at,
    )


@router.post("/{comparison_id}/vote", response_model=VoteResponse)
@limiter.limit("10/minute")
async def vote_comparison(
    request: Request,
    comparison_id: UUID,
    body: VoteRequest,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """
    Vote for the best provider response in a comparison.

    Rate limit: 10 requests/minute
    """
    # Verify comparison exists and belongs to user
    comparison = await session.get(ComparisonResult, comparison_id)
    if not comparison:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comparison not found",
        )
    if comparison.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    vote = await CompareService.record_vote(
        comparison_id=comparison_id,
        user_id=current_user.id,
        provider_name=body.provider_name,
        quality_score=body.quality_score,
        session=session,
    )

    return VoteResponse(
        id=vote.id,
        comparison_id=vote.comparison_id,
        provider_name=vote.provider_name,
        quality_score=vote.quality_score,
    )


@router.get("/stats", response_model=list[ProviderStats])
@limiter.limit("20/minute")
async def get_comparison_stats(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Get aggregated quality statistics per provider.

    Rate limit: 20 requests/minute
    """
    stats = await CompareService.get_stats(session)
    return [ProviderStats(**s) for s in stats]
