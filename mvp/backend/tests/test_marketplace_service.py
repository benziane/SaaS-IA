"""
Tests for the Marketplace module - service, listings, reviews, installs, and routes.

All tests mock DB and AI providers. Uses pytest-asyncio.
"""

import json
from datetime import UTC, datetime
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.marketplace import MarketplaceListing, MarketplaceReview, MarketplaceInstall


# ---------------------------------------------------------------------------
# Helper to create a listing in the DB
# ---------------------------------------------------------------------------


async def _create_listing(
    session,
    user_id,
    title="Test Listing",
    listing_type="module",
    category="ai",
    is_published=False,
    price=0.0,
):
    listing = MarketplaceListing(
        author_id=user_id,
        title=title,
        description="A test marketplace listing",
        type=listing_type,
        category=category,
        price=price,
        version="1.0.0",
        content_json="{}",
        tags_json='["test"]',
        preview_images_json="[]",
        is_published=is_published,
    )
    session.add(listing)
    await session.commit()
    await session.refresh(listing)
    return listing


# ---------------------------------------------------------------------------
# MarketplaceService tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestMarketplaceService:
    """Tests for MarketplaceService business logic."""

    async def test_create_listing(self, session):
        from app.modules.marketplace.service import MarketplaceService

        service = MarketplaceService(session)
        user_id = uuid4()

        listing = await service.create_listing(
            user_id=user_id,
            data={
                "title": "My AI Module",
                "description": "An amazing AI module",
                "type": "module",
                "category": "ai",
                "price": 9.99,
                "version": "1.0.0",
                "content": {"config": "value"},
                "tags": ["ai", "nlp"],
            },
        )

        assert listing.title == "My AI Module"
        assert listing.author_id == user_id
        assert listing.is_published is False
        assert listing.price == 9.99

    async def test_create_listing_invalid_type(self, session):
        from app.modules.marketplace.service import MarketplaceService

        service = MarketplaceService(session)

        with pytest.raises(ValueError, match="Invalid type"):
            await service.create_listing(
                user_id=uuid4(),
                data={
                    "title": "Bad Listing",
                    "description": "Invalid type",
                    "type": "invalid_type",
                    "category": "ai",
                },
            )

    async def test_create_listing_invalid_category(self, session):
        from app.modules.marketplace.service import MarketplaceService

        service = MarketplaceService(session)

        with pytest.raises(ValueError, match="Invalid category"):
            await service.create_listing(
                user_id=uuid4(),
                data={
                    "title": "Bad Listing",
                    "description": "Invalid category",
                    "type": "module",
                    "category": "invalid_cat",
                },
            )

    async def test_publish_listing(self, session):
        from app.modules.marketplace.service import MarketplaceService

        service = MarketplaceService(session)
        user_id = uuid4()

        listing = await _create_listing(session, user_id)
        assert listing.is_published is False

        published = await service.publish_listing(user_id, listing.id)
        assert published is not None
        assert published.is_published is True

    async def test_unpublish_listing(self, session):
        from app.modules.marketplace.service import MarketplaceService

        service = MarketplaceService(session)
        user_id = uuid4()

        listing = await _create_listing(session, user_id, is_published=True)
        unpublished = await service.unpublish_listing(user_id, listing.id)
        assert unpublished is not None
        assert unpublished.is_published is False

    async def test_list_listings_public_only_published(self, session):
        from app.modules.marketplace.service import MarketplaceService

        service = MarketplaceService(session)
        user_id = uuid4()

        await _create_listing(session, user_id, title="Published", is_published=True)
        await _create_listing(session, user_id, title="Draft", is_published=False)

        listings, total = await service.list_listings()
        assert total == 1
        assert listings[0].title == "Published"

    async def test_search_listings(self, session):
        from app.modules.marketplace.service import MarketplaceService

        service = MarketplaceService(session)
        user_id = uuid4()

        await _create_listing(session, user_id, title="YouTube SEO Workflow", is_published=True)
        await _create_listing(session, user_id, title="Data Analysis Tool", is_published=True)

        listings, total = await service.list_listings(search="YouTube")
        assert total == 1
        assert listings[0].title == "YouTube SEO Workflow"

    async def test_install_listing(self, session):
        from app.modules.marketplace.service import MarketplaceService

        service = MarketplaceService(session)
        author_id = uuid4()
        installer_id = uuid4()

        listing = await _create_listing(session, author_id, is_published=True)

        install = await service.install_listing(installer_id, listing.id)
        assert install is not None
        assert install.user_id == installer_id
        assert install.listing_id == listing.id

        # Verify installs_count incremented
        await session.refresh(listing)
        assert listing.installs_count == 1

    async def test_install_listing_already_installed(self, session):
        from app.modules.marketplace.service import MarketplaceService

        service = MarketplaceService(session)
        author_id = uuid4()
        installer_id = uuid4()

        listing = await _create_listing(session, author_id, is_published=True)
        await service.install_listing(installer_id, listing.id)

        # Try installing again
        second = await service.install_listing(installer_id, listing.id)
        assert second is None  # Already installed

    async def test_uninstall_listing(self, session):
        from app.modules.marketplace.service import MarketplaceService

        service = MarketplaceService(session)
        author_id = uuid4()
        installer_id = uuid4()

        listing = await _create_listing(session, author_id, is_published=True)
        await service.install_listing(installer_id, listing.id)

        uninstalled = await service.uninstall_listing(installer_id, listing.id)
        assert uninstalled is True

        await session.refresh(listing)
        assert listing.installs_count == 0

    async def test_add_review(self, session):
        from app.modules.marketplace.service import MarketplaceService

        service = MarketplaceService(session)
        author_id = uuid4()
        reviewer_id = uuid4()

        listing = await _create_listing(session, author_id, is_published=True)

        review = await service.add_review(
            user_id=reviewer_id,
            listing_id=listing.id,
            data={"rating": 5, "comment": "Excellent module!"},
        )
        assert review is not None
        assert review.rating == 5
        assert review.comment == "Excellent module!"

    async def test_no_self_review(self, session):
        from app.modules.marketplace.service import MarketplaceService

        service = MarketplaceService(session)
        author_id = uuid4()

        listing = await _create_listing(session, author_id, is_published=True)

        with pytest.raises(ValueError, match="Cannot review your own listing"):
            await service.add_review(
                user_id=author_id,
                listing_id=listing.id,
                data={"rating": 5, "comment": "I love my own stuff"},
            )

    async def test_one_review_per_user(self, session):
        from app.modules.marketplace.service import MarketplaceService

        service = MarketplaceService(session)
        author_id = uuid4()
        reviewer_id = uuid4()

        listing = await _create_listing(session, author_id, is_published=True)

        # First review succeeds
        await service.add_review(
            user_id=reviewer_id,
            listing_id=listing.id,
            data={"rating": 4, "comment": "Good"},
        )

        # Second review by same user should fail
        with pytest.raises(ValueError, match="already reviewed"):
            await service.add_review(
                user_id=reviewer_id,
                listing_id=listing.id,
                data={"rating": 5, "comment": "Changed my mind"},
            )

    async def test_get_reviews(self, session):
        from app.modules.marketplace.service import MarketplaceService

        service = MarketplaceService(session)
        author_id = uuid4()

        listing = await _create_listing(session, author_id, is_published=True)

        # Add reviews from different users
        for i in range(3):
            reviewer_id = uuid4()
            await service.add_review(
                user_id=reviewer_id,
                listing_id=listing.id,
                data={"rating": 3 + (i % 3), "comment": f"Review {i}"},
            )

        reviews = await service.get_reviews(listing.id)
        assert len(reviews) == 3

    async def test_featured_listings(self, session):
        from app.modules.marketplace.service import MarketplaceService

        service = MarketplaceService(session)
        user_id = uuid4()

        # Create listings with different ratings
        for i in range(3):
            listing = await _create_listing(
                session, user_id,
                title=f"Listing {i}",
                is_published=True,
            )
            listing.rating = 5.0 - i
            listing.installs_count = 100 - (i * 10)
            session.add(listing)
        await session.commit()

        featured = await service.get_featured(limit=2)
        assert len(featured) == 2
        # Should be ordered by rating desc
        assert featured[0].rating >= featured[1].rating

    async def test_categories_count(self):
        from app.modules.marketplace.service import MarketplaceService

        categories = MarketplaceService.get_categories()
        assert len(categories) == 8
        ids = [c["id"] for c in categories]
        assert "ai" in ids
        assert "productivity" in ids
        assert "content" in ids
        assert "data" in ids
        assert "media" in ids
        assert "security" in ids
        assert "automation" in ids
        assert "other" in ids

    async def test_delete_listing_soft_delete(self, session):
        from app.modules.marketplace.service import MarketplaceService

        service = MarketplaceService(session)
        user_id = uuid4()

        listing = await _create_listing(session, user_id, is_published=True)
        deleted = await service.delete_listing(user_id, listing.id)
        assert deleted is True

        await session.refresh(listing)
        assert listing.is_deleted is True
        assert listing.is_published is False

    async def test_get_my_listings(self, session):
        from app.modules.marketplace.service import MarketplaceService

        service = MarketplaceService(session)
        user_id = uuid4()
        other_id = uuid4()

        await _create_listing(session, user_id, title="Mine")
        await _create_listing(session, other_id, title="Not Mine")

        my_listings = await service.get_my_listings(user_id)
        assert len(my_listings) == 1
        assert my_listings[0].title == "Mine"


# ---------------------------------------------------------------------------
# Route-level tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestMarketplaceRoutesAuth:
    """Test that authenticated marketplace endpoints require authentication."""

    async def test_create_listing_requires_auth(self, client):
        resp = await client.post("/api/marketplace/listings", json={
            "title": "Test",
            "description": "Test desc",
            "type": "module",
            "category": "ai",
        })
        assert resp.status_code in (401, 403)

    async def test_publish_listing_requires_auth(self, client):
        fake_id = str(uuid4())
        resp = await client.post(f"/api/marketplace/listings/{fake_id}/publish")
        assert resp.status_code in (401, 403)

    async def test_install_listing_requires_auth(self, client):
        fake_id = str(uuid4())
        resp = await client.post(f"/api/marketplace/listings/{fake_id}/install")
        assert resp.status_code in (401, 403)

    async def test_add_review_requires_auth(self, client):
        fake_id = str(uuid4())
        resp = await client.post(
            f"/api/marketplace/listings/{fake_id}/reviews",
            json={"rating": 5, "comment": "Great"},
        )
        assert resp.status_code in (401, 403)
