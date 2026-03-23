"""
Transcription schemas for request/response validation
"""

import re
from typing import Generic, List, Optional, TypeVar
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl, field_validator

from app.models.transcription import TranscriptionStatus

# Accepted YouTube URL patterns (must match at least one)
_YOUTUBE_URL_PATTERNS = [
    re.compile(r'^https?://(?:www\.)?youtube\.com/watch\?.*v=[a-zA-Z0-9_-]{11}'),
    re.compile(r'^https?://(?:www\.)?youtu\.be/[a-zA-Z0-9_-]{11}'),
    re.compile(r'^https?://(?:www\.)?youtube\.com/embed/[a-zA-Z0-9_-]{11}'),
]

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper"""
    items: List[T]
    total: int = Field(..., description="Total number of items matching the query")
    skip: int = Field(..., description="Number of items skipped")
    limit: int = Field(..., description="Maximum number of items per page")
    has_more: bool = Field(..., description="Whether more items are available beyond this page")


class TranscriptionCreate(BaseModel):
    """Schema for creating a transcription job"""
    source_type: str = Field("youtube", description="Source type: 'youtube', 'upload', or 'url'")
    video_url: str = Field(..., max_length=2048, description="YouTube or media URL")
    language: Optional[str] = Field("auto", max_length=10, description="Language code (e.g., 'en', 'fr', 'auto')")

    @field_validator("source_type")
    @classmethod
    def validate_source_type(cls, v: str) -> str:
        """Validate that source_type is one of the allowed values."""
        allowed = {"youtube", "upload", "url"}
        v = v.strip().lower()
        if v not in allowed:
            raise ValueError(f"source_type must be one of: {', '.join(sorted(allowed))}")
        return v

    @field_validator("video_url")
    @classmethod
    def validate_video_url(cls, v: str, info) -> str:
        """Validate the URL based on source_type."""
        v = v.strip()
        if not v:
            raise ValueError("video_url must not be empty")
        if len(v) > 2048:
            raise ValueError("video_url must not exceed 2048 characters")

        # For upload source_type, video_url is set internally; skip URL validation
        source_type = info.data.get("source_type", "youtube")
        if source_type == "upload":
            return v

        # For "url" source_type, accept any http/https URL
        if source_type == "url":
            if not v.startswith(("http://", "https://")):
                raise ValueError("video_url must be a valid HTTP or HTTPS URL")
            return v

        # Default: youtube validation
        if not any(pattern.match(v) for pattern in _YOUTUBE_URL_PATTERNS):
            raise ValueError(
                "video_url must be a valid YouTube URL "
                "(youtube.com/watch?v=, youtu.be/, or youtube.com/embed/)"
            )
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "language": "auto",
                "source_type": "youtube"
            }
        }


class TranscriptionUpdate(BaseModel):
    """Schema for updating a transcription job"""
    status: Optional[TranscriptionStatus] = None
    text: Optional[str] = None
    confidence: Optional[float] = None
    duration_seconds: Optional[int] = None
    error: Optional[str] = None


class TranscriptionRead(BaseModel):
    """Schema for transcription response"""
    id: UUID
    user_id: UUID
    video_url: str
    language: Optional[str]
    source_type: Optional[str] = "youtube"
    original_filename: Optional[str] = None
    status: TranscriptionStatus
    text: Optional[str]
    confidence: Optional[float]
    duration_seconds: Optional[int]
    error: Optional[str]
    retry_count: int
    speaker_count: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "987e6543-e21b-12d3-a456-426614174000",
                "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "language": "en",
                "status": "completed",
                "text": "This is a sample transcription...",
                "confidence": 0.95,
                "duration_seconds": 180,
                "error": None,
                "retry_count": 0,
                "created_at": "2025-11-13T21:00:00Z",
                "updated_at": "2025-11-13T21:03:00Z",
                "completed_at": "2025-11-13T21:03:00Z"
            }
        }


class SpeakerUtterance(BaseModel):
    """A single speaker utterance."""
    speaker: str
    text: str
    start: int  # milliseconds
    end: int  # milliseconds
    confidence: Optional[float] = None


class TranscriptionWithSpeakers(TranscriptionRead):
    """Transcription response with speaker diarization data."""
    speakers: list[SpeakerUtterance] = []
    speaker_count: Optional[int] = None


# ========================================================================
# YouTube Enhanced Transcription Schemas
# ========================================================================


class YouTubeMetadata(BaseModel):
    """YouTube video metadata."""
    video_id: str = ""
    title: str = ""
    description: str = ""
    uploader: str = ""
    channel_url: str = ""
    duration_seconds: int = 0
    view_count: int = 0
    like_count: int = 0
    upload_date: str = ""
    thumbnail: str = ""
    tags: list[str] = []
    categories: list[str] = []
    chapters: list[dict] = []
    language: str = ""
    is_live: bool = False


class TranscriptSegment(BaseModel):
    """A segment of transcription with timestamp."""
    text: str
    start: float
    end: float = 0
    duration: float = 0
    confidence: Optional[float] = None


class SmartTranscribeRequest(BaseModel):
    """Request for smart transcription."""
    video_url: str = Field(..., min_length=1, max_length=2000)
    language: str = Field(default="auto", max_length=10)
    prefer_provider: str = Field(default="auto", max_length=30)


class SmartTranscribeResponse(BaseModel):
    """Response from smart transcription."""
    text: str = ""
    segments: list[TranscriptSegment] = []
    language: str = ""
    duration_seconds: int = 0
    confidence: float = 0
    provider: str = ""
    is_manual: bool = False
    error: Optional[str] = None


class PlaylistTranscribeRequest(BaseModel):
    """Request for playlist bulk transcription."""
    playlist_url: str = Field(..., min_length=1, max_length=2000)
    language: str = Field(default="auto", max_length=10)
    max_videos: int = Field(default=20, ge=1, le=100)


class VideoTranscriptResult(BaseModel):
    """Result for a single video in bulk transcription."""
    video_id: str = ""
    title: str = ""
    url: str = ""
    transcript: str = ""
    provider: str = ""
    duration: int = 0
    language: str = ""
    success: bool = False
    error: Optional[str] = None
    metadata: Optional[YouTubeMetadata] = None


class PlaylistTranscribeResponse(BaseModel):
    """Response from playlist bulk transcription."""
    success: bool = True
    total: int = 0
    transcribed: int = 0
    results: list[VideoTranscriptResult] = []
    error: Optional[str] = None


class MetadataRequest(BaseModel):
    """Request for YouTube metadata extraction."""
    video_url: str = Field(..., min_length=1, max_length=2000)


class VideoDownloadRequest(BaseModel):
    """Request for video download."""
    video_url: str = Field(..., min_length=1, max_length=2000)
    format_type: str = Field(default="best[height<=720]", max_length=100)


class ChapterSummary(BaseModel):
    """A chapter with its summary."""
    title: str = ""
    start_time: float = 0
    end_time: float = 0
    text: str = ""
    summary: str = ""


class AutoChapterResponse(BaseModel):
    """Response from auto-chaptering."""
    video_id: str = ""
    title: str = ""
    chapters: list[ChapterSummary] = []
    full_summary: str = ""
    provider: str = ""

