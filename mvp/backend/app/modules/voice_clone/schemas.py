"""
Voice Clone schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class VoiceProfileCreate(BaseModel):
    """Create a voice profile from audio sample."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    provider: str = Field(default="elevenlabs", description="elevenlabs, openai, fish_audio")
    language: str = Field(default="auto", max_length=10)
    settings: dict = Field(default_factory=dict, description="stability, similarity_boost, speed")


class VoiceProfileRead(BaseModel):
    """Voice profile response."""
    id: UUID
    user_id: UUID
    name: str
    description: Optional[str]
    provider: str
    language: str
    sample_duration_s: Optional[float]
    status: str
    settings_json: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SynthesizeRequest(BaseModel):
    """Request TTS synthesis."""
    text: str = Field(..., min_length=1, max_length=10000)
    voice_id: Optional[str] = Field(None, description="Voice profile ID (omit for default voice)")
    provider: str = Field(default="elevenlabs")
    output_format: str = Field(default="mp3", description="mp3, wav, ogg")
    language: str = Field(default="auto")
    speed: float = Field(default=1.0, ge=0.5, le=2.0)


class SynthesizeFromSourceRequest(BaseModel):
    """Synthesize audio from a transcription or document."""
    source_type: str = Field(..., description="transcription, document")
    source_id: str = Field(...)
    voice_id: Optional[str] = None
    provider: str = Field(default="elevenlabs")
    language: str = Field(default="auto")


class DubRequest(BaseModel):
    """Request video/audio dubbing to another language."""
    source_type: str = Field(..., description="transcription, url")
    source_id: Optional[str] = None
    source_url: Optional[str] = None
    target_language: str = Field(..., description="Target language code (en, fr, es, de, etc.)")
    voice_id: Optional[str] = None
    provider: str = Field(default="elevenlabs")


class SynthesisRead(BaseModel):
    """Synthesis job response."""
    id: UUID
    user_id: UUID
    voice_id: Optional[UUID]
    source_type: str
    provider: str
    output_format: str
    audio_url: Optional[str]
    duration_s: Optional[float]
    language: str
    target_language: Optional[str]
    status: str
    error: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BuiltinVoice(BaseModel):
    """A built-in voice option."""
    id: str
    name: str
    language: str
    gender: str
    provider: str
    preview_url: Optional[str] = None
