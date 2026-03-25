"""
Data Analyst schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DatasetRead(BaseModel):
    """Dataset response."""
    id: UUID
    user_id: UUID
    name: str
    filename: str
    file_type: str
    file_size: int
    row_count: int
    column_count: int
    columns_json: str
    preview_json: str
    stats_json: str
    status: str
    error: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ColumnInfo(BaseModel):
    """Column metadata."""
    name: str
    dtype: str
    non_null: int
    unique: int
    sample_values: list[str]


class AskDataRequest(BaseModel):
    """Ask a natural language question about a dataset."""
    question: str = Field(..., min_length=1, max_length=2000)
    analysis_type: str = Field(default="general", description="general, trend, correlation, anomaly, forecast")
    provider: str = Field(default="gemini")


class ChartSpec(BaseModel):
    """Chart specification for frontend rendering."""
    type: str  # bar, line, pie, scatter, histogram, heatmap, table, kpi
    title: str
    data: dict
    config: dict = Field(default_factory=dict)


class InsightItem(BaseModel):
    """An insight discovered from analysis."""
    insight: str
    confidence: float = Field(ge=0, le=1)
    category: str  # trend, anomaly, correlation, distribution, summary


class AnalysisRead(BaseModel):
    """Analysis response."""
    id: UUID
    dataset_id: UUID
    user_id: UUID
    question: str
    analysis_type: str
    answer: Optional[str]
    charts: list[ChartSpec]
    insights: list[InsightItem]
    code_executed: Optional[str]
    status: str
    provider: Optional[str]
    error: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class AutoAnalyzeRequest(BaseModel):
    """Request automatic analysis of a dataset."""
    provider: str = Field(default="gemini")
    depth: str = Field(default="standard", description="quick, standard, deep")


class GenerateReportRequest(BaseModel):
    """Generate a comprehensive report from analyses."""
    analysis_ids: list[str] = Field(default_factory=list, description="Specific analyses to include (empty = all)")
    format: str = Field(default="markdown", description="markdown, html")
    title: Optional[str] = None
