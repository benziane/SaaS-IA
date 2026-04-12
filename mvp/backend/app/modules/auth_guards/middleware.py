"""
Email verification guard dependencies.

Two variants:
  - require_verified_email: hard block (403) if email not verified
  - require_verified_email_soft: pass-through, just attaches verified status to user
    (use when you want to warn but not block)

Usage in a route:
    @router.post("/sensitive-action")
    async def action(current_user: User = Depends(require_verified_email)):
        ...
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.models.user import User

# Use the same OAuth2 scheme so FastAPI knows to expect a Bearer token.
_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def _lazy_get_current_user(
    token: str = Depends(_oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Resolve current user with a lazy import to break the circular
    dependency between app.auth and app.modules.auth_guards.middleware."""
    from app.auth import get_current_user

    return await get_current_user(token=token, session=session)


async def require_verified_email(
    current_user: User = Depends(_lazy_get_current_user),
) -> User:
    """
    Dependency: blocks with 403 if user has not verified their email.

    In DEV_MODE (ENVIRONMENT=development), this check is skipped entirely
    so seeded dev users can access all endpoints without email verification.
    """
    from app.config import settings

    if settings.dev_mode:
        return current_user

    if not current_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "EMAIL_NOT_VERIFIED",
                "message": "Please verify your email address before using this feature.",
                "action": "resend_verification",
            },
        )
    return current_user


async def require_verified_email_soft(
    current_user: User = Depends(_lazy_get_current_user),
) -> User:
    """
    Soft variant: always passes through, does NOT block.
    Use for logging/analytics when you want to track unverified usage
    without breaking anything.
    """
    return current_user
