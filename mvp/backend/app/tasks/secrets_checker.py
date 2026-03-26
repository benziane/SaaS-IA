"""
Celery beat task -- daily check for secrets needing rotation.

Runs once per day, queries the secret_registrations table, and creates
notifications for any secrets that are overdue, expiring soon, or
compromised.
"""

import asyncio

import structlog

from app.celery_app import celery_app

logger = structlog.get_logger()


@celery_app.task(name="secrets.check_rotations", bind=True, max_retries=2)
def check_secret_rotations(self):
    """Daily check for secrets needing rotation. Creates notifications."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(_check_rotations_async())
            return result
        finally:
            loop.close()
    except Exception as exc:
        logger.error("secrets_check_failed", error=str(exc))
        raise self.retry(exc=exc, countdown=300)


async def _check_rotations_async() -> dict:
    """Async implementation of the rotation check."""
    from app.core.secrets_manager import SecretsManager
    from app.database import get_session_context

    async with get_session_context() as session:
        alerts = await SecretsManager.get_alerts(session)

        if not alerts:
            logger.info("secrets_check_ok", message="All secrets are healthy.")
            return {"status": "ok", "alerts": 0}

        # Log alerts
        for alert in alerts:
            log_fn = logger.critical if alert["urgency"] == "critical" else logger.warning
            log_fn(
                "secret_rotation_alert",
                name=alert["name"],
                urgency=alert["urgency"],
                message=alert["message"],
            )

        # Try to create notifications for admin users
        try:
            from app.core.notifications import create_notification
            from app.models.user import Role, User
            from sqlmodel import select

            result = await session.execute(
                select(User).where(User.role == Role.ADMIN, User.is_active == True)
            )
            admins = list(result.scalars().all())

            for admin in admins:
                # Only notify for critical/overdue alerts
                urgent_alerts = [a for a in alerts if a["urgency"] in ("critical", "overdue")]
                if urgent_alerts:
                    summary = "; ".join(a["message"] for a in urgent_alerts[:3])
                    await create_notification(
                        user_id=admin.id,
                        title="Secret Rotation Required",
                        message=summary,
                        notification_type="warning",
                        session=session,
                    )
        except Exception as exc:
            # Notifications module may not be available; log and continue
            logger.debug("secrets_notification_skipped", error=str(exc))

        logger.info(
            "secrets_check_completed",
            total_alerts=len(alerts),
            critical=sum(1 for a in alerts if a["urgency"] == "critical"),
            overdue=sum(1 for a in alerts if a["urgency"] == "overdue"),
            warning=sum(1 for a in alerts if a["urgency"] == "warning"),
        )

        return {
            "status": "alerts",
            "total": len(alerts),
            "details": alerts,
        }
