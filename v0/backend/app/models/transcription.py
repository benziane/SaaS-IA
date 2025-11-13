"""
Database models for transcription management
"""
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, Float, JSON, Boolean
from sqlalchemy.sql import func

from app.core.database import Base


class TranscriptionStatus(str, PyEnum):
    """Status of transcription process"""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    EXTRACTING = "extracting"
    TRANSCRIBING = "transcribing"
    POST_PROCESSING = "post_processing"
    COMPLETED = "completed"
    FAILED = "failed"


class LanguageCode(str, PyEnum):
    """Supported languages"""
    FRENCH = "fr"
    ENGLISH = "en"
    ARABIC = "ar"
    AUTO = "auto"


class Transcription(Base):
    """Model for storing transcription information"""

    __tablename__ = "transcriptions"

    id = Column(Integer, primary_key=True, index=True)

    # YouTube video information
    youtube_url = Column(String(500), nullable=False)
    video_id = Column(String(100), nullable=False, index=True)
    video_title = Column(String(500))
    video_duration = Column(Float)  # Duration in seconds
    channel_name = Column(String(200))

    # Transcription details
    language = Column(Enum(LanguageCode), default=LanguageCode.AUTO)
    detected_language = Column(String(10))

    # Status and progress
    status = Column(Enum(TranscriptionStatus), default=TranscriptionStatus.PENDING, index=True)
    progress = Column(Integer, default=0)  # 0-100
    error_message = Column(Text)

    # Transcription results
    raw_transcript = Column(Text)  # Raw transcription before post-processing
    corrected_transcript = Column(Text)  # Final corrected and formatted transcript

    # Processing metadata
    transcription_service = Column(String(50))  # whisper, assemblyai, etc.
    model_used = Column(String(100))
    processing_time = Column(Float)  # Time in seconds
    confidence_score = Column(Float)  # Average confidence score

    # Additional metadata
    word_count = Column(Integer)
    metadata = Column(JSON)  # Store additional metadata as JSON

    # File paths
    audio_file_path = Column(String(500))

    # Flags
    is_public = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True))

    def __repr__(self):
        return f"<Transcription(id={self.id}, video_id={self.video_id}, status={self.status})>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "youtube_url": self.youtube_url,
            "video_id": self.video_id,
            "video_title": self.video_title,
            "video_duration": self.video_duration,
            "channel_name": self.channel_name,
            "language": self.language,
            "detected_language": self.detected_language,
            "status": self.status,
            "progress": self.progress,
            "error_message": self.error_message,
            "raw_transcript": self.raw_transcript,
            "corrected_transcript": self.corrected_transcript,
            "transcription_service": self.transcription_service,
            "model_used": self.model_used,
            "processing_time": self.processing_time,
            "confidence_score": self.confidence_score,
            "word_count": self.word_count,
            "metadata": self.metadata,
            "audio_file_path": self.audio_file_path,
            "is_public": self.is_public,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
