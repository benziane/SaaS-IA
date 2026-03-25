"""
Sentry / GlitchTip error tracking for the SaaS-IA platform.

Initialises the Sentry SDK with FastAPI, SQLAlchemy, Celery, Redis, HTTPX,
asyncio, and logging integrations. Filters noisy exceptions and health-check
transactions to keep the event budget focused on real issues.

All sentry_sdk imports are wrapped in try/except ImportError so the
application starts normally when sentry-sdk is not installed.

Usage (in lifespan or main.py):
    from app.core.error_tracking import init_error_tracking

    init_error_tracking()
"""

import asyncio
import os
from typing import Any

import structlog

from app.config import settings
from app.middleware.request_id import request_id_ctx

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# Graceful degradation: sentry-sdk is optional
# ---------------------------------------------------------------------------

HAS_SENTRY = False

try:
    import sentry_sdk

    HAS_SENTRY = True
except ImportError:
    pass


# ---------------------------------------------------------------------------
# Event filters
# ---------------------------------------------------------------------------

_IGNORED_EXCEPTIONS = (
    ConnectionResetError,
    BrokenPipeError,
    asyncio.CancelledError,
)


def _before_send(event: dict[str, Any], hint: dict[str, Any]) -> dict[str, Any] | None:
    """
    Pre-send hook: drop noisy exceptions and enrich events with request_id.
    """
    if "exc_info" in hint:
        exc_type, exc_value, _tb = hint["exc_info"]
        if isinstance(exc_value, _IGNORED_EXCEPTIONS):
            return None

    # Enrich with request_id from contextvars
    rid = request_id_ctx.get()
    if rid:
        event.setdefault("tags", {})["request_id"] = rid

    return event


def _before_send_transaction(
    event: dict[str, Any], hint: dict[str, Any]
) -> dict[str, Any] | None:
    """
    Pre-send hook for transactions: drop health-check and metrics endpoints
    to avoid polluting the performance dashboard.
    """
    transaction_name = event.get("transaction", "")
    if "/health/" in transaction_name or "/metrics" in transaction_name:
        return None
    return event


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

def init_error_tracking() -> None:
    """
    Initialise Sentry / GlitchTip error tracking.

    Reads the DSN from ``settings.SENTRY_DSN`` (if the attribute exists) or
    the ``SENTRY_DSN`` environment variable. If neither is set the function
    logs a message and returns without error.

    Safe to call even when sentry-sdk is not installed.
    """
    if not HAS_SENTRY:
        logger.info("error_tracking_skipped", reason="sentry-sdk not installed")
        return

    dsn = getattr(settings, "SENTRY_DSN", None) or os.getenv("SENTRY_DSN", "")
    if not dsn:
        logger.info("error_tracking_disabled", reason="SENTRY_DSN not configured")
        return

    is_production = settings.ENVIRONMENT.lower() == "production"
    version = getattr(settings, "APP_VERSION", None) or os.getenv("APP_VERSION", "1.0.0")

    # Collect integrations that are actually importable
    integrations: list = []

    try:
        from sentry_sdk.integrations.fastapi import FastApiIntegration

        integrations.append(FastApiIntegration(transaction_style="endpoint"))
    except ImportError:
        pass

    try:
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

        integrations.append(SqlalchemyIntegration())
    except ImportError:
        pass

    try:
        from sentry_sdk.integrations.celery import CeleryIntegration

        integrations.append(CeleryIntegration())
    except ImportError:
        pass

    try:
        from sentry_sdk.integrations.redis import RedisIntegration

        integrations.append(RedisIntegration())
    except ImportError:
        pass

    try:
        from sentry_sdk.integrations.httpx import HttpxIntegration

        integrations.append(HttpxIntegration())
    except ImportError:
        pass

    try:
        from sentry_sdk.integrations.asyncio import AsyncioIntegration

        integrations.append(AsyncioIntegration())
    except ImportError:
        pass

    try:
        from sentry_sdk.integrations.logging import LoggingIntegration

        integrations.append(LoggingIntegration(event_level="ERROR"))
    except ImportError:
        pass

    sentry_sdk.init(
        dsn=dsn,
        environment=settings.ENVIRONMENT,
        release=f"saas-ia@{version}",
        traces_sample_rate=0.1 if is_production else 1.0,
        send_default_pii=False,
        integrations=integrations,
        before_send=_before_send,
        before_send_transaction=_before_send_transaction,
    )

    logger.info(
        "error_tracking_initialized",
        environment=settings.ENVIRONMENT,
        integrations_count=len(integrations),
    )
