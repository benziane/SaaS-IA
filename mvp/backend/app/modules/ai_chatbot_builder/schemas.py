"""
AI Chatbot Builder schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ChatbotCreate(BaseModel):
    """Create a new chatbot."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)
    system_prompt: str = Field(..., min_length=1, max_length=10000)
    model: str = Field(default="gemini", max_length=50)
    knowledge_base_ids: Optional[list[UUID]] = None
    personality: str = Field(default="professional", max_length=50)
    welcome_message: Optional[str] = Field(default=None, max_length=1000)
    theme: Optional[dict] = None


class ChatbotRead(BaseModel):
    """Chatbot response schema."""
    id: UUID
    user_id: UUID
    name: str
    description: Optional[str]
    system_prompt: str
    model: str
    knowledge_base_ids: Optional[list[UUID]]
    personality: str
    welcome_message: Optional[str]
    theme: Optional[dict]
    is_published: bool
    embed_token: Optional[str]
    channels: list
    conversations_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChatbotUpdate(BaseModel):
    """Update chatbot settings."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)
    system_prompt: Optional[str] = Field(default=None, min_length=1, max_length=10000)
    model: Optional[str] = Field(default=None, max_length=50)
    personality: Optional[str] = Field(default=None, max_length=50)
    welcome_message: Optional[str] = Field(default=None, max_length=1000)
    theme: Optional[dict] = None


class ChatMessageCreate(BaseModel):
    """Send a message to a chatbot."""
    message: str = Field(..., min_length=1, max_length=5000)
    session_id: Optional[str] = Field(default=None, max_length=100)


class ChatMessageRead(BaseModel):
    """A single chat message."""
    id: str
    role: str  # user | assistant
    content: str
    sources: Optional[list] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ChannelConfig(BaseModel):
    """Channel deployment configuration."""
    type: str = Field(..., pattern="^(web_widget|whatsapp|telegram|slack|api)$")
    config: dict = Field(default_factory=dict)
    is_active: bool = Field(default=True)


class ChatbotAnalytics(BaseModel):
    """Chatbot usage analytics."""
    chatbot_id: UUID
    total_conversations: int
    total_messages: int
    avg_messages_per_conversation: float
    satisfaction_score: Optional[float]
    top_questions: list


class EmbedCodeResponse(BaseModel):
    """Embed code snippet for website integration."""
    embed_token: str
    html_snippet: str
    script_url: str
