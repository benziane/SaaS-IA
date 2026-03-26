"""
Audit module service — thin wrapper around AuditLogger for route consumption.
"""

from datetime import datetime
from typing import Optional

from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.audit_log import AuditLogger


class AuditService:
    """Service layer for audit log queries and verification."""

    @staticmethod
    async def query_logs(
        user_id: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        action: str | None = None,
        tenant_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
        session: AsyncSession = None,
    ) -> tuple[list, int]:
        """Query audit log with filters."""
        return await AuditLogger.query(
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset,
            session=session,
        )

    @staticmethod
    async def verify_chain(
        last_n: int,
        session: AsyncSession,
    ) -> dict:
        """Verify hash chain integrity."""
        return await AuditLogger.verify_chain(last_n=last_n, session=session)

    @staticmethod
    async def get_stats(
        tenant_id: str | None = None,
        days: int = 30,
        session: AsyncSession = None,
    ) -> dict:
        """Get audit statistics."""
        return await AuditLogger.get_stats(
            tenant_id=tenant_id,
            days=days,
            session=session,
        )
