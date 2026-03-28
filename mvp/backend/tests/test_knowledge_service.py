"""
Tests for the knowledge module: service logic, chunking, search, and API routes.

All tests run without external services (no database, no Redis, no AI providers).
"""

import json
import os
import pytest
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


# ---------------------------------------------------------------------------
# Service-level tests (KnowledgeService)
# ---------------------------------------------------------------------------


class TestChunkText:
    """Test the _chunk_text static method."""

    def test_chunk_short_text(self):
        from app.modules.knowledge.service import KnowledgeService

        text = "Short text that fits in a single chunk."
        chunks = KnowledgeService._chunk_text(text)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_chunk_empty_text(self):
        from app.modules.knowledge.service import KnowledgeService

        chunks = KnowledgeService._chunk_text("")
        assert chunks == []

    def test_chunk_whitespace_only(self):
        from app.modules.knowledge.service import KnowledgeService

        chunks = KnowledgeService._chunk_text("   \n\n   ")
        assert chunks == []

    def test_chunk_long_text_splits(self):
        from app.modules.knowledge.service import KnowledgeService

        # Create text with multiple paragraphs exceeding chunk size
        paragraphs = [f"Paragraph {i}. " + "word " * 80 for i in range(10)]
        text = "\n\n".join(paragraphs)
        chunks = KnowledgeService._chunk_text(text, chunk_size=500, overlap=50)
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk) > 0

    def test_chunk_preserves_content(self):
        from app.modules.knowledge.service import KnowledgeService

        text = "First paragraph here.\n\nSecond paragraph here."
        chunks = KnowledgeService._chunk_text(text, chunk_size=5000)
        # With a large chunk_size the whole text fits in one chunk
        assert len(chunks) == 1
        assert "First paragraph" in chunks[0]
        assert "Second paragraph" in chunks[0]


class TestTokenizeAndTfIdf:
    """Test tokenization and TF-IDF helpers."""

    def test_tokenize_basic(self):
        from app.modules.knowledge.service import KnowledgeService

        tokens = KnowledgeService._tokenize("Hello World 123")
        assert tokens == ["hello", "world", "123"]

    def test_tokenize_special_chars(self):
        from app.modules.knowledge.service import KnowledgeService

        tokens = KnowledgeService._tokenize("l'intelligence artificielle!")
        assert "intelligence" in tokens
        assert "artificielle" in tokens

    def test_compute_tf(self):
        from app.modules.knowledge.service import KnowledgeService

        tokens = ["hello", "world", "hello"]
        tf = KnowledgeService._compute_tf(tokens)
        assert abs(tf["hello"] - 2 / 3) < 0.001
        assert abs(tf["world"] - 1 / 3) < 0.001

    def test_compute_tf_empty(self):
        from app.modules.knowledge.service import KnowledgeService

        tf = KnowledgeService._compute_tf([])
        assert tf == {}

    def test_cosine_similarity_identical(self):
        from app.modules.knowledge.service import KnowledgeService

        vec = {"a": 1.0, "b": 2.0}
        similarity = KnowledgeService._cosine_similarity(vec, vec)
        assert abs(similarity - 1.0) < 0.001

    def test_cosine_similarity_no_overlap(self):
        from app.modules.knowledge.service import KnowledgeService

        vec_a = {"a": 1.0, "b": 2.0}
        vec_b = {"c": 1.0, "d": 2.0}
        similarity = KnowledgeService._cosine_similarity(vec_a, vec_b)
        assert similarity == 0.0

    def test_cosine_similarity_partial_overlap(self):
        from app.modules.knowledge.service import KnowledgeService

        vec_a = {"a": 1.0, "b": 2.0, "c": 1.0}
        vec_b = {"b": 1.0, "c": 3.0, "d": 1.0}
        similarity = KnowledgeService._cosine_similarity(vec_a, vec_b)
        assert 0.0 < similarity < 1.0


