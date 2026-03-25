"""
Image Generation schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class GenerateImageRequest(BaseModel):
    """Generate an image from a text prompt."""
    prompt: str = Field(..., min_length=1, max_length=5000)
    negative_prompt: Optional[str] = Field(None, max_length=2000)
    style: str = Field(default="realistic", description="realistic, artistic, cartoon, sketch, digital_art, photography, watercolor, 3d_render, flat_design, minimalist")
    provider: str = Field(default="gemini", description="gemini, dall-e, stable_diffusion")
    width: int = Field(default=1024, ge=256, le=2048)
    height: int = Field(default=1024, ge=256, le=2048)
    project_id: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "A futuristic city skyline at sunset with flying cars",
                "style": "digital_art",
                "width": 1024,
                "height": 1024,
            }
        }


class ThumbnailRequest(BaseModel):
    """Generate a YouTube thumbnail from transcription content."""
    source_type: str = Field(..., description="transcription, text")
    source_id: Optional[str] = None
    text: Optional[str] = Field(None, max_length=5000)
    style: str = Field(default="photography")
    provider: str = Field(default="gemini")


class EditImageRequest(BaseModel):
    """Edit or create a variation of an existing image."""
    image_id: str = Field(...)
    edit_prompt: str = Field(..., min_length=1, max_length=2000)
    provider: str = Field(default="gemini")


class ImageRead(BaseModel):
    """Generated image response."""
    id: UUID
    user_id: UUID
    prompt: str
    negative_prompt: Optional[str]
    style: str
    provider: str
    model: Optional[str]
    width: int
    height: int
    image_url: Optional[str]
    thumbnail_url: Optional[str]
    source_type: str
    source_id: Optional[str]
    status: str
    error: Optional[str]
    metadata_json: str
    created_at: datetime

    class Config:
        from_attributes = True


class ImageProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)


class ImageProjectRead(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    description: Optional[str]
    image_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BulkGenerateRequest(BaseModel):
    """Generate multiple images for social media pack."""
    prompts: list[str] = Field(..., min_length=1, max_length=10)
    style: str = Field(default="realistic")
    provider: str = Field(default="gemini")
    width: int = Field(default=1024)
    height: int = Field(default=1024)
    project_id: Optional[str] = None
