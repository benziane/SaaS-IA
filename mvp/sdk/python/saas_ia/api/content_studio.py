"""Content Studio API — multi-format content generation (10 formats)."""

from __future__ import annotations

from typing import Any

from saas_ia.api.base import BaseAPI


class ContentStudioAPI(BaseAPI):
    """Wraps ``/api/content-studio`` endpoints."""

    # -- Projects -----------------------------------------------------------

    async def create_project(
        self,
        title: str,
        *,
        description: str | None = None,
        source_text: str | None = None,
    ) -> dict[str, Any]:
        """Create a content project."""
        body: dict[str, Any] = {"title": title}
        if description:
            body["description"] = description
        if source_text:
            body["source_text"] = source_text
        return await self._post("/api/content-studio/projects", json=body)

    async def list_projects(
        self,
        *,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[dict[str, Any]]:
        """List content projects."""
        return await self._get(
            "/api/content-studio/projects",
            params={"limit": limit, "offset": offset},
        )

    async def delete_project(self, project_id: str) -> None:
        """Delete a project and all its content pieces."""
        await self._delete(f"/api/content-studio/projects/{project_id}")

    # -- Content generation -------------------------------------------------

    async def generate(
        self,
        project_id: str,
        formats: list[str],
        *,
        tone: str | None = None,
        language: str | None = None,
    ) -> list[dict[str, Any]]:
        """Generate content in one or more formats for a project."""
        body: dict[str, Any] = {"formats": formats}
        if tone:
            body["tone"] = tone
        if language:
            body["language"] = language
        return await self._post(
            f"/api/content-studio/projects/{project_id}/generate",
            json=body,
        )

    async def list_contents(self, project_id: str) -> list[dict[str, Any]]:
        """Get all content pieces for a project."""
        return await self._get(
            f"/api/content-studio/projects/{project_id}/contents"
        )

    async def update_content(
        self,
        content_id: str,
        *,
        content: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Update a content piece."""
        body: dict[str, Any] = {}
        if content is not None:
            body["content"] = content
        if metadata is not None:
            body["metadata"] = metadata
        return await self._put(
            f"/api/content-studio/contents/{content_id}",
            json=body,
        )

    async def regenerate_content(self, content_id: str) -> dict[str, Any]:
        """Regenerate a content piece."""
        return await self._post(
            f"/api/content-studio/contents/{content_id}/regenerate"
        )

    # -- URL-based generation -----------------------------------------------

    async def from_url(
        self,
        url: str,
        formats: list[str],
        *,
        tone: str | None = None,
    ) -> list[dict[str, Any]]:
        """Crawl a URL and generate content from its text."""
        body: dict[str, Any] = {"url": url, "formats": formats}
        if tone:
            body["tone"] = tone
        return await self._post("/api/content-studio/from-url", json=body)

    # -- Reference ----------------------------------------------------------

    async def list_formats(self) -> list[dict[str, Any]]:
        """List available content formats."""
        return await self._get("/api/content-studio/formats")
