"""Presentation Gen API — AI slide generation (5 templates)."""

from __future__ import annotations

from typing import Any

from saas_ia.api.base import BaseAPI


class PresentationGenAPI(BaseAPI):
    """Wraps ``/api/presentations`` endpoints."""

    async def create(
        self,
        topic: str,
        *,
        template: str | None = None,
        slide_count: int | None = None,
        language: str | None = None,
    ) -> dict[str, Any]:
        """Generate a presentation from a topic."""
        body: dict[str, Any] = {"topic": topic}
        if template:
            body["template"] = template
        if slide_count:
            body["slide_count"] = slide_count
        if language:
            body["language"] = language
        return await self._post("/api/presentations", json=body)

    async def list(
        self,
        *,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[dict[str, Any]]:
        """List presentations."""
        return await self._get(
            "/api/presentations",
            params={"limit": limit, "offset": offset},
        )

    async def get(self, presentation_id: str) -> dict[str, Any]:
        """Get presentation with slides."""
        return await self._get(f"/api/presentations/{presentation_id}")

    async def delete(self, presentation_id: str) -> None:
        """Delete a presentation."""
        await self._delete(f"/api/presentations/{presentation_id}")

    async def update_slide(
        self,
        presentation_id: str,
        position: int,
        *,
        title: str | None = None,
        content: str | None = None,
        notes: str | None = None,
        layout: str | None = None,
    ) -> dict[str, Any]:
        """Update a slide at a given position."""
        body: dict[str, Any] = {}
        if title is not None:
            body["title"] = title
        if content is not None:
            body["content"] = content
        if notes is not None:
            body["notes"] = notes
        if layout is not None:
            body["layout"] = layout
        return await self._put(
            f"/api/presentations/{presentation_id}/slides/{position}",
            json=body,
        )

    async def insert_slide(
        self,
        presentation_id: str,
        after_position: int,
        **slide_data: Any,
    ) -> dict[str, Any]:
        """Insert a slide after a given position."""
        return await self._post(
            f"/api/presentations/{presentation_id}/slides/{after_position}",
            json=slide_data,
        )

    async def remove_slide(
        self, presentation_id: str, position: int
    ) -> None:
        """Remove a slide."""
        await self._delete(
            f"/api/presentations/{presentation_id}/slides/{position}"
        )

    async def export(
        self,
        presentation_id: str,
        format: str = "html",
    ) -> Any:
        """Export presentation (html, markdown, pdf)."""
        return await self._post(
            f"/api/presentations/{presentation_id}/export",
            json={"format": format},
        )

    async def from_transcript(
        self,
        transcription_id: str,
        *,
        template: str | None = None,
        slide_count: int | None = None,
    ) -> dict[str, Any]:
        """Generate a presentation from a transcription."""
        body: dict[str, Any] = {"transcription_id": transcription_id}
        if template:
            body["template"] = template
        if slide_count:
            body["slide_count"] = slide_count
        return await self._post("/api/presentations/from-transcript", json=body)

    async def list_templates(self) -> list[dict[str, Any]]:
        """List available presentation templates."""
        return await self._get("/api/presentations/templates")
