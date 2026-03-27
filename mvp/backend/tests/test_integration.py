"""
Integration tests for SaaS-IA API endpoints.

Uses httpx.AsyncClient with SQLite async in-memory database.
Tests actual HTTP request/response flow through FastAPI.
"""

import os
import pytest
import asyncio
from datetime import datetime
from uuid import uuid4

# Set test env before any app imports
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-integration-tests")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "")
os.environ.setdefault("ASSEMBLYAI_API_KEY", "MOCK")
os.environ.setdefault("GEMINI_API_KEY", "MOCK")
os.environ.setdefault("CLAUDE_API_KEY", "MOCK")
os.environ.setdefault("GROQ_API_KEY", "MOCK")

import httpx
from unittest.mock import AsyncMock, patch
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession as SAAsyncSession
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import get_session
from app.auth import get_password_hash, create_access_token
from app.models.user import User, Role
from app.models.transcription import Transcription, TranscriptionStatus  # noqa: F401
from app.models.conversation import Conversation, Message  # noqa: F401
from app.models.billing import Plan, UserQuota  # noqa: F401
from app.models.compare import ComparisonResult, ComparisonVote  # noqa: F401
from app.models.pipeline import Pipeline, PipelineExecution  # noqa: F401
from app.models.knowledge import Document, DocumentChunk  # noqa: F401
from app.models.api_key import APIKey  # noqa: F401
from app.models.workspace import Workspace, WorkspaceMember, SharedItem, Comment  # noqa: F401


# ---------------------------------------------------------------------------
# Redis isolation — session-scoped, autouse
# ---------------------------------------------------------------------------
# When the full pytest suite runs, earlier test modules import app.rate_limit
# (with a real Redis URL from tests/conftest.py), creating Redis-backed
# singletons before this file can override REDIS_URL.  The setdefault() calls
# above arrive too late for those module-level singletons.
#
# Fix A: Replace the SlowAPI limiter's storage with an in-memory backend so
#         @limiter.limit() decorators never touch Redis.
# Fix B: Reset app.cache._redis_client to None so the lazy getter re-evaluates
#         REDIS_URL on the first async call, and patch _get_redis to return a
#         lightweight in-memory mock so login-lockout, feature-flags, token-
#         blacklist, and the sliding-window middleware all work without Redis.

class _MockRedis:
    """Minimal in-memory Redis mock for test isolation."""

    def __init__(self):
        self._store: dict = {}

    async def ping(self) -> bool:
        return True

    async def get(self, key: str):
        return self._store.get(key)

    async def set(self, key: str, value, ex: int = None, px: int = None):
        self._store[key] = value
        return True

    # alias used by some Redis clients
    async def setex(self, key: str, time: int, value):
        self._store[key] = value
        return True

    async def delete(self, *keys: str):
        for k in keys:
            self._store.pop(k, None)
        return len(keys)

    async def exists(self, *keys: str) -> int:
        return sum(1 for k in keys if k in self._store)

    async def incr(self, key: str) -> int:
        val = int(self._store.get(key, 0)) + 1
        self._store[key] = val
        return val

    async def expire(self, key: str, seconds: int) -> bool:
        return key in self._store

    async def ttl(self, key: str) -> int:
        return -2 if key not in self._store else -1

    async def keys(self, pattern: str = "*"):
        return list(self._store.keys())

    async def flushdb(self):
        self._store.clear()

    async def aclose(self):
        pass

    async def close(self):
        pass

    def pipeline(self, transaction: bool = True):
        return _MockPipeline(self)

    async def scan_iter(self, match: str = "*"):
        import fnmatch
        for k in list(self._store.keys()):
            if fnmatch.fnmatch(k, match):
                yield k


