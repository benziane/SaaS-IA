"""
Multi-Agent Crew schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AgentDefinition(BaseModel):
    """Definition of a single agent in a crew."""
    id: str
    role: str = Field(..., description="Agent role: researcher, writer, reviewer, analyst, coder, translator, summarizer, creative, custom")
    name: str = Field(..., max_length=100)
    goal: str = Field(..., max_length=500)
    backstory: Optional[str] = Field(None, max_length=1000)
    tools: list[str] = Field(default_factory=list, description="Available tools: search_knowledge, crawl_web, summarize, translate, sentiment, generate, compare, content_studio")
    provider: Optional[str] = Field(None, max_length=50)
    max_iterations: int = Field(default=3, ge=1, le=10)


class CrewCreate(BaseModel):
    """Request to create a crew."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    goal: Optional[str] = Field(None, max_length=2000)
    agents: list[AgentDefinition] = Field(default_factory=list)
    process_type: str = Field(default="sequential", description="sequential, parallel, hierarchical")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Content Research Team",
                "goal": "Research a topic and write a comprehensive article",
                "agents": [
                    {"id": "a1", "role": "researcher", "name": "Research Agent", "goal": "Find relevant information", "tools": ["crawl_web", "search_knowledge"]},
                    {"id": "a2", "role": "writer", "name": "Writer Agent", "goal": "Write engaging content", "tools": ["generate", "content_studio"]},
                    {"id": "a3", "role": "reviewer", "name": "Reviewer Agent", "goal": "Review and improve quality", "tools": ["generate"]},
                ],
                "process_type": "sequential",
            }
        }


class CrewUpdate(BaseModel):
    """Update a crew."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    goal: Optional[str] = Field(None, max_length=2000)
    agents: Optional[list[AgentDefinition]] = None
    process_type: Optional[str] = None
    status: Optional[str] = None


class CrewRead(BaseModel):
    """Crew response schema."""
    id: UUID
    user_id: UUID
    name: str
    description: Optional[str]
    goal: Optional[str]
    agents: list[AgentDefinition]
    process_type: str
    status: str
    is_template: bool
    template_category: Optional[str]
    run_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CrewRunRequest(BaseModel):
    """Request to run a crew."""
    instruction: str = Field(..., min_length=1, max_length=5000)
    input_data: dict = Field(default_factory=dict)


class AgentMessage(BaseModel):
    """A message between agents."""
    agent_id: str
    agent_name: str
    role: str
    content: str
    tool_used: Optional[str] = None
    iteration: int = 0
    timestamp: str


class CrewRunRead(BaseModel):
    """Crew run response schema."""
    id: UUID
    crew_id: UUID
    user_id: UUID
    status: str
    instruction: str
    current_agent: int
    total_agents: int
    messages: list[AgentMessage]
    final_output: Optional[str]
    error: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_ms: Optional[int]
    tokens_used: int
    created_at: datetime

    class Config:
        from_attributes = True


class CrewTemplate(BaseModel):
    """A pre-built crew template."""
    id: str
    name: str
    description: str
    category: str
    goal: str
    agents: list[AgentDefinition]
    process_type: str
    icon: str = "Groups"
