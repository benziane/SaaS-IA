"""
Social Publisher API routes - Social media publishing hub.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth import get_current_user
from app.database import get_session
from app.models.user import User
from app.modules.social_publisher.schemas import (
    PostAnalytics,
    PostCreate,
    PostRead,
    RecycleRequest,
    ScheduleUpdate,
    SocialAccountCreate,
    SocialAccountRead,
)
from app.modules.social_publisher.service import SocialPublisherService
from app.rate_limit import limiter

router = APIRouter()


# ------------------------------------------------------------------
# Account endpoints
# ------------------------------------------------------------------


@router.post("/accounts", response_model=SocialAccountRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def connect_account(
    request: Request,
    body: SocialAccountCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Connect a social media account.

    Supported platforms: twitter, linkedin, instagram, tiktok, facebook.
    The access token is hashed before storage and never returned.

    Rate limit: 10 requests/minute
    """
    valid_platforms = ["twitter", "linkedin", "instagram", "tiktok", "facebook"]
    if body.platform not in valid_platforms:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid platform '{body.platform}'. Must be one of: {valid_platforms}",
        )

    try:
        account = await SocialPublisherService.connect_account(
            user_id=current_user.id,
            platform=body.platform,
            access_token=body.access_token,
            account_name=body.account_name,
            session=session,
        )
        return account
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/accounts", response_model=list[SocialAccountRead])
@limiter.limit("20/minute")
async def list_accounts(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    List all connected social media accounts.

    Rate limit: 20 requests/minute
    """
    return await SocialPublisherService.list_accounts(current_user.id, session)


@router.delete("/accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def disconnect_account(
    request: Request,
    account_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Disconnect (deactivate) a social media account.

    Rate limit: 10 requests/minute
    """
    success = await SocialPublisherService.disconnect_account(
        current_user.id, account_id, session
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
    return None


# ------------------------------------------------------------------
# Post endpoints
# ------------------------------------------------------------------


@router.post("/posts", status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_post(
    request: Request,
    body: PostCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Create a social media post (draft or scheduled).

    Rate limit: 10 requests/minute
    """
    valid_platforms = ["twitter", "linkedin", "instagram", "tiktok", "facebook"]
    invalid = [p for p in body.platforms if p not in valid_platforms]
    if invalid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid platforms: {invalid}. Valid: {valid_platforms}",
        )

    try:
        post = await SocialPublisherService.create_post(
            user_id=current_user.id,
            content=body.content,
            platforms=body.platforms,
            session=session,
            schedule_at=body.schedule_at,
            media_urls=body.media_urls,
            hashtags=body.hashtags,
        )
        return SocialPublisherService.serialize_post(post)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/posts")
@limiter.limit("20/minute")
async def list_posts(
    request: Request,
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status: draft, scheduled, published, failed"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    List social media posts with optional status filtering.

    Rate limit: 20 requests/minute
    """
    posts, total = await SocialPublisherService.list_posts(
        user_id=current_user.id,
        session=session,
        status=status_filter,
        limit=limit,
        offset=offset,
    )
    return {
        "posts": [SocialPublisherService.serialize_post(p) for p in posts],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/posts/{post_id}")
@limiter.limit("20/minute")
async def get_post(
    request: Request,
    post_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Get a single post by ID.

    Rate limit: 20 requests/minute
    """
    post = await SocialPublisherService.get_post(current_user.id, post_id, session)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )
    return SocialPublisherService.serialize_post(post)


@router.post("/posts/{post_id}/publish")
@limiter.limit("5/minute")
async def publish_post(
    request: Request,
    post_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Publish a post to all target platforms immediately.

    Rate limit: 5 requests/minute
    """
    try:
        post = await SocialPublisherService.publish_post(
            current_user.id, post_id, session
        )
        return SocialPublisherService.serialize_post(post)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.put("/posts/{post_id}/schedule")
@limiter.limit("10/minute")
async def schedule_post(
    request: Request,
    post_id: UUID,
    body: ScheduleUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Schedule or reschedule a post.

    Rate limit: 10 requests/minute
    """
    post = await SocialPublisherService.schedule_post(
        current_user.id, post_id, body.schedule_at, session
    )
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found or already published",
        )
    return SocialPublisherService.serialize_post(post)


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def delete_post(
    request: Request,
    post_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Delete a draft or failed post.

    Published posts cannot be deleted.

    Rate limit: 10 requests/minute
    """
    success = await SocialPublisherService.delete_post(
        current_user.id, post_id, session
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found or cannot be deleted (already published)",
        )
    return None


@router.get("/posts/{post_id}/analytics", response_model=list[PostAnalytics])
@limiter.limit("20/minute")
async def get_analytics(
    request: Request,
    post_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Get analytics for a published post (mock data).

    Returns per-platform metrics: impressions, engagements, clicks, shares.

    Rate limit: 20 requests/minute
    """
    analytics = await SocialPublisherService.get_analytics(
        current_user.id, post_id, session
    )
    if not analytics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )
    return analytics


@router.post("/recycle")
@limiter.limit("5/minute")
async def recycle_content(
    request: Request,
    body: RecycleRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Recycle existing content (from Content Studio) into a social media post.

    Uses AI to adapt the content for the target platforms.

    Rate limit: 5 requests/minute
    """
    valid_platforms = ["twitter", "linkedin", "instagram", "tiktok", "facebook"]
    invalid = [p for p in body.platforms if p not in valid_platforms]
    if invalid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid platforms: {invalid}. Valid: {valid_platforms}",
        )

    post = await SocialPublisherService.recycle_content(
        user_id=current_user.id,
        content_id=body.content_id,
        platforms=body.platforms,
        session=session,
        custom_instructions=body.custom_instructions,
    )
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source content not found",
        )
    return SocialPublisherService.serialize_post(post)


@router.get("/platforms")
async def list_platforms():
    """List all supported social media platforms."""
    return {
        "platforms": [
            {"id": "twitter", "name": "Twitter / X", "description": "Short-form posts, threads", "max_length": 280, "icon": "Twitter"},
            {"id": "linkedin", "name": "LinkedIn", "description": "Professional networking posts", "max_length": 3000, "icon": "LinkedIn"},
            {"id": "instagram", "name": "Instagram", "description": "Visual content with captions", "max_length": 2200, "icon": "Instagram"},
            {"id": "tiktok", "name": "TikTok", "description": "Short video descriptions", "max_length": 2200, "icon": "TikTok"},
            {"id": "facebook", "name": "Facebook", "description": "Social posts and articles", "max_length": 63206, "icon": "Facebook"},
        ]
    }
