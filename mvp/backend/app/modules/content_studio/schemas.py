"""
Content Studio schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    """Create a content project from a source."""
    title: str = Field(..., min_length=1, max_length=300)
    source_type: str = Field(..., description="Source type: text, transcription, document, url")
    source_text: Optional[str] = Field(None, max_length=50000)
    source_id: Optional[str] = Field(None, description="UUID of transcription or document")
    language: str = Field(default="auto", max_length=10)
    tone: str = Field(default="professional", max_length=50)
    target_audience: Optional[str] = Field(None, max_length=200)
    keywords: Optional[list[str]] = Field(None, max_length=20)

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Mon article sur l'IA",
                "source_type": "text",
                "source_text": "L'intelligence artificielle transforme le monde...",
                "tone": "engaging",
                "target_audience": "tech professionals",
                "keywords": ["IA", "innovation", "2026"],
            }
        }


class ProjectRead(BaseModel):
    """Project response schema."""
    id: UUID
    user_id: UUID
    title: str
    source_type: str
    language: str
    tone: str
    target_audience: Optional[str]
    keywords: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GenerateRequest(BaseModel):
    """Request to generate content in specific formats."""
    formats: list[str] = Field(
        ...,
        description="Formats to generate: blog_article, twitter_thread, linkedin_post, newsletter, instagram_carousel, youtube_description, seo_meta, press_release, email_campaign, podcast_notes",
    )
    provider: Optional[str] = Field(None, description="AI provider to use")
    custom_instructions: Optional[str] = Field(None, max_length=2000)

    class Config:
        json_schema_extra = {
            "example": {
                "formats": ["blog_article", "twitter_thread", "linkedin_post"],
                "custom_instructions": "Use a conversational tone",
            }
        }


class ContentRead(BaseModel):
    """Generated content response."""
    id: UUID
    project_id: UUID
    format: str
    title: Optional[str]
    content: str
    metadata_json: str
    status: str
    provider: Optional[str]
    word_count: int
    version: int
    scheduled_at: Optional[datetime]
    published_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ContentUpdate(BaseModel):
    """Update generated content."""
    title: Optional[str] = Field(None, max_length=500)
    content: Optional[str] = Field(None, max_length=50000)
    status: Optional[str] = None
    scheduled_at: Optional[datetime] = None


class RegenerateRequest(BaseModel):
    """Regenerate a piece of content with optional tweaks."""
    custom_instructions: Optional[str] = Field(None, max_length=2000)
    provider: Optional[str] = None


class GenerateFromURLRequest(BaseModel):
    """Generate content directly from a URL."""
    url: str = Field(..., min_length=5)
    title: Optional[str] = Field(None, max_length=300)
    formats: list[str] = Field(...)
    tone: str = Field(default="professional")
    target_audience: Optional[str] = None
    keywords: Optional[list[str]] = None
    provider: Optional[str] = None
