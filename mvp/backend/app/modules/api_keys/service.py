"""
API Key service - Key generation, verification, and management.
"""

import hashlib
import json
import secrets
from datetime import datetime, date
from typing import Optional
from uuid import UUID

import structlog
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.api_key import APIKey

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# Daily rate-limit helpers (Redis-backed, fail-open)
# ---------------------------------------------------------------------------

async def _get_daily_usage(key_hash: str) -> Optional[int]:
    """Return the current daily request count for the given key hash, or None if Redis unavailable."""
    try:
        from app.cache import _get_redis
        redis_client = await _get_redis()
        if redis_client is None:
            return None
        redis_key = f"saas_ia:apikey_daily:{key_hash}:{date.today().isoformat()}"
        value = await redis_client.get(redis_key)
        return int(value) if value is not None else 0
    except Exception as exc:
        logger.debug("apikey_daily_usage_read_error", error=str(exc))
        return None


async def _increment_daily_usage(key_hash: str) -> Optional[int]:
    """Increment and return the new daily count. Sets a 25-hour TTL so the key auto-expires."""
    try:
        from app.cache import _get_redis
        redis_client = await _get_redis()
        if redis_client is None:
            return None
        redis_key = f"saas_ia:apikey_daily:{key_hash}:{date.today().isoformat()}"
        new_count = await redis_client.incr(redis_key)
        if new_count == 1:
            await redis_client.expire(redis_key, 90000)  # 25 hours
        return int(new_count)
    except Exception as exc:
        logger.debug("apikey_daily_usage_incr_error", error=str(exc))
        return None


class APIKeyService:
    """Service for managing API keys."""

    @staticmethod
    def generate_key() -> str:
        """Generate a secure API key."""
        return f"sk-{secrets.token_urlsafe(32)}"

    @staticmethod
    def hash_key(key: str) -> str:
        """Hash an API key for storage."""
        return hashlib.sha256(key.encode()).hexdigest()

    @staticmethod
    async def create_key(
        user_id: UUID,
        name: str,
        permissions: list[str],
        rate_limit_per_day: int,
        session: AsyncSession,
    ) -> tuple[APIKey, str]:
        """
        Create a new API key.

        Returns the APIKey model and the plain-text key (shown only once).
        """
        raw_key = APIKeyService.generate_key()
        key_hash = APIKeyService.hash_key(raw_key)
        key_prefix = raw_key[:8]

        api_key = APIKey(
            user_id=user_id,
            name=name,
            key_hash=key_hash,
            key_prefix=key_prefix,
            permissions_json=json.dumps(permissions),
            rate_limit_per_day=rate_limit_per_day,
        )
        session.add(api_key)
        await session.commit()
        await session.refresh(api_key)

        logger.info(
            "api_key_created",
            user_id=str(user_id),
            key_id=str(api_key.id),
            name=name,
        )

        return api_key, raw_key

    @staticmethod
    async def verify_key(key: str, session: AsyncSession) -> Optional[tuple[UUID, list[str]]]:
        """
        Verify an API key.

        Returns (user_id, permissions) if valid, None otherwise.
        Raises HTTPException(429) when daily rate limit is exceeded.
        """
        key_hash = APIKeyService.hash_key(key)

        result = await session.execute(
            select(APIKey).where(
                APIKey.key_hash == key_hash,
                APIKey.is_active == True,
            )
        )
        api_key = result.scalar_one_or_none()

        if api_key is None:
            return None

        # Check expiration
        if api_key.expires_at and api_key.expires_at < datetime.utcnow():
            return None

        # --- HIGH-02: enforce daily rate limit via Redis ---
        daily_limit = api_key.rate_limit_per_day or 1000
        current_usage = await _get_daily_usage(key_hash)
        if current_usage is not None and current_usage >= daily_limit:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=429,
                detail="API key daily rate limit exceeded",
                headers={
                    "Retry-After": "3600",
                    "X-RateLimit-Limit-Day": str(daily_limit),
                    "X-RateLimit-Remaining-Day": "0",
                },
            )

        # Increment daily counter (fail-open: if Redis is down we still allow)
        await _increment_daily_usage(key_hash)

        # Update last used
        api_key.last_used_at = datetime.utcnow()
        session.add(api_key)
        await session.commit()

        permissions = json.loads(api_key.permissions_json)
        return api_key.user_id, permissions

    @staticmethod
    async def list_keys(user_id: UUID, session: AsyncSession) -> list[APIKey]:
        """List all API keys for a user."""
        result = await session.execute(
            select(APIKey)
            .where(APIKey.user_id == user_id)
            .order_by(APIKey.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def revoke_key(
        key_id: UUID,
        user_id: UUID,
        session: AsyncSession,
    ) -> bool:
        """Revoke (deactivate) an API key."""
        api_key = await session.get(APIKey, key_id)
        if not api_key or api_key.user_id != user_id:
            return False

        api_key.is_active = False
        session.add(api_key)
        await session.commit()

        logger.info("api_key_revoked", key_id=str(key_id))
        return True
