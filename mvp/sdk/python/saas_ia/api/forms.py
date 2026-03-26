"""AI Forms API — conversational forms with AI generation and scoring."""

from __future__ import annotations

from typing import Any

from saas_ia.api.base import BaseAPI


class FormsAPI(BaseAPI):
    """Wraps ``/api/forms`` endpoints."""

    # -- CRUD ---------------------------------------------------------------

    async def create(
        self,
        title: str,
        fields: list[dict[str, Any]],
        *,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Create a form."""
        body: dict[str, Any] = {"title": title, "fields": fields}
        if description:
            body["description"] = description
        return await self._post("/api/forms", json=body)

    async def list(
        self,
        *,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[dict[str, Any]]:
        """List forms."""
        return await self._get(
            "/api/forms",
            params={"limit": limit, "offset": offset},
        )

    async def get(self, form_id: str) -> dict[str, Any]:
        """Get form details."""
        return await self._get(f"/api/forms/{form_id}")

    async def update(
        self,
        form_id: str,
        *,
        title: str | None = None,
        description: str | None = None,
        fields: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Update a form."""
        body: dict[str, Any] = {}
        if title is not None:
            body["title"] = title
        if description is not None:
            body["description"] = description
        if fields is not None:
            body["fields"] = fields
        return await self._put(f"/api/forms/{form_id}", json=body)

    async def delete(self, form_id: str) -> None:
        """Soft-delete a form."""
        await self._delete(f"/api/forms/{form_id}")

    # -- Publishing ---------------------------------------------------------

    async def publish(self, form_id: str) -> dict[str, Any]:
        """Publish form and generate share token."""
        return await self._post(f"/api/forms/{form_id}/publish")

    async def close(self, form_id: str) -> None:
        """Close form to new responses."""
        await self._post(f"/api/forms/{form_id}/close")

    # -- Responses ----------------------------------------------------------

    async def list_responses(
        self,
        form_id: str,
        *,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[dict[str, Any]]:
        """List form responses."""
        return await self._get(
            f"/api/forms/{form_id}/responses",
            params={"limit": limit, "offset": offset},
        )

    async def get_response(
        self, form_id: str, response_id: str
    ) -> dict[str, Any]:
        """Get a single response."""
        return await self._get(
            f"/api/forms/{form_id}/responses/{response_id}"
        )

    async def analytics(self, form_id: str) -> dict[str, Any]:
        """AI analysis of all responses."""
        return await self._get(f"/api/forms/{form_id}/analytics")

    async def score_response(
        self, form_id: str, response_id: str
    ) -> dict[str, Any]:
        """AI scoring of a specific response."""
        return await self._post(
            f"/api/forms/{form_id}/responses/{response_id}/score"
        )

    # -- AI generation ------------------------------------------------------

    async def generate(
        self,
        prompt: str,
        *,
        field_count: int | None = None,
    ) -> dict[str, Any]:
        """Generate a form from a natural language prompt."""
        body: dict[str, Any] = {"prompt": prompt}
        if field_count:
            body["field_count"] = field_count
        return await self._post("/api/forms/generate", json=body)

    # -- Public endpoints ---------------------------------------------------

    async def get_public(self, token: str) -> dict[str, Any]:
        """Get a published form by its share token."""
        return await self._get(f"/api/forms/public/{token}")

    async def submit_public(
        self, token: str, answers: dict[str, Any]
    ) -> dict[str, Any]:
        """Submit a response to a public form."""
        return await self._post(
            f"/api/forms/public/{token}/submit",
            json={"answers": answers},
        )