class _MockPipeline:
    def __init__(self, redis: "_MockRedis"):
        self._redis = redis
        self._commands: list = []

    def incr(self, key):
        self._commands.append(("incr", key)); return self

    def expire(self, key, seconds):
        self._commands.append(("expire", key, seconds)); return self

    def set(self, key, value, ex=None):
        self._commands.append(("set", key, value, ex)); return self

    def get(self, key):
        self._commands.append(("get", key)); return self

    def delete(self, *keys):
        self._commands.append(("delete", *keys)); return self

    def zadd(self, key, mapping):
        self._commands.append(("zadd", key, mapping)); return self

    def zremrangebyscore(self, key, min_score, max_score):
        self._commands.append(("zremrangebyscore", key, min_score, max_score)); return self

    def zcard(self, key):
        self._commands.append(("zcard", key)); return self

    async def execute(self):
        results = []
        for cmd in self._commands:
            op = cmd[0]
            if op == "incr":
                results.append(await self._redis.incr(cmd[1]))
            elif op == "expire":
                results.append(await self._redis.expire(cmd[1], cmd[2]))
            elif op == "set":
                results.append(await self._redis.set(cmd[1], cmd[2], ex=cmd[3] if len(cmd) > 3 else None))
            elif op == "get":
                results.append(await self._redis.get(cmd[1]))
            elif op == "delete":
                results.append(await self._redis.delete(*cmd[1:]))
            elif op in ("zadd", "zremrangebyscore", "zcard"):
                results.append(0)
            else:
                results.append(None)
        self._commands.clear()
        return results


_mock_redis_instance = _MockRedis()


@pytest.fixture(scope="session", autouse=True)
def _patch_app_state():
    """
    Session-scoped fixture that patches all Redis-dependent app singletons
    to use an in-memory mock, ensuring no real Redis connection is attempted.

    Patches applied:
    1. SlowAPI limiter storage -> MemoryStorage (fixes @limiter.limit() decorators)
    2. app.cache._get_redis -> returns _mock_redis_instance (fixes login lockout,
       token blacklist, feature flags, sliding-window rate limiter)
    3. app.cache._redis_client reset to None so the lazy getter is clean
    """
    import app.cache as _cache_mod
    from limits.storage import MemoryStorage
    from limits.strategies import FixedWindowRateLimiter
    from app.rate_limit import limiter

    # Fix 1: SlowAPI limiter -> in-memory storage
    _orig_storage = limiter._storage
    _orig_limiter = limiter._limiter
    mem_storage = MemoryStorage()
    mem_limiter = FixedWindowRateLimiter(mem_storage)
    limiter._storage = mem_storage
    limiter._limiter = mem_limiter

    # Fix 2 & 3: Reset the lazy Redis singleton and patch _get_redis
    _orig_redis_client = _cache_mod._redis_client
    _cache_mod._redis_client = None

    async def _mock_get_redis():
        return _mock_redis_instance

    with patch("app.cache._get_redis", side_effect=_mock_get_redis):
        yield

    # Restore originals
    limiter._storage = _orig_storage
    limiter._limiter = _orig_limiter
    _cache_mod._redis_client = _orig_redis_client


# ---------------------------------------------------------------------------
# Test database setup
# ---------------------------------------------------------------------------

TEST_ENGINE = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    echo=False,
    future=True,
)

