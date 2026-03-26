"""Pipelines API — sequential AI operation chaining with 23 step types."""

from __future__ import annotations

from typing import Any

from saas_ia.api.base import BaseAPI


class PipelineAPI(BaseAPI):
    """Wraps ``/api/pipelines`` endpoints."""

    # -- CRUD ---------------------------------------------------------------

    async def create(
        self,
        name: str,
        steps: list[dict[str, Any]],
        *,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Create a pipeline."""
        body: dict[str, Any] = {"name": name, "steps": steps}
        if description:
            body["description"] = description
        return await self._post("/api/pipelines/", json=body)

    async def list(
        self,
        *,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[dict[str, Any]]:
        """List pipelines."""
        return await self._get(
            "/api/pipelines/",
            params={"limit": limit, "offset": offset},
        )

    async def get(self, pipeline_id: str) -> dict[str, Any]:
        """Get pipeline by ID."""
        return await self._get(f"/api/pipelines/{pipeline_id}")

    async def update(
        self,
        pipeline_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        steps: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Update a pipeline."""
        body: dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if description is not None:
            body["description"] = description
        if steps is not None:
            body["steps"] = steps
        return await self._put(f"/api/pipelines/{pipeline_id}", json=body)

    async def delete(self, pipeline_id: str) -> None:
        """Delete a pipeline."""
        await self._delete(f"/api/pipelines/{pipeline_id}")

    # -- Execution ----------------------------------------------------------

    async def execute(
        self,
        pipeline_id: str,
        input_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute a pipeline with input data."""
        return await self._post(
            f"/api/pipelines/{pipeline_id}/execute",
            json={"input_data": input_data},
        )

    async def list_executions(
        self,
        pipeline_id: str,
        *,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[dict[str, Any]]:
        """List executions for a pipeline."""
        return await self._get(
            f"/api/pipelines/{pipeline_id}/executions",
            params={"limit": limit, "offset": offset},
        )

    async def get_execution(self, execution_id: str) -> dict[str, Any]:
        """Get execution details by ID."""
        return await self._get(f"/api/pipelines/executions/{execution_id}")
