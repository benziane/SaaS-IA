"""
Marketplace service - Business logic for the module/template marketplace.
"""

import json
from datetime import UTC, datetime
from typing import Optional
from uuid import UUID

import structlog
from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.marketplace import (
    MarketplaceInstall,
    MarketplaceListing,
    MarketplaceReview,
)
from app.models.user import User

logger = structlog.get_logger()

VALID_TYPES = {"module", "template", "prompt", "workflow", "dataset"}
VALID_CATEGORIES = {"ai", "productivity", "content", "data", "media", "security", "automation", "other"}
VALID_SORT_OPTIONS = {"newest", "popular", "rating", "price_asc", "price_desc"}


class MarketplaceService:
    """Service for the marketplace: listings, reviews, installs."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_listing(self, user_id: UUID, data: dict) -> MarketplaceListing:
        """Create a new marketplace listing."""
        listing_type = data.get("type", "")
        if listing_type not in VALID_TYPES:
            raise ValueError(f"Invalid type: {listing_type}. Must be one of {VALID_TYPES}")

        category = data.get("category", "other")
        if category not in VALID_CATEGORIES:
            raise ValueError(f"Invalid category: {category}. Must be one of {VALID_CATEGORIES}")

        listing = MarketplaceListing(
            author_id=user_id,
            title=data["title"],
            description=data["description"],
            type=listing_type,
            category=category,
            price=data.get("price", 0.0),
            version=data.get("version", "1.0.0"),
            content_json=json.dumps(data.get("content", {}), ensure_ascii=False),
            tags_json=json.dumps(data.get("tags") or [], ensure_ascii=False),
            preview_images_json=json.dumps(data.get("preview_images") or [], ensure_ascii=False),
        )
        self.session.add(listing)
        await self.session.commit()
        await self.session.refresh(listing)

        logger.info(
            "marketplace_listing_created",
            listing_id=str(listing.id),
            title=listing.title,
            type=listing.type,
        )
        return listing

    async def list_listings(
        self,
        type: Optional[str] = None,
        category: Optional[str] = None,
        sort_by: str = "newest",
        search: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[MarketplaceListing], int]:
        """Browse/search published marketplace listings (public)."""
        base = select(MarketplaceListing).where(
            MarketplaceListing.is_published == True,
            MarketplaceListing.is_deleted == False,
        )

        if type:
            base = base.where(MarketplaceListing.type == type)
        if category:
            base = base.where(MarketplaceListing.category == category)
        if search:
            pattern = f"%{search}%"
            base = base.where(
                MarketplaceListing.title.ilike(pattern)
                | MarketplaceListing.description.ilike(pattern)
            )

        # Count
        count_stmt = select(func.count()).select_from(base.subquery())
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar_one()

        # Sort
        if sort_by == "popular":
            base = base.order_by(MarketplaceListing.installs_count.desc())
        elif sort_by == "rating":
            base = base.order_by(MarketplaceListing.rating.desc())
        elif sort_by == "price_asc":
            base = base.order_by(MarketplaceListing.price.asc())
        elif sort_by == "price_desc":
            base = base.order_by(MarketplaceListing.price.desc())
        else:
            base = base.order_by(MarketplaceListing.created_at.desc())

        base = base.offset(offset).limit(limit)
        result = await self.session.execute(base)
        return list(result.scalars().all()), total

    async def get_listing(self, listing_id: UUID) -> Optional[MarketplaceListing]:
        """Get a listing by ID (must be published or not deleted for public)."""
        listing = await self.session.get(MarketplaceListing, listing_id)
        if not listing or listing.is_deleted:
            return None
        return listing

    async def update_listing(
        self, user_id: UUID, listing_id: UUID, data: dict
    ) -> Optional[MarketplaceListing]:
        """Update a listing (author only)."""
        listing = await self.session.get(MarketplaceListing, listing_id)
        if not listing or listing.is_deleted or listing.author_id != user_id:
            return None

        if "title" in data and data["title"]:
            listing.title = data["title"]
        if "description" in data and data["description"]:
            listing.description = data["description"]
        if "price" in data and data["price"] is not None:
            listing.price = data["price"]
        if "version" in data and data["version"]:
            listing.version = data["version"]
        if "content" in data and data["content"] is not None:
            listing.content_json = json.dumps(data["content"], ensure_ascii=False)
        if "tags" in data and data["tags"] is not None:
            listing.tags_json = json.dumps(data["tags"], ensure_ascii=False)

        listing.updated_at = datetime.now(UTC)
        self.session.add(listing)
        await self.session.commit()
        await self.session.refresh(listing)
        return listing

    async def publish_listing(
        self, user_id: UUID, listing_id: UUID
    ) -> Optional[MarketplaceListing]:
        """Publish a listing (author only)."""
        listing = await self.session.get(MarketplaceListing, listing_id)
        if not listing or listing.is_deleted or listing.author_id != user_id:
            return None

        listing.is_published = True
        listing.updated_at = datetime.now(UTC)
        self.session.add(listing)
        await self.session.commit()
        await self.session.refresh(listing)

        logger.info("marketplace_listing_published", listing_id=str(listing_id))
        return listing

    async def unpublish_listing(
        self, user_id: UUID, listing_id: UUID
    ) -> Optional[MarketplaceListing]:
        """Unpublish a listing (author only)."""
        listing = await self.session.get(MarketplaceListing, listing_id)
        if not listing or listing.is_deleted or listing.author_id != user_id:
            return None

        listing.is_published = False
        listing.updated_at = datetime.now(UTC)
        self.session.add(listing)
        await self.session.commit()
        await self.session.refresh(listing)

        logger.info("marketplace_listing_unpublished", listing_id=str(listing_id))
        return listing

    async def delete_listing(
        self, user_id: UUID, listing_id: UUID
    ) -> bool:
        """Soft-delete a listing (author only)."""
        listing = await self.session.get(MarketplaceListing, listing_id)
        if not listing or listing.author_id != user_id:
            return False

        listing.is_deleted = True
        listing.is_published = False
        listing.updated_at = datetime.now(UTC)
        self.session.add(listing)
        await self.session.commit()

        logger.info("marketplace_listing_deleted", listing_id=str(listing_id))
        return True

    async def install_listing(
        self, user_id: UUID, listing_id: UUID
    ) -> Optional[MarketplaceInstall]:
        """Install/activate a listing for a user."""
        listing = await self.session.get(MarketplaceListing, listing_id)
        if not listing or listing.is_deleted or not listing.is_published:
            return None

        # Check if already installed
        existing = await self.session.execute(
            select(MarketplaceInstall).where(
                MarketplaceInstall.user_id == user_id,
                MarketplaceInstall.listing_id == listing_id,
            )
        )
        if existing.scalars().first():
            return None  # Already installed

        install = MarketplaceInstall(
            user_id=user_id,
            listing_id=listing_id,
            version=listing.version,
        )
        self.session.add(install)

        listing.installs_count += 1
        self.session.add(listing)

        await self.session.commit()
        await self.session.refresh(install)

        logger.info(
            "marketplace_installed",
            listing_id=str(listing_id),
            user_id=str(user_id),
        )
        return install

    async def uninstall_listing(
        self, user_id: UUID, listing_id: UUID
    ) -> bool:
        """Uninstall/remove a listing from a user."""
        result = await self.session.execute(
            select(MarketplaceInstall).where(
                MarketplaceInstall.user_id == user_id,
                MarketplaceInstall.listing_id == listing_id,
            )
        )
        install = result.scalars().first()
        if not install:
            return False

        await self.session.delete(install)

        listing = await self.session.get(MarketplaceListing, listing_id)
        if listing and listing.installs_count > 0:
            listing.installs_count -= 1
            self.session.add(listing)

        await self.session.commit()

        logger.info(
            "marketplace_uninstalled",
            listing_id=str(listing_id),
            user_id=str(user_id),
        )
        return True

    async def list_installed(
        self, user_id: UUID
    ) -> list[MarketplaceInstall]:
        """List all installed items for a user."""
        result = await self.session.execute(
            select(MarketplaceInstall)
            .where(MarketplaceInstall.user_id == user_id)
            .order_by(MarketplaceInstall.installed_at.desc())
        )
        return list(result.scalars().all())

    async def add_review(
        self, user_id: UUID, listing_id: UUID, data: dict
    ) -> Optional[MarketplaceReview]:
        """Add a review (one per user per listing). Returns None if listing not found."""
        listing = await self.session.get(MarketplaceListing, listing_id)
        if not listing or listing.is_deleted or not listing.is_published:
            return None

        # Prevent reviewing own listing
        if listing.author_id == user_id:
            raise ValueError("Cannot review your own listing")

        # Check for existing review (unique constraint)
        existing = await self.session.execute(
            select(MarketplaceReview).where(
                MarketplaceReview.user_id == user_id,
                MarketplaceReview.listing_id == listing_id,
            )
        )
        if existing.scalars().first():
            raise ValueError("You have already reviewed this listing")

        review = MarketplaceReview(
            user_id=user_id,
            listing_id=listing_id,
            rating=data["rating"],
            comment=data.get("comment"),
        )
        self.session.add(review)

        # Recalculate average rating
        listing.reviews_count += 1
        all_reviews = await self.session.execute(
            select(MarketplaceReview.rating).where(
                MarketplaceReview.listing_id == listing_id
            )
        )
        ratings = [r for (r,) in all_reviews.all()]
        ratings.append(data["rating"])
        listing.rating = round(sum(ratings) / len(ratings), 2)
        self.session.add(listing)

        await self.session.commit()
        await self.session.refresh(review)

        logger.info(
            "marketplace_review_added",
            listing_id=str(listing_id),
            user_id=str(user_id),
            rating=data["rating"],
        )
        return review

    async def get_reviews(
        self, listing_id: UUID, limit: int = 20, offset: int = 0
    ) -> list[MarketplaceReview]:
        """List reviews for a listing."""
        result = await self.session.execute(
            select(MarketplaceReview)
            .where(MarketplaceReview.listing_id == listing_id)
            .order_by(MarketplaceReview.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_my_listings(
        self, user_id: UUID
    ) -> list[MarketplaceListing]:
        """List all listings created by a user."""
        result = await self.session.execute(
            select(MarketplaceListing)
            .where(
                MarketplaceListing.author_id == user_id,
                MarketplaceListing.is_deleted == False,
            )
            .order_by(MarketplaceListing.updated_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    def get_categories() -> list[dict]:
        """Return all available categories."""
        categories = [
            {"id": "ai", "name": "AI & Machine Learning", "icon": "SmartToy"},
            {"id": "productivity", "name": "Productivity", "icon": "Speed"},
            {"id": "content", "name": "Content Creation", "icon": "Edit"},
            {"id": "data", "name": "Data & Analytics", "icon": "BarChart"},
            {"id": "media", "name": "Media & Creative", "icon": "Image"},
            {"id": "security", "name": "Security & Compliance", "icon": "Shield"},
            {"id": "automation", "name": "Automation", "icon": "AutoMode"},
            {"id": "other", "name": "Other", "icon": "Category"},
        ]
        return categories

    async def get_featured(self, limit: int = 8) -> list[MarketplaceListing]:
        """Return top-rated published listings."""
        result = await self.session.execute(
            select(MarketplaceListing)
            .where(
                MarketplaceListing.is_published == True,
                MarketplaceListing.is_deleted == False,
            )
            .order_by(
                MarketplaceListing.rating.desc(),
                MarketplaceListing.installs_count.desc(),
            )
            .limit(limit)
        )
        return list(result.scalars().all())

    async def _get_user_name(self, user_id: UUID) -> str:
        """Get a user's display name."""
        user = await self.session.get(User, user_id)
        if user:
            return user.full_name or user.email.split("@")[0]
        return "Unknown"
