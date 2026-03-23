"""
Cost tracker API routes.
"""

import csv
import io

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth import get_current_user
from app.database import get_session
from app.models.user import User
from app.modules.cost_tracker.schemas import CostDashboard
from app.modules.cost_tracker.service import CostTrackerService
from app.rate_limit import limiter

router = APIRouter()


@router.get("/dashboard", response_model=CostDashboard)
@limiter.limit("20/minute")
async def get_cost_dashboard(
    request: Request,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Get AI cost dashboard with summary, provider/module breakdowns,
    optimization recommendations, and recent usage logs.

    Rate limit: 20 requests/minute
    """
    data = await CostTrackerService.get_dashboard(
        user_id=current_user.id,
        days=days,
        session=session,
    )

    return CostDashboard(**data)


@router.get("/alerts")
@limiter.limit("20/minute")
async def get_cost_alerts(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Get budget alerts and spending warnings.

    Checks daily spending vs average, weekly trends, and
    suggests provider optimizations.

    Rate limit: 20 requests/minute
    """
    alerts = await CostTrackerService.get_alerts(current_user.id, session)
    return alerts


@router.get("/export")
@limiter.limit("5/minute")
async def export_costs_csv(
    request: Request,
    days: int = Query(default=30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Export AI usage logs as a CSV file.

    Rate limit: 5 requests/minute
    """
    logs = await CostTrackerService.get_usage_logs(current_user.id, days, session)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Date", "Provider", "Model", "Module", "Action",
        "Input Tokens", "Output Tokens", "Total Tokens",
        "Cost (cents)", "Latency (ms)", "Status",
    ])
    for log in logs:
        writer.writerow([
            log.created_at.isoformat(),
            log.provider,
            log.model,
            log.module,
            log.action,
            log.input_tokens,
            log.output_tokens,
            log.total_tokens,
            log.cost_cents,
            log.latency_ms,
            "success" if log.success else "failed",
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=ai-costs-{days}d.csv",
        },
    )
