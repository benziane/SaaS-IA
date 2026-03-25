"""
Token blacklist system using Redis (CRIT-03 fix).

Provides per-token (JTI) and per-user revocation with graceful
fail-open behaviour when Redis is unavailable.

Key layout in Redis:
    token_blacklist:{jti}           -> "1"          (TTL = remaining token lifetime)
    token_blacklist:user:{user_id}  -> ISO timestamp (TTL = REFRESH_TOKEN_EXPIRE_DAYS)
"""

from datetime import datetime, timezone
from typing import Optional

import structlog

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# Internal Redis accessor (reuses the lazy client from app.cache)
# ---------------------------------------------------------------------------

async def _get_redis():
    """Return the async Redis client or None."""
    try:
        from app.cache import _get_redis as _cache_get_redis
        return await _cache_get_redis()
    except Exception as e:
        logger.warning("token_blacklist_redis_unavailable", error=str(e))
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def blacklist_token(jti: str, expires_in: int) -> None:
    """
    Add a single token JTI to the blacklist.

    Parameters
    ----------
    jti : str
        The JWT ID claim of the token to revoke.
    expires_in : int
        Seconds until the token would naturally expire.
        Used as the Redis TTL so the key auto-cleans.
    """
    try:
        client = await _get_redis()
        if client is None:
            logger.warning(
                "token_blacklist_skip",
                reason="redis_unavailable",
                jti=jti,
            )
            return
        ttl = max(expires_in, 1)
        await client.set(f"token_blacklist:{jti}", "1", ex=ttl)
        logger.info("token_blacklisted", jti=jti, ttl=ttl)
    except Exception as e:
        logger.warning("token_blacklist_error", jti=jti, error=str(e))


async def is_blacklisted(jti: str) -> bool:
    """
    Check whether a token JTI has been explicitly blacklisted.

    Returns False (fail-open) when Redis is unavailable.
    """
    try:
        client = await _get_redis()
        if client is None:
            return False
        result = await client.get(f"token_blacklist:{jti}")
        return result is not None
    except Exception as e:
        logger.warning("token_blacklist_check_error", jti=jti, error=str(e))
        return False


async def blacklist_user_tokens(user_id: str) -> None:
    """
    Invalidate *all* tokens for a user by recording a revoked-at timestamp.

    Any token whose ``iat`` (issued-at) is earlier than this timestamp will
    be rejected by ``is_user_tokens_revoked()``.

    The key lives for REFRESH_TOKEN_EXPIRE_DAYS so it covers even the
    longest-lived token that could still be valid.
    """
    try:
        from app.config import settings

        client = await _get_redis()
        if client is None:
            logger.warning(
                "token_blacklist_user_skip",
                reason="redis_unavailable",
                user_id=user_id,
            )
            return
        revoked_at = datetime.now(timezone.utc).isoformat()
        ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
        await client.set(
            f"token_blacklist:user:{user_id}",
            revoked_at,
            ex=ttl,
        )
        logger.info("user_tokens_blacklisted", user_id=user_id, revoked_at=revoked_at)
    except Exception as e:
        logger.warning(
            "token_blacklist_user_error", user_id=user_id, error=str(e)
        )


async def is_user_tokens_revoked(user_id: str, token_iat: Optional[int]) -> bool:
    """
    Check if tokens for *user_id* issued before the revoked-at timestamp
    should be rejected.

    Parameters
    ----------
    user_id : str
        The user identifier (email or UUID string stored in ``sub``).
    token_iat : int | None
        The ``iat`` (issued-at) claim from the JWT, as a Unix timestamp.

    Returns False (fail-open) when Redis is unavailable or when no
    revocation record exists for the user.
    """
    if token_iat is None:
        return False
    try:
        client = await _get_redis()
        if client is None:
            return False
        revoked_at_str = await client.get(f"token_blacklist:user:{user_id}")
        if revoked_at_str is None:
            return False
        revoked_at = datetime.fromisoformat(revoked_at_str)
        token_issued = datetime.fromtimestamp(token_iat, tz=timezone.utc)
        return token_issued < revoked_at
    except Exception as e:
        logger.warning(
            "token_blacklist_user_check_error",
            user_id=user_id,
            error=str(e),
        )
        return False
