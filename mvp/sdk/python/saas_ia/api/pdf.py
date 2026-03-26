"""PDF Processor API — text/table extraction (PyMuPDF + pdfplumber)."""

from __future__ import annotations

from typing import Any, BinaryIO

from saas_ia.api.base import BaseAPI


class PDFAPI(BaseAPI):
    """Wraps ``/api/pdf`` endpoints."""

    async def process(
        self,
        file: BinaryIO,
        filename: str = "document.pdf",
    ) -> dict[str, Any]:
        """Upload and process a PDF file."""
        return await self._post(
            "/api/pdf/process",
            files={"file": (filename, file)},
        )

    async def list(self) -> list[dict[str, Any]]:
        """List processed PDFs."""
        return await self._get("/api/pdf/")

    async def get(self, pdf_id: str) -> dict[str, Any]:
        """Get a processed PDF result."""
        return await self._get(f"/api/pdf/{pdf_id}")

    async def delete(self, pdf_id: str) -> None:
        """Delete a processed PDF."""
        await self._delete(f"/api/pdf/{pdf_id}")
