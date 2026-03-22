"""
Conversation schemas for request/response validation
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ConversationCreate(BaseModel):
    """Schema for creating a new conversation"""
    transcription_id: Optional[UUID] = Field(
        default=None,
        description="Optional transcription ID to provide context for the conversation"
    )


class ConversationRead(BaseModel):
    """Schema for conversation list response"""
    id: UUID
    title: Optional[str]
    transcription_id: Optional[UUID]
    message_count: int = Field(
        default=0, description="Total number of messages in the conversation"
    )
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    """Schema for sending a new message in a conversation"""
    content: str = Field(
        ..., min_length=1, max_length=10000,
        description="Message content to send to the AI assistant"
    )


class MessageRead(BaseModel):
    """Schema for message response"""
    id: UUID
    role: str
    content: str
    provider: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationWithMessages(BaseModel):
    """Schema for a conversation with its full message history"""
    id: UUID
    title: Optional[str]
    transcription_id: Optional[UUID]
    messages: List[MessageRead] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
