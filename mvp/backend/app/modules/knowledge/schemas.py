"""
Knowledge Base schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentRead(BaseModel):
    """Document response schema."""
    id: UUID
    filename: str
    content_type: str
    total_chunks: int
    status: str
    error: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SearchRequest(BaseModel):
    """Semantic search request."""
    query: str = Field(..., min_length=1, max_length=5000)
    limit: int = Field(default=5, ge=1, le=20)


class SearchResult(BaseModel):
    """A single search result."""
    chunk_id: UUID
    document_id: UUID
    filename: str
    content: str
    score: float
    chunk_index: int


class SearchResponse(BaseModel):
    """Search response with results."""
    query: str
    results: list[SearchResult]
    total: int


class AskRequest(BaseModel):
    """RAG question request."""
    question: str = Field(..., min_length=1, max_length=5000)
    limit: int = Field(default=5, ge=1, le=10)


class AskResponse(BaseModel):
    """RAG answer response."""
    question: str
    answer: str
    sources: list[SearchResult]
    provider: str
