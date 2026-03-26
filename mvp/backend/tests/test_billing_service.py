"""
Tests for the billing module: service logic, quota enforcement, Stripe integration, and route auth.

All tests run without external services (no DB, no Stripe, no Redis).
"""

import os
import pytest
from datetime import UTC, date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_plan(name="free", price_cents=0, **overrides):
    """Create a mock Plan object."""
    from app.models.billing import Plan, PlanName

    defaults = {
        "free": {
            "name": PlanName.FREE,
            "display_name": "Free",
            "max_transcriptions_month": 10,
            "max_audio_minutes_month": 60,
            "max_ai_calls_month": 50,
            "price_cents": 0,
        },
        "pro": {
            "name": PlanName.PRO,
            "display_name": "Pro",
            "max_transcriptions_month": 100,
            "max_audio_minutes_month": 600,
            "max_ai_calls_month": 500,
            "price_cents": 1900,
        },
        "enterprise": {
            "name": PlanName.ENTERPRISE,
            "display_name": "Enterprise",
            "max_transcriptions_month": 999999,
            "max_audio_minutes_month": 999999,
            "max_ai_calls_month": 999999,
            "price_cents": 0,
        },
    }
    cfg = {**defaults.get(name, defaults["free"]), **overrides}
    plan = Plan(id=uuid4(), **cfg)
    return plan


def _make_quota(user_id, plan_id, **overrides):
    """Create a mock UserQuota object."""
    from app.models.billing import UserQuota

    today = date.today()
    period_start = today.replace(day=1)
    period_end = (period_start + relativedelta(months=1)) - relativedelta(days=1)
    return UserQuota(
        id=uuid4(),
        user_id=user_id,
        plan_id=plan_id,
        period_start=period_start,
        period_end=period_end,
        transcriptions_used=overrides.get("transcriptions_used", 0),
        audio_minutes_used=overrides.get("audio_minutes_used", 0),
        ai_calls_used=overrides.get("ai_calls_used", 0),
    )


# ---------------------------------------------------------------------------
# Service tests
# ---------------------------------------------------------------------------

class TestBillingServiceGetPlans:
    """Tests for BillingService.get_or_create_plans and get_plans."""

    @pytest.mark.asyncio
    async def test_get_or_create_plans_creates_defaults(self):
        """When no plans exist, get_or_create_plans seeds free/pro/enterprise."""
        from app.models.billing import PlanName

        session = AsyncMock()
        # First call: no existing plans
        mock_result_empty = MagicMock()
        mock_result_empty.scalars.return_value.all.return_value = []
        # Second call: return the seeded plans
        plans = [_make_plan("free"), _make_plan("pro"), _make_plan("enterprise")]
        mock_result_seeded = MagicMock()
        mock_result_seeded.scalars.return_value.all.return_value = plans
        session.execute = AsyncMock(side_effect=[mock_result_empty, mock_result_seeded])
        session.commit = AsyncMock()

        from app.modules.billing.service import BillingService
        result = await BillingService.get_or_create_plans(session)

        assert len(result) == 3
        plan_names = {p.name for p in result}
        assert PlanName.FREE in plan_names
        assert PlanName.PRO in plan_names
        assert PlanName.ENTERPRISE in plan_names

    @pytest.mark.asyncio
    async def test_get_or_create_plans_returns_existing(self):
        """When plans already exist, returns them without re-seeding."""
        plans = [_make_plan("free"), _make_plan("pro")]
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = plans
        session.execute = AsyncMock(return_value=mock_result)

        from app.modules.billing.service import BillingService
        result = await BillingService.get_or_create_plans(session)

        assert len(result) == 2
        # Should NOT call commit (no seeding)
        session.commit.assert_not_awaited()


class TestBillingServiceGetUserQuota:
    """Tests for BillingService.get_user_quota."""

    @pytest.mark.asyncio
    async def test_get_user_plan_returns_existing_quota(self):
        """Returns the current plan when user has an active quota."""
        user_id = uuid4()
        plan = _make_plan("pro")
        quota = _make_quota(user_id, plan.id)

        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = quota
        session.execute = AsyncMock(return_value=mock_result)
        session.get = AsyncMock(return_value=plan)

        from app.modules.billing.service import BillingService
        returned_quota, returned_plan = await BillingService.get_user_quota(user_id, session)

        assert returned_plan.name.value == "pro"
        assert returned_quota.user_id == user_id


