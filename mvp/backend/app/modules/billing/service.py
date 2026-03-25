"""
Billing service - Business logic for plans and quotas.
"""

from datetime import UTC, date, datetime
from dateutil.relativedelta import relativedelta
from typing import Optional
from uuid import UUID

import structlog
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.billing import Plan, PlanName, UserQuota

logger = structlog.get_logger()


class BillingService:
    """Service for managing plans and user quotas."""

    @staticmethod
    async def get_or_create_plans(session: AsyncSession) -> list[Plan]:
        """Ensure default plans exist and return them."""
        result = await session.execute(select(Plan))
        plans = list(result.scalars().all())
        if plans:
            return plans

        defaults = [
            Plan(
                name=PlanName.FREE,
                display_name="Free",
                max_transcriptions_month=10,
                max_audio_minutes_month=60,
                max_ai_calls_month=50,
                price_cents=0,
            ),
            Plan(
                name=PlanName.PRO,
                display_name="Pro",
                max_transcriptions_month=100,
                max_audio_minutes_month=600,
                max_ai_calls_month=500,
                price_cents=1900,
            ),
            Plan(
                name=PlanName.ENTERPRISE,
                display_name="Enterprise",
                max_transcriptions_month=999999,
                max_audio_minutes_month=999999,
                max_ai_calls_month=999999,
                price_cents=0,
            ),
        ]
        for plan in defaults:
            session.add(plan)
        await session.commit()

        result = await session.execute(select(Plan))
        return list(result.scalars().all())

    @staticmethod
    async def get_plans(session: AsyncSession) -> list[Plan]:
        """Return all active plans."""
        result = await session.execute(
            select(Plan).where(Plan.is_active == True).order_by(Plan.price_cents.asc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_user_quota(user_id: UUID, session: AsyncSession) -> tuple[UserQuota, Plan]:
        """
        Get or create the current billing period quota for a user.

        Automatically assigns the Free plan to new users and creates
        a new period when the current one expires.
        """
        today = date.today()

        # Try to find active quota
        result = await session.execute(
            select(UserQuota).where(
                UserQuota.user_id == user_id,
                UserQuota.period_end >= today,
            ).order_by(UserQuota.period_start.desc())
        )
        quota = result.scalar_one_or_none()

        if quota is not None:
            plan = await session.get(Plan, quota.plan_id)
            return quota, plan

        # No active quota: create one with the Free plan
        plans = await BillingService.get_or_create_plans(session)
        free_plan = next((p for p in plans if p.name == PlanName.FREE), plans[0])

        period_start = today.replace(day=1)
        period_end = (period_start + relativedelta(months=1)) - relativedelta(days=1)

        quota = UserQuota(
            user_id=user_id,
            plan_id=free_plan.id,
            period_start=period_start,
            period_end=period_end,
        )
        session.add(quota)
        await session.commit()
        await session.refresh(quota)

        logger.info(
            "user_quota_created",
            user_id=str(user_id),
            plan=free_plan.name.value,
            period_end=str(period_end),
        )

        return quota, free_plan

    @staticmethod
    async def check_quota(user_id: UUID, resource_type: str, session: AsyncSession) -> bool:
        """
        Check if a user has remaining quota for a given resource.

        resource_type: "transcription", "audio_minutes", or "ai_call"
        Returns True if quota is available, False if exceeded.
        """
        quota, plan = await BillingService.get_user_quota(user_id, session)

        if resource_type == "transcription":
            return quota.transcriptions_used < plan.max_transcriptions_month
        elif resource_type == "audio_minutes":
            return quota.audio_minutes_used < plan.max_audio_minutes_month
        elif resource_type == "ai_call":
            return quota.ai_calls_used < plan.max_ai_calls_month
        else:
            logger.warning("unknown_resource_type", resource_type=resource_type)
            return True

    @staticmethod
    async def consume_quota(
        user_id: UUID,
        resource_type: str,
        amount: int,
        session: AsyncSession,
    ) -> None:
        """
        Increment usage for a given resource type.

        resource_type: "transcription", "audio_minutes", or "ai_call"
        """
        quota, _ = await BillingService.get_user_quota(user_id, session)

        if resource_type == "transcription":
            quota.transcriptions_used += amount
        elif resource_type == "audio_minutes":
            quota.audio_minutes_used += amount
        elif resource_type == "ai_call":
            quota.ai_calls_used += amount

        quota.updated_at = datetime.now(UTC)
        session.add(quota)
        await session.commit()

        logger.info(
            "quota_consumed",
            user_id=str(user_id),
            resource=resource_type,
            amount=amount,
        )

    @staticmethod
    async def reset_monthly_quotas(session: AsyncSession) -> int:
        """
        Reset quotas for all users whose billing period has ended.

        Returns the number of quotas reset.
        """
        today = date.today()
        result = await session.execute(
            select(UserQuota).where(UserQuota.period_end < today)
        )
        expired_quotas = list(result.scalars().all())

        count = 0
        for quota in expired_quotas:
            period_start = today.replace(day=1)
            period_end = (period_start + relativedelta(months=1)) - relativedelta(days=1)

            quota.transcriptions_used = 0
            quota.audio_minutes_used = 0
            quota.ai_calls_used = 0
            quota.period_start = period_start
            quota.period_end = period_end
            quota.updated_at = datetime.now(UTC)
            session.add(quota)
            count += 1

        if count > 0:
            await session.commit()
            logger.info("monthly_quotas_reset", count=count)

        return count
