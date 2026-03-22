"""
Pipeline schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PipelineStep(BaseModel):
    """A single step in a pipeline."""
    id: str
    type: str = Field(..., description="Step type: transcription, summarize, translate, export")
    config: dict = Field(default_factory=dict)
    position: int


class PipelineCreate(BaseModel):
    """Request to create a pipeline."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    steps: list[PipelineStep] = Field(default_factory=list)
    is_template: bool = False

    class Config:
        json_schema_extra = {
            "example": {
                "name": "YouTube to Summary",
                "description": "Transcribe YouTube video and generate summary",
                "steps": [
                    {"id": "step1", "type": "transcription", "config": {"language": "auto"}, "position": 0},
                    {"id": "step2", "type": "summarize", "config": {"max_length": 500}, "position": 1},
                ],
            }
        }


class PipelineUpdate(BaseModel):
    """Request to update a pipeline."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    steps: Optional[list[PipelineStep]] = None
    status: Optional[str] = None


class PipelineRead(BaseModel):
    """Pipeline response schema."""
    id: UUID
    user_id: UUID
    name: str
    description: Optional[str]
    steps: list[PipelineStep]
    status: str
    is_template: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ExecutionRead(BaseModel):
    """Pipeline execution response schema."""
    id: UUID
    pipeline_id: UUID
    user_id: UUID
    status: str
    current_step: int
    total_steps: int
    results: list[dict]
    error: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True
