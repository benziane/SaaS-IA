"""
Audit module API routes.

All endpoints require admin role. The audit log is immutable —
these endpoints are read-only.
"""

import csv
import io
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth import require_role
from app.database import get_session
from app.models.user import Role, User
from app.modules.audit.schemas import (
    AuditQueryResponse,
    AuditStatsResponse,
    AuditVerifyResponse,
)
from app.modules.audit.service import AuditService
from app.rate_limit import limiter

router = APIRouter()


@router.get("", response_model=AuditQueryResponse)
@limiter.limit("30/minute")
async def query_audit_log(
    request: Request,
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    resource_id: Optional[str] = Query(None, description="Filter by resource ID"),
    action: Optional[str] = Query(None, description="Filter by action (create, update, delete, ...)"),
    start_date: Optional[datetime] = Query(None, description="Filter events after this date (ISO 8601)"),
    end_date: Optional[datetime] = Query(None, description="Filter events before this date (ISO 8601)"),
    limit: int = Query(50, ge=1, le=200, description="Max entries per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    current_user: User = Depends(require_role(Role.ADMIN)),
    session: AsyncSession = Depends(get_session),
):
    """
    Query the immutable audit log with filters.

    Admin only. Returns paginated audit entries sorted by most recent first.

    Rate limit: 30 requests/minute
    """
    entries, total = await AuditService.query_logs(
        user_id=user_id,
        resource_type=resource_type,
        resource_id=resource_id,
        action=action,
        tenant_id=str(current_user.tenant_id) if current_user.tenant_id else None,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
        session=session,
    )

    return AuditQueryResponse(
        entries=entries,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/verify", response_model=AuditVerifyResponse)
@limiter.limit("5/minute")
async def verify_audit_chain(
    request: Request,
    last_n: int = Query(1000, ge=1, le=10000, description="Number of recent records to verify"),
    current_user: User = Depends(require_role(Role.ADMIN)),
    session: AsyncSession = Depends(get_session),
):
    """
    Verify hash chain integrity of the audit log.

    Checks that each record's hash matches its content and that
    previous_hash links are unbroken. Detects tampering or deletion.

    Admin only. Rate limit: 5 requests/minute
    """
    result = await AuditService.verify_chain(last_n=last_n, session=session)
    return AuditVerifyResponse(**result)


@router.get("/export")
@limiter.limit("3/minute")
async def export_audit_csv(
    request: Request,
    user_id: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(10000, ge=1, le=50000),
    current_user: User = Depends(require_role(Role.ADMIN)),
    session: AsyncSession = Depends(get_session),
):
    """
    Export audit log as CSV.

    Admin only. Returns up to 50,000 records matching the filters.

    Rate limit: 3 requests/minute
    """
    entries, _ = await AuditService.query_logs(
        user_id=user_id,
        resource_type=resource_type,
        action=action,
        tenant_id=str(current_user.tenant_id) if current_user.tenant_id else None,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=0,
        session=session,
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "Timestamp", "Action", "Resource Type", "Resource ID",
        "User ID", "Tenant ID", "IP Address", "User Agent",
        "Details", "Record Hash", "Previous Hash",
    ])
    for entry in entries:
        writer.writerow([
            str(entry.id),
            entry.created_at.isoformat(),
            entry.action,
            entry.resource_type,
            entry.resource_id or "",
            str(entry.user_id) if entry.user_id else "",
            str(entry.tenant_id) if entry.tenant_id else "",
            entry.ip_address or "",
            entry.user_agent or "",
            entry.details_json or "",
            entry.record_hash,
            entry.previous_hash or "",
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=audit-log-export.csv",
        },
    )


@router.get("/stats", response_model=AuditStatsResponse)
@limiter.limit("20/minute")
async def get_audit_stats(
    request: Request,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(require_role(Role.ADMIN)),
    session: AsyncSession = Depends(get_session),
):
    """
    Get audit log statistics.

    Returns event counts by action type, resource type, user, and day.

    Admin only. Rate limit: 20 requests/minute
    """
    stats = await AuditService.get_stats(
        tenant_id=str(current_user.tenant_id) if current_user.tenant_id else None,
        days=days,
        session=session,
    )
    return AuditStatsResponse(**stats)
