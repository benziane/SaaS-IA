"""
Transcription schemas for request/response validation
"""

from typing import Optional
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl

from app.models.transcription import TranscriptionStatus


class TranscriptionCreate(BaseModel):
    """Schema for creating a transcription job"""
    video_url: str = Field(..., max_length=500, description="YouTube video URL")
    language: Optional[str] = Field("auto", max_length=10, description="Language code (e.g., 'en', 'fr', 'auto')")
    
    class Config:
        json_schema_extra = {
            "example": {
                "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "language": "auto"
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
    status: TranscriptionStatus
    text: Optional[str]
    confidence: Optional[float]
    duration_seconds: Optional[int]
    error: Optional[str]
    retry_count: int
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

