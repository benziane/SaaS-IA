"""
Marketplace API routes - Browse, publish, install, and review marketplace items.
"""

import json
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth import get_current_user
from app.database import get_session
from app.models.user import User
from app.modules.marketplace.schemas import (
    InstallRead,
    ListingCreate,
    ListingRead,
    ListingUpdate,
    ReviewCreate,
    ReviewRead,
)
from app.modules.marketplace.service import MarketplaceService
from app.rate_limit import limiter

router = APIRouter()


async def _listing_to_read(
    listing, service: MarketplaceService
) -> ListingRead:
    """Convert a MarketplaceListing model to ListingRead schema."""
    author_name = await service._get_user_name(listing.author_id)
    return ListingRead(
        id=listing.id,
        author_id=listing.author_id,
        author_name=author_name,
        title=listing.title,
        description=listing.description,
        type=listing.type,
        category=listing.category,
        price=listing.price,
        version=listing.version,
        content=json.loads(listing.content_json) if listing.content_json else {},
        tags=json.loads(listing.tags_json) if listing.tags_json else [],
        preview_images=json.loads(listing.preview_images_json) if listing.preview_images_json else [],
        rating=listing.rating,
        reviews_count=listing.reviews_count,
        installs_count=listing.installs_count,
        is_published=listing.is_published,
        created_at=listing.created_at,
        updated_at=listing.updated_at,
    )


async def _review_to_read(
    review, service: MarketplaceService
) -> ReviewRead:
    """Convert a MarketplaceReview model to ReviewRead schema."""
    user_name = await service._get_user_name(review.user_id)
    return ReviewRead(
        id=review.id,
        user_id=review.user_id,
        user_name=user_name,
        listing_id=review.listing_id,
        rating=review.rating,
        comment=review.comment,
        created_at=review.created_at,
    )


# ─── Public endpoints (no auth required for browsing) ────────────────────────


