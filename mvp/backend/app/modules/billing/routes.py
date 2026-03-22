"""
Billing API routes - Plans and quota management.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth import get_current_user
from app.database import get_session
from app.models.user import User
from app.modules.billing.schemas import PlanRead, QuotaRead
from app.modules.billing.service import BillingService
from app.rate_limit import limiter

router = APIRouter()


@router.get("/plans", response_model=list[PlanRead])
@limiter.limit("30/minute")
async def list_plans(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """
    List all available subscription plans.

    Rate limit: 30 requests/minute
    """
    plans = await BillingService.get_or_create_plans(session)
    return [p for p in plans if p.is_active]


@router.get("/quota", response_model=QuotaRead)
@limiter.limit("30/minute")
async def get_my_quota(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Get the current user's quota and usage for the billing period.

    Rate limit: 30 requests/minute
    """
    quota, plan = await BillingService.get_user_quota(current_user.id, session)

    # Calculate max usage across all resource types as overall percent
    pcts = []
    if plan.max_transcriptions_month > 0:
        pcts.append(quota.transcriptions_used / plan.max_transcriptions_month)
    if plan.max_audio_minutes_month > 0:
        pcts.append(quota.audio_minutes_used / plan.max_audio_minutes_month)
    if plan.max_ai_calls_month > 0:
        pcts.append(quota.ai_calls_used / plan.max_ai_calls_month)
    usage_percent = round(max(pcts) * 100, 1) if pcts else 0.0

    return QuotaRead(
        plan=PlanRead.model_validate(plan),
        transcriptions_used=quota.transcriptions_used,
        transcriptions_limit=plan.max_transcriptions_month,
        audio_minutes_used=quota.audio_minutes_used,
        audio_minutes_limit=plan.max_audio_minutes_month,
        ai_calls_used=quota.ai_calls_used,
        ai_calls_limit=plan.max_ai_calls_month,
        period_start=quota.period_start,
        period_end=quota.period_end,
        usage_percent=usage_percent,
    )
