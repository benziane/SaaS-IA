"""
Graceful shutdown lifespan manager for the FastAPI application.

Handles:
- Startup validation (SECRET_KEY, DATABASE_URL)
- Database initialization
- Signal handling (SIGTERM, SIGINT)
- Active request draining before shutdown
- Clean disposal of database engine and Redis connections
"""

import asyncio
import signal
from contextlib import asynccontextmanager

import structlog

from app.config import settings
from app.database import engine, init_db

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# Shutdown coordination
# ---------------------------------------------------------------------------

_shutting_down: asyncio.Event = asyncio.Event()
_active_requests: int = 0
_active_lock: asyncio.Lock = asyncio.Lock()


async def _increment_active() -> None:
    """Increment the active request counter."""
    global _active_requests
    async with _active_lock:
        _active_requests += 1


async def _decrement_active() -> None:
    """Decrement the active request counter."""
    global _active_requests
    async with _active_lock:
        _active_requests = max(0, _active_requests - 1)


def is_shutting_down() -> bool:
    """Return True when the application is in shutdown phase."""
    return _shutting_down.is_set()


async def _wait_for_drain(timeout: float = 30.0) -> None:
    """
    Wait until all in-flight requests complete or *timeout* seconds elapse.

    Polls every 0.5 s so active connections have time to finish gracefully.
    """
    elapsed = 0.0
    interval = 0.5
    while elapsed < timeout:
        async with _active_lock:
            current = _active_requests
        if current == 0:
            logger.info("drain_complete", elapsed=round(elapsed, 1))
            return
        logger.info(
            "drain_waiting",
            active_requests=current,
            elapsed=round(elapsed, 1),
            timeout=timeout,
        )
        await asyncio.sleep(interval)
        elapsed += interval

    async with _active_lock:
        remaining = _active_requests
    logger.warning(
        "drain_timeout",
        remaining_requests=remaining,
        timeout=timeout,
    )


# ---------------------------------------------------------------------------
# Lifespan context manager
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app):
    """
    Application lifespan manager.

    STARTUP:
      - Validate critical configuration (SECRET_KEY, DATABASE_URL)
      - Initialize the database (create tables via init_db)
      - Install OS signal handlers for graceful shutdown

    SHUTDOWN:
      - Set the shutting-down flag
      - Drain active requests (up to 30 s)
      - Dispose the SQLAlchemy async engine
      - Close the Redis connection (if active)
      - Log completion
    """

    # ---- Startup ----
    logger.info(
        "application_startup",
        app_name=settings.APP_NAME,
        environment=settings.ENVIRONMENT,
    )

    # Security checks (mirrors original main.py logic)
    _weak_default = "change-me-in-production-use-strong-random-key"
    if not settings.SECRET_KEY or settings.SECRET_KEY == _weak_default:
        logger.critical(
            "insecure_secret_key",
            msg="SECRET_KEY is missing or still set to the weak default. "
                "Set a strong random SECRET_KEY in your .env file before "
                "running in production.",
        )

    if not settings.DATABASE_URL:
        logger.critical(
            "missing_database_url",
            msg="DATABASE_URL is not configured. "
                "Set DATABASE_URL in your .env file.",
        )

    # Initialize database tables
    await init_db()
    logger.info("database_initialized")

    # Start crawl4ai singleton browser (avoids 2s Playwright cold-start per request)
    try:
        from app.modules.web_crawler.service import init_crawler
        await init_crawler()
    except Exception as exc:
        logger.debug("crawl4ai_init_skipped", error=str(exc))

    # Recover orphaned skill_seekers jobs (stuck in RUNNING after restart)
    try:
        from app.modules.skill_seekers.service import SkillSeekersService
        recovered = await SkillSeekersService.recover_orphaned_jobs()
        if recovered:
            logger.info("skill_seekers_orphaned_recovered", count=recovered)
    except Exception as exc:
        logger.debug("skill_seekers_recovery_skipped", error=str(exc))

    # Seed default secrets for rotation tracking
    try:
        from app.core.secrets_manager import seed_default_secrets
        from app.database import get_session_context

        async with get_session_context() as session:
            seeded = await seed_default_secrets(session)
            if seeded:
                logger.info("secrets_defaults_seeded", count=seeded)
    except Exception as exc:
        logger.debug("secrets_seed_skipped", error=str(exc))

    # Install signal handlers for graceful shutdown
    loop = asyncio.get_running_loop()

    def _signal_handler(sig: signal.Signals) -> None:
        logger.info("shutdown_signal_received", signal=sig.name)
        _shutting_down.set()

    try:
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, _signal_handler, sig)
    except NotImplementedError:
        # Windows does not support add_signal_handler on ProactorEventLoop
        logger.debug("signal_handlers_not_supported", reason="platform")

    yield

    # ---- Shutdown ----
    logger.info("shutdown_started")
    _shutting_down.set()

    # Drain active requests
    await _wait_for_drain(timeout=30.0)

    # Close crawl4ai singleton browser
    try:
        from app.modules.web_crawler.service import close_crawler
        await close_crawler()
    except Exception as exc:
        logger.debug("crawl4ai_close_skipped", error=str(exc))

    # Dispose database engine
    try:
        await engine.dispose()
        logger.info("database_engine_disposed")
    except Exception as exc:
        logger.error("engine_dispose_error", error=str(exc))

    # Close Redis connection
    try:
        from app.cache import _redis_client
        if _redis_client is not None:
            await _redis_client.aclose()
            logger.info("redis_connection_closed")
    except Exception as exc:
        logger.error("redis_close_error", error=str(exc))

    logger.info("shutdown_complete")
