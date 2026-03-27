"""
Route-level tests: verify that require_verified_email is wired up on the
right endpoints.

Strategy: mock the guard itself (not the DB or auth layer) so that:
  - "unverified" path  → guard raises HTTPException(403, EMAIL_NOT_VERIFIED)
  - "verified"  path   → guard returns a mock User and any downstream service
                         is also mocked to avoid DB/network calls.

Actual URL prefixes (from manifest.json):
  - /api/keys/          (module: api_keys)
  - /api/billing/…      (module: billing)
  - /api/social-publisher/… (module: social_publisher)
"""

import os
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
import httpx
from fastapi import HTTPException

# Ensure env vars are set before any app import
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-unit-tests-only")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test_saas_ia")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
os.environ.setdefault("ASSEMBLYAI_API_KEY", "MOCK")
os.environ.setdefault("GEMINI_API_KEY", "MOCK")
os.environ.setdefault("CLAUDE_API_KEY", "MOCK")
os.environ.setdefault("GROQ_API_KEY", "MOCK")

pytestmark = pytest.mark.anyio


# ---------------------------------------------------------------------------
# Fixture: reset_rate_limiter (autouse — resets slowapi in-memory storage between tests)
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_rate_limiter():
    from limits.storage import MemoryStorage
    from limits.strategies import FixedWindowRateLimiter
    from app.rate_limit import limiter
    limiter._storage = MemoryStorage()
    limiter._limiter = FixedWindowRateLimiter(limiter._storage)
    yield


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

GUARD_PATH = "app.modules.auth_guards.middleware.require_verified_email"


def _mock_user():
    user = MagicMock()
    user.id = uuid4()
    user.email = "verified@example.com"
    user.email_verified = True
    return user


def _guard_raises_403():
    """Return an async callable that always raises the 403 guard error."""
    async def _raise():
        raise HTTPException(
            status_code=403,
            detail={
                "code": "EMAIL_NOT_VERIFIED",
                "message": "Please verify your email address before using this feature.",
                "action": "resend_verification",
            },
        )
    return _raise


def _guard_returns_user(user):
    """Return an async callable that returns the given mock user."""
    async def _pass():
        return user
    return _pass


async def _make_client(app):
    """Create an httpx.AsyncClient wired to the ASGI app (no real server)."""
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://testserver")


# ---------------------------------------------------------------------------
# Fixture: bare app instance with DB/Redis lifecycle mocked out
# ---------------------------------------------------------------------------

@pytest.fixture()
def _app():
    with patch("app.database.init_db", new_callable=AsyncMock), \
         patch("app.database.engine") as mock_engine, \
         patch("app.cache._get_redis", new_callable=AsyncMock, return_value=None):
        mock_engine.dispose = AsyncMock()
        from app.main import app as _a
        yield _a


# ---------------------------------------------------------------------------
# 1. POST /api/keys/ — api_keys module
# ---------------------------------------------------------------------------

async def test_create_api_key_403_when_not_verified(_app):
    """Guard raises 403 → endpoint returns 403 with EMAIL_NOT_VERIFIED."""
    _app.dependency_overrides[
        _import_guard()
    ] = _guard_raises_403()

    try:
        async with await _make_client(_app) as client:
            resp = await client.post(
                "/api/keys/",
                json={"name": "my-key", "permissions": ["read"]},
            )
        assert resp.status_code == 403
        assert resp.json()["detail"]["code"] == "EMAIL_NOT_VERIFIED"
    finally:
        _app.dependency_overrides.clear()


async def test_create_api_key_201_when_verified(_app):
    """Guard passes → endpoint proceeds; service is mocked to avoid DB."""
    user = _mock_user()
    _app.dependency_overrides[_import_guard()] = _guard_returns_user(user)

    mock_api_key = MagicMock()
    mock_api_key.id = uuid4()
    mock_api_key.name = "my-key"
    mock_api_key.key_prefix = "sk-test"
    mock_api_key.rate_limit_per_day = 1000

    with patch(
        "app.modules.api_keys.service.APIKeyService.create_key",
        new_callable=AsyncMock,
        return_value=(mock_api_key, "sk-test-raw-key-value"),
    ):
        try:
            async with await _make_client(_app) as client:
                resp = await client.post(
                    "/api/keys/",
                    json={"name": "my-key", "permissions": ["read"]},
                )
            assert resp.status_code == 201
        finally:
            _app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# 2. POST /api/billing/checkout
# ---------------------------------------------------------------------------

async def test_billing_checkout_403_when_not_verified(_app):
    """Billing checkout is blocked for unverified users."""
    _app.dependency_overrides[_import_guard()] = _guard_raises_403()

    try:
        async with await _make_client(_app) as client:
            resp = await client.post(
                "/api/billing/checkout",
                json={"plan_name": "pro"},
            )
        assert resp.status_code == 403
        assert resp.json()["detail"]["code"] == "EMAIL_NOT_VERIFIED"
    finally:
        _app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# 3. POST /api/billing/portal
# ---------------------------------------------------------------------------

async def test_billing_portal_403_when_not_verified(_app):
    """Billing portal is blocked for unverified users."""
    _app.dependency_overrides[_import_guard()] = _guard_raises_403()

    try:
        async with await _make_client(_app) as client:
            resp = await client.post("/api/billing/portal")
        assert resp.status_code == 403
        assert resp.json()["detail"]["code"] == "EMAIL_NOT_VERIFIED"
    finally:
        _app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# 4. POST /api/social-publisher/accounts
# ---------------------------------------------------------------------------

async def test_social_connect_account_403_when_not_verified(_app):
    """Connecting a social account is blocked for unverified users."""
    _app.dependency_overrides[_import_guard()] = _guard_raises_403()

    try:
        async with await _make_client(_app) as client:
            resp = await client.post(
                "/api/social-publisher/accounts",
                json={
                    "platform": "twitter",
                    "access_token": "tok",
                    "account_name": "myhandle",
                },
            )
        assert resp.status_code == 403
        assert resp.json()["detail"]["code"] == "EMAIL_NOT_VERIFIED"
    finally:
        _app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# 5. POST /api/social-publisher/posts
# ---------------------------------------------------------------------------

async def test_social_create_post_403_when_not_verified(_app):
    """Creating a social post is blocked for unverified users."""
    _app.dependency_overrides[_import_guard()] = _guard_raises_403()

    try:
        async with await _make_client(_app) as client:
            resp = await client.post(
                "/api/social-publisher/posts",
                json={
                    "content": "Hello world",
                    "platforms": ["twitter"],
                },
            )
        assert resp.status_code == 403
        assert resp.json()["detail"]["code"] == "EMAIL_NOT_VERIFIED"
    finally:
        _app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Lazy import helper — avoids circular import at module load time
# ---------------------------------------------------------------------------

def _import_guard():
    from app.modules.auth_guards.middleware import require_verified_email
    return require_verified_email