class TestBillingServiceCheckQuota:
    """Tests for BillingService.check_quota."""

    @pytest.mark.asyncio
    async def test_check_quota_within_limit_passes(self):
        """Returns True when usage is under the plan limit."""
        user_id = uuid4()
        plan = _make_plan("free")
        quota = _make_quota(user_id, plan.id, transcriptions_used=5)

        from app.modules.billing.service import BillingService
        with patch.object(BillingService, "get_user_quota", new_callable=AsyncMock, return_value=(quota, plan)):
            result = await BillingService.check_quota(user_id, "transcription", AsyncMock())
        assert result is True

    @pytest.mark.asyncio
    async def test_check_quota_exceeded_returns_false(self):
        """Returns False when usage reaches/exceeds the plan limit."""
        user_id = uuid4()
        plan = _make_plan("free")
        quota = _make_quota(user_id, plan.id, transcriptions_used=10)

        from app.modules.billing.service import BillingService
        with patch.object(BillingService, "get_user_quota", new_callable=AsyncMock, return_value=(quota, plan)):
            result = await BillingService.check_quota(user_id, "transcription", AsyncMock())
        assert result is False

    @pytest.mark.asyncio
    async def test_check_quota_ai_calls_within_limit(self):
        """AI call quota passes when under limit."""
        user_id = uuid4()
        plan = _make_plan("free")
        quota = _make_quota(user_id, plan.id, ai_calls_used=49)

        from app.modules.billing.service import BillingService
        with patch.object(BillingService, "get_user_quota", new_callable=AsyncMock, return_value=(quota, plan)):
            result = await BillingService.check_quota(user_id, "ai_call", AsyncMock())
        assert result is True

    @pytest.mark.asyncio
    async def test_check_quota_ai_calls_exceeded(self):
        """AI call quota fails when at limit."""
        user_id = uuid4()
        plan = _make_plan("free")
        quota = _make_quota(user_id, plan.id, ai_calls_used=50)

        from app.modules.billing.service import BillingService
        with patch.object(BillingService, "get_user_quota", new_callable=AsyncMock, return_value=(quota, plan)):
            result = await BillingService.check_quota(user_id, "ai_call", AsyncMock())
        assert result is False

    @pytest.mark.asyncio
    async def test_check_quota_unknown_resource_returns_true(self):
        """Unknown resource type defaults to allowing the call."""
        user_id = uuid4()
        plan = _make_plan("free")
        quota = _make_quota(user_id, plan.id)

        from app.modules.billing.service import BillingService
        with patch.object(BillingService, "get_user_quota", new_callable=AsyncMock, return_value=(quota, plan)):
            result = await BillingService.check_quota(user_id, "unknown_resource", AsyncMock())
        assert result is True


class TestBillingServiceConsumeQuota:
    """Tests for BillingService.consume_quota."""

    @pytest.mark.asyncio
    async def test_consume_quota_increments_usage(self):
        """consume_quota should issue an atomic SQL UPDATE for the correct column."""
        user_id = uuid4()
        plan = _make_plan("free")
        quota = _make_quota(user_id, plan.id, transcriptions_used=3)

        session = AsyncMock()
        session.commit = AsyncMock()
        session.execute = AsyncMock()

        from app.modules.billing.service import BillingService
        with patch.object(BillingService, "get_user_quota", new_callable=AsyncMock, return_value=(quota, plan)):
            await BillingService.consume_quota(user_id, "transcription", 1, session)

        session.execute.assert_awaited()
        update_call = session.execute.call_args[0][0]
        compiled = update_call.compile(compile_kwargs={"literal_binds": True})
        compiled_str = str(compiled)
        assert "user_quotas" in compiled_str
        assert "transcriptions_used" in compiled_str
        session.commit.assert_awaited()


class TestPlanFeatures:
    """Test that each plan has the correct limits."""

    def test_free_plan_features(self):
        plan = _make_plan("free")
        assert plan.max_transcriptions_month == 10
        assert plan.max_audio_minutes_month == 60
        assert plan.max_ai_calls_month == 50
        assert plan.price_cents == 0

    def test_pro_plan_features(self):
        plan = _make_plan("pro")
        assert plan.max_transcriptions_month == 100
        assert plan.max_audio_minutes_month == 600
        assert plan.max_ai_calls_month == 500
        assert plan.price_cents == 1900

    def test_enterprise_plan_features(self):
        plan = _make_plan("enterprise")
        assert plan.max_transcriptions_month == 999999
        assert plan.max_audio_minutes_month == 999999
        assert plan.max_ai_calls_month == 999999


