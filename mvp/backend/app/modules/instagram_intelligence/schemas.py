"""Instagram intelligence schemas."""

from typing import Optional
from pydantic import BaseModel


class ProfileAnalyzeRequest(BaseModel):
    username: str
    max_reels: int = 10
    transcribe: bool = True
    language: str = "auto"


class ReelDownloadRequest(BaseModel):
    reel_url: str
    transcribe: bool = True
    language: str = "auto"


class ReelResult(BaseModel):
    reel_id: str
    username: str
    caption: str
    likes: int
    comments: int
    views: int
    duration_seconds: float
    thumbnail_url: Optional[str]
    reel_url: str
    transcript: Optional[str]
    transcript_language: Optional[str]
    sentiment_label: Optional[str]
    sentiment_score: Optional[float]
    provider: str


class ProfileReport(BaseModel):
    username: str
    full_name: str
    bio: str
    followers: int
    following: int
    post_count: int
    reels_analyzed: int
    reels: list[ReelResult]
    avg_sentiment_score: Optional[float]
    top_topics: list[str]


class ValidateProfileResult(BaseModel):
    valid: bool
    username: str
    exists: bool
    is_private: bool
    error: Optional[str]
