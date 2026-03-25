"""
Repo Analyzer schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


VALID_ANALYSIS_TYPES = {"structure", "tech_stack", "quality", "documentation", "dependencies", "security", "all"}
VALID_DEPTHS = {"quick", "standard", "deep"}


class AnalysisCreate(BaseModel):
    """Request to create a repo analysis."""
    repo_url: str = Field(..., min_length=5, description="GitHub repository URL or owner/repo")
    analysis_types: list[str] = Field(default=["all"], description="Types of analysis to run")
    depth: str = Field(default="standard", description="Analysis depth: quick, standard, deep")

    @field_validator("analysis_types")
    @classmethod
    def validate_analysis_types(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("At least one analysis type is required")
        invalid = [t for t in v if t not in VALID_ANALYSIS_TYPES]
        if invalid:
            raise ValueError(
                f"Invalid analysis type(s): {invalid}. "
                f"Valid types: {sorted(VALID_ANALYSIS_TYPES)}"
            )
        return v

    @field_validator("depth")
    @classmethod
    def validate_depth(cls, v: str) -> str:
        if v not in VALID_DEPTHS:
            raise ValueError(f"Invalid depth: {v}. Valid: {sorted(VALID_DEPTHS)}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "repo_url": "https://github.com/fastapi/fastapi",
                "analysis_types": ["all"],
                "depth": "standard",
            }
        }


class CompareRequest(BaseModel):
    """Request to compare multiple repositories."""
    repo_urls: list[str] = Field(..., min_length=2, max_length=5, description="2-5 repo URLs to compare")
    analysis_types: list[str] = Field(default=["tech_stack", "quality", "structure"], description="Types to compare")

    @field_validator("analysis_types")
    @classmethod
    def validate_analysis_types(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("At least one analysis type is required")
        invalid = [t for t in v if t not in VALID_ANALYSIS_TYPES]
        if invalid:
            raise ValueError(f"Invalid analysis type(s): {invalid}")
        return v


class TechStackResult(BaseModel):
    """Tech stack detection result."""
    languages: dict[str, float] = Field(default_factory=dict, description="Language -> percentage")
    frameworks: list[str] = Field(default_factory=list)
    build_tools: list[str] = Field(default_factory=list)
    package_manager: str = Field(default="unknown")
    runtime: str = Field(default="unknown")


class QualityResult(BaseModel):
    """Code quality scoring result."""
    score: float = Field(default=0.0, ge=0, le=100, description="Quality score 0-100")
    grade: str = Field(default="F", description="Letter grade A-F")
    issues: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class StructureResult(BaseModel):
    """Repository structure analysis result."""
    total_files: int = Field(default=0)
    total_lines: int = Field(default=0)
    tree: dict = Field(default_factory=dict)
    key_files: list[str] = Field(default_factory=list)


class DependencyResult(BaseModel):
    """Dependency analysis result."""
    total: int = Field(default=0)
    direct: int = Field(default=0)
    dev: int = Field(default=0)
    outdated: list[str] = Field(default_factory=list)
    vulnerabilities: list[str] = Field(default_factory=list)


class SecurityResult(BaseModel):
    """Security scan result."""
    issues: list[dict] = Field(default_factory=list)
    risk_level: str = Field(default="low", description="low, medium, high, critical")
    secrets_found: int = Field(default=0)
    env_files_committed: int = Field(default=0)


class AnalysisRead(BaseModel):
    """Analysis response schema."""
    id: UUID
    user_id: UUID
    repo_url: str
    repo_name: str
    status: str
    analysis_types: list[str]
    depth: str
    results: Optional[dict] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaginatedAnalyses(BaseModel):
    """Paginated analyses response."""
    items: list[AnalysisRead]
    total: int
    skip: int
    limit: int
    has_more: bool


class CompareResult(BaseModel):
    """Comparison result for multiple repos."""
    repos: list[dict]
    summary: dict
