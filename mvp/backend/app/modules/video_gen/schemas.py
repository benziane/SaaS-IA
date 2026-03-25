"""
Video Generation schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class GenerateVideoRequest(BaseModel):
    """Generate a video from text or image."""
    title: str = Field(..., min_length=1, max_length=300)
    prompt: str = Field(..., min_length=1, max_length=5000)
    video_type: str = Field(default="text_to_video", description="text_to_video, image_to_video, clip_highlights, avatar_talking, explainer, short_form")
    provider: str = Field(default="gemini", description="gemini, runway, kling, heygen")
    duration_s: float = Field(default=10.0, ge=1.0, le=120.0)
    width: int = Field(default=1920)
    height: int = Field(default=1080)
    style: Optional[str] = Field(None, max_length=100)
    project_id: Optional[str] = None
    settings: dict = Field(default_factory=dict, description="motion, aspect_ratio, fps, etc.")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "AI Platform Demo",
                "prompt": "A sleek, modern SaaS dashboard with data visualizations animating on screen",
                "video_type": "text_to_video",
                "duration_s": 10,
            }
        }


class ClipHighlightsRequest(BaseModel):
    """Generate highlight clips from a transcription."""
    transcription_id: str = Field(...)
    max_clips: int = Field(default=5, ge=1, le=20)
    clip_duration_s: float = Field(default=30.0, ge=5.0, le=120.0)
    format: str = Field(default="short_form", description="short_form, highlight, summary")
    provider: str = Field(default="gemini")


class AvatarVideoRequest(BaseModel):
    """Generate a talking avatar video."""
    text: str = Field(..., min_length=1, max_length=5000)
    avatar_style: str = Field(default="professional", description="professional, casual, animated")
    voice_id: Optional[str] = None
    background: str = Field(default="office", description="office, studio, custom, transparent")
    provider: str = Field(default="heygen")


class VideoFromSourceRequest(BaseModel):
    """Generate video from transcription, document, or content studio output."""
    source_type: str = Field(..., description="transcription, document, content")
    source_id: str = Field(...)
    video_type: str = Field(default="explainer")
    title: Optional[str] = None
    provider: str = Field(default="gemini")
    duration_s: float = Field(default=30.0)


class VideoRead(BaseModel):
    """Generated video response."""
    id: UUID
    user_id: UUID
    title: str
    description: Optional[str]
    video_type: str
    prompt: str
    provider: str
    source_type: Optional[str]
    source_id: Optional[str]
    video_url: Optional[str]
    thumbnail_url: Optional[str]
    duration_s: Optional[float]
    width: int
    height: int
    format: str
    status: str
    error: Optional[str]
    settings_json: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VideoProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)


class VideoProjectRead(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    description: Optional[str]
    video_count: int
    total_duration_s: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
