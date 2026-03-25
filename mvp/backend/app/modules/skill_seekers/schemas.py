"""
Skill Seekers schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ScrapeJobCreate(BaseModel):
    """Request to create a scrape job."""
    repos: list[str] = Field(..., min_length=1, max_length=10, description="GitHub repos (owner/repo format)")
    targets: list[str] = Field(default=["claude"], max_length=5, description="Package targets")
    enhance: bool = Field(default=False, description="Run AI enhancement pass")

    class Config:
        json_schema_extra = {
            "example": {
                "repos": ["anthropics/claude-code", "langchain-ai/langchain"],
                "targets": ["claude"],
                "enhance": False,
            }
        }


class ScrapeJobRead(BaseModel):
    """Scrape job response schema."""
    id: UUID
    user_id: UUID
    repos: list[str]
    targets: list[str]
    enhance: bool
    status: str
    progress: int
    current_step: str
    output_files: list[str]
    error: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaginatedJobs(BaseModel):
    """Paginated scrape jobs response."""
    items: list[ScrapeJobRead]
    total: int
    skip: int
    limit: int
    has_more: bool
