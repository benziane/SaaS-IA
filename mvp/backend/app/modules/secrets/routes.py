"""
Secrets API routes -- admin-only endpoints for secret rotation management.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth import get_current_user
from app.database import get_session
from app.models.user import Role, User
from app.modules.secrets.schemas import (
    SecretAlertRead,
    SecretHealthRead,
    SecretRead,
    SecretRegisterRequest,
    SecretRotateRequest,
    RotationCheckRead,
)
from app.modules.secrets.service import SecretsService
from app.rate_limit import limiter

router = APIRouter()


def _require_admin(current_user: User) -> User:
    """Raise 403 if the user is not an admin."""
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required for secrets management",
        )
    return current_user


@router.get("", response_model=list[SecretRead])
@limiter.limit("30/minute")
async def list_secrets(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    List all registered secrets with their rotation status.

    Admin only. Rate limit: 30/minute.
    """
    _require_admin(current_user)
    secrets = await SecretsService.list_secrets(session)
    return secrets


@router.get("/alerts", response_model=list[SecretAlertRead])
@limiter.limit("30/minute")
async def get_alerts(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Get rotation alerts (expiring, overdue, compromised).

    Admin only. Rate limit: 30/minute.
    """
    _require_admin(current_user)
    return await SecretsService.get_alerts(session)


@router.get("/health", response_model=SecretHealthRead)
@limiter.limit("30/minute")
async def secrets_health(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Overall secrets health score (0-100).

    Admin only. Rate limit: 30/minute.
    """
    _require_admin(current_user)
    return await SecretsService.get_health(session)


@router.post("/register", status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def register_secret(
    request: Request,
    body: SecretRegisterRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Register a new secret for rotation tracking.

    Admin only. Rate limit: 10/minute.
    """
    _require_admin(current_user)
    await SecretsService.register(
        name=body.name,
        secret_type=body.secret_type,
        rotation_days=body.rotation_days,
        notes=body.notes,
        session=session,
    )
    return {"message": f"Secret '{body.name}' registered for rotation tracking."}


@router.post("/{name}/rotate")
@limiter.limit("10/minute")
async def start_rotation(
    request: Request,
    name: str,
    body: SecretRotateRequest | None = None,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Start rotation of a secret (marks as 'rotating').

    Admin only. Rate limit: 10/minute.
    """
    _require_admin(current_user)
    try:
        hint = body.hint if body else None
        await SecretsService.start_rotation(name, hint, session)
        return {"message": f"Rotation started for '{name}'. Deploy new key, then call /complete."}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/{name}/complete")
@limiter.limit("10/minute")
async def complete_rotation(
    request: Request,
    name: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Complete rotation of a secret (marks as 'active', resets timer).

    Admin only. Rate limit: 10/minute.
    """
    _require_admin(current_user)
    try:
        await SecretsService.complete_rotation(name, session)
        return {"message": f"Rotation completed for '{name}'."}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/{name}/compromised")
@limiter.limit("5/minute")
async def mark_compromised(
    request: Request,
    name: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Mark a secret as compromised. Triggers urgent rotation alert.

    Admin only. Rate limit: 5/minute.
    """
    _require_admin(current_user)
    try:
        await SecretsService.mark_compromised(name, session)
        return {"message": f"Secret '{name}' marked as COMPROMISED. Rotate immediately!"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