class TestUploadDocument:
    """Test KnowledgeService.upload_document."""

    @pytest.mark.asyncio
    async def test_upload_document_creates_record(self):
        from app.modules.knowledge.service import KnowledgeService
        from app.models.knowledge import DocumentStatus

        user_id = uuid4()
        session = AsyncMock()
        session.flush = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        mock_emb = MagicMock()
        mock_emb.is_available.return_value = False
        with patch.dict("sys.modules", {"app.modules.knowledge.embedding_service": mock_emb}):
            doc = await KnowledgeService.upload_document(
                user_id=user_id,
                filename="test.txt",
                content_type="text/plain",
                text_content="This is a test document with some content.",
                session=session,
            )

        assert doc is not None
        assert doc.filename == "test.txt"
        assert doc.content_type == "text/plain"
        assert doc.user_id == user_id
        # session.add should have been called (document + chunks)
        assert session.add.called

    @pytest.mark.asyncio
    async def test_upload_document_empty_text_still_creates(self):
        """Even an empty-ish text produces at least 1 chunk."""
        from app.modules.knowledge.service import KnowledgeService

        user_id = uuid4()
        session = AsyncMock()
        session.flush = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        mock_emb = MagicMock()
        mock_emb.is_available.return_value = False
        with patch.dict("sys.modules", {"app.modules.knowledge.embedding_service": mock_emb}):
            doc = await KnowledgeService.upload_document(
                user_id=user_id,
                filename="empty.txt",
                content_type="text/plain",
                text_content="x",
                session=session,
            )

        assert doc is not None


class TestListDocuments:
    """Test KnowledgeService.list_documents."""

    @pytest.mark.asyncio
    async def test_list_documents_returns_list(self):
        from app.modules.knowledge.service import KnowledgeService

        user_id = uuid4()
        mock_doc = MagicMock()
        mock_doc.user_id = user_id
        mock_doc.filename = "doc1.txt"

        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_doc]
        session.execute = AsyncMock(return_value=mock_result)

        docs = await KnowledgeService.list_documents(user_id, session)
        assert len(docs) == 1
        assert docs[0].filename == "doc1.txt"

    @pytest.mark.asyncio
    async def test_list_documents_empty(self):
        from app.modules.knowledge.service import KnowledgeService

        user_id = uuid4()
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=mock_result)

        docs = await KnowledgeService.list_documents(user_id, session)
        assert docs == []


class TestDeleteDocument:
    """Test KnowledgeService.delete_document."""

    @pytest.mark.asyncio
    async def test_delete_document_success(self):
        from app.modules.knowledge.service import KnowledgeService

        user_id = uuid4()
        doc_id = uuid4()
        mock_doc = MagicMock()
        mock_doc.user_id = user_id

        session = AsyncMock()
        session.get = AsyncMock(return_value=mock_doc)
        mock_chunks_result = MagicMock()
        mock_chunks_result.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=mock_chunks_result)
        session.delete = AsyncMock()
        session.commit = AsyncMock()

        result = await KnowledgeService.delete_document(doc_id, user_id, session)
        assert result is True
        session.delete.assert_called_with(mock_doc)

    @pytest.mark.asyncio
    async def test_delete_document_not_found(self):
        from app.modules.knowledge.service import KnowledgeService

        user_id = uuid4()
        doc_id = uuid4()

        session = AsyncMock()
        session.get = AsyncMock(return_value=None)

        result = await KnowledgeService.delete_document(doc_id, user_id, session)
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_document_wrong_user(self):
        from app.modules.knowledge.service import KnowledgeService

        user_id = uuid4()
        other_user_id = uuid4()
        doc_id = uuid4()
        mock_doc = MagicMock()
        mock_doc.user_id = other_user_id

        session = AsyncMock()
        session.get = AsyncMock(return_value=mock_doc)

        result = await KnowledgeService.delete_document(doc_id, user_id, session)
        assert result is False


