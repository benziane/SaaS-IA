"""
Code Sandbox schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SandboxCreate(BaseModel):
    """Create a new code sandbox."""
    name: str = Field(..., min_length=1, max_length=200)
    language: str = Field(default="python", max_length=30)
    description: Optional[str] = Field(default=None, max_length=2000)


class SandboxRead(BaseModel):
    """Sandbox response."""
    id: UUID
    user_id: UUID
    name: str
    language: str
    description: Optional[str]
    cells: list[dict]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CellCreate(BaseModel):
    """Add a cell to a sandbox."""
    cell_type: str = Field(default="code", max_length=20)
    source: str = Field(..., max_length=50000)
    language: str = Field(default="python", max_length=30)


class CellUpdate(BaseModel):
    """Update cell source code."""
    source: str = Field(..., max_length=50000)


class CellResult(BaseModel):
    """Result of cell execution."""
    cell_id: str
    output: Optional[str] = None
    error: Optional[str] = None
    execution_time_ms: Optional[float] = None
    status: str  # success, error, running, timeout


class CodeGenerateRequest(BaseModel):
    """Generate code from natural language."""
    prompt: str = Field(..., min_length=1, max_length=3000)
    language: str = Field(default="python", max_length=30)
    context: Optional[str] = Field(default=None, max_length=5000)


class CodeGenerateResponse(BaseModel):
    """Generated code response."""
    code: str
    explanation: str
    language: str


class CodeExplainRequest(BaseModel):
    """Explain code."""
    code: str = Field(..., min_length=1, max_length=50000)


class CodeExplainResponse(BaseModel):
    """Code explanation response."""
    explanation: str
    complexity: Optional[str] = None


class CodeDebugRequest(BaseModel):
    """Debug code with error context."""
    code: str = Field(..., min_length=1, max_length=50000)
    error: str = Field(..., min_length=1, max_length=5000)


class CodeDebugResponse(BaseModel):
    """Debug response."""
    fixed_code: str
    explanation: str
    root_cause: str
