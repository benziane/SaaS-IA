"""
Sentiment analysis API routes.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth import get_current_user
from app.database import get_session
from app.models.user import User
from app.models.transcription import Transcription, TranscriptionStatus
from app.modules.sentiment.schemas import (
    SentimentRequest,
    SentimentResponse,
    SentimentSegment,
    TranscriptionSentimentRequest,
)
from app.modules.sentiment.service import SentimentService
from app.modules.billing.middleware import require_ai_call_quota
from app.modules.billing.service import BillingService
from app.rate_limit import limiter

router = APIRouter()


@router.post("/analyze", response_model=SentimentResponse)
@limiter.limit("10/minute")
async def analyze_sentiment(
    request: Request,
    body: SentimentRequest,
    current_user: User = Depends(require_ai_call_quota),
    session: AsyncSession = Depends(get_session),
):
    """
    Analyze sentiment and emotions in text.

    Returns overall sentiment, per-segment analysis, and emotion summary.

    Rate limit: 10 requests/minute
    """
    result = await SentimentService.analyze_text(body.text)

    await BillingService.consume_quota(current_user.id, "ai_call", 1, session)

    return SentimentResponse(
        overall_sentiment=result["overall_sentiment"],
        overall_score=result["overall_score"],
        segments=[SentimentSegment(**s) for s in result["segments"]],
        emotion_summary=result["emotion_summary"],
        positive_percent=result["positive_percent"],
        negative_percent=result["negative_percent"],
        neutral_percent=result["neutral_percent"],
    )


@router.post("/transcription", response_model=SentimentResponse)
@limiter.limit("5/minute")
async def analyze_transcription_sentiment(
    request: Request,
    body: TranscriptionSentimentRequest,
    current_user: User = Depends(require_ai_call_quota),
    session: AsyncSession = Depends(get_session),
):
    """
    Analyze sentiment of a completed transcription.

    Rate limit: 5 requests/minute
    """
    transcription = await session.get(Transcription, body.transcription_id)
    if not transcription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transcription not found")
    if transcription.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    if transcription.status != TranscriptionStatus.COMPLETED or not transcription.text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Transcription not completed")

    result = await SentimentService.analyze_text(transcription.text)

    await BillingService.consume_quota(current_user.id, "ai_call", 1, session)

    return SentimentResponse(
        overall_sentiment=result["overall_sentiment"],
        overall_score=result["overall_score"],
        segments=[SentimentSegment(**s) for s in result["segments"]],
        emotion_summary=result["emotion_summary"],
        positive_percent=result["positive_percent"],
        negative_percent=result["negative_percent"],
        neutral_percent=result["neutral_percent"],
    )
