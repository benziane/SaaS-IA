"""
PDF Processor schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PDFUploadResponse(BaseModel):
    """Response after uploading a PDF."""
    id: UUID
    user_id: UUID
    filename: str
    num_pages: int
    file_size_kb: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class PDFRead(BaseModel):
    """Full PDF document response."""
    id: UUID
    user_id: UUID
    filename: str
    num_pages: int
    file_size_kb: int
    text_content: Optional[str] = None
    pages: list[dict] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    summary: Optional[str] = None
    keywords: list[str] = Field(default_factory=list)
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PDFQueryRequest(BaseModel):
    """RAG query against a PDF."""
    question: str = Field(..., min_length=1, max_length=5000)
    pdf_id: UUID


class PDFQueryResponse(BaseModel):
    """RAG query response."""
    answer: str
    sources: list[dict] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class PDFExportRequest(BaseModel):
    """Export PDF content."""
    format: str = Field(default="markdown", description="markdown, txt, or json")
    include_images: bool = False


class PDFBatchUpload(BaseModel):
    """Batch upload response."""
    files_count: int
    uploaded: list[PDFUploadResponse] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class PDFCompareRequest(BaseModel):
    """Compare multiple PDFs."""
    pdf_ids: list[UUID] = Field(..., min_length=2, max_length=5)
    comparison_type: str = Field(default="content", description="content, structure, or summary")


class PDFSummarizeRequest(BaseModel):
    """Summarize a PDF."""
    style: str = Field(default="executive", description="executive, detailed, or bullet_points")
