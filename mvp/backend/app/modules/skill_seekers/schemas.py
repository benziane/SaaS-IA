"""
Skill Seekers schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

# Valid targets supported by skill-seekers CLI
VALID_TARGETS = {"claude", "openai", "gemini", "langchain", "llama-index", "markdown"}


class ScrapeJobCreate(BaseModel):
    """Request to create a scrape job."""
    repos: list[str] = Field(..., min_length=1, max_length=10, description="GitHub repos (owner/repo format)")
    targets: list[str] = Field(default=["claude"], max_length=5, description="Package targets")
    enhance: bool = Field(default=False, description="Run AI enhancement pass")

    @field_validator("targets")
    @classmethod
    def validate_targets(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("At least one target is required")
        invalid = [t for t in v if t not in VALID_TARGETS]
        if invalid:
            raise ValueError(
                f"Invalid target(s): {invalid}. "
                f"Valid targets: {sorted(VALID_TARGETS)}"
            )
        return v

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


class ScrapeJobStats(BaseModel):
    """Scrape job statistics for a user."""
    total_jobs: int
    completed: int
    failed: int
    pending: int
    running: int
    total_repos_scraped: int
    recent_jobs: list[dict]


class CancelJobResponse(BaseModel):
    """Response for cancel job endpoint."""
    status: str
    job_id: str
