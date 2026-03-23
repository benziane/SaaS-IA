"""
Transcription model
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class TranscriptionStatus(str, Enum):
    """Transcription job status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Transcription(SQLModel, table=True):
    """Transcription job model"""
    __tablename__ = "transcriptions"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    
    # Input
    video_url: str = Field(max_length=500)
    language: Optional[str] = Field(default="auto", max_length=10)
    source_type: Optional[str] = Field(default="youtube", max_length=20)
    original_filename: Optional[str] = Field(default=None, max_length=500)
    
    # Status
    status: TranscriptionStatus = Field(default=TranscriptionStatus.PENDING)
    
    # Output
    text: Optional[str] = Field(default=None)
    confidence: Optional[float] = Field(default=None)
    duration_seconds: Optional[int] = Field(default=None)
    
    # Speaker diarization
    speakers_json: Optional[str] = Field(default=None)
    speaker_count: Optional[int] = Field(default=None)

    # Error handling
    error: Optional[str] = Field(default=None, max_length=1000)
    retry_count: int = Field(default=0)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)
    
    class Config:
        json_schema_extra = {
            "example": {
                "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "language": "auto",
                "status": "pending"
            }
        }

