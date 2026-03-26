"""Code Sandbox API — secure code execution + AI code gen/debug."""

from __future__ import annotations

from typing import Any

from saas_ia.api.base import BaseAPI


class CodeSandboxAPI(BaseAPI):
    """Wraps ``/api/sandbox`` endpoints."""

    # -- Sandboxes ----------------------------------------------------------

    async def create(
        self,
        name: str,
        *,
        language: str | None = None,
    ) -> dict[str, Any]:
        """Create a sandbox."""
        body: dict[str, Any] = {"name": name}
        if language:
            body["language"] = language
        return await self._post("/api/sandbox/sandboxes", json=body)

    async def list(
        self,
        *,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[dict[str, Any]]:
        """List sandboxes."""
        return await self._get(
            "/api/sandbox/sandboxes",
            params={"limit": limit, "offset": offset},
        )

    async def get(self, sandbox_id: str) -> dict[str, Any]:
        """Get sandbox with cells."""
        return await self._get(f"/api/sandbox/sandboxes/{sandbox_id}")

    async def delete(self, sandbox_id: str) -> None:
        """Delete a sandbox."""
        await self._delete(f"/api/sandbox/sandboxes/{sandbox_id}")

    # -- Cells --------------------------------------------------------------

    async def add_cell(
        self,
        sandbox_id: str,
        source: str,
        *,
        order: int | None = None,
    ) -> dict[str, Any]:
        """Add a cell to a sandbox."""
        body: dict[str, Any] = {"source": source}
        if order is not None:
            body["order"] = order
        return await self._post(
            f"/api/sandbox/sandboxes/{sandbox_id}/cells",
            json=body,
        )

    async def update_cell(
        self,
        sandbox_id: str,
        cell_id: str,
        source: str,
    ) -> dict[str, Any]:
        """Update cell source code."""
        return await self._put(
            f"/api/sandbox/sandboxes/{sandbox_id}/cells/{cell_id}",
            json={"source": source},
        )

    async def remove_cell(self, sandbox_id: str, cell_id: str) -> None:
        """Remove a cell."""
        await self._delete(
            f"/api/sandbox/sandboxes/{sandbox_id}/cells/{cell_id}"
        )

    async def execute_cell(
        self, sandbox_id: str, cell_id: str
    ) -> dict[str, Any]:
        """Execute a cell in the sandbox."""
        return await self._post(
            f"/api/sandbox/sandboxes/{sandbox_id}/cells/{cell_id}/execute"
        )

    # -- AI code tools ------------------------------------------------------

    async def generate(
        self,
        prompt: str,
        *,
        language: str | None = None,
    ) -> dict[str, Any]:
        """Generate code from a natural language prompt."""
        body: dict[str, Any] = {"prompt": prompt}
        if language:
            body["language"] = language
        return await self._post("/api/sandbox/generate", json=body)

    async def explain(
        self,
        code: str,
        *,
        language: str | None = None,
    ) -> dict[str, Any]:
        """Explain code with AI."""
        body: dict[str, Any] = {"code": code}
        if language:
            body["language"] = language
        return await self._post("/api/sandbox/explain", json=body)

    async def debug(
        self,
        code: str,
        error: str,
        *,
        language: str | None = None,
    ) -> dict[str, Any]:
        """Debug code with AI."""
        body: dict[str, Any] = {"code": code, "error": error}
        if language:
            body["language"] = language
        return await self._post("/api/sandbox/debug", json=body)
