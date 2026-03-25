"""
Notification service with WebSocket push and DB persistence.

Handles creating, listing, marking read, and pushing real-time
notifications to connected WebSocket clients.
"""

from datetime import UTC, datetime
from typing import Optional
from uuid import UUID

import structlog
from sqlalchemy import func as sa_func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.notification import Notification, NotificationType
from app.core.websocket_manager import manager, build_message

logger = structlog.get_logger()


class NotificationService:
    """In-app notification system with WebSocket push."""

    @staticmethod
    async def create_notification(
        user_id: UUID,
        title: str,
        body: str = "",
        type: str = NotificationType.INFO,
        link: Optional[str] = None,
        session: Optional[AsyncSession] = None,
    ) -> dict:
        """
        Create a notification in DB and push via WebSocket if user is online.

        If no session is provided, only the WebSocket push is attempted
        (useful for transient/system notifications).
        """
        notification_data = {
            "title": title,
            "body": body,
            "type": type,
            "link": link,
        }

        notification_id = None

        # Persist to DB if session is available
        if session is not None:
            notification = Notification(
                user_id=user_id,
                title=title,
                body=body,
                type=type,
                link=link,
            )
            session.add(notification)
            await session.commit()
            await session.refresh(notification)
            notification_id = notification.id
            notification_data["id"] = str(notification.id)
            notification_data["created_at"] = notification.created_at.isoformat()
            notification_data["is_read"] = False

        # Push via WebSocket if user is connected
        try:
            user_id_str = str(user_id)
            rooms = await manager.get_user_rooms(user_id_str)
            if rooms:
                ws_msg = build_message(
                    "notification",
                    notification_data,
                    user_id=user_id_str,
                )
                await manager.send_personal(user_id_str, ws_msg)
                logger.debug(
                    "notification_pushed_ws",
                    user_id=user_id_str,
                    title=title,
                )
        except Exception as e:
            logger.debug(
                "notification_ws_push_failed",
                user_id=str(user_id),
                error=str(e),
            )

        logger.info(
            "notification_created",
            user_id=str(user_id),
            type=type,
            title=title,
            notification_id=str(notification_id) if notification_id else None,
        )

        return notification_data

    @staticmethod
    async def get_notifications(
        user_id: UUID,
        session: AsyncSession,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:
        """List notifications for a user, optionally filtered to unread only."""
        query = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        if unread_only:
            query = query.where(Notification.is_read == False)  # noqa: E712

        result = await session.execute(query)
        notifications = result.scalars().all()

        return [
            {
                "id": str(n.id),
                "title": n.title,
                "body": n.body,
                "type": n.type,
                "link": n.link,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat(),
            }
            for n in notifications
        ]

    @staticmethod
    async def mark_read(
        user_id: UUID,
        notification_id: UUID,
        session: AsyncSession,
    ) -> bool:
        """Mark a single notification as read. Returns True if found and updated."""
        result = await session.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
        )
        notification = result.scalar_one_or_none()
        if notification is None:
            return False

        notification.is_read = True
        session.add(notification)
        await session.commit()
        return True

    @staticmethod
    async def mark_all_read(user_id: UUID, session: AsyncSession) -> int:
        """Mark all unread notifications as read. Returns count updated."""
        result = await session.execute(
            select(Notification).where(
                Notification.user_id == user_id,
                Notification.is_read == False,  # noqa: E712
            )
        )
        notifications = result.scalars().all()
        count = 0
        for n in notifications:
            n.is_read = True
            session.add(n)
            count += 1

        if count > 0:
            await session.commit()

        return count

    @staticmethod
    async def get_unread_count(user_id: UUID, session: AsyncSession) -> int:
        """Count unread notifications for a user."""
        result = await session.execute(
            select(sa_func.count())
            .select_from(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read == False,  # noqa: E712
            )
        )
        return result.scalar_one()
