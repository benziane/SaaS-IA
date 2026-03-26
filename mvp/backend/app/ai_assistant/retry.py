"""Async retry helper with exponential backoff for AI provider calls."""

import asyncio

import structlog

logger = structlog.get_logger(__name__)

MAX_RETRIES = 3
BACKOFF_SECONDS = [1, 2, 4]

TRANSIENT_STATUS_CODES = {429, 502, 503}


def is_transient(exc: Exception) -> bool:
    if isinstance(exc, (TimeoutError, ConnectionError, OSError)):
        return True
    try:
        import httpx
        if isinstance(exc, httpx.TimeoutException):
            return True
    except ImportError:
        pass
    status = getattr(exc, "status_code", None) or getattr(exc, "status", None)
    if status and int(status) in TRANSIENT_STATUS_CODES:
        return True
    if hasattr(exc, "response"):
        resp = exc.response
        resp_status = getattr(resp, "status_code", None) or getattr(resp, "status", None)
        if resp_status and int(resp_status) in TRANSIENT_STATUS_CODES:
            return True
    return False


async def with_retries(coro_fn, *, provider: str):
    """Call an async callable with retry on transient errors.

    Args:
        coro_fn: Zero-arg async callable that returns the result.
        provider: Provider name for logging.

    Returns:
        The result of coro_fn().
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return await coro_fn()
        except Exception as exc:
            if attempt == MAX_RETRIES or not is_transient(exc):
                raise
            delay = BACKOFF_SECONDS[attempt - 1]
            logger.warning(
                "provider_retry",
                provider=provider,
                attempt=attempt,
                delay=delay,
                error=str(exc),
            )
            await asyncio.sleep(delay)
