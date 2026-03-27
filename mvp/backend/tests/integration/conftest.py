"""
Integration test fixtures -- configurable via USE_REAL_DB, USE_REAL_REDIS env vars.

Mock mode (default):
    USE_REAL_DB=false  -> SQLite in-memory (aiosqlite)
    USE_REAL_REDIS=false -> dict-based mock Redis

Real mode:
    USE_REAL_DB=true   -> PostgreSQL via TEST_DATABASE_URL
    USE_REAL_REDIS=true -> Redis via TEST_REDIS_URL
"""

import os
import json
import asyncio
import importlib
from datetime import UTC, datetime, timedelta
from uuid import uuid4
from typing import AsyncGenerator
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

# ---------------------------------------------------------------------------
# Configuration (read once at import time)
# ---------------------------------------------------------------------------

USE_REAL_DB = os.getenv("USE_REAL_DB", "false").lower() == "true"
USE_REAL_REDIS = os.getenv("USE_REAL_REDIS", "false").lower() == "true"
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5435/saas_ia_test",
)
TEST_REDIS_URL = os.getenv("TEST_REDIS_URL", "redis://localhost:6382/15")

# ---------------------------------------------------------------------------
# Environment overrides (must happen before any app import)
# ---------------------------------------------------------------------------

_TEST_ENV = {
    "ENVIRONMENT": "testing",
    "SECRET_KEY": "integration-test-secret-key-not-for-production",
    "ALGORITHM": "HS256",
    "ACCESS_TOKEN_EXPIRE_MINUTES": "30",
    "REFRESH_TOKEN_EXPIRE_DAYS": "7",
    "DATABASE_URL": TEST_DATABASE_URL if USE_REAL_DB else "postgresql+asyncpg://test:test@localhost:5432/test_db",
    "REDIS_URL": TEST_REDIS_URL if USE_REAL_REDIS else "redis://localhost:6379/15",
    "ASSEMBLYAI_API_KEY": "MOCK",
    "GEMINI_API_KEY": "MOCK",
    "CLAUDE_API_KEY": "MOCK",
    "GROQ_API_KEY": "MOCK",
    "DEBUG": "true",
    "LOG_LEVEL": "WARNING",
}

for key, value in _TEST_ENV.items():
    os.environ[key] = value


# ---------------------------------------------------------------------------
# Mock Redis implementation (dict-based, no fakeredis dependency)
# ---------------------------------------------------------------------------

class MockRedis:
    """Minimal async Redis mock backed by an in-memory dict."""

    def __init__(self):
        self._store: dict[str, str] = {}
        self._ttls: dict[str, float] = {}

    async def ping(self) -> bool:
        return True

    async def get(self, key: str):
        self._expire_check(key)
        return self._store.get(key)

    async def set(self, key: str, value: str, ex: int = None, px: int = None):
        self._store[key] = value
        if ex is not None:
            self._ttls[key] = asyncio.get_event_loop().time() + ex
        elif px is not None:
            self._ttls[key] = asyncio.get_event_loop().time() + (px / 1000.0)
        return True

    async def delete(self, *keys: str):
        count = 0
        for k in keys:
            if k in self._store:
                del self._store[k]
                self._ttls.pop(k, None)
                count += 1
        return count

    async def exists(self, *keys: str) -> int:
        count = 0
        for k in keys:
            self._expire_check(k)
            if k in self._store:
                count += 1
        return count

    async def incr(self, key: str) -> int:
        self._expire_check(key)
        val = int(self._store.get(key, "0")) + 1
        self._store[key] = str(val)
        return val

    async def expire(self, key: str, seconds: int) -> bool:
        if key in self._store:
            self._ttls[key] = asyncio.get_event_loop().time() + seconds
            return True
        return False

    async def ttl(self, key: str) -> int:
        self._expire_check(key)
        if key not in self._store:
            return -2
        if key not in self._ttls:
            return -1
        remaining = self._ttls[key] - asyncio.get_event_loop().time()
        return max(int(remaining), 0)

    async def keys(self, pattern: str = "*"):
        import fnmatch
        self._expire_check_all()
        return [k for k in self._store if fnmatch.fnmatch(k, pattern)]

    async def flushdb(self):
        self._store.clear()
        self._ttls.clear()

    async def aclose(self):
        pass

    async def close(self):
        pass

    def pipeline(self):
        return MockPipeline(self)

    async def scan_iter(self, match: str = "*"):
        import fnmatch
        self._expire_check_all()
        for k in list(self._store.keys()):
            if fnmatch.fnmatch(k, match):
                yield k

    def _expire_check(self, key: str):
        if key in self._ttls:
            try:
                now = asyncio.get_event_loop().time()
            except RuntimeError:
                return
            if now >= self._ttls[key]:
                self._store.pop(key, None)
                self._ttls.pop(key, None)

    def _expire_check_all(self):
        try:
            now = asyncio.get_event_loop().time()
        except RuntimeError:
            return
        expired = [k for k, t in self._ttls.items() if now >= t]
        for k in expired:
            self._store.pop(k, None)
            self._ttls.pop(k, None)