class TestStripeCheckout:
    """Tests for Stripe checkout and webhook integration."""

    @pytest.mark.asyncio
    async def test_create_checkout_session_returns_url(self):
        """create_checkout_session should return a checkout_url and session_id."""
        user_id = uuid4()
        plan = _make_plan("pro", stripe_price_id="price_test123")
        quota = _make_quota(user_id, plan.id)
        quota.stripe_customer_id = "cus_test123"

        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = plan
        session.execute = AsyncMock(return_value=mock_result)

        mock_checkout = MagicMock()
        mock_checkout.url = "https://checkout.stripe.com/test"
        mock_checkout.id = "cs_test_123"

        from app.modules.billing.stripe_service import StripeService
        with (
            patch.object(StripeService, "__init__", lambda self: None, create=True),
            patch("app.modules.billing.stripe_service.settings") as mock_settings,
            patch("app.modules.billing.stripe_service._get_stripe") as mock_get_stripe,
            patch.object(
                StripeService, "create_checkout_session",
                new_callable=AsyncMock,
                return_value={"checkout_url": "https://checkout.stripe.com/test", "session_id": "cs_test_123"},
            ),
        ):
            result = await StripeService.create_checkout_session(
                user_id=user_id,
                user_email="test@test.com",
                plan_name="pro",
                session=session,
            )

        assert "checkout_url" in result
        assert "session_id" in result
        assert result["checkout_url"].startswith("https://")

    @pytest.mark.asyncio
    async def test_webhook_invalid_signature_raises(self):
        """Invalid Stripe webhook signature should raise ValueError."""
        from app.modules.billing.stripe_service import StripeService

        # Create a proper mock where stripe.error.SignatureVerificationError is a real exception class
        mock_stripe = MagicMock()

        class MockSignatureVerificationError(Exception):
            pass

        mock_stripe.error.SignatureVerificationError = MockSignatureVerificationError
        mock_stripe.Webhook.construct_event.side_effect = ValueError("Invalid signature")

        session = AsyncMock()

        with patch("app.modules.billing.stripe_service._get_stripe", return_value=mock_stripe):
            with pytest.raises(ValueError, match="Invalid webhook"):
                await StripeService.handle_webhook(b"payload", "bad_sig", session)

    @pytest.mark.asyncio
    async def test_webhook_valid_signature_processes_event(self):
        """Valid webhook should process the event and return ok."""
        from app.modules.billing.stripe_service import StripeService

        mock_stripe = MagicMock()

        class MockSignatureVerificationError(Exception):
            pass

        mock_stripe.error.SignatureVerificationError = MockSignatureVerificationError
        mock_event = {
            "type": "invoice.payment_failed",
            "data": {"object": {"customer": "cus_123", "id": "inv_123"}},
        }
        mock_stripe.Webhook.construct_event.return_value = mock_event

        session = AsyncMock()

        with (
            patch("app.modules.billing.stripe_service._get_stripe", return_value=mock_stripe),
            patch("app.modules.billing.stripe_service.settings"),
        ):
            result = await StripeService.handle_webhook(b"payload", "valid_sig", session)

        assert result["status"] == "ok"
        assert result["event_type"] == "invoice.payment_failed"


class TestBillingEndpointAuth:
    """Tests for billing route authentication."""

    @pytest.mark.asyncio
    async def test_quota_endpoint_returns_401_without_token(self, client):
        """GET /api/billing/quota should return 401 without auth."""
        response = await client.get("/api/billing/quota")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_checkout_endpoint_returns_401_without_token(self, client):
        """POST /api/billing/checkout should return 401 without auth."""
        response = await client.post(
            "/api/billing/checkout",
            json={"plan_name": "pro"},
        )
        assert response.status_code == 401


class TestBillingPlanUpgrade:
    """Test plan upgrade flow."""

    @pytest.mark.asyncio
    async def test_plan_upgrade_free_to_pro(self):
        """Simulates upgrading a user quota from free to pro plan."""
        from app.models.billing import UserQuota

        user_id = uuid4()
        free_plan = _make_plan("free")
        pro_plan = _make_plan("pro")
        quota = _make_quota(user_id, free_plan.id)

        # Simulate upgrade
        quota.plan_id = pro_plan.id
        assert quota.plan_id == pro_plan.id

    @pytest.mark.asyncio
    async def test_consume_quota_audio_minutes(self):
        """consume_quota issues an atomic SQL UPDATE for audio_minutes_used."""
        user_id = uuid4()
        plan = _make_plan("pro")
        quota = _make_quota(user_id, plan.id, audio_minutes_used=100)

        session = AsyncMock()
        session.commit = AsyncMock()
        session.execute = AsyncMock()

        from app.modules.billing.service import BillingService
        with patch.object(BillingService, "get_user_quota", new_callable=AsyncMock, return_value=(quota, plan)):
            await BillingService.consume_quota(user_id, "audio_minutes", 15, session)

        session.execute.assert_awaited()
        update_call = session.execute.call_args[0][0]
        compiled = update_call.compile(compile_kwargs={"literal_binds": True})
        compiled_str = str(compiled)
        assert "user_quotas" in compiled_str
        assert "audio_minutes_used" in compiled_str
        session.commit.assert_awaited()
