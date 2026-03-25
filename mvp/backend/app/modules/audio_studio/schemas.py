"""
Audio Studio schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Audio files
# ---------------------------------------------------------------------------

class AudioUploadResponse(BaseModel):
    """Response after uploading an audio file."""
    id: UUID
    user_id: UUID
    filename: str
    duration_seconds: float
    sample_rate: int
    channels: int
    format: str
    file_size_kb: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class AudioRead(BaseModel):
    """Full audio file details."""
    id: UUID
    user_id: UUID
    filename: str
    duration_seconds: float
    sample_rate: int
    channels: int
    format: str
    file_size_kb: int
    transcript: Optional[str] = None
    chapters: list = Field(default_factory=list)
    status: str
    waveform_data: Optional[list[float]] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Editing
# ---------------------------------------------------------------------------

class AudioEditOperation(BaseModel):
    """A single edit operation."""
    type: str = Field(
        ...,
        description="trim, fade_in, fade_out, normalize, noise_reduction, speed_change, merge",
    )
    params: dict = Field(default_factory=dict)


class AudioEditRequest(BaseModel):
    """Request to apply a sequence of edit operations."""
    operations: list[AudioEditOperation] = Field(..., min_length=1)


# ---------------------------------------------------------------------------
# Chapters
# ---------------------------------------------------------------------------

class ChapterCreate(BaseModel):
    """Manually create a chapter marker."""
    title: str = Field(..., min_length=1, max_length=200)
    start_time: float = Field(..., ge=0)
    end_time: float = Field(..., ge=0)
    description: Optional[str] = Field(None, max_length=500)


# ---------------------------------------------------------------------------
# Podcast
# ---------------------------------------------------------------------------

class PodcastEpisodeCreate(BaseModel):
    """Create a podcast episode."""
    title: str = Field(..., min_length=1, max_length=300)
    description: str = Field(default="", max_length=5000)
    audio_id: UUID
    chapters: list[ChapterCreate] = Field(default_factory=list)
    show_notes: Optional[str] = Field(None, max_length=10000)
    publish_date: Optional[datetime] = None


class PodcastEpisodeRead(BaseModel):
    """Podcast episode response."""
    id: UUID
    user_id: UUID
    audio_id: UUID
    title: str
    description: str
    show_notes: Optional[str] = None
    publish_date: Optional[datetime] = None
    is_published: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RSSFeedConfig(BaseModel):
    """Configuration for generating an RSS podcast feed."""
    title: str = Field(..., min_length=1, max_length=300)
    description: str = Field(default="", max_length=5000)
    author: str = Field(default="", max_length=200)
    email: str = Field(default="", max_length=200)
    language: str = Field(default="en", max_length=10)
    category: str = Field(default="Technology", max_length=100)
    image_url: Optional[str] = Field(None, max_length=1000)


# ---------------------------------------------------------------------------
# Split
# ---------------------------------------------------------------------------

class SplitRequest(BaseModel):
    """Request to split audio by silence."""
    min_silence_ms: int = Field(default=1000, ge=200, le=10000)
    silence_thresh_db: int = Field(default=-40, ge=-80, le=-10)
