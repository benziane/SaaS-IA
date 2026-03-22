"""
Conversation API schemas for request/response validation.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.conversation import MessageRole


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class ConversationCreate(BaseModel):
    """Body for creating a new conversation."""
    transcription_id: Optional[UUID] = Field(
        default=None,
        description="Optional transcription to attach as context."
    )


class MessageCreate(BaseModel):
    """Body for sending a new user message."""
    content: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="User message text."
    )


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class MessageRead(BaseModel):
    """Single message in a conversation."""
    id: UUID
    conversation_id: UUID
    role: MessageRole
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationRead(BaseModel):
    """Conversation summary (list view)."""
    id: UUID
    user_id: UUID
    title: Optional[str]
    transcription_id: Optional[UUID]
    message_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversationWithMessages(BaseModel):
    """Conversation detail with full message history."""
    id: UUID
    user_id: UUID
    title: Optional[str]
    transcription_id: Optional[UUID]
    messages: List[MessageRead] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaginatedConversations(BaseModel):
    """Paginated list of conversations."""
    items: List[ConversationRead]
    total: int = Field(..., description="Total number of conversations")
    skip: int = Field(..., description="Number of items skipped")
    limit: int = Field(..., description="Maximum items per page")
    has_more: bool = Field(..., description="More items available")
