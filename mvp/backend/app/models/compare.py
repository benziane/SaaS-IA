"""
Compare models: Multi-model comparison results and votes.
"""

from datetime import UTC, datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class ComparisonResult(SQLModel, table=True):
    """Stores a multi-model comparison run."""
    __tablename__ = "comparison_results"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    prompt: str = Field(max_length=10000)
    providers_used: str = Field(max_length=500)
    results_json: str = Field(default="{}")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ComparisonVote(SQLModel, table=True):
    """User vote for the best response in a comparison."""
    __tablename__ = "comparison_votes"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    comparison_id: UUID = Field(foreign_key="comparison_results.id", index=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    provider_name: str = Field(max_length=50)
    quality_score: int = Field(ge=1, le=5)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
