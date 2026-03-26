"""Knowledge Base API — document upload, chunking, hybrid search, RAG."""

from __future__ import annotations

from typing import Any, BinaryIO

from saas_ia.api.base import BaseAPI


class KnowledgeAPI(BaseAPI):
    """Wraps ``/api/knowledge`` endpoints."""

    # -- Documents ----------------------------------------------------------

    async def upload(
        self,
        file: BinaryIO,
        filename: str = "upload.txt",
    ) -> dict[str, Any]:
        """Upload a document (TXT, MD, CSV; max 10 MB)."""
        return await self._post(
            "/api/knowledge/upload",
            files={"file": (filename, file)},
        )

    async def list_documents(self) -> list[dict[str, Any]]:
        """List user documents."""
        return await self._get("/api/knowledge/documents")

    async def list_chunks(self, document_id: str) -> list[dict[str, Any]]:
        """List chunks for a document."""
        return await self._get(f"/api/knowledge/documents/{document_id}/chunks")

    async def delete_document(self, document_id: str) -> None:
        """Delete a document and all its chunks."""
        await self._delete(f"/api/knowledge/documents/{document_id}")

    # -- Search -------------------------------------------------------------

    async def search(
        self,
        query: str,
        *,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """Hybrid search (auto-detects best mode)."""
        body: dict[str, Any] = {"query": query}
        if limit is not None:
            body["limit"] = limit
        return await self._post("/api/knowledge/search", json=body)

    async def vector_search(
        self,
        query: str,
        *,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """Vector-only search using pgvector."""
        body: dict[str, Any] = {"query": query}
        if limit is not None:
            body["limit"] = limit
        return await self._post("/api/knowledge/search/vector", json=body)

    async def search_status(self) -> dict[str, Any]:
        """Get available search modes and their status."""
        return await self._get("/api/knowledge/search/status")

    # -- RAG ----------------------------------------------------------------

    async def ask(
        self,
        question: str,
        *,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """Ask a question -- searches knowledge base and generates an AI answer."""
        body: dict[str, Any] = {"question": question}
        if limit is not None:
            body["limit"] = limit
        return await self._post("/api/knowledge/ask", json=body)

    # -- Maintenance --------------------------------------------------------

    async def reindex_embeddings(self) -> dict[str, Any]:
        """Reindex all chunks with fresh embeddings."""
        return await self._post("/api/knowledge/reindex-embeddings")
