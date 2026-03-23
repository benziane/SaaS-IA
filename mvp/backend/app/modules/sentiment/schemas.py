"""
Sentiment analysis schemas.
"""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SentimentRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=50000)


class SentimentSegment(BaseModel):
    text: str
    sentiment: str  # positive, negative, neutral
    score: float  # -1.0 to 1.0
    emotions: list[str] = []


class SentimentResponse(BaseModel):
    overall_sentiment: str
    overall_score: float
    segments: list[SentimentSegment]
    emotion_summary: dict[str, int]  # emotion -> count
    positive_percent: float
    negative_percent: float
    neutral_percent: float


class TranscriptionSentimentRequest(BaseModel):
    transcription_id: UUID