TestSessionLocal = sessionmaker(
    TEST_ENGINE,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def override_get_session():
    async with TestSessionLocal() as session:
        yield session


# Override the dependency
app.dependency_overrides[get_session] = override_get_session


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
async def setup_db():
    """Create all tables before each test, drop after.  Also clears module-
    level caches (feature flags, mock Redis) so tests are fully isolated."""
    # Clear feature-flag in-memory caches populated by previous tests
    from app.core.feature_flags import _flag_cache
    from app.middleware.feature_flag_middleware import _module_flag_cache
    _flag_cache.clear()
    _module_flag_cache.clear()
    # Reset mock Redis so each test starts with a clean slate
    _mock_redis_instance._store.clear()

    async with TEST_ENGINE.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with TEST_ENGINE.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest.fixture()
async def test_user():
    """Create a test user in the database."""
    async with TestSessionLocal() as session:
        user = User(
            email="integration@test.com",
            hashed_password=get_password_hash("TestPassword123!"),
            full_name="Integration Tester",
            role=Role.USER,
            is_active=True,
            email_verified=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


@pytest.fixture()
def auth_token(test_user):
    """Create a JWT token for the test user."""
    return create_access_token(data={"sub": test_user.email})


@pytest.fixture()
def auth_headers(auth_token):
    """HTTP headers with Bearer token."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture()
async def client():
    """Create an httpx async test client."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac


# ---------------------------------------------------------------------------
# Health & Root
# ---------------------------------------------------------------------------

class TestHealthEndpoints:
    """Test basic health and root endpoints."""

    @pytest.mark.asyncio
    async def test_root(self, client):
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "SaaS-IA" in data["message"]

    @pytest.mark.asyncio
    async def test_health(self, client):
        _up = {"status": "up", "latency_ms": 0.1}
        with (
            patch("app.api.health._check_postgres", new_callable=AsyncMock, return_value=_up),
            patch("app.api.health._check_redis", new_callable=AsyncMock, return_value=_up),
        ):
            response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_modules_list_requires_auth(self, client):
        """Since HIGH-05 fix, /api/modules requires authentication."""
        response = await client.get("/api/modules")
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class TestAuthEndpoints:
    """Test authentication endpoints."""

    @pytest.mark.asyncio
    async def test_register(self, client):
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecureP@ss123",
                "full_name": "New User",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client, test_user):
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "integration@test.com",
                "password": "SecureP@ss123",
                "full_name": "Duplicate User",
            },
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_login(self, client, test_user):
        response = await client.post(
            "/api/auth/login",
            data={
                "username": "integration@test.com",
                "password": "TestPassword123!",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client, test_user):
        response = await client.post(
            "/api/auth/login",
            data={
                "username": "integration@test.com",
                "password": "WrongPassword1",
            },
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_me(self, client, auth_headers):
        response = await client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "integration@test.com"

    @pytest.mark.asyncio
    async def test_me_unauthorized(self, client):
        response = await client.get("/api/auth/me")
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Billing
# ---------------------------------------------------------------------------

class TestBillingEndpoints:
    """Test billing endpoints."""

    @pytest.mark.asyncio
    async def test_get_plans(self, client):
        response = await client.get("/api/billing/plans")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3
        names = [p["name"] for p in data]
        assert "free" in names
        assert "pro" in names

    @pytest.mark.asyncio
    async def test_get_quota(self, client, auth_headers):
        response = await client.get("/api/billing/quota", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "plan" in data
        assert "transcriptions_used" in data
        assert "transcriptions_limit" in data
        assert data["transcriptions_used"] == 0

    @pytest.mark.asyncio
    async def test_get_quota_unauthorized(self, client):
        response = await client.get("/api/billing/quota")
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Transcription
# ---------------------------------------------------------------------------

class TestTranscriptionEndpoints:
    """Test transcription endpoints."""

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires PostgreSQL - SQLite in-memory doesn't share state across connections for billing quota check")
    async def test_create_transcription(self, client, auth_headers):
        response = await client.post(
            "/api/transcription/",
            json={
                "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "language": "auto",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_list_transcriptions(self, client, auth_headers):
        response = await client.get("/api/transcription/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_get_stats(self, client, auth_headers):
        response = await client.get("/api/transcription/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_transcriptions" in data


# ---------------------------------------------------------------------------
# Conversations
# ---------------------------------------------------------------------------

class TestConversationEndpoints:
    """Test conversation endpoints."""

    @pytest.mark.asyncio
    async def test_create_conversation(self, client, auth_headers):
        response = await client.post(
            "/api/conversations/",
            json={},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert "id" in data

    @pytest.mark.asyncio
    async def test_list_conversations(self, client, auth_headers):
        response = await client.get("/api/conversations/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    @pytest.mark.asyncio
    async def test_delete_nonexistent_conversation(self, client, auth_headers):
        fake_id = str(uuid4())
        response = await client.delete(
            f"/api/conversations/{fake_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Pipelines
# ---------------------------------------------------------------------------

class TestPipelineEndpoints:
    """Test pipeline endpoints."""

    @pytest.mark.asyncio
    async def test_create_pipeline(self, client, auth_headers):
        response = await client.post(
            "/api/pipelines/",
            json={
                "name": "Test Pipeline",
                "description": "A test pipeline",
                "steps": [
                    {"id": "s1", "type": "summarize", "config": {}, "position": 0},
                ],
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Pipeline"
        assert len(data["steps"]) == 1

    @pytest.mark.asyncio
    async def test_list_pipelines(self, client, auth_headers):
        response = await client.get("/api/pipelines/", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_pipeline_crud(self, client, auth_headers):
        # Create
        create_resp = await client.post(
            "/api/pipelines/",
            json={"name": "CRUD Test", "steps": []},
            headers=auth_headers,
        )
        assert create_resp.status_code == 201
        pipeline_id = create_resp.json()["id"]

        # Get
        get_resp = await client.get(f"/api/pipelines/{pipeline_id}", headers=auth_headers)
        assert get_resp.status_code == 200
        assert get_resp.json()["name"] == "CRUD Test"

        # Update
        update_resp = await client.put(
            f"/api/pipelines/{pipeline_id}",
            json={"name": "Updated Name"},
            headers=auth_headers,
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["name"] == "Updated Name"

        # Delete
        delete_resp = await client.delete(f"/api/pipelines/{pipeline_id}", headers=auth_headers)
        assert delete_resp.status_code == 204


# ---------------------------------------------------------------------------
# Knowledge Base
# ---------------------------------------------------------------------------

class TestKnowledgeEndpoints:
    """Test knowledge base endpoints."""

    @pytest.mark.asyncio
    async def test_list_documents_empty(self, client, auth_headers):
        response = await client.get("/api/knowledge/documents", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_upload_document(self, client, auth_headers):
        content = b"This is a test document with some content for chunking."
        response = await client.post(
            "/api/knowledge/upload",
            files={"file": ("test.txt", content, "text/plain")},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["filename"] == "test.txt"
        assert data["status"] == "indexed"
        assert data["total_chunks"] >= 1

    @pytest.mark.asyncio
    async def test_search_documents(self, client, auth_headers):
        # Upload first
        content = b"Machine learning is a subset of artificial intelligence that focuses on training models."
        await client.post(
            "/api/knowledge/upload",
            files={"file": ("ml.txt", content, "text/plain")},
            headers=auth_headers,
        )

        # Search
        response = await client.post(
            "/api/knowledge/search",
            json={"query": "machine learning"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_upload_unsupported_format(self, client, auth_headers):
        response = await client.post(
            "/api/knowledge/upload",
            files={"file": ("test.pdf", b"fake pdf", "application/pdf")},
            headers=auth_headers,
        )
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# API Keys
# ---------------------------------------------------------------------------

class TestAPIKeyEndpoints:
    """Test API key management endpoints."""

    @pytest.mark.asyncio
    async def test_create_api_key(self, client, auth_headers):
        response = await client.post(
            "/api/keys/",
            json={"name": "Test Key"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Key"
        assert "key" in data
        assert data["key"].startswith("sk-")

    @pytest.mark.asyncio
    async def test_list_api_keys(self, client, auth_headers):
        # Create a key first
        await client.post(
            "/api/keys/",
            json={"name": "List Test"},
            headers=auth_headers,
        )

        response = await client.get("/api/keys/", headers=auth_headers)
        assert response.status_code == 200
        keys = response.json()
        assert len(keys) >= 1
        # Key secret should NOT be in list response
        assert "key" not in keys[0] or keys[0].get("key") is None

    @pytest.mark.asyncio
    async def test_revoke_api_key(self, client, auth_headers):
        # Create
        create_resp = await client.post(
            "/api/keys/",
            json={"name": "Revoke Test"},
            headers=auth_headers,
        )
        key_id = create_resp.json()["id"]

        # Revoke
        revoke_resp = await client.delete(f"/api/keys/{key_id}", headers=auth_headers)
        assert revoke_resp.status_code == 204

    @pytest.mark.asyncio
    async def test_revoke_nonexistent_key(self, client, auth_headers):
        response = await client.delete(f"/api/keys/{uuid4()}", headers=auth_headers)
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Public API v1
# ---------------------------------------------------------------------------

class TestPublicAPIv1:
    """Test public API v1 endpoints with API key auth."""

    @pytest.mark.asyncio
    async def test_public_api_no_key(self, client):
        response = await client.post("/v1/transcribe", json={"video_url": "test"})
        assert response.status_code in [401, 422]

    @pytest.mark.asyncio
    async def test_public_api_invalid_key(self, client):
        response = await client.post(
            "/v1/transcribe",
            json={"video_url": "test"},
            headers={"X-API-Key": "sk-invalid-key"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_public_api_get_job_not_found(self, client, auth_headers):
        # Create a real API key
        create_resp = await client.post(
            "/api/keys/",
            json={"name": "Public Test"},
            headers=auth_headers,
        )
        api_key = create_resp.json()["key"]

        response = await client.get(
            f"/v1/jobs/{uuid4()}",
            headers={"X-API-Key": api_key},
        )
        assert response.status_code == 404
