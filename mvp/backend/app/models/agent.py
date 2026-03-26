"""
AI Agent models: Autonomous task execution.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class AgentStatus(str, Enum):
    PLANNING = "planning"
    EXECUTING = "executing"
    COMPLETED = "completed"
    PARTIAL_FAILURE = "partial_failure"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentRun(SQLModel, table=True):
    """A single agent execution run."""
    __tablename__ = "agent_runs"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    instruction: str = Field(max_length=5000)
    status: AgentStatus = Field(default=AgentStatus.PLANNING)
    plan_json: str = Field(default="[]")
    results_json: str = Field(default="[]")
    current_step: int = Field(default=0)
    total_steps: int = Field(default=0)
    error: Optional[str] = Field(default=None, max_length=2000)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)


class AgentStep(SQLModel, table=True):
    """Individual step within an agent run."""
    __tablename__ = "agent_steps"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    run_id: UUID = Field(foreign_key="agent_runs.id", index=True)
    step_index: int = Field(default=0)
    action: str = Field(max_length=50)
    description: str = Field(max_length=500)
    input_json: str = Field(default="{}")
    output_json: str = Field(default="{}")
    status: AgentStatus = Field(default=AgentStatus.PLANNING)
    error: Optional[str] = Field(default=None, max_length=1000)
    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)
