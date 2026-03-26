# Integration Tests

Configurable integration test suite for the SaaS-IA platform. Tests can run against mock (in-memory) or real (PostgreSQL + Redis) backends, controlled by environment variables.

## Quick Start

### Mock mode (default, no external dependencies)

```bash
cd mvp/backend
USE_REAL_DB=false USE_REAL_REDIS=false python -m pytest tests/integration/ -v --tb=short --no-cov

# Or via Makefile (from mvp/):
make test-integration
```

### Real mode (requires Docker services)

```bash
# Start infrastructure
cd mvp && docker compose up -d postgres redis

# Run tests
cd mvp/backend
USE_REAL_DB=true USE_REAL_REDIS=true python -m pytest tests/integration/ -v --tb=short --no-cov

# Or via Makefile (from mvp/):
make test-integration-real
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `USE_REAL_DB` | `false` | `true` = PostgreSQL via `TEST_DATABASE_URL`, `false` = SQLite in-memory |
| `USE_REAL_REDIS` | `false` | `true` = Redis via `TEST_REDIS_URL`, `false` = dict-based mock |
| `TEST_DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5435/saas_ia_test` | PostgreSQL connection string (only used when `USE_REAL_DB=true`) |
| `TEST_REDIS_URL` | `redis://localhost:6382/15` | Redis URL using DB 15 for test isolation (only used when `USE_REAL_REDIS=true`) |

## Test Files

| File | Tests | Description |
|---|---|---|
| `conftest.py` | -- | Shared fixtures: `db_engine`, `session`, `redis_client`, `client`, `auth_headers`, `cleanup` |
| `test_full_lifecycle.py` | ~30 | End-to-end lifecycle: auth, transcription, content pipeline, chatbot, marketplace, conversation, knowledge, cross-module |
| `test_database.py` | ~15 | Schema validation, CRUD operations, connection pooling, Alembic migrations |
| `test_redis.py` | ~10 | Cache ops, rate limiting, token blacklist, feature flags, TTL expiry |
| `test_modules_loading.py` | ~10 | Module discovery, manifest validation, endpoint registration, health probes, middleware |
| `test_websocket.py` | ~8 | WebSocket auth, messaging, rooms, presence |

## Design Principles

1. **Dual-mode**: Every test works in both mock and real mode. Tests that require a specific backend use `@pytest.mark.skipif`.

2. **Isolation**: Each test gets a fresh database session (rolled back after test in mock mode, tables truncated in real mode). Redis is flushed after each test.

3. **No unit test impact**: Integration tests live in `tests/integration/` -- existing unit tests in `tests/` remain unchanged.

4. **Graceful degradation**: Lifecycle tests use `pytest.skip()` when an endpoint is unavailable (e.g., quota limits, missing AI provider) rather than failing hard.

5. **Autouse cleanup**: The `cleanup` fixture runs after every test to ensure a clean state.

## Fixtures

### `db_engine` (session-scoped)
Creates the database engine. Real mode uses PostgreSQL with `create_all`/`drop_all`. Mock mode uses SQLite in-memory.

### `session` (function-scoped)
Provides an async SQLAlchemy session. Rolls back after each test.

### `redis_client` (function-scoped)
Provides a Redis client. Real mode uses `redis.asyncio`. Mock mode uses an in-memory `MockRedis` class with dict storage.

### `client` (function-scoped)
httpx `AsyncClient` with the full FastAPI app and overridden dependencies (session, Redis).

### `auth_headers` (function-scoped)
Authorization headers with a valid JWT for a real database user (requires `test_user_in_db`).

### `auth_headers_static` (function-scoped)
Authorization headers with a statically-generated JWT. Does not require a DB user -- useful for module loading tests.

### `cleanup` (autouse)
Post-test cleanup: truncates tables (real) or recreates schema (mock), flushes Redis.
