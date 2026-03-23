"""
Workspace schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

ALLOWED_ITEM_TYPES = {"transcription", "pipeline", "document", "conversation", "comparison"}


class WorkspaceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)


class WorkspaceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None


class WorkspaceRead(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    owner_id: UUID
    is_active: bool
    member_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MemberRead(BaseModel):
    id: UUID
    user_id: UUID
    user_email: str
    role: str
    joined_at: datetime

    class Config:
        from_attributes = True


class InviteRequest(BaseModel):
    email: str = Field(..., max_length=255)
    role: str = Field(default="viewer")


class ShareItemRequest(BaseModel):
    item_type: str = Field(..., max_length=50)
    item_id: UUID

    @field_validator("item_type")
    @classmethod
    def validate_item_type(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in ALLOWED_ITEM_TYPES:
            raise ValueError(
                f"item_type must be one of: {', '.join(sorted(ALLOWED_ITEM_TYPES))}"
            )
        return v


class SharedItemRead(BaseModel):
    id: UUID
    item_type: str
    item_id: UUID
    shared_by: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)


class CommentRead(BaseModel):
    id: UUID
    user_id: UUID
    content: str
    created_at: datetime

    class Config:
        from_attributes = True