class TestSearchTfidf:
    """Test KnowledgeService.search_tfidf."""

    @pytest.mark.asyncio
    async def test_search_tfidf_returns_results(self):
        from app.modules.knowledge.service import KnowledgeService

        user_id = uuid4()
        chunk = MagicMock()
        chunk.id = uuid4()
        chunk.document_id = uuid4()
        chunk.content = "machine learning artificial intelligence neural networks"
        chunk.chunk_index = 0

        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = [(chunk, "ml_paper.txt")]
        session.execute = AsyncMock(return_value=mock_result)

        results = await KnowledgeService.search_tfidf(
            user_id, "machine learning", session
        )
        assert len(results) >= 1
        assert results[0]["filename"] == "ml_paper.txt"
        assert results[0]["score"] > 0

    @pytest.mark.asyncio
    async def test_search_tfidf_no_chunks(self):
        from app.modules.knowledge.service import KnowledgeService

        user_id = uuid4()
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = []
        session.execute = AsyncMock(return_value=mock_result)

        results = await KnowledgeService.search_tfidf(user_id, "test", session)
        assert results == []

    @pytest.mark.asyncio
    async def test_search_tfidf_no_matching_terms(self):
        from app.modules.knowledge.service import KnowledgeService

        user_id = uuid4()
        chunk = MagicMock()
        chunk.id = uuid4()
        chunk.document_id = uuid4()
        chunk.content = "apples oranges bananas fruits"
        chunk.chunk_index = 0

        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = [(chunk, "fruits.txt")]
        session.execute = AsyncMock(return_value=mock_result)

        results = await KnowledgeService.search_tfidf(
            user_id, "quantum physics entanglement", session
        )
        # No common tokens, so no results with score > 0
        assert results == []

    @pytest.mark.asyncio
    async def test_search_respects_limit(self):
        from app.modules.knowledge.service import KnowledgeService

        user_id = uuid4()
        # Create many chunks with matching terms
        chunks_and_filenames = []
        for i in range(10):
            chunk = MagicMock()
            chunk.id = uuid4()
            chunk.document_id = uuid4()
            chunk.content = f"python programming code development iteration {i}"
            chunk.chunk_index = 0
            chunks_and_filenames.append((chunk, f"doc_{i}.txt"))

        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = chunks_and_filenames
        session.execute = AsyncMock(return_value=mock_result)

        results = await KnowledgeService.search_tfidf(
            user_id, "python programming", session, limit=3
        )
        assert len(results) <= 3


class TestSearchSmartDispatch:
    """Test KnowledgeService.search (smart dispatch)."""

    @pytest.mark.asyncio
    async def test_search_falls_back_to_tfidf(self):
        from app.modules.knowledge.service import KnowledgeService

        user_id = uuid4()
        chunk = MagicMock()
        chunk.id = uuid4()
        chunk.document_id = uuid4()
        chunk.content = "test content for search"
        chunk.chunk_index = 0

        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = [(chunk, "test.txt")]
        session.execute = AsyncMock(return_value=mock_result)

        mock_emb = MagicMock()
        mock_emb.is_available.return_value = False
        with patch.dict("sys.modules", {"app.modules.knowledge.embedding_service": mock_emb}):
            results = await KnowledgeService.search(
                user_id, "test content", session
            )

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_empty_query_returns_empty(self):
        """Search with a query having no alphanumeric tokens returns empty."""
        from app.modules.knowledge.service import KnowledgeService

        user_id = uuid4()
        chunk = MagicMock()
        chunk.id = uuid4()
        chunk.document_id = uuid4()
        chunk.content = "some document text"
        chunk.chunk_index = 0

        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = [(chunk, "doc.txt")]
        session.execute = AsyncMock(return_value=mock_result)

        mock_emb = MagicMock()
        mock_emb.is_available.return_value = False
        with patch.dict("sys.modules", {"app.modules.knowledge.embedding_service": mock_emb}):
            # Special chars only - no real tokens
            results = await KnowledgeService.search(
                user_id, "!@#$%", session
            )

        # No matching tokens -> empty results
        assert results == []


# ---------------------------------------------------------------------------
# Route-level tests (API endpoints via httpx)
# ---------------------------------------------------------------------------


class TestKnowledgeEndpointAuth:
    """Test that knowledge endpoints require authentication."""

    @pytest.mark.asyncio
    async def test_upload_requires_auth(self, client):
        resp = await client.post(
            "/api/knowledge/upload",
            files={"file": ("test.txt", b"hello", "text/plain")},
        )
        assert resp.status_code == 401 or resp.status_code == 403

    @pytest.mark.asyncio
    async def test_list_documents_requires_auth(self, client):
        resp = await client.get("/api/knowledge/documents")
        assert resp.status_code == 401 or resp.status_code == 403

    @pytest.mark.asyncio
    async def test_search_requires_auth(self, client):
        resp = await client.post(
            "/api/knowledge/search",
            json={"query": "test"},
        )
        assert resp.status_code == 401 or resp.status_code == 403

    @pytest.mark.asyncio
    async def test_delete_requires_auth(self, client):
        fake_id = str(uuid4())
        resp = await client.delete(f"/api/knowledge/documents/{fake_id}")
        assert resp.status_code == 401 or resp.status_code == 403


