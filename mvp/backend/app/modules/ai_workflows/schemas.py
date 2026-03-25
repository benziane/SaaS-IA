"""
AI Workflows schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class WorkflowNode(BaseModel):
    """A single node in a workflow graph."""
    id: str
    type: str = Field(..., description="Node type: action, condition, transform, output")
    action: str = Field(..., description="Action: summarize, translate, sentiment, generate, crawl, transcribe, search_knowledge, compare, notify, content_studio, webhook_call")
    label: str = Field(default="")
    config: dict = Field(default_factory=dict)
    position_x: float = Field(default=0)
    position_y: float = Field(default=0)


class WorkflowEdge(BaseModel):
    """Connection between two workflow nodes."""
    id: str
    source: str
    target: str
    condition: Optional[str] = Field(None, description="Optional condition expression")


class WorkflowCreate(BaseModel):
    """Request to create a workflow."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    trigger_type: str = Field(default="manual")
    trigger_config: dict = Field(default_factory=dict)
    nodes: list[WorkflowNode] = Field(default_factory=list)
    edges: list[WorkflowEdge] = Field(default_factory=list)
    schedule_cron: Optional[str] = Field(None, max_length=100)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "YouTube to Blog",
                "description": "Auto-generate blog post from YouTube transcription",
                "trigger_type": "manual",
                "nodes": [
                    {"id": "n1", "type": "action", "action": "transcribe", "label": "Transcribe Video", "config": {"language": "auto"}, "position_x": 100, "position_y": 100},
                    {"id": "n2", "type": "action", "action": "summarize", "label": "Summarize", "config": {"max_length": 500}, "position_x": 300, "position_y": 100},
                    {"id": "n3", "type": "action", "action": "content_studio", "label": "Generate Blog", "config": {"format": "blog_article"}, "position_x": 500, "position_y": 100},
                ],
                "edges": [
                    {"id": "e1", "source": "n1", "target": "n2"},
                    {"id": "e2", "source": "n2", "target": "n3"},
                ],
            }
        }


class WorkflowUpdate(BaseModel):
    """Request to update a workflow."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    trigger_type: Optional[str] = None
    trigger_config: Optional[dict] = None
    nodes: Optional[list[WorkflowNode]] = None
    edges: Optional[list[WorkflowEdge]] = None
    status: Optional[str] = None
    schedule_cron: Optional[str] = None


class WorkflowRead(BaseModel):
    """Workflow response schema."""
    id: UUID
    user_id: UUID
    name: str
    description: Optional[str]
    trigger_type: str
    trigger_config: dict
    nodes: list[WorkflowNode]
    edges: list[WorkflowEdge]
    status: str
    is_template: bool
    template_category: Optional[str]
    run_count: int
    last_run_at: Optional[datetime]
    schedule_cron: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RunRead(BaseModel):
    """Workflow run response schema."""
    id: UUID
    workflow_id: UUID
    user_id: UUID
    status: str
    trigger_type: str
    current_node: int
    total_nodes: int
    results: list[dict]
    error: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_ms: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class TriggerRequest(BaseModel):
    """Trigger a workflow manually with optional input data."""
    input_data: dict = Field(default_factory=dict, description="Input data passed to first node")


class WorkflowTemplate(BaseModel):
    """A workflow template for quick setup."""
    id: str
    name: str
    description: str
    category: str
    trigger_type: str
    nodes: list[WorkflowNode]
    edges: list[WorkflowEdge]
    icon: str = "AutoFixHigh"
