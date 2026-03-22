"""
Compare schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CompareRequest(BaseModel):
    """Request to compare multiple AI providers."""
    prompt: str = Field(..., min_length=1, max_length=10000)
    providers: list[str] = Field(
        default=["gemini", "claude", "groq"],
        min_length=1,
        max_length=5,
    )

    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "Explain quantum computing in simple terms",
                "providers": ["gemini", "claude", "groq"],
            }
        }


class ProviderResult(BaseModel):
    """Result from a single AI provider."""
    provider: str
    model: str
    response: str
    response_time_ms: int
    error: Optional[str] = None


class CompareResponse(BaseModel):
    """Response containing results from all providers."""
    id: UUID
    prompt: str
    results: list[ProviderResult]
    created_at: datetime

    class Config:
        from_attributes = True


class VoteRequest(BaseModel):
    """Request to vote for the best provider response."""
    provider_name: str = Field(..., min_length=1, max_length=50)
    quality_score: int = Field(..., ge=1, le=5)


class VoteResponse(BaseModel):
    """Response after recording a vote."""
    id: UUID
    comparison_id: UUID
    provider_name: str
    quality_score: int

    class Config:
        from_attributes = True


class ProviderStats(BaseModel):
    """Aggregated statistics for a provider."""
    provider: str
    total_votes: int
    avg_score: float
    win_count: int
