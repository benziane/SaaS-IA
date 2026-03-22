"""
Tests for the billing module: plans, quotas, and service logic.

All tests run without external services.
"""

import os
import pytest
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


class TestPlanModel:
    """Test Plan model and enum."""

    def test_plan_name_enum_values(self):
        from app.models.billing import PlanName
        assert PlanName.FREE == "free"
        assert PlanName.PRO == "pro"
        assert PlanName.ENTERPRISE == "enterprise"

    def test_plan_creation(self):
        from app.models.billing import Plan, PlanName
        plan = Plan(
            name=PlanName.FREE,
            display_name="Free",
            max_transcriptions_month=10,
            max_audio_minutes_month=60,
            max_ai_calls_month=50,
            price_cents=0,
        )
        assert plan.name == PlanName.FREE
        assert plan.display_name == "Free"
        assert plan.max_transcriptions_month == 10
        assert plan.max_audio_minutes_month == 60
        assert plan.max_ai_calls_month == 50
        assert plan.price_cents == 0
        assert plan.is_active is True

    def test_pro_plan_limits(self):
        from app.models.billing import Plan, PlanName
        plan = Plan(
            name=PlanName.PRO,
            display_name="Pro",
            max_transcriptions_month=100,
            max_audio_minutes_month=600,
            max_ai_calls_month=500,
            price_cents=1900,
        )
        assert plan.max_transcriptions_month == 100
        assert plan.max_audio_minutes_month == 600
        assert plan.max_ai_calls_month == 500
        assert plan.price_cents == 1900

    def test_enterprise_plan_unlimited(self):
        from app.models.billing import Plan, PlanName
        plan = Plan(
            name=PlanName.ENTERPRISE,
            display_name="Enterprise",
            max_transcriptions_month=999999,
            max_audio_minutes_month=999999,
            max_ai_calls_month=999999,
            price_cents=0,
        )
        assert plan.max_transcriptions_month == 999999
        assert plan.max_ai_calls_month == 999999


class TestUserQuotaModel:
    """Test UserQuota model."""

    def test_quota_creation(self):
        from app.models.billing import UserQuota
        user_id = uuid4()
        plan_id = uuid4()
        quota = UserQuota(
            user_id=user_id,
            plan_id=plan_id,
            period_start=date(2026, 3, 1),
            period_end=date(2026, 3, 31),
        )
        assert quota.user_id == user_id
        assert quota.plan_id == plan_id
        assert quota.transcriptions_used == 0
        assert quota.audio_minutes_used == 0
        assert quota.ai_calls_used == 0

    def test_quota_default_values(self):
        from app.models.billing import UserQuota
        quota = UserQuota(
            user_id=uuid4(),
            plan_id=uuid4(),
            period_start=date.today(),
            period_end=date.today(),
        )
        assert quota.transcriptions_used == 0
        assert quota.audio_minutes_used == 0
        assert quota.ai_calls_used == 0


class TestBillingSchemas:
    """Test billing Pydantic schemas."""

    def test_plan_read_schema(self):
        from app.modules.billing.schemas import PlanRead
        plan_data = {
            "id": str(uuid4()),
            "name": "free",
            "display_name": "Free",
            "max_transcriptions_month": 10,
            "max_audio_minutes_month": 60,
            "max_ai_calls_month": 50,
            "price_cents": 0,
            "is_active": True,
        }
        plan = PlanRead(**plan_data)
        assert plan.display_name == "Free"
        assert plan.price_cents == 0

    def test_quota_read_schema(self):
        from app.modules.billing.schemas import PlanRead, QuotaRead
        plan_data = {
            "id": str(uuid4()),
            "name": "free",
            "display_name": "Free",
            "max_transcriptions_month": 10,
            "max_audio_minutes_month": 60,
            "max_ai_calls_month": 50,
            "price_cents": 0,
            "is_active": True,
        }
        quota_data = {
            "plan": plan_data,
            "transcriptions_used": 5,
            "transcriptions_limit": 10,
            "audio_minutes_used": 30,
            "audio_minutes_limit": 60,
            "ai_calls_used": 20,
            "ai_calls_limit": 50,
            "period_start": "2026-03-01",
            "period_end": "2026-03-31",
            "usage_percent": 50.0,
        }
        quota = QuotaRead(**quota_data)
        assert quota.transcriptions_used == 5
        assert quota.usage_percent == 50.0
        assert quota.plan.display_name == "Free"

    def test_quota_read_high_usage(self):
        from app.modules.billing.schemas import PlanRead, QuotaRead
        plan_data = {
            "id": str(uuid4()),
            "name": "free",
            "display_name": "Free",
            "max_transcriptions_month": 10,
            "max_audio_minutes_month": 60,
            "max_ai_calls_month": 50,
            "price_cents": 0,
            "is_active": True,
        }
        quota_data = {
            "plan": plan_data,
            "transcriptions_used": 9,
            "transcriptions_limit": 10,
            "audio_minutes_used": 55,
            "audio_minutes_limit": 60,
            "ai_calls_used": 48,
            "ai_calls_limit": 50,
            "period_start": "2026-03-01",
            "period_end": "2026-03-31",
            "usage_percent": 96.0,
        }
        quota = QuotaRead(**quota_data)
        assert quota.usage_percent == 96.0


class TestCeleryApp:
    """Test Celery app configuration."""

    def test_celery_app_created(self):
        from app.celery_app import celery_app
        assert celery_app is not None
        assert celery_app.main == "saas_ia"

    def test_celery_config_json_serializer(self):
        from app.celery_app import celery_app
        assert celery_app.conf.task_serializer == "json"
        assert celery_app.conf.result_serializer == "json"

    def test_celery_config_utc(self):
        from app.celery_app import celery_app
        assert celery_app.conf.enable_utc is True
        assert celery_app.conf.timezone == "UTC"

    def test_celery_config_acks_late(self):
        from app.celery_app import celery_app
        assert celery_app.conf.task_acks_late is True


class TestCeleryTasks:
    """Test Celery task registration."""

    def test_transcription_task_registered(self):
        from app.modules.transcription.tasks import process_transcription_task
        assert process_transcription_task.name == "transcription.process"
        assert process_transcription_task.max_retries == 3

    def test_upload_task_registered(self):
        from app.modules.transcription.tasks import process_upload_task
        assert process_upload_task.name == "transcription.process_upload"
        assert process_upload_task.max_retries == 3

    def test_conversation_task_registered(self):
        from app.modules.conversation.tasks import process_ai_response_task
        assert process_ai_response_task.name == "conversation.process_ai_response"


class TestCeleryAvailability:
    """Test Celery availability check in routes."""

    def test_celery_unavailable_returns_false(self):
        from app.modules.transcription.routes import _celery_available
        # Without a real Celery broker, should return False
        result = _celery_available()
        assert result is False
