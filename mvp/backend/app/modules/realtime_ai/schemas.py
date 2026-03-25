"""
Realtime AI schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    """Create a realtime AI session."""
    title: Optional[str] = Field(None, max_length=300)
    mode: str = Field(default="voice", description="voice, vision, voice_vision, meeting")
    provider: str = Field(default="gemini", description="gemini, openai, groq")
    system_prompt: Optional[str] = Field(None, max_length=5000)
    knowledge_base_id: Optional[str] = Field(None, description="Link a knowledge base for RAG")
    config: dict = Field(default_factory=dict, description="voice, language, model settings")


class SessionRead(BaseModel):
    """Session response schema."""
    id: UUID
    user_id: UUID
    title: Optional[str]
    mode: str
    status: str
    provider: str
    model: Optional[str]
    system_prompt: Optional[str]
    knowledge_base_id: Optional[str]
    config_json: str
    total_turns: int
    audio_duration_s: float
    tokens_used: int
    started_at: datetime
    ended_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class SessionMessage(BaseModel):
    """A single message in a realtime session."""
    role: str = Field(..., description="user, assistant, system")
    content: str
    content_type: str = Field(default="text", description="text, audio, image")
    timestamp: str
    metadata: dict = Field(default_factory=dict)


class SessionTranscript(BaseModel):
    """Full session transcript."""
    session_id: UUID
    title: Optional[str]
    mode: str
    messages: list[SessionMessage]
    summary: Optional[str]
    total_turns: int
    duration_s: float


class SendMessageRequest(BaseModel):
    """Send a message in a realtime session."""
    content: str = Field(..., min_length=1, max_length=10000)
    content_type: str = Field(default="text", description="text, audio_base64, image_base64")


class SessionSummaryRequest(BaseModel):
    """Request to generate session summary."""
    max_length: int = Field(default=500, ge=100, le=2000)


class RealtimeConfig(BaseModel):
    """Available realtime configuration options."""
    providers: list[dict]
    modes: list[dict]
    languages: list[dict]
