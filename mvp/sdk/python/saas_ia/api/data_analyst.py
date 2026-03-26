"""Data Analyst API — CSV/JSON/Excel analysis with DuckDB + NL queries."""

from __future__ import annotations

from typing import Any, BinaryIO

from saas_ia.api.base import BaseAPI


class DataAnalystAPI(BaseAPI):
    """Wraps ``/api/data`` endpoints."""

    # -- Datasets -----------------------------------------------------------

    async def upload_dataset(
        self,
        file: BinaryIO,
        filename: str = "data.csv",
    ) -> dict[str, Any]:
        """Upload a dataset (CSV, JSON, or Excel)."""
        return await self._post(
            "/api/data/datasets",
            files={"file": (filename, file)},
        )

    async def list_datasets(
        self,
        *,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[dict[str, Any]]:
        """List datasets."""
        return await self._get(
            "/api/data/datasets",
            params={"limit": limit, "offset": offset},
        )

    async def get_dataset(self, dataset_id: str) -> dict[str, Any]:
        """Get dataset with preview."""
        return await self._get(f"/api/data/datasets/{dataset_id}")

    async def delete_dataset(self, dataset_id: str) -> None:
        """Delete a dataset and its analyses."""
        await self._delete(f"/api/data/datasets/{dataset_id}")

    # -- Analysis -----------------------------------------------------------

    async def ask(
        self,
        dataset_id: str,
        question: str,
    ) -> dict[str, Any]:
        """Ask a natural language question about a dataset."""
        return await self._post(
            f"/api/data/datasets/{dataset_id}/ask",
            json={"question": question},
        )

    async def auto_analyze(self, dataset_id: str) -> dict[str, Any]:
        """Run automatic analysis on a dataset."""
        return await self._post(f"/api/data/datasets/{dataset_id}/auto-analyze")

    async def report(self, dataset_id: str) -> dict[str, Any]:
        """Generate a comprehensive report for a dataset."""
        return await self._post(f"/api/data/datasets/{dataset_id}/report")

    async def list_analyses(
        self,
        dataset_id: str,
        *,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[dict[str, Any]]:
        """List analyses for a dataset."""
        return await self._get(
            f"/api/data/datasets/{dataset_id}/analyses",
            params={"limit": limit, "offset": offset},
        )
