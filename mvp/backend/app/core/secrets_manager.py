"""
Secrets Manager -- rotation tracking, dual-key transitions, audit.

This module NEVER stores actual secret values. It only tracks metadata
(name, type, rotation date, status). The actual values stay in .env /
environment variables.
"""

from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Optional
from uuid import UUID

import structlog
from sqlmodel import select, update
from sqlmodel.ext.asyncio.session import AsyncSession

logger = structlog.get_logger()


class SecretType(str, Enum):
    API_KEY = "api_key"
    DATABASE = "database"
    JWT = "jwt"
    WEBHOOK = "webhook"
    OTHER = "other"


class SecretStatus(str, Enum):
    ACTIVE = "active"
    ROTATING = "rotating"
    EXPIRED = "expired"
    COMPROMISED = "compromised"


class SecretsManager:
    """Manages secret lifecycle: registration, rotation, monitoring."""

    @staticmethod
    async def register_secret(
        name: str,
        secret_type: SecretType,
        rotation_days: int = 90,
        *,
        session: AsyncSession,
        notes: str | None = None,
    ) -> None:
        """Register a secret for rotation tracking.

        If a secret with the same *name* already exists, this is a no-op so
        the method is safe to call on every startup.
        """
        from app.models.secrets_manager import SecretRegistration

        existing = await session.execute(
            select(SecretRegistration).where(SecretRegistration.name == name)
        )
        if existing.scalar_one_or_none() is not None:
            return

        now = datetime.now(UTC)
        registration = SecretRegistration(
            name=name,
            secret_type=secret_type.value,
            status=SecretStatus.ACTIVE.value,
            rotation_days=rotation_days,
            registered_at=now,
            last_rotated_at=now,
            next_rotation_at=now + timedelta(days=rotation_days),
            rotation_count=0,
            notes=notes,
            created_at=now,
            updated_at=now,
        )
        session.add(registration)
        await session.commit()
        logger.info(
            "secret_registered",
            name=name,
            secret_type=secret_type.value,
            rotation_days=rotation_days,
        )

    @staticmethod
    async def check_rotations(session: AsyncSession) -> list[dict]:
        """Check which secrets need rotation (age > rotation_days).

        Returns list of ``{name, type, age_days, status, urgency}``.
        """
        from app.models.secrets_manager import SecretRegistration

        result = await session.execute(
            select(SecretRegistration).where(
                SecretRegistration.status.in_([  # type: ignore[attr-defined]
                    SecretStatus.ACTIVE.value,
                    SecretStatus.ROTATING.value,
                ])
            )
        )
        secrets = list(result.scalars().all())
        now = datetime.now(UTC)
        alerts: list[dict] = []

        for s in secrets:
            ref = s.last_rotated_at or s.registered_at
            age_days = (now - ref).days
            overdue_days = age_days - s.rotation_days

            if overdue_days <= -30:
                continue  # Not close to rotation yet

            urgency = "ok"
            if overdue_days > 0:
                urgency = "overdue"
            elif overdue_days > -14:
                urgency = "soon"
            elif overdue_days > -30:
                urgency = "upcoming"

            alerts.append({
                "name": s.name,
                "type": s.secret_type,
                "age_days": age_days,
                "rotation_days": s.rotation_days,
                "status": s.status,
                "urgency": urgency,
                "overdue_days": max(overdue_days, 0),
            })

        return alerts

    @staticmethod
    async def start_rotation(
        name: str,
        new_value_hint: str | None = None,
        *,
        session: AsyncSession,
    ) -> None:
        """Mark a secret as ``rotating``.

        Both old and new keys should work during the transition window.
        *new_value_hint* is NOT the actual value -- just optional metadata
        (e.g. ``"rotated via admin panel"``).
        """
        from app.models.secrets_manager import SecretRegistration

        result = await session.execute(
            select(SecretRegistration).where(SecretRegistration.name == name)
        )
        secret = result.scalar_one_or_none()
        if secret is None:
            raise ValueError(f"Secret '{name}' is not registered")

        now = datetime.now(UTC)
        secret.status = SecretStatus.ROTATING.value
        secret.notes = new_value_hint or secret.notes
        secret.updated_at = now
        session.add(secret)
        await session.commit()

        logger.info("secret_rotation_started", name=name)

    @staticmethod
    async def complete_rotation(name: str, *, session: AsyncSession) -> None:
        """Mark rotation as complete. Old key is now expired."""
        from app.models.secrets_manager import SecretRegistration

        result = await session.execute(
            select(SecretRegistration).where(SecretRegistration.name == name)
        )
        secret = result.scalar_one_or_none()
        if secret is None:
            raise ValueError(f"Secret '{name}' is not registered")

        now = datetime.now(UTC)
        secret.status = SecretStatus.ACTIVE.value
        secret.last_rotated_at = now
        secret.next_rotation_at = now + timedelta(days=secret.rotation_days)
        secret.rotation_count += 1
        secret.updated_at = now
        session.add(secret)
        await session.commit()

        logger.info(
            "secret_rotation_completed",
            name=name,
            rotation_count=secret.rotation_count,
        )

    @staticmethod
    async def get_status(session: AsyncSession) -> list[dict]:
        """Get status of all registered secrets."""
        from app.models.secrets_manager import SecretRegistration

        result = await session.execute(
            select(SecretRegistration).order_by(SecretRegistration.name)
        )
        secrets = list(result.scalars().all())
        now = datetime.now(UTC)

        return [
            {
                "id": str(s.id),
                "name": s.name,
                "secret_type": s.secret_type,
                "status": s.status,
                "rotation_days": s.rotation_days,
                "registered_at": s.registered_at.isoformat(),
                "last_rotated_at": s.last_rotated_at.isoformat() if s.last_rotated_at else None,
                "next_rotation_at": s.next_rotation_at.isoformat() if s.next_rotation_at else None,
                "rotation_count": s.rotation_count,
                "age_days": (now - (s.last_rotated_at or s.registered_at)).days,
                "notes": s.notes,
            }
            for s in secrets
        ]

    @staticmethod
    async def get_alerts(session: AsyncSession) -> list[dict]:
        """Get secrets that need attention (expiring soon, overdue, compromised)."""
        from app.models.secrets_manager import SecretRegistration

        result = await session.execute(select(SecretRegistration))
        secrets = list(result.scalars().all())
        now = datetime.now(UTC)
        alerts: list[dict] = []

        for s in secrets:
            if s.status == SecretStatus.COMPROMISED.value:
                alerts.append({
                    "name": s.name,
                    "type": s.secret_type,
                    "status": s.status,
                    "urgency": "critical",
                    "message": f"Secret '{s.name}' is marked as COMPROMISED. Rotate immediately!",
                })
                continue

            ref = s.last_rotated_at or s.registered_at
            age_days = (now - ref).days
            days_until_rotation = s.rotation_days - age_days

            if days_until_rotation < 0:
                alerts.append({
                    "name": s.name,
                    "type": s.secret_type,
                    "status": s.status,
                    "urgency": "overdue",
                    "message": f"Secret '{s.name}' is {abs(days_until_rotation)} days overdue for rotation.",
                    "overdue_days": abs(days_until_rotation),
                })
            elif days_until_rotation <= 14:
                alerts.append({
                    "name": s.name,
                    "type": s.secret_type,
                    "status": s.status,
                    "urgency": "warning",
                    "message": f"Secret '{s.name}' needs rotation in {days_until_rotation} days.",
                    "days_remaining": days_until_rotation,
                })

        # Sort: critical first, then overdue, then warning
        priority = {"critical": 0, "overdue": 1, "warning": 2}
        alerts.sort(key=lambda a: priority.get(a["urgency"], 99))
        return alerts

    @staticmethod
    async def mark_compromised(name: str, *, session: AsyncSession) -> None:
        """Mark a secret as compromised. Triggers urgent rotation alert."""
        from app.models.secrets_manager import SecretRegistration

        result = await session.execute(
            select(SecretRegistration).where(SecretRegistration.name == name)
        )
        secret = result.scalar_one_or_none()
        if secret is None:
            raise ValueError(f"Secret '{name}' is not registered")

        secret.status = SecretStatus.COMPROMISED.value
        secret.updated_at = datetime.now(UTC)
        session.add(secret)
        await session.commit()

        logger.critical(
            "secret_marked_compromised",
            name=name,
            msg=f"Secret '{name}' has been marked as COMPROMISED. Immediate rotation required.",
        )

    @staticmethod
    async def get_health_score(session: AsyncSession) -> dict:
        """Compute an overall health score for all tracked secrets.

        Score is 0-100 where 100 means all secrets are healthy and recently
        rotated. Deductions are applied for overdue, compromised, or soon-to-
        expire secrets.
        """
        from app.models.secrets_manager import SecretRegistration

        result = await session.execute(select(SecretRegistration))
        secrets = list(result.scalars().all())
        now = datetime.now(UTC)

        if not secrets:
            return {"score": 100, "total": 0, "details": "No secrets registered."}

        total = len(secrets)
        deductions = 0.0

        compromised = 0
        overdue = 0
        warning = 0
        healthy = 0

        for s in secrets:
            if s.status == SecretStatus.COMPROMISED.value:
                deductions += 25
                compromised += 1
                continue

            ref = s.last_rotated_at or s.registered_at
            age_days = (now - ref).days
            days_until = s.rotation_days - age_days

            if days_until < 0:
                deductions += 15
                overdue += 1
            elif days_until <= 14:
                deductions += 5
                warning += 1
            else:
                healthy += 1

        score = max(0, round(100 - (deductions / total) * 100 / 25 * (deductions / total)))
        # Simpler: proportional
        score = max(0, round(100 - (deductions * 100 / (total * 25))))

        return {
            "score": score,
            "total": total,
            "healthy": healthy,
            "warning": warning,
            "overdue": overdue,
            "compromised": compromised,
        }