class MockPipeline:
    """Minimal pipeline mock that queues commands."""

    def __init__(self, redis: MockRedis):
        self._redis = redis
        self._commands: list = []

    def incr(self, key: str):
        self._commands.append(("incr", key))
        return self

    def expire(self, key: str, seconds: int):
        self._commands.append(("expire", key, seconds))
        return self

    def set(self, key: str, value: str, ex: int = None):
        self._commands.append(("set", key, value, ex))
        return self

    def get(self, key: str):
        self._commands.append(("get", key))
        return self

    def delete(self, *keys: str):
        self._commands.append(("delete", *keys))
        return self

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
        self._commands.clear()
        return results


# ---------------------------------------------------------------------------
# Model imports helper
# ---------------------------------------------------------------------------

# All known model modules. Each is imported silently; failures are ignored
# because some models use PostgreSQL-specific features (e.g. sa_type_kwargs)
# that are unavailable in SQLite mock mode.
_ALL_MODEL_MODULES = [
    "app.models.tenant",
    "app.models.user",
    "app.models.transcription",
    "app.models.conversation",
    "app.models.billing",
    "app.models.compare",
    "app.models.pipeline",
    "app.models.knowledge",
    "app.models.api_key",
    "app.models.workspace",
    "app.models.agent",
    "app.models.cost_tracking",
    "app.models.notification",
    "app.models.outbox",
    "app.models.audit_log",
    "app.models.secrets_manager",
    "app.models.skill_seekers",
    "app.models.content_studio",
    "app.models.ai_chatbot_builder",
    "app.models.marketplace",
    "app.models.social_publisher",
    "app.models.integration_hub",
    "app.models.voice_clone",
    "app.models.image_gen",
    "app.models.video_gen",
    "app.models.data_analyst",
    "app.models.fine_tuning",
    "app.models.multi_agent",
    "app.models.realtime_ai",
    "app.models.security_guardian",
    "app.models.workflow",
    "app.models.ai_memory",
    "app.models.ai_forms",
    "app.models.code_sandbox",
    "app.models.presentation_gen",
    "app.models.pdf_processor",
    "app.models.audio_studio",
    "app.models.repo_analyzer",
]


def _import_all_models():
    """Import all model modules, silently skipping failures."""
    for mod_path in _ALL_MODEL_MODULES:
        try:
            importlib.import_module(mod_path)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Fixture: reset_rate_limiter (autouse — resets slowapi in-memory storage between tests)
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_rate_limiter():
    from limits.storage import MemoryStorage
    from limits.strategies import FixedWindowRateLimiter
    from app.rate_limit import limiter
    original_storage = limiter._storage
    original_limiter = limiter._limiter
    limiter._storage = MemoryStorage()
    limiter._limiter = FixedWindowRateLimiter(limiter._storage)
    yield
    limiter._storage = original_storage
    limiter._limiter = original_limiter


