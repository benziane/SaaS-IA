"""
AI Forms schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class FormField(BaseModel):
    """Definition of a single form field."""
    field_id: str = Field(..., min_length=1, max_length=100)
    type: str = Field(
        ...,
        pattern="^(text|email|number|select|multiselect|rating|textarea|date|file)$",
    )
    label: str = Field(..., min_length=1, max_length=500)
    required: bool = Field(default=False)
    options: Optional[list[str]] = None
    validation: Optional[dict] = None
    condition: Optional[dict] = None


class FormCreate(BaseModel):
    """Create a new form."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)
    fields: list[FormField] = Field(default_factory=list)
    style: str = Field(default="conversational", max_length=50)
    thank_you_message: Optional[str] = Field(default=None, max_length=1000)
    is_public: bool = Field(default=False)


class FormUpdate(BaseModel):
    """Update form settings."""
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)
    fields: Optional[list[FormField]] = None
    style: Optional[str] = Field(default=None, max_length=50)
    thank_you_message: Optional[str] = Field(default=None, max_length=1000)
    is_public: Optional[bool] = None


class FormRead(BaseModel):
    """Form response schema."""
    id: UUID
    user_id: UUID
    title: str
    description: Optional[str]
    fields: list[FormField]
    style: str
    thank_you_message: Optional[str]
    is_public: bool
    share_token: Optional[str]
    responses_count: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FormResponseCreate(BaseModel):
    """Submit a response to a form."""
    answers: dict = Field(..., min_length=1)


class FormResponseRead(BaseModel):
    """Form response read schema."""
    id: UUID
    form_id: UUID
    answers: dict
    score: Optional[float]
    analysis: Optional[str]
    submitted_at: datetime

    class Config:
        from_attributes = True


class FormGenerateRequest(BaseModel):
    """AI form generation from natural language."""
    prompt: str = Field(..., min_length=5, max_length=2000)
    num_fields: int = Field(default=5, ge=1, le=30)


class FormAnalysisRead(BaseModel):
    """Form analytics and AI insights."""
    form_id: UUID
    total_responses: int
    completion_rate: float
    field_stats: dict
    ai_insights: Optional[str]
