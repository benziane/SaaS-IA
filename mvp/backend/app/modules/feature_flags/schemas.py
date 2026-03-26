"""
Feature Flags schemas for request/response validation.
"""

from typing import Any, Optional

from pydantic import BaseModel, Field


class FeatureFlagRead(BaseModel):
    """Single feature flag with current state."""
    name: str
    default: Optional[bool] = None
    override: Optional[str] = None
    effective: Any = None


class FeatureFlagList(BaseModel):
    """List of all feature flags."""
    count: int
    flags: dict[str, FeatureFlagRead]


class FeatureFlagUpdate(BaseModel):
    """Request to set a feature flag value."""
    value: str = Field(
        ...,
        description="Flag value: 'true', 'false', '30%' (percentage rollout), or 'users:uuid1,uuid2' (whitelist)",
        examples=["true", "false", "30%", "users:abc-123,def-456"],
    )


class FeatureFlagUserResolved(BaseModel):
    """All flags resolved for a specific user."""
    user_id: str
    flags: dict[str, bool]


class KillSwitchResponse(BaseModel):
    """Response for kill switch / restore operations."""
    module: str
    flag_name: str
    action: str
    status: str
