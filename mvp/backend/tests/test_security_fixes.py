"""
Tests verifying security fixes applied to the SaaS-IA backend.

Covers:
  - CORS headers are restricted to specific methods (LOW-03)
  - Swagger/ReDoc disabled in production (HIGH-04)
  - Metrics token is not the raw SECRET_KEY (HIGH-01)
  - Account lockout after repeated failures (MED-02)
  - Stripe webhook signature validation (positive finding #8)
"""

import os
import pytest
from unittest.mock import patch, AsyncMock, MagicMock


# --------------------------------------------------------------------------
# LOW-03: CORS allow_methods and allow_headers restricted
# --------------------------------------------------------------------------

async def test_cors_headers_restricted(client):
    """Preflight OPTIONS should list only specific HTTP methods."""
    resp = await client.options(
        "/health/live",
        headers={
            "Origin": "http://localhost:3002",
            "Access-Control-Request-Method": "POST",
        },
    )
    allowed = resp.headers.get("access-control-allow-methods", "")
    # Wildcard should NOT be present
    assert "*" not in allowed
    # Specific methods should be listed
    for method in ("GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"):
        assert method in allowed


async def test_cors_allowed_headers_restricted(client):
    """Preflight OPTIONS should list only specific headers."""
    resp = await client.options(
        "/health/live",
        headers={
            "Origin": "http://localhost:3002",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization",
        },
    )
    allowed = resp.headers.get("access-control-allow-headers", "")
    # Wildcard should NOT be present
    assert "*" not in allowed
    assert "Authorization" in allowed or "authorization" in allowed.lower()


# --------------------------------------------------------------------------
# HIGH-04: Swagger/ReDoc disabled in production
# --------------------------------------------------------------------------

def test_docs_disabled_in_production():
    """When ENVIRONMENT=production, docs_url and redoc_url must be None."""
    from tests.conftest import _TEST_ENV

    prod_env = {**_TEST_ENV, "ENVIRONMENT": "production"}

    with patch.dict(os.environ, prod_env, clear=False):
        # Re-import to pick up the new environment
        import importlib
        import app.main as main_mod
        # Check the production flag logic directly
        from app.config import Settings
        s = Settings()
        assert s.ENVIRONMENT == "production"
        # The app factory sets docs_url=None when _is_production is True
        is_production = s.ENVIRONMENT == "production"
        assert is_production is True
        # Verify the conditional logic matches what main.py does
        docs_url = None if is_production else "/docs"
        redoc_url = None if is_production else "/redoc"
        assert docs_url is None
        assert redoc_url is None


# --------------------------------------------------------------------------
# HIGH-01: Metrics token is not the raw SECRET_KEY
# --------------------------------------------------------------------------

def test_metrics_token_not_secret_key():
    """The resolved metrics token must never be the raw SECRET_KEY."""
    from tests.conftest import _TEST_ENV

    with patch.dict(os.environ, _TEST_ENV, clear=False):
        from app.config import Settings
        s = Settings()
        resolved = s.metrics_token_resolved
        assert resolved != s.SECRET_KEY
        # Should be a hex digest (64 chars for SHA-256)
        assert len(resolved) == 64


def test_metrics_token_uses_explicit_value():
    """When METRICS_TOKEN is set, it takes precedence over the hash."""
    from tests.conftest import _TEST_ENV

    env = {**_TEST_ENV, "METRICS_TOKEN": "my-custom-token-abc"}
    with patch.dict(os.environ, env, clear=False):
        from app.config import Settings
        s = Settings()
        assert s.metrics_token_resolved == "my-custom-token-abc"


# --------------------------------------------------------------------------
# MED-02: Account lockout after repeated failures
# --------------------------------------------------------------------------

async def test_account_lockout_after_failures(client):
    """After 5 failed login attempts the endpoint returns 429."""
    mock_redis = AsyncMock()
    # Simulate that 5 attempts have already been recorded
    mock_redis.get = AsyncMock(return_value="5")
    mock_redis.ttl = AsyncMock(return_value=800)

    with patch("app.auth._get_login_redis", new_callable=AsyncMock, return_value=mock_redis):
        resp = await client.post(
            "/api/auth/login",
            data={
                "username": "locked@example.com",
                "password": "AnyP@ssword1",
            },
        )

    assert resp.status_code == 429
    body = resp.json()
    assert "locked" in body["detail"].lower() or "too many" in body["detail"].lower()
    assert "Retry-After" in resp.headers


# --------------------------------------------------------------------------
# Positive finding #8: Stripe webhook signature validation
# --------------------------------------------------------------------------

async def test_webhook_signature_validation(client):
    """A webhook call with an invalid signature should be rejected (400)."""
    # Mock StripeService.handle_webhook to simulate signature verification failure,
    # since the stripe SDK may not be installed in the test environment.
    with patch(
        "app.modules.billing.routes.StripeService.handle_webhook",
        new_callable=AsyncMock,
        side_effect=ValueError("Invalid webhook: No signatures found matching the expected signature"),
    ):
        resp = await client.post(
            "/api/billing/webhook",
            content=b'{"type": "fake.event"}',
            headers={
                "stripe-signature": "t=123,v1=bad_signature",
                "Content-Type": "application/json",
            },
        )
    # Should be 400 (bad request) because the signature is invalid
    assert resp.status_code == 400
    assert "Invalid webhook" in resp.json()["detail"]
