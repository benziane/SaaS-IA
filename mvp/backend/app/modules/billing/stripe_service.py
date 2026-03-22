"""
Stripe integration service for payment processing.
"""

import json
from datetime import date, datetime
from typing import Optional
from uuid import UUID

import structlog
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import settings
from app.models.billing import Plan, PlanName, UserQuota
from app.modules.billing.service import BillingService

logger = structlog.get_logger()


def _get_stripe():
    """Lazy import and configure stripe."""
    import stripe
    stripe.api_key = settings.STRIPE_SECRET_KEY
    return stripe


class StripeService:
    """Service for Stripe payment operations."""

    @staticmethod
    async def create_checkout_session(
        user_id: UUID,
        user_email: str,
        plan_name: str,
        session: AsyncSession,
    ) -> dict:
        """
        Create a Stripe Checkout session for upgrading to a paid plan.

        Returns checkout_url and session_id.
        """
        stripe = _get_stripe()

        if not settings.STRIPE_SECRET_KEY:
            raise ValueError("Stripe is not configured. Set STRIPE_SECRET_KEY in .env")

        # Get the target plan
        result = await session.execute(
            select(Plan).where(Plan.name == plan_name)
        )
        plan = result.scalar_one_or_none()
        if not plan:
            raise ValueError(f"Plan '{plan_name}' not found")

        if plan.price_cents == 0:
            raise ValueError("Cannot create checkout for free plan")

        # Get or create Stripe price ID
        price_id = plan.stripe_price_id or settings.STRIPE_PRICE_PRO_MONTHLY
        if not price_id:
            raise ValueError("No Stripe price ID configured for this plan")

        # Get user quota for customer ID
        quota, _ = await BillingService.get_user_quota(user_id, session)

        # Create or reuse Stripe customer
        customer_id = quota.stripe_customer_id
        if not customer_id:
            customer = stripe.Customer.create(
                email=user_email,
                metadata={"user_id": str(user_id)},
            )
            customer_id = customer.id
            quota.stripe_customer_id = customer_id
            session.add(quota)
            await session.commit()

        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            customer=customer_id,
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=f"{settings.CORS_ORIGINS.split(',')[0]}/billing?success=true",
            cancel_url=f"{settings.CORS_ORIGINS.split(',')[0]}/billing?canceled=true",
            metadata={
                "user_id": str(user_id),
                "plan_name": plan_name,
            },
        )

        logger.info(
            "stripe_checkout_created",
            user_id=str(user_id),
            plan=plan_name,
            session_id=checkout_session.id,
        )

        return {
            "checkout_url": checkout_session.url,
            "session_id": checkout_session.id,
        }

    @staticmethod
    async def create_portal_session(
        user_id: UUID,
        session: AsyncSession,
    ) -> dict:
        """Create a Stripe billing portal session for managing subscription."""
        stripe = _get_stripe()

        if not settings.STRIPE_SECRET_KEY:
            raise ValueError("Stripe is not configured")

        quota, _ = await BillingService.get_user_quota(user_id, session)

        if not quota.stripe_customer_id:
            raise ValueError("No Stripe customer found. Subscribe to a plan first.")

        portal_session = stripe.billing_portal.Session.create(
            customer=quota.stripe_customer_id,
            return_url=f"{settings.CORS_ORIGINS.split(',')[0]}/billing",
        )

        return {"portal_url": portal_session.url}

    @staticmethod
    async def handle_webhook(
        payload: bytes,
        signature: str,
        session: AsyncSession,
    ) -> dict:
        """
        Handle Stripe webhook events.

        Processes:
        - checkout.session.completed: Upgrade user plan
        - customer.subscription.deleted: Downgrade to free
        - invoice.payment_failed: Log warning
        """
        stripe = _get_stripe()

        try:
            event = stripe.Webhook.construct_event(
                payload, signature, settings.STRIPE_WEBHOOK_SECRET
            )
        except (ValueError, stripe.error.SignatureVerificationError) as e:
            logger.warning("stripe_webhook_invalid", error=str(e))
            raise ValueError(f"Invalid webhook: {str(e)}")

        event_type = event["type"]
        data = event["data"]["object"]

        logger.info("stripe_webhook_received", event_type=event_type)

        if event_type == "checkout.session.completed":
            await StripeService._handle_checkout_completed(data, session)
        elif event_type == "customer.subscription.deleted":
            await StripeService._handle_subscription_deleted(data, session)
        elif event_type == "invoice.payment_failed":
            logger.warning(
                "stripe_payment_failed",
                customer=data.get("customer"),
                invoice=data.get("id"),
            )

        return {"status": "ok", "event_type": event_type}

    @staticmethod
    async def _handle_checkout_completed(data: dict, session: AsyncSession):
        """Upgrade user to paid plan after successful checkout."""
        user_id = data.get("metadata", {}).get("user_id")
        plan_name = data.get("metadata", {}).get("plan_name", "pro")
        subscription_id = data.get("subscription")

        if not user_id:
            logger.warning("stripe_checkout_no_user_id", data=data)
            return

        from uuid import UUID as UUIDType

        # Get the target plan
        result = await session.execute(
            select(Plan).where(Plan.name == plan_name)
        )
        plan = result.scalar_one_or_none()
        if not plan:
            logger.error("stripe_plan_not_found", plan_name=plan_name)
            return

        # Update user quota to the new plan
        quota, _ = await BillingService.get_user_quota(UUIDType(user_id), session)
        quota.plan_id = plan.id
        quota.stripe_subscription_id = subscription_id
        quota.updated_at = datetime.utcnow()
        session.add(quota)
        await session.commit()

        logger.info(
            "stripe_plan_upgraded",
            user_id=user_id,
            plan=plan_name,
            subscription_id=subscription_id,
        )

    @staticmethod
    async def _handle_subscription_deleted(data: dict, session: AsyncSession):
        """Downgrade user to free plan when subscription is canceled."""
        customer_id = data.get("customer")

        if not customer_id:
            return

        # Find the user quota by stripe customer ID
        result = await session.execute(
            select(UserQuota).where(UserQuota.stripe_customer_id == customer_id)
        )
        quota = result.scalar_one_or_none()
        if not quota:
            logger.warning("stripe_customer_not_found", customer_id=customer_id)
            return

        # Get free plan
        free_result = await session.execute(
            select(Plan).where(Plan.name == PlanName.FREE)
        )
        free_plan = free_result.scalar_one_or_none()
        if not free_plan:
            return

        quota.plan_id = free_plan.id
        quota.stripe_subscription_id = None
        quota.updated_at = datetime.utcnow()
        session.add(quota)
        await session.commit()

        logger.info(
            "stripe_subscription_canceled",
            customer_id=customer_id,
            downgraded_to="free",
        )
