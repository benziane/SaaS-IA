"""
API Key management routes.
"""

import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth import get_current_user
from app.modules.auth_guards.middleware import require_verified_email
from app.database import get_session
from app.models.user import User
from app.modules.api_keys.schemas import APIKeyCreate, APIKeyCreated, APIKeyRead
from app.modules.api_keys.service import APIKeyService
from app.rate_limit import limiter

router = APIRouter()


@router.post("/", response_model=APIKeyCreated, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def create_api_key(
    request: Request,
    body: APIKeyCreate,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """
    Create a new API key.

    The key is returned in plain text ONLY in this response.
    Store it securely - it cannot be retrieved again.

    Rate limit: 5 requests/minute
    """
    api_key, raw_key = await APIKeyService.create_key(
        user_id=current_user.id,
        name=body.name,
        permissions=body.permissions,
        rate_limit_per_day=body.rate_limit_per_day,
        session=session,
    )

    return APIKeyCreated(
        id=api_key.id,
        name=api_key.name,
        key=raw_key,
        key_prefix=api_key.key_prefix,
        permissions=body.permissions,
        rate_limit_per_day=api_key.rate_limit_per_day,
    )


@router.get("/", response_model=list[APIKeyRead])
@limiter.limit("20/minute")
async def list_api_keys(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    List all API keys for the current user.

    Keys are returned without the secret - only the prefix is shown.

    Rate limit: 20 requests/minute
    """
    keys = await APIKeyService.list_keys(current_user.id, session)
    return [
        APIKeyRead(
            id=k.id,
            name=k.name,
            key_prefix=k.key_prefix,
            permissions=json.loads(k.permissions_json),
            rate_limit_per_day=k.rate_limit_per_day,
            is_active=k.is_active,
            last_used_at=k.last_used_at,
            created_at=k.created_at,
        )
        for k in keys
    ]


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def revoke_api_key(
    request: Request,
    key_id: UUID,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """
    Revoke an API key.

    Rate limit: 10 requests/minute
    """
    revoked = await APIKeyService.revoke_key(key_id, current_user.id, session)
    if not revoked:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )
    return None