class TestKnowledgeSearchEndpoint:
    """Test the search endpoint with authentication."""

    @pytest.mark.asyncio
    async def test_search_endpoint_returns_results(self, app, auth_headers, test_user):
        from app.auth import get_current_user
        from app.modules.auth_guards.middleware import require_verified_email
        from app.database import get_session

        mock_session = AsyncMock()
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[require_verified_email] = lambda: test_user
        app.dependency_overrides[get_session] = lambda: mock_session

        try:
            import httpx

            with (
                patch(
                    "app.modules.knowledge.service.KnowledgeService.search",
                    new_callable=AsyncMock,
                    return_value=[
                        {
                            "chunk_id": str(uuid4()),
                            "document_id": str(uuid4()),
                            "filename": "test.txt",
                            "content": "search result content",
                            "score": 0.85,
                            "chunk_index": 0,
                        }
                    ],
                ),
                patch("app.cache.cache_get", new_callable=AsyncMock, return_value=None),
                patch("app.cache.cache_set", new_callable=AsyncMock),
                patch("app.database.init_db", new_callable=AsyncMock),
                patch("app.database.engine") as mock_engine,
                patch("app.cache._get_redis", new_callable=AsyncMock, return_value=None),
            ):
                mock_engine.dispose = AsyncMock()
                transport = httpx.ASGITransport(app=app)
                async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as ac:
                    resp = await ac.post(
                        "/api/knowledge/search",
                        json={"query": "test"},
                        headers=auth_headers,
                    )
                assert resp.status_code == 200
                data = resp.json()
                assert data["query"] == "test"
                assert len(data["results"]) == 1
        finally:
            app.dependency_overrides.clear()


class TestKnowledgeDocumentNotFound:
    """Test 404 responses for missing documents."""

    @pytest.mark.asyncio
    async def test_chunks_not_found(self, app, auth_headers, test_user):
        from app.auth import get_current_user
        from app.modules.auth_guards.middleware import require_verified_email
        from app.database import get_session

        mock_session = AsyncMock()
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[require_verified_email] = lambda: test_user
        app.dependency_overrides[get_session] = lambda: mock_session

        try:
            import httpx

            fake_id = str(uuid4())
            with (
                patch(
                    "app.modules.knowledge.service.KnowledgeService.list_document_chunks",
                    new_callable=AsyncMock,
                    return_value=None,
                ),
                patch("app.database.init_db", new_callable=AsyncMock),
                patch("app.database.engine") as mock_engine,
                patch("app.cache._get_redis", new_callable=AsyncMock, return_value=None),
            ):
                mock_engine.dispose = AsyncMock()
                transport = httpx.ASGITransport(app=app)
                async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as ac:
                    resp = await ac.get(
                        f"/api/knowledge/documents/{fake_id}/chunks",
                        headers=auth_headers,
                    )
                assert resp.status_code == 404
        finally:
            app.dependency_overrides.clear()


class TestKnowledgeSchemas:
    """Test knowledge Pydantic schemas."""

    def test_document_read_schema(self):
        from app.modules.knowledge.schemas import DocumentRead

        doc = DocumentRead(
            id=uuid4(),
            filename="test.txt",
            content_type="text/plain",
            total_chunks=5,
            status="indexed",
            error=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        assert doc.filename == "test.txt"
        assert doc.total_chunks == 5
        assert doc.status == "indexed"

    def test_search_request_validation(self):
        from app.modules.knowledge.schemas import SearchRequest

        req = SearchRequest(query="test query", limit=10)
        assert req.query == "test query"
        assert req.limit == 10

    def test_search_request_min_length(self):
        from pydantic import ValidationError
        from app.modules.knowledge.schemas import SearchRequest

        with pytest.raises(ValidationError):
            SearchRequest(query="", limit=5)

    def test_search_response_schema(self):
        from app.modules.knowledge.schemas import SearchResponse, SearchResult

        resp = SearchResponse(
            query="test",
            results=[
                SearchResult(
                    chunk_id=uuid4(),
                    document_id=uuid4(),
                    filename="doc.txt",
                    content="content",
                    score=0.9,
                    chunk_index=0,
                )
            ],
            total=1,
        )
        assert resp.total == 1
        assert resp.results[0].score == 0.9

    def test_ask_request_schema(self):
        from app.modules.knowledge.schemas import AskRequest

        req = AskRequest(question="What is AI?", limit=3)
        assert req.question == "What is AI?"
        assert req.limit == 3
