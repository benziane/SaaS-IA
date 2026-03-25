"""
Tests for Kubernetes-ready health check endpoints.

Endpoints tested:
  - GET /health/live   (liveness probe)
  - GET /health/ready  (readiness probe)
  - GET /health/startup (startup probe)
"""

import pytest
from unittest.mock import AsyncMock, patch


# --------------------------------------------------------------------------
# Liveness probe
# --------------------------------------------------------------------------

async def test_liveness_probe(client):
    """GET /health/live always returns 200 with status='alive'."""
    resp = await client.get("/health/live")
    assert resp.status_code == 200

    body = resp.json()
    assert body["status"] == "alive"
    assert "timestamp" in body


# --------------------------------------------------------------------------
# Readiness probe
# --------------------------------------------------------------------------

async def test_readiness_probe_healthy(client):
    """GET /health/ready returns 200 when Postgres and Redis are reachable."""
    pg_ok = {"status": "up", "latency_ms": 1.0}
    redis_ok = {"status": "up", "latency_ms": 0.5}

    with (
        patch("app.api.health._check_postgres", new_callable=AsyncMock, return_value=pg_ok),
        patch("app.api.health._check_redis", new_callable=AsyncMock, return_value=redis_ok),
    ):
        resp = await client.get("/health/ready")

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "healthy"
    assert body["checks"]["postgres"]["status"] == "up"
    assert body["checks"]["redis"]["status"] == "up"


async def test_readiness_probe_unhealthy(client):
    """GET /health/ready returns 503 when a dependency is down."""
    pg_ok = {"status": "up", "latency_ms": 1.0}
    redis_down = {"status": "down", "latency_ms": 0, "error": "connection refused"}

    with (
        patch("app.api.health._check_postgres", new_callable=AsyncMock, return_value=pg_ok),
        patch("app.api.health._check_redis", new_callable=AsyncMock, return_value=redis_down),
    ):
        resp = await client.get("/health/ready")

    assert resp.status_code == 503
    body = resp.json()
    assert body["status"] == "unhealthy"


# --------------------------------------------------------------------------
# Startup probe
# --------------------------------------------------------------------------

async def test_startup_probe(client):
    """GET /health/startup returns 200 after modules are registered.

    The test app goes through full startup (module discovery +
    mark_startup_complete), so the probe should already indicate
    'started'.
    """
    resp = await client.get("/health/startup")
    assert resp.status_code == 200

    body = resp.json()
    assert body["status"] == "started"
    assert "uptime_seconds" in body
    assert "modules_count" in body
    assert isinstance(body["modules"], list)


async def test_startup_probe_not_ready():
    """GET /health/startup returns 503 before mark_startup_complete() is called."""
    import app.api.health as health_mod

    # Save and temporarily reset the startup flag.
    original = health_mod._startup_complete
    health_mod._startup_complete = False
    try:
        from starlette.testclient import TestClient
        from fastapi import FastAPI

        mini_app = FastAPI()
        mini_app.include_router(health_mod.router)

        with TestClient(mini_app) as tc:
            resp = tc.get("/health/startup")
            assert resp.status_code == 503
            assert resp.json()["status"] == "starting"
    finally:
        health_mod._startup_complete = original
