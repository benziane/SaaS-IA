"""
Redis cache utility for frequently accessed data.

Provides a simple async get/set interface with TTL support.
Falls back gracefully when Redis is unavailable.
"""

import json
from typing import Any, Optional

import structlog

logger = structlog.get_logger()

_redis_client = None


async def _get_redis():
    """Lazy-initialize async Redis client."""
    global _redis_client
    if _redis_client is not None:
        return _redis_client

    from app.config import settings

    redis_url = (settings.REDIS_URL or "").strip()
    if not redis_url:
        return None

    try:
        import redis.asyncio as aioredis
        _redis_client = aioredis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=3,
        )
        await _redis_client.ping()
        logger.info("redis_cache_connected", url=redis_url)
        return _redis_client
    except Exception as e:
        logger.warning("redis_cache_unavailable", error=str(e))
        _redis_client = None
        return None


async def cache_get(key: str) -> Optional[Any]:
    """Get a value from cache. Returns None on miss or error."""
    try:
        client = await _get_redis()
        if client is None:
            return None
        value = await client.get(f"saas_ia:{key}")
        if value is not None:
            return json.loads(value)
    except Exception as e:
        logger.debug("cache_get_error", key=key, error=str(e))
    return None


async def cache_set(key: str, value: Any, ttl_seconds: int = 300) -> None:
    """Set a value in cache with TTL. Fails silently."""
    try:
        client = await _get_redis()
        if client is None:
            return
        await client.set(
            f"saas_ia:{key}",
            json.dumps(value, default=str),
            ex=ttl_seconds,
        )
    except Exception as e:
        logger.debug("cache_set_error", key=key, error=str(e))


async def cache_delete(key: str) -> None:
    """Delete a key from cache. Fails silently."""
    try:
        client = await _get_redis()
        if client is None:
            return
        await client.delete(f"saas_ia:{key}")
    except Exception as e:
        logger.debug("cache_delete_error", key=key, error=str(e))


async def cache_delete_pattern(pattern: str) -> None:
    """Delete all keys matching a pattern. Fails silently."""
    try:
        client = await _get_redis()
        if client is None:
            return
        keys = []
        async for key in client.scan_iter(f"saas_ia:{pattern}"):
            keys.append(key)
        if keys:
            await client.delete(*keys)
    except Exception as e:
        logger.debug("cache_delete_pattern_error", pattern=pattern, error=str(e))