# ---------------------------------------------------------------------------
# Fixture: db_engine
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def event_loop():
    """Create a session-scoped event loop for async fixtures."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def db_engine():
    """
    Create a database engine.

    - Real mode: async PostgreSQL engine using TEST_DATABASE_URL.
    - Mock mode: async SQLite in-memory engine.
    """
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlmodel import SQLModel

    # Import all models so metadata is populated
    _import_all_models()

    if USE_REAL_DB:
        engine = create_async_engine(
            TEST_DATABASE_URL,
            echo=False,
            future=True,
            pool_size=5,
            max_overflow=5,
            pool_pre_ping=True,
        )
    else:
        engine = create_async_engine(
            "sqlite+aiosqlite://",
            echo=False,
            future=True,
        )

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield engine

    if USE_REAL_DB:
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.drop_all)

    await engine.dispose()


# ---------------------------------------------------------------------------
# Fixture: session
# ---------------------------------------------------------------------------

@pytest.fixture()
async def session(db_engine):
    """
    Provide an async database session.

    Each test gets its own session. Uncommitted changes are rolled back
    on teardown.
    """
    from sqlalchemy.orm import sessionmaker
    from sqlmodel.ext.asyncio.session import AsyncSession

    async_session_factory = sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_factory() as sess:
        yield sess

        # Rollback any uncommitted changes
        await sess.rollback()


# ---------------------------------------------------------------------------
# Fixture: redis_client
# ---------------------------------------------------------------------------

_session_redis_client = None


@pytest.fixture(scope="session")
async def _session_redis():
    """Session-scoped Redis client (internal)."""
    global _session_redis_client
    if USE_REAL_REDIS:
        import redis.asyncio as aioredis
        _session_redis_client = aioredis.from_url(
            TEST_REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=5,
        )
        await _session_redis_client.ping()
        yield _session_redis_client
        await _session_redis_client.flushdb()
        await _session_redis_client.aclose()
    else:
        _session_redis_client = MockRedis()
        yield _session_redis_client


@pytest.fixture()
async def redis_client(_session_redis):
    """
    Provide a Redis client for each test.

    Uses the session-scoped client and flushes after each test.
    """
    yield _session_redis
    await _session_redis.flushdb()


# ---------------------------------------------------------------------------
# Fixture: client (httpx.AsyncClient with overridden dependencies)
# ---------------------------------------------------------------------------

@pytest.fixture()
async def client(db_engine, _session_redis):
    """
    Provide an httpx.AsyncClient wired to the real FastAPI app with
    overridden database session and Redis dependencies.

    NOTE: This fixture does NOT flush Redis or reset the DB between
    tests, allowing lifecycle test classes to share state across
    test methods.  Use the ``cleanup_db`` fixture explicitly when
    you need a clean database.
    """
    import httpx
    from sqlalchemy.orm import sessionmaker
    from sqlmodel.ext.asyncio.session import AsyncSession

    from app.database import get_session
    from app.main import app as fastapi_app

    async_session_factory = sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def override_get_session():
        async with async_session_factory() as sess:
            yield sess

    # Override DB session dependency
    fastapi_app.dependency_overrides[get_session] = override_get_session

    transport = httpx.ASGITransport(app=fastapi_app)

    # Provide the mock/real Redis to ALL Redis consumers in the app.
    # This ensures login lockout, token blacklist, and cache all use
    # the same Redis client (mock in mock mode, real in real mode).
    mock_redis_return = AsyncMock(return_value=_session_redis)

    with (
        patch("app.database.init_db", new_callable=AsyncMock),
        patch("app.database.engine") as mock_engine,
        patch("app.cache._get_redis", mock_redis_return),
        patch("app.core.token_blacklist._get_redis", mock_redis_return),
        patch("app.auth._get_login_redis", mock_redis_return),
    ):
        mock_engine.dispose = AsyncMock()
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as ac:
            yield ac

    fastapi_app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Fixture: cleanup_db (explicit, NOT autouse)
# ---------------------------------------------------------------------------

@pytest.fixture()
async def cleanup_db(db_engine):
    """
    Explicitly clean all database tables.

    Call this fixture when you need a fresh database state.
    NOT autouse -- lifecycle test classes share state across methods.
    """
    yield

    from sqlmodel import SQLModel

    if USE_REAL_DB:
        async with db_engine.begin() as conn:
            from sqlalchemy import text
            result = await conn.execute(
                text(
                    "SELECT tablename FROM pg_tables "
                    "WHERE schemaname = 'public'"
                )
            )
            tables = [row[0] for row in result.fetchall()]
            if tables:
                table_list = ", ".join(f'"{t}"' for t in tables)
                await conn.execute(
                    text(f"TRUNCATE TABLE {table_list} CASCADE")
                )
    else:
        async with db_engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.drop_all)
            await conn.run_sync(SQLModel.metadata.create_all)


# ---------------------------------------------------------------------------
# Fixture: test_user_in_db
# ---------------------------------------------------------------------------

@pytest.fixture()
async def test_user_in_db(session):
    """
    Create a real user in the database and return it.

    This user has a known password so integration tests can log in.
    """
    from app.auth import get_password_hash
    from app.models.user import User, Role

    user = User(
        id=uuid4(),
        email=f"integ_{uuid4().hex[:8]}@test.com",
        hashed_password=get_password_hash("IntegTest123!"),
        full_name="Integration Test User",
        role=Role.USER,
        is_active=True,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


# ---------------------------------------------------------------------------
# Fixture: auth_headers
# ---------------------------------------------------------------------------

@pytest.fixture()
def auth_headers(test_user_in_db):
    """
    Return Authorization headers with a valid JWT for the test user.

    Uses direct token creation (no HTTP login round-trip needed).
    """
    from app.auth import create_access_token

    token = create_access_token(data={"sub": test_user_in_db.email})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def auth_headers_static():
    """
    Return Authorization headers with a statically-generated JWT.

    Useful for tests that do not need a real DB user (e.g. module loading).
    """
    from jose import jwt

    secret = _TEST_ENV["SECRET_KEY"]
    algorithm = _TEST_ENV["ALGORITHM"]
    expire = datetime.now(UTC) + timedelta(minutes=30)

    payload = {
        "sub": "static-integ@test.com",
        "exp": expire,
        "type": "access",
    }
    token = jwt.encode(payload, secret, algorithm=algorithm)
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Helpers available to all integration tests
# ---------------------------------------------------------------------------

async def register_user(client, email: str, password: str, full_name: str = "Test User") -> dict:
    """Helper: register a user via API and return the response object."""
    resp = await client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "full_name": full_name},
    )
    return resp


async def login_user(client, email: str, password: str) -> dict:
    """Helper: login a user via API and return the response object."""
    resp = await client.post(
        "/api/auth/login",
        data={"username": email, "password": password},
    )
    return resp
