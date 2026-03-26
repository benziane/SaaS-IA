"""
Secrets module service -- thin wrapper around SecretsManager for route consumption.
"""

import structlog
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.secrets_manager import (
    SecretStatus,
    SecretType,
    SecretsManager,
    seed_default_secrets,
)

logger = structlog.get_logger()


class SecretsService:
    """Service layer for the secrets rotation module."""

    @staticmethod
    async def list_secrets(session: AsyncSession) -> list[dict]:
        return await SecretsManager.get_status(session)

    @staticmethod
    async def get_alerts(session: AsyncSession) -> list[dict]:
        return await SecretsManager.get_alerts(session)

    @staticmethod
    async def check_rotations(session: AsyncSession) -> list[dict]:
        return await SecretsManager.check_rotations(session)

    @staticmethod
    async def register(
        name: str,
        secret_type: str,
        rotation_days: int,
        notes: str | None,
        session: AsyncSession,
    ) -> None:
        try:
            stype = SecretType(secret_type)
        except ValueError:
            stype = SecretType.OTHER
        await SecretsManager.register_secret(
            name=name,
            secret_type=stype,
            rotation_days=rotation_days,
            session=session,
            notes=notes,
        )

    @staticmethod
    async def start_rotation(
        name: str,
        hint: str | None,
        session: AsyncSession,
    ) -> None:
        await SecretsManager.start_rotation(name, hint, session=session)

    @staticmethod
    async def complete_rotation(name: str, session: AsyncSession) -> None:
        await SecretsManager.complete_rotation(name, session=session)

    @staticmethod
    async def mark_compromised(name: str, session: AsyncSession) -> None:
        await SecretsManager.mark_compromised(name, session=session)

    @staticmethod
    async def get_health(session: AsyncSession) -> dict:
        return await SecretsManager.get_health_score(session)

    @staticmethod
    async def seed_defaults(session: AsyncSession) -> int:
        return await seed_default_secrets(session)
