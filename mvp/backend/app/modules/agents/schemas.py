"""
Agent schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AgentRunRequest(BaseModel):
    instruction: str = Field(..., min_length=1, max_length=5000)


class AgentStepRead(BaseModel):
    id: UUID
    step_index: int
    action: str
    description: str
    status: str
    error: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class AgentRunRead(BaseModel):
    id: UUID
    instruction: str
    status: str
    current_step: int
    total_steps: int
    steps: list[AgentStepRead] = []
    error: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True
