"""
Marketplace schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ListingCreate(BaseModel):
    """Request to create a marketplace listing."""
    title: str = Field(..., min_length=1, max_length=300)
    description: str = Field(..., min_length=1, max_length=5000)
    type: str = Field(
        ...,
        description="Listing type: module, template, prompt, workflow, dataset",
    )
    category: str = Field(
        ...,
        description="Category: ai, productivity, content, data, media, security, automation, other",
    )
    price: float = Field(default=0.0, ge=0, description="Price in USD, 0 = free")
    version: str = Field(default="1.0.0", max_length=20)
    content: dict = Field(default_factory=dict, description="The listing payload (template data, prompt text, etc.)")
    tags: Optional[list[str]] = Field(default=None, max_length=20)
    preview_images: Optional[list[str]] = Field(default=None, description="URLs to preview images")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "YouTube SEO Workflow",
                "description": "Automated workflow to generate SEO-optimized descriptions from YouTube videos",
                "type": "workflow",
                "category": "content",
                "price": 0,
                "version": "1.0.0",
                "content": {"nodes": [], "edges": []},
                "tags": ["seo", "youtube", "automation"],
            }
        }


class ListingUpdate(BaseModel):
    """Request to update a marketplace listing."""
    title: Optional[str] = Field(None, min_length=1, max_length=300)
    description: Optional[str] = Field(None, min_length=1, max_length=5000)
    price: Optional[float] = Field(None, ge=0)
    version: Optional[str] = Field(None, max_length=20)
    content: Optional[dict] = None
    tags: Optional[list[str]] = None


class ListingRead(BaseModel):
    """Marketplace listing response schema."""
    id: UUID
    author_id: UUID
    author_name: str
    title: str
    description: str
    type: str
    category: str
    price: float
    version: str
    content: dict
    tags: list[str]
    preview_images: list[str]
    rating: float
    reviews_count: int
    installs_count: int
    is_published: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReviewCreate(BaseModel):
    """Request to add a review to a listing."""
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=2000)


class ReviewRead(BaseModel):
    """Marketplace review response schema."""
    id: UUID
    user_id: UUID
    user_name: str
    listing_id: UUID
    rating: int
    comment: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class InstallRead(BaseModel):
    """Marketplace install response schema."""
    id: UUID
    user_id: UUID
    listing_id: UUID
    installed_at: datetime
    version: str

    class Config:
        from_attributes = True