# -----------------------------------------------------------------------
# Default secrets to auto-register on startup
# -----------------------------------------------------------------------

DEFAULT_SECRETS: list[dict] = [
    {"name": "GEMINI_API_KEY", "type": SecretType.API_KEY, "rotation_days": 90},
    {"name": "ANTHROPIC_API_KEY", "type": SecretType.API_KEY, "rotation_days": 90},
    {"name": "GROQ_API_KEY", "type": SecretType.API_KEY, "rotation_days": 90},
    {"name": "ASSEMBLYAI_API_KEY", "type": SecretType.API_KEY, "rotation_days": 90},
    {"name": "STRIPE_SECRET_KEY", "type": SecretType.API_KEY, "rotation_days": 180},
    {"name": "SECRET_KEY", "type": SecretType.JWT, "rotation_days": 365},
    {"name": "DATABASE_URL", "type": SecretType.DATABASE, "rotation_days": 180},
]


async def seed_default_secrets(session: AsyncSession) -> int:
    """Register the default set of secrets for tracking.

    Safe to call repeatedly -- already-registered secrets are skipped.
    Returns the number of newly registered secrets.
    """
    count = 0
    for entry in DEFAULT_SECRETS:
        from app.models.secrets_manager import SecretRegistration

        existing = await session.execute(
            select(SecretRegistration).where(
                SecretRegistration.name == entry["name"]
            )
        )
        if existing.scalar_one_or_none() is None:
            await SecretsManager.register_secret(
                name=entry["name"],
                secret_type=entry["type"],
                rotation_days=entry["rotation_days"],
                session=session,
            )
            count += 1
    return count
