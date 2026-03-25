"""
Social Publisher schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SocialAccountCreate(BaseModel):
    """Connect a social media account."""
    platform: str = Field(..., description="Platform: twitter, linkedin, instagram, tiktok, facebook")
    access_token: str = Field(..., min_length=1, description="OAuth access token for the platform")
    account_name: str = Field(..., min_length=1, max_length=200, description="Display name or handle")

    class Config:
        json_schema_extra = {
            "example": {
                "platform": "twitter",
                "access_token": "oauth_token_here",
                "account_name": "@myaccount",
            }
        }


class SocialAccountRead(BaseModel):
    """Social account response (token never exposed)."""
    id: UUID
    user_id: UUID
    platform: str
    account_name: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PostCreate(BaseModel):
    """Create a social media post."""
    content: str = Field(..., min_length=1, max_length=10000)
    platforms: list[str] = Field(..., min_length=1, description="Target platforms: twitter, linkedin, instagram, tiktok, facebook")
    schedule_at: Optional[datetime] = Field(None, description="Schedule for later (UTC). Omit for draft.")
    media_urls: Optional[list[str]] = Field(None, max_length=10, description="Media attachment URLs")
    hashtags: Optional[list[str]] = Field(None, max_length=30, description="Hashtags to append")

    class Config:
        json_schema_extra = {
            "example": {
                "content": "Excited to share our latest AI update!",
                "platforms": ["twitter", "linkedin"],
                "hashtags": ["AI", "SaaS", "innovation"],
            }
        }


class PostRead(BaseModel):
    """Social post response."""
    id: UUID
    user_id: UUID
    content: str
    platforms: list[str]
    status: str
    published_at: Optional[datetime]
    schedule_at: Optional[datetime]
    results: dict
    media_urls: list[str]
    hashtags: list[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PostAnalytics(BaseModel):
    """Analytics for a published post on a platform."""
    post_id: UUID
    platform: str
    impressions: int
    engagements: int
    clicks: int
    shares: int


class ScheduleUpdate(BaseModel):
    """Update post schedule."""
    schedule_at: datetime = Field(..., description="New scheduled time (UTC)")


class RecycleRequest(BaseModel):
    """Recycle existing content for social media."""
    content_id: str = Field(..., description="UUID of content to recycle (from content_studio)")
    platforms: list[str] = Field(..., min_length=1)
    custom_instructions: Optional[str] = Field(None, max_length=2000)
