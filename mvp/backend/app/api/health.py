"""
Kubernetes-ready health check endpoints.

Three probes following K8s conventions:
- /health/live   -> liveness  (always 200 if the process is running)
- /health/ready  -> readiness (200 only when Postgres + Redis respond)
- /health/startup -> startup  (200 only after the application has finished booting)

Usage:
    from app.api.health import router as health_router, mark_startup_complete
    app.include_router(health_router)
    mark_startup_complete(["transcription", "knowledge", ...])
"""

import asyncio
import time

import structlog
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.database import engine
from app.cache import _get_redis

logger = structlog.get_logger()

router = APIRouter(prefix="/health", tags=["health"])

# ── Startup state ────────────────────────────────────────────────────────────

_startup_complete: bool = False
_startup_time: float = time.time()
_modules_loaded: list[str] = []


def mark_startup_complete(modules: list[str]) -> None:
    """Call once after all modules have been registered."""
    global _startup_complete, _modules_loaded
    _startup_complete = True
    _modules_loaded = list(modules)
    logger.info(
        "startup_marked_complete",
        modules_count=len(modules),
        elapsed_s=round(time.time() - _startup_time, 2),
    )


# ── Internal checks ─────────────────────────────────────────────────────────

async def _check_postgres() -> dict:
    """Ping PostgreSQL and return status + latency."""
    t0 = time.monotonic()
    try:
        async with asyncio.timeout(5):
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        latency_ms = round((time.monotonic() - t0) * 1000, 1)
        return {"status": "up", "latency_ms": latency_ms}
    except Exception as exc:
        latency_ms = round((time.monotonic() - t0) * 1000, 1)
        logger.warning("health_postgres_fail", error=str(exc))
        return {"status": "down", "latency_ms": latency_ms, "error": str(exc)}


async def _check_redis() -> dict:
    """Ping Redis and return status + latency."""
    t0 = time.monotonic()
    try:
        client = await _get_redis()
        if client is None:
            return {"status": "down", "latency_ms": 0, "error": "redis not configured"}
        async with asyncio.timeout(3):
            await client.ping()
        latency_ms = round((time.monotonic() - t0) * 1000, 1)
        return {"status": "up", "latency_ms": latency_ms}
    except Exception as exc:
        latency_ms = round((time.monotonic() - t0) * 1000, 1)
        logger.warning("health_redis_fail", error=str(exc))
        return {"status": "down", "latency_ms": latency_ms, "error": str(exc)}


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/live")
async def liveness():
    """Liveness probe -- always 200 if the process is running."""
    return {"status": "alive", "timestamp": time.time()}


@router.get("/ready")
async def readiness():
    """Readiness probe -- 200 only when all dependencies respond."""
    postgres_result, redis_result = await asyncio.gather(
        _check_postgres(),
        _check_redis(),
    )

    checks = {
        "postgres": postgres_result,
        "redis": redis_result,
    }

    all_up = all(c["status"] == "up" for c in checks.values())
    status_code = 200 if all_up else 503
    status_label = "healthy" if all_up else "unhealthy"

    return JSONResponse(
        status_code=status_code,
        content={
            "status": status_label,
            "checks": checks,
        },
    )


@router.get("/startup")
async def startup():
    """Startup probe -- 503 until the application has fully booted."""
    if not _startup_complete:
        return JSONResponse(
            status_code=503,
            content={
                "status": "starting",
                "uptime_seconds": round(time.time() - _startup_time, 2),
            },
        )

    return {
        "status": "started",
        "uptime_seconds": round(time.time() - _startup_time, 2),
        "modules_loaded": len(_modules_loaded),
    }
