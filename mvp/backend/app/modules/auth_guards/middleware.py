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

from app.auth import get_current_user
from app.models.user import User


async def require_verified_email(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency: blocks with 403 if user has not verified their email.

    Add to any route that requires a verified email address.
    Example: premium features, publishing, API key creation.
    """
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
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Soft variant: always passes through, does NOT block.
    Use for logging/analytics when you want to track unverified usage
    without breaking anything.
    """
    return current_user
