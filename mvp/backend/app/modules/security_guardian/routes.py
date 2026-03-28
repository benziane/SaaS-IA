"""
Security Guardian API routes - AI safety, PII detection, audit, guardrails.
"""

import json
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth import get_current_user
from app.modules.auth_guards.middleware import require_verified_email
from app.database import get_session
from app.models.user import User
from app.modules.security_guardian.schemas import (
    AuditLogRead,
    GuardrailRuleCreate,
    GuardrailRuleRead,
    GuardrailRuleUpdate,
    ScanFinding,
    ScanRead,
    ScanRequest,
    SecurityDashboard,
)
from app.modules.security_guardian.service import SecurityGuardianService
from app.rate_limit import limiter

router = APIRouter()


@router.post("/scan", response_model=ScanRead)
@limiter.limit("10/minute")
async def scan_content(
    request: Request, body: ScanRequest,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """Scan content for PII, prompt injection, and safety issues. Rate limit: 10/min"""
    scan = await SecurityGuardianService.scan_content(
        user_id=current_user.id, text=body.text, scan_types=body.scan_types,
        auto_redact=body.auto_redact, target_type=body.target_type,
        target_id=body.target_id, session=session,
    )
    findings = json.loads(scan.findings_json) if scan.findings_json else []
    return ScanRead(
        id=scan.id, scan_type=scan.scan_type, target_type=scan.target_type,
        status=scan.status.value if hasattr(scan.status, "value") else scan.status,
        findings=[ScanFinding(**f) for f in findings],
        findings_count=scan.findings_count,
        severity=scan.severity.value if scan.severity and hasattr(scan.severity, "value") else (scan.severity if isinstance(scan.severity, str) else None),
        auto_redacted=scan.auto_redacted,
        redacted_text=scan.redacted_text,
        created_at=scan.created_at,
    )


@router.get("/dashboard", response_model=SecurityDashboard)
@limiter.limit("20/minute")
async def get_dashboard(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get security dashboard overview. Rate limit: 20/min"""
    data = await SecurityGuardianService.get_dashboard(current_user.id, session)
    return SecurityDashboard(**data)


@router.get("/audit", response_model=list[AuditLogRead])
@limiter.limit("20/minute")
async def list_audit_logs(
    request: Request,
    module: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    flagged_only: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List audit log entries with filters. Rate limit: 20/min"""
    logs = await SecurityGuardianService.get_audit_logs(
        current_user.id, session, module=module, action=action,
        flagged_only=flagged_only, limit=limit, skip=skip,
    )
    return [
        AuditLogRead(
            id=log.id, user_id=log.user_id,
            action=log.action.value if hasattr(log.action, "value") else log.action,
            module=log.module, provider=log.provider, model=log.model,
            input_preview=log.input_preview, output_preview=log.output_preview,
            tokens_used=log.tokens_used, cost_usd=log.cost_usd,
            risk_level=log.risk_level.value if log.risk_level and hasattr(log.risk_level, "value") else (log.risk_level if isinstance(log.risk_level, str) else None),
            flagged=log.flagged, created_at=log.created_at,
        ) for log in logs
    ]


@router.post("/guardrails", response_model=GuardrailRuleRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_guardrail(
    request: Request, body: GuardrailRuleCreate,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """Create a guardrail rule. Rate limit: 10/min"""
    rule = await SecurityGuardianService.create_guardrail(
        user_id=current_user.id, name=body.name, description=body.description,
        rule_type=body.rule_type, config=body.config,
        action=body.action, severity=body.severity, session=session,
    )
    return rule


@router.get("/guardrails", response_model=list[GuardrailRuleRead])
@limiter.limit("20/minute")
async def list_guardrails(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List guardrail rules. Rate limit: 20/min"""
    return await SecurityGuardianService.list_guardrails(current_user.id, session)


@router.put("/guardrails/{rule_id}", response_model=GuardrailRuleRead)
@limiter.limit("10/minute")
async def update_guardrail(
    request: Request, rule_id: UUID, body: GuardrailRuleUpdate,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """Update a guardrail rule. Rate limit: 10/min"""
    rule = await SecurityGuardianService.update_guardrail(
        rule_id, current_user.id, body.model_dump(exclude_unset=True), session,
    )
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    return rule


@router.delete("/guardrails/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def delete_guardrail(
    request: Request, rule_id: UUID,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """Delete a guardrail rule. Rate limit: 10/min"""
    if not await SecurityGuardianService.delete_guardrail(rule_id, current_user.id, session):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
