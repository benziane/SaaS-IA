"""
API Key service - Key generation, verification, and management.
"""

import hashlib
import json
import secrets
from datetime import datetime
from typing import Optional
from uuid import UUID

import structlog
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.api_key import APIKey

logger = structlog.get_logger()


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