@router.get("/listings", response_model=list[ListingRead])
@limiter.limit("30/minute")
async def browse_listings(
    request: Request,
    type: Optional[str] = Query(None, description="Filter by type: module, template, prompt, workflow, dataset"),
    category: Optional[str] = Query(None, description="Filter by category"),
    sort_by: str = Query("newest", description="Sort: newest, popular, rating, price_asc, price_desc"),
    search: Optional[str] = Query(None, description="Search in title and description"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    """
    Browse published marketplace listings (public, no auth needed).

    Rate limit: 30 requests/minute
    """
    service = MarketplaceService(session)
    listings, _ = await service.list_listings(
        type=type,
        category=category,
        sort_by=sort_by,
        search=search,
        limit=limit,
        offset=offset,
    )
    return [await _listing_to_read(l, service) for l in listings]


@router.get("/listings/{listing_id}", response_model=ListingRead)
@limiter.limit("30/minute")
async def get_listing(
    request: Request,
    listing_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """
    Get a listing by ID (public).

    Rate limit: 30 requests/minute
    """
    service = MarketplaceService(session)
    listing = await service.get_listing(listing_id)
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found",
        )
    return await _listing_to_read(listing, service)


@router.get("/categories")
@limiter.limit("30/minute")
async def get_categories(request: Request):
    """
    Get all available marketplace categories (public).

    Rate limit: 30 requests/minute
    """
    return MarketplaceService.get_categories()


@router.get("/featured", response_model=list[ListingRead])
@limiter.limit("30/minute")
async def get_featured(
    request: Request,
    limit: int = Query(8, ge=1, le=20),
    session: AsyncSession = Depends(get_session),
):
    """
    Get top-rated featured listings (public).

    Rate limit: 30 requests/minute
    """
    service = MarketplaceService(session)
    listings = await service.get_featured(limit)
    return [await _listing_to_read(l, service) for l in listings]


@router.get("/listings/{listing_id}/reviews", response_model=list[ReviewRead])
@limiter.limit("30/minute")
async def get_reviews(
    request: Request,
    listing_id: UUID,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    """
    Get reviews for a listing (public).

    Rate limit: 30 requests/minute
    """
    service = MarketplaceService(session)
    reviews = await service.get_reviews(listing_id, limit, offset)
    return [await _review_to_read(r, service) for r in reviews]


# ─── Authenticated endpoints ─────────────────────────────────────────────────


@router.post("/listings", response_model=ListingRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_listing(
    request: Request,
    body: ListingCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Create a new marketplace listing.

    Rate limit: 10 requests/minute
    """
    service = MarketplaceService(session)
    try:
        listing = await service.create_listing(
            user_id=current_user.id,
            data=body.model_dump(),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return await _listing_to_read(listing, service)


@router.put("/listings/{listing_id}", response_model=ListingRead)
@limiter.limit("10/minute")
async def update_listing(
    request: Request,
    listing_id: UUID,
    body: ListingUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Update a listing (author only).

    Rate limit: 10 requests/minute
    """
    service = MarketplaceService(session)
    listing = await service.update_listing(
        user_id=current_user.id,
        listing_id=listing_id,
        data=body.model_dump(exclude_unset=True),
    )
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found or not authorized",
        )
    return await _listing_to_read(listing, service)


@router.post("/listings/{listing_id}/publish", response_model=ListingRead)
@limiter.limit("10/minute")
async def publish_listing(
    request: Request,
    listing_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Publish a listing to the marketplace (author only).

    Rate limit: 10 requests/minute
    """
    service = MarketplaceService(session)
    listing = await service.publish_listing(current_user.id, listing_id)
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found or not authorized",
        )
    return await _listing_to_read(listing, service)


@router.post("/listings/{listing_id}/unpublish", response_model=ListingRead)
@limiter.limit("10/minute")
async def unpublish_listing(
    request: Request,
    listing_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Unpublish a listing from the marketplace (author only).

    Rate limit: 10 requests/minute
    """
    service = MarketplaceService(session)
    listing = await service.unpublish_listing(current_user.id, listing_id)
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found or not authorized",
        )
    return await _listing_to_read(listing, service)


@router.delete("/listings/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def delete_listing(
    request: Request,
    listing_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Soft-delete a listing (author only).

    Rate limit: 10 requests/minute
    """
    service = MarketplaceService(session)
    deleted = await service.delete_listing(current_user.id, listing_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found or not authorized",
        )
    return None


@router.post("/listings/{listing_id}/install", response_model=InstallRead)
@limiter.limit("10/minute")
async def install_listing(
    request: Request,
    listing_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Install a marketplace listing for the current user.

    Rate limit: 10 requests/minute
    """
    service = MarketplaceService(session)
    install = await service.install_listing(current_user.id, listing_id)
    if not install:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Listing not found, not published, or already installed",
        )
    return InstallRead(
        id=install.id,
        user_id=install.user_id,
        listing_id=install.listing_id,
        installed_at=install.installed_at,
        version=install.version,
    )


@router.delete("/listings/{listing_id}/install", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def uninstall_listing(
    request: Request,
    listing_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Uninstall a marketplace listing for the current user.

    Rate limit: 10 requests/minute
    """
    service = MarketplaceService(session)
    uninstalled = await service.uninstall_listing(current_user.id, listing_id)
    if not uninstalled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Install not found",
        )
    return None


@router.get("/installed", response_model=list[InstallRead])
@limiter.limit("20/minute")
async def list_installed(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    List all marketplace items installed by the current user.

    Rate limit: 20 requests/minute
    """
    service = MarketplaceService(session)
    installs = await service.list_installed(current_user.id)
    return [
        InstallRead(
            id=i.id,
            user_id=i.user_id,
            listing_id=i.listing_id,
            installed_at=i.installed_at,
            version=i.version,
        )
        for i in installs
    ]


@router.post("/listings/{listing_id}/reviews", response_model=ReviewRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def add_review(
    request: Request,
    listing_id: UUID,
    body: ReviewCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Add a review to a marketplace listing (one per user per listing).

    Rate limit: 5 requests/minute
    """
    service = MarketplaceService(session)
    try:
        review = await service.add_review(
            user_id=current_user.id,
            listing_id=listing_id,
            data=body.model_dump(),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found or not published",
        )
    return await _review_to_read(review, service)


@router.get("/my-listings", response_model=list[ListingRead])
@limiter.limit("20/minute")
async def get_my_listings(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    List the current user's own marketplace listings.

    Rate limit: 20 requests/minute
    """
    service = MarketplaceService(session)
    listings = await service.get_my_listings(current_user.id)
    return [await _listing_to_read(l, service) for l in listings]
