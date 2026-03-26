"""Compare API — multi-provider comparison with voting."""

from __future__ import annotations

from typing import Any

from saas_ia.api.base import BaseAPI


class CompareAPI(BaseAPI):
    """Wraps ``/api/compare`` endpoints."""

    async def run(
        self,
        prompt: str,
        *,
        providers: list[str] | None = None,
    ) -> dict[str, Any]:
        """Run a prompt across multiple providers."""
        body: dict[str, Any] = {"prompt": prompt}
        if providers:
            body["providers"] = providers
        return await self._post("/api/compare/run", json=body)

    async def vote(
        self,
        comparison_id: str,
        winner_provider: str,
    ) -> dict[str, Any]:
        """Vote for the best provider response."""
        return await self._post(
            f"/api/compare/{comparison_id}/vote",
            json={"winner_provider": winner_provider},
        )

    async def stats(self) -> dict[str, Any]:
        """Get aggregated provider quality stats."""
        return await self._get("/api/compare/stats")
