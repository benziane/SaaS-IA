"""
Pipeline models: User-defined AI processing pipelines.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class PipelineStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Pipeline(SQLModel, table=True):
    """User-defined AI processing pipeline."""
    __tablename__ = "pipelines"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    name: str = Field(max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    steps_json: str = Field(default="[]")
    status: PipelineStatus = Field(default=PipelineStatus.DRAFT)
    is_template: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PipelineExecution(SQLModel, table=True):
    """Record of a pipeline execution."""
    __tablename__ = "pipeline_executions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    pipeline_id: UUID = Field(foreign_key="pipelines.id", index=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    status: ExecutionStatus = Field(default=ExecutionStatus.PENDING)
    current_step: int = Field(default=0)
    total_steps: int = Field(default=0)
    results_json: str = Field(default="[]")
    error: Optional[str] = Field(default=None, max_length=2000)
    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
