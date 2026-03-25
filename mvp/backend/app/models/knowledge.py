"""
Knowledge Base models: Documents and chunks for RAG.

Supports both TF-IDF (legacy) and pgvector (v2) search.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column
from sqlmodel import Field, SQLModel


class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"


class Document(SQLModel, table=True):
    """A user-uploaded document in the knowledge base."""
    __tablename__ = "documents"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    filename: str = Field(max_length=500)
    content_type: str = Field(max_length=100)
    total_chunks: int = Field(default=0)
    status: DocumentStatus = Field(default=DocumentStatus.PENDING)
    error: Optional[str] = Field(default=None, max_length=1000)
    embedding_model: Optional[str] = Field(default=None, max_length=100)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class DocumentChunk(SQLModel, table=True):
    """A chunk of a document for retrieval."""
    __tablename__ = "document_chunks"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    document_id: UUID = Field(foreign_key="documents.id", index=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    content: str
    chunk_index: int = Field(default=0)
    metadata_json: str = Field(default="{}")
    # pgvector embedding - nullable for backward compat with existing chunks
    # Stored as a pgvector vector(384) column via migration
    # Not declared here as SQLModel type - managed via raw SQL in migration
    created_at: datetime = Field(default_factory=datetime.utcnow)
