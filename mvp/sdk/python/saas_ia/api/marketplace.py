"""Marketplace API — browse, publish, install, and review community items."""

from __future__ import annotations

from typing import Any

from saas_ia.api.base import BaseAPI


class MarketplaceAPI(BaseAPI):
    """Wraps ``/api/marketplace`` endpoints."""

    # -- Public browsing ----------------------------------------------------

    async def browse(
        self,
        *,
        category: str | None = None,
        search: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[dict[str, Any]]:
        """Browse marketplace listings."""
        return await self._get(
            "/api/marketplace/listings",
            params={
                "category": category,
                "search": search,
                "limit": limit,
                "offset": offset,
            },
        )

    async def get_listing(self, listing_id: str) -> dict[str, Any]:
        """Get listing details."""
        return await self._get(f"/api/marketplace/listings/{listing_id}")

    async def get_reviews(self, listing_id: str) -> list[dict[str, Any]]:
        """Get reviews for a listing."""
        return await self._get(
            f"/api/marketplace/listings/{listing_id}/reviews"
        )

    async def categories(self) -> list[dict[str, Any]]:
        """List categories."""
        return await self._get("/api/marketplace/categories")

    async def featured(self) -> list[dict[str, Any]]:
        """Get featured listings."""
        return await self._get("/api/marketplace/featured")

    # -- Authoring ----------------------------------------------------------

    async def create_listing(
        self,
        title: str,
        description: str,
        category: str,
        *,
        price: float | None = None,
        tags: list[str] | None = None,
        content_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a new listing."""
        body: dict[str, Any] = {
            "title": title,
            "description": description,
            "category": category,
        }
        if price is not None:
            body["price"] = price
        if tags:
            body["tags"] = tags
        if content_data:
            body["content_data"] = content_data
        return await self._post("/api/marketplace/listings", json=body)

    async def update_listing(
        self,
        listing_id: str,
        *,
        title: str | None = None,
        description: str | None = None,
        price: float | None = None,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """Update a listing."""
        body: dict[str, Any] = {}
        if title is not None:
            body["title"] = title
        if description is not None:
            body["description"] = description
        if price is not None:
            body["price"] = price
        if tags is not None:
            body["tags"] = tags
        return await self._put(
            f"/api/marketplace/listings/{listing_id}",
            json=body,
        )

    async def publish(self, listing_id: str) -> None:
        """Publish a listing."""
        await self._post(f"/api/marketplace/listings/{listing_id}/publish")

    async def unpublish(self, listing_id: str) -> None:
        """Unpublish a listing."""
        await self._post(f"/api/marketplace/listings/{listing_id}/unpublish")

    async def delete_listing(self, listing_id: str) -> None:
        """Soft-delete a listing."""
        await self._delete(f"/api/marketplace/listings/{listing_id}")

    async def my_listings(self) -> list[dict[str, Any]]:
        """List own listings."""
        return await self._get("/api/marketplace/my-listings")

    # -- Install / uninstall ------------------------------------------------

    async def install(self, listing_id: str) -> dict[str, Any]:
        """Install a listing."""
        return await self._post(
            f"/api/marketplace/listings/{listing_id}/install"
        )

    async def uninstall(self, listing_id: str) -> None:
        """Uninstall a listing."""
        await self._delete(f"/api/marketplace/listings/{listing_id}/install")

    async def installed(self) -> list[dict[str, Any]]:
        """List installed items."""
        return await self._get("/api/marketplace/installed")

    # -- Reviews ------------------------------------------------------------

    async def add_review(
        self,
        listing_id: str,
        rating: int,
        *,
        comment: str | None = None,
    ) -> dict[str, Any]:
        """Add a review to a listing."""
        body: dict[str, Any] = {"rating": rating}
        if comment:
            body["comment"] = comment
        return await self._post(
            f"/api/marketplace/listings/{listing_id}/reviews",
            json=body,
        )
