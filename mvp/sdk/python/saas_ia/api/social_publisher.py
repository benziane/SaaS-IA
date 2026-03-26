"""Social Publisher API — multi-platform social media publishing."""

from __future__ import annotations

from typing import Any

from saas_ia.api.base import BaseAPI


class SocialPublisherAPI(BaseAPI):
    """Wraps ``/api/social-publisher`` endpoints."""

    # -- Accounts -----------------------------------------------------------

    async def connect_account(
        self,
        platform: str,
        credentials: dict[str, str],
    ) -> dict[str, Any]:
        """Connect a social media account."""
        return await self._post(
            "/api/social-publisher/accounts",
            json={"platform": platform, "credentials": credentials},
        )

    async def list_accounts(self) -> list[dict[str, Any]]:
        """List connected accounts."""
        return await self._get("/api/social-publisher/accounts")

    async def disconnect_account(self, account_id: str) -> None:
        """Disconnect an account."""
        await self._delete(f"/api/social-publisher/accounts/{account_id}")

    # -- Posts --------------------------------------------------------------

    async def create_post(
        self,
        content: str,
        platforms: list[str],
        *,
        scheduled_at: str | None = None,
    ) -> dict[str, Any]:
        """Create a post (draft or scheduled)."""
        body: dict[str, Any] = {
            "content": content,
            "platforms": platforms,
        }
        if scheduled_at:
            body["scheduled_at"] = scheduled_at
        return await self._post("/api/social-publisher/posts", json=body)

    async def list_posts(
        self,
        *,
        status: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[dict[str, Any]]:
        """List posts (filterable by status)."""
        return await self._get(
            "/api/social-publisher/posts",
            params={"status": status, "limit": limit, "offset": offset},
        )

    async def get_post(self, post_id: str) -> dict[str, Any]:
        """Get post details."""
        return await self._get(f"/api/social-publisher/posts/{post_id}")

    async def publish_post(self, post_id: str) -> dict[str, Any]:
        """Publish a post immediately."""
        return await self._post(
            f"/api/social-publisher/posts/{post_id}/publish"
        )

    async def schedule_post(
        self, post_id: str, scheduled_at: str
    ) -> dict[str, Any]:
        """Schedule or reschedule a post."""
        return await self._put(
            f"/api/social-publisher/posts/{post_id}/schedule",
            json={"scheduled_at": scheduled_at},
        )

    async def delete_post(self, post_id: str) -> None:
        """Delete a draft or failed post."""
        await self._delete(f"/api/social-publisher/posts/{post_id}")

    async def post_analytics(self, post_id: str) -> dict[str, Any]:
        """Get post analytics."""
        return await self._get(
            f"/api/social-publisher/posts/{post_id}/analytics"
        )

    # -- Content recycling --------------------------------------------------

    async def recycle(
        self,
        content_id: str,
        platforms: list[str],
    ) -> dict[str, Any]:
        """Recycle Content Studio content for social media."""
        return await self._post(
            "/api/social-publisher/recycle",
            json={"content_id": content_id, "platforms": platforms},
        )

    # -- Reference ----------------------------------------------------------

    async def list_platforms(self) -> list[dict[str, Any]]:
        """List supported platforms."""
        return await self._get("/api/social-publisher/platforms")
