"""
Quota verification dependencies for use in other modules.
"""

from fastapi import Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth import get_current_user
from app.database import get_session
from app.models.user import User
from app.modules.billing.service import BillingService


async def require_transcription_quota(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Dependency that verifies the user has transcription quota remaining."""
    has_quota = await BillingService.check_quota(
        current_user.id, "transcription", session
    )
    if not has_quota:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Monthly transcription quota exceeded. Please upgrade your plan.",
        )
    return current_user


async def require_ai_call_quota(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Dependency that verifies the user has AI call quota remaining."""
    has_quota = await BillingService.check_quota(
        current_user.id, "ai_call", session
    )
    if not has_quota:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Monthly AI call quota exceeded. Please upgrade your plan.",
        )
    return current_user
