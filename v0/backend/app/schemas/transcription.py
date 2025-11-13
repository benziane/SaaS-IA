"""
Pydantic schemas for transcription API
"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, HttpUrl, Field, validator

from app.models.transcription import TranscriptionStatus, LanguageCode


class TranscriptionCreate(BaseModel):
    """Schema for creating a new transcription"""
    youtube_url: str = Field(..., description="YouTube video URL")
    language: LanguageCode = Field(
        default=LanguageCode.AUTO,
        description="Target language for transcription (auto-detect if not specified)"
    )

    @validator("youtube_url")
    def validate_youtube_url(cls, v):
        """Validate that the URL is a valid YouTube URL"""
        if not v:
            raise ValueError("YouTube URL is required")

        # Accept various YouTube URL formats
        valid_patterns = [
            "youtube.com/watch?v=",
            "youtu.be/",
            "youtube.com/embed/",
            "youtube.com/v/",
        ]

        if not any(pattern in v for pattern in valid_patterns):
            raise ValueError("Invalid YouTube URL format")

        return v


class TranscriptionUpdate(BaseModel):
    """Schema for updating transcription status"""
    status: Optional[TranscriptionStatus] = None
    progress: Optional[int] = Field(None, ge=0, le=100)
    error_message: Optional[str] = None
    raw_transcript: Optional[str] = None
    corrected_transcript: Optional[str] = None
    detected_language: Optional[str] = None
    confidence_score: Optional[float] = Field(None, ge=0, le=1)
    processing_time: Optional[float] = None
    word_count: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class TranscriptionResponse(BaseModel):
    """Schema for transcription response"""
    id: int
    youtube_url: str
    video_id: str
    video_title: Optional[str] = None
    video_duration: Optional[float] = None
    channel_name: Optional[str] = None
    language: LanguageCode
    detected_language: Optional[str] = None
    status: TranscriptionStatus
    progress: int
    error_message: Optional[str] = None
    raw_transcript: Optional[str] = None
    corrected_transcript: Optional[str] = None
    transcription_service: Optional[str] = None
    model_used: Optional[str] = None
    processing_time: Optional[float] = None
    confidence_score: Optional[float] = None
    word_count: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    is_public: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TranscriptionList(BaseModel):
    """Schema for listing transcriptions"""
    transcriptions: list[TranscriptionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class TranscriptionStats(BaseModel):
    """Schema for transcription statistics"""
    total_transcriptions: int
    completed: int
    in_progress: int
    failed: int
    total_duration: float  # Total video duration in seconds
    total_processing_time: float  # Total processing time in seconds
    average_confidence: float
    languages: Dict[str, int]  # Language distribution
