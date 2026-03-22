"""
Tests for Sprint 5: Knowledge Base RAG and API Keys.

All tests run without external services.
"""

import json
import os
import pytest
from datetime import datetime
from uuid import uuid4


class TestKnowledgeModels:
    """Test Knowledge Base models."""

    def test_document_creation(self):
        from app.models.knowledge import Document, DocumentStatus
        doc = Document(
            user_id=uuid4(),
            filename="test.txt",
            content_type="text/plain",
        )
        assert doc.filename == "test.txt"
        assert doc.status == DocumentStatus.PENDING
        assert doc.total_chunks == 0

    def test_document_status_enum(self):
        from app.models.knowledge import DocumentStatus
        assert DocumentStatus.PENDING == "pending"
        assert DocumentStatus.PROCESSING == "processing"
        assert DocumentStatus.INDEXED == "indexed"
        assert DocumentStatus.FAILED == "failed"

    def test_document_chunk_creation(self):
        from app.models.knowledge import DocumentChunk
        chunk = DocumentChunk(
            document_id=uuid4(),
            user_id=uuid4(),
            content="Test content",
            chunk_index=0,
        )
        assert chunk.content == "Test content"
        assert chunk.chunk_index == 0


class TestKnowledgeService:
    """Test KnowledgeService text processing methods."""

    def test_chunk_text_basic(self):
        from app.modules.knowledge.service import KnowledgeService
        text = "This is paragraph one.\n\nThis is paragraph two.\n\nThis is paragraph three."
        chunks = KnowledgeService._chunk_text(text, chunk_size=100, overlap=10)
        assert len(chunks) >= 1
        assert all(len(c) <= 200 for c in chunks)

    def test_chunk_text_empty(self):
        from app.modules.knowledge.service import KnowledgeService
        chunks = KnowledgeService._chunk_text("")
        assert chunks == []

    def test_chunk_text_single_paragraph(self):
        from app.modules.knowledge.service import KnowledgeService
        text = "Short paragraph."
        chunks = KnowledgeService._chunk_text(text)
        assert len(chunks) == 1
        assert chunks[0] == "Short paragraph."

    def test_tokenize(self):
        from app.modules.knowledge.service import KnowledgeService
        tokens = KnowledgeService._tokenize("Hello World! Test 123")
        assert "hello" in tokens
        assert "world" in tokens
        assert "123" in tokens

    def test_compute_tf(self):
        from app.modules.knowledge.service import KnowledgeService
        tokens = ["hello", "world", "hello"]
        tf = KnowledgeService._compute_tf(tokens)
        assert abs(tf["hello"] - 2/3) < 0.001
        assert abs(tf["world"] - 1/3) < 0.001

    def test_cosine_similarity_identical(self):
        from app.modules.knowledge.service import KnowledgeService
        vec = {"a": 1.0, "b": 0.5}
        score = KnowledgeService._cosine_similarity(vec, vec)
        assert abs(score - 1.0) < 0.001

    def test_cosine_similarity_orthogonal(self):
        from app.modules.knowledge.service import KnowledgeService
        vec_a = {"a": 1.0}
        vec_b = {"b": 1.0}
        score = KnowledgeService._cosine_similarity(vec_a, vec_b)
        assert score == 0.0

    def test_cosine_similarity_empty(self):
        from app.modules.knowledge.service import KnowledgeService
        score = KnowledgeService._cosine_similarity({}, {"a": 1.0})
        assert score == 0.0


class TestKnowledgeSchemas:
    """Test Knowledge Base schemas."""

    def test_document_read_schema(self):
        from app.modules.knowledge.schemas import DocumentRead
        doc = DocumentRead(
            id=uuid4(),
            filename="test.txt",
            content_type="text/plain",
            total_chunks=5,
            status="indexed",
            error=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        assert doc.total_chunks == 5

    def test_search_request_schema(self):
        from app.modules.knowledge.schemas import SearchRequest
        req = SearchRequest(query="test query")
        assert req.limit == 5

    def test_search_request_empty_rejected(self):
        from app.modules.knowledge.schemas import SearchRequest
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            SearchRequest(query="")

    def test_ask_request_schema(self):
        from app.modules.knowledge.schemas import AskRequest
        req = AskRequest(question="What is this about?")
        assert req.limit == 5


class TestAPIKeyModel:
    """Test API Key model."""

    def test_api_key_creation(self):
        from app.models.api_key import APIKey
        key = APIKey(
            user_id=uuid4(),
            name="Test Key",
            key_hash="abc123",
            key_prefix="sk-abcde",
        )
        assert key.name == "Test Key"
        assert key.is_active is True
        assert key.rate_limit_per_day == 1000

    def test_api_key_default_permissions(self):
        from app.models.api_key import APIKey
        key = APIKey(
            user_id=uuid4(),
            name="Test",
            key_hash="hash",
            key_prefix="sk-abc",
        )
        permissions = json.loads(key.permissions_json)
        assert "read" in permissions
        assert "write" in permissions


class TestAPIKeyService:
    """Test APIKeyService methods."""

    def test_generate_key_format(self):
        from app.modules.api_keys.service import APIKeyService
        key = APIKeyService.generate_key()
        assert key.startswith("sk-")
        assert len(key) > 20

    def test_generate_key_unique(self):
        from app.modules.api_keys.service import APIKeyService
        keys = {APIKeyService.generate_key() for _ in range(10)}
        assert len(keys) == 10

    def test_hash_key_deterministic(self):
        from app.modules.api_keys.service import APIKeyService
        key = "sk-test-key"
        h1 = APIKeyService.hash_key(key)
        h2 = APIKeyService.hash_key(key)
        assert h1 == h2

    def test_hash_key_different_keys(self):
        from app.modules.api_keys.service import APIKeyService
        h1 = APIKeyService.hash_key("key1")
        h2 = APIKeyService.hash_key("key2")
        assert h1 != h2


class TestAPIKeySchemas:
    """Test API Key schemas."""

    def test_api_key_create_schema(self):
        from app.modules.api_keys.schemas import APIKeyCreate
        create = APIKeyCreate(name="My Key")
        assert create.name == "My Key"
        assert create.rate_limit_per_day == 1000

    def test_api_key_create_empty_name_rejected(self):
        from app.modules.api_keys.schemas import APIKeyCreate
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            APIKeyCreate(name="")

    def test_api_key_read_schema(self):
        from app.modules.api_keys.schemas import APIKeyRead
        read = APIKeyRead(
            id=uuid4(),
            name="Test",
            key_prefix="sk-abc",
            permissions=["read", "write"],
            rate_limit_per_day=1000,
            is_active=True,
            last_used_at=None,
            created_at=datetime.utcnow(),
        )
        assert read.is_active is True

    def test_api_key_created_schema(self):
        from app.modules.api_keys.schemas import APIKeyCreated
        created = APIKeyCreated(
            id=uuid4(),
            name="Test",
            key="sk-full-key-here",
            key_prefix="sk-full-",
            permissions=["read"],
            rate_limit_per_day=500,
        )
        assert "shown again" in created.message


class TestModuleManifests:
    """Test Sprint 5 module manifests."""

    def test_knowledge_manifest(self):
        with open("app/modules/knowledge/manifest.json") as f:
            manifest = json.load(f)
        assert manifest["name"] == "knowledge"
        assert manifest["prefix"] == "/api/knowledge"

    def test_api_keys_manifest(self):
        with open("app/modules/api_keys/manifest.json") as f:
            manifest = json.load(f)
        assert manifest["name"] == "api_keys"
        assert manifest["prefix"] == "/api/keys"
