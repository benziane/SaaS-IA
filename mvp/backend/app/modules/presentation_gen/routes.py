"""
Presentation Gen API routes - AI-powered presentation generation.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth import get_current_user
from app.modules.auth_guards.middleware import require_verified_email
from app.database import get_session
from app.models.user import User
from app.modules.billing.middleware import require_ai_call_quota
from app.modules.billing.service import BillingService
from app.modules.presentation_gen.schemas import (
    VALID_EXPORT_FORMATS,
    VALID_STYLES,
    VALID_TEMPLATES,
    ExportRequest,
    PresentationCreate,
    PresentationFromTranscript,
    PresentationRead,
    SlideInsert,
    SlideUpdate,
)
from app.modules.presentation_gen.service import PresentationGenService
from app.rate_limit import limiter

router = APIRouter()


def _to_read(presentation) -> dict:
    """Convert a Presentation model to PresentationRead-compatible dict."""
    import json

    slides = []
    try:
        slides = json.loads(presentation.slides_json) if presentation.slides_json else []
    except (json.JSONDecodeError, TypeError):
        slides = []

    return {
        "id": presentation.id,
        "user_id": presentation.user_id,
        "title": presentation.title,
        "topic": presentation.topic,
        "num_slides": presentation.num_slides,
        "style": presentation.style,
        "template": presentation.template,
        "slides": slides,
        "status": presentation.status,
        "format": presentation.format,
        "download_url": presentation.download_url,
        "created_at": presentation.created_at,
        "updated_at": presentation.updated_at,
    }


@router.post("", response_model=PresentationRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def create_presentation(
    request: Request,
    body: PresentationCreate,
    current_user: User = Depends(require_ai_call_quota),
    session: AsyncSession = Depends(get_session),
):
    """
    Generate a new AI presentation from a topic and optional source material.

    Rate limit: 5 requests/minute
    """
    if body.style not in VALID_STYLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid style '{body.style}'. Valid: {sorted(VALID_STYLES)}",
        )

    if body.template not in VALID_TEMPLATES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid template '{body.template}'. Valid: {sorted(VALID_TEMPLATES)}",
        )

    service = PresentationGenService(session)
    presentation = await service.generate_presentation(
        user_id=current_user.id,
        title=body.title,
        topic=body.topic,
        num_slides=body.num_slides,
        style=body.style,
        template=body.template,
        language=body.language,
        source_text=body.source_text,
        source_url=body.source_url,
    )

    await BillingService.consume_quota(current_user.id, "ai_call", 1, session)
    return _to_read(presentation)


@router.get("", response_model=list[PresentationRead])
@limiter.limit("20/minute")
async def list_presentations(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    List user's presentations with pagination.

    Rate limit: 20 requests/minute
    """
    service = PresentationGenService(session)
    presentations, _ = await service.list_presentations(current_user.id, skip, limit)
    return [_to_read(p) for p in presentations]


@router.get("/templates")
async def get_templates():
    """List available presentation templates with descriptions."""
    return {"templates": PresentationGenService.get_templates()}


@router.get("/{presentation_id}", response_model=PresentationRead)
@limiter.limit("30/minute")
async def get_presentation(
    request: Request,
    presentation_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Get a single presentation with all slides.

    Rate limit: 30 requests/minute
    """
    service = PresentationGenService(session)
    presentation = await service.get_presentation(current_user.id, presentation_id)
    if not presentation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Presentation not found",
        )
    return _to_read(presentation)


@router.put("/{presentation_id}/slides/{slide_number}", response_model=PresentationRead)
@limiter.limit("15/minute")
async def update_slide(
    request: Request,
    presentation_id: UUID,
    slide_number: int,
    body: SlideUpdate,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """
    Update a single slide by number.

    Rate limit: 15 requests/minute
    """
    service = PresentationGenService(session)
    presentation = await service.update_slide(
        user_id=current_user.id,
        presentation_id=presentation_id,
        slide_number=slide_number,
        updates=body.model_dump(exclude_unset=True),
    )
    if not presentation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Presentation or slide not found",
        )
    return _to_read(presentation)


@router.post("/{presentation_id}/slides/{after_slide}", response_model=PresentationRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def add_slide(
    request: Request,
    presentation_id: UUID,
    after_slide: int,
    body: SlideInsert,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """
    Insert a new slide after a given position.

    Rate limit: 10 requests/minute
    """
    service = PresentationGenService(session)
    presentation = await service.add_slide(
        user_id=current_user.id,
        presentation_id=presentation_id,
        after_slide=after_slide,
        slide_data=body.model_dump(),
    )
    if not presentation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Presentation not found",
        )
    return _to_read(presentation)


@router.delete("/{presentation_id}/slides/{slide_number}", response_model=PresentationRead)
@limiter.limit("10/minute")
async def remove_slide(
    request: Request,
    presentation_id: UUID,
    slide_number: int,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """
    Remove a slide by number. At least one slide must remain.

    Rate limit: 10 requests/minute
    """
    service = PresentationGenService(session)
    presentation = await service.remove_slide(
        user_id=current_user.id,
        presentation_id=presentation_id,
        slide_number=slide_number,
    )
    if not presentation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Presentation or slide not found, or cannot remove the last slide",
        )
    return _to_read(presentation)


@router.post("/{presentation_id}/export")
@limiter.limit("5/minute")
async def export_presentation(
    request: Request,
    presentation_id: UUID,
    body: ExportRequest,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """
    Export presentation to HTML, Markdown, or PDF.

    Rate limit: 5 requests/minute
    """
    if body.format not in VALID_EXPORT_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid format '{body.format}'. Valid: {sorted(VALID_EXPORT_FORMATS)}",
        )

    service = PresentationGenService(session)
    result = await service.export_presentation(
        user_id=current_user.id,
        presentation_id=presentation_id,
        export_format=body.format,
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Presentation not found",
        )
    return result


@router.post("/from-transcript", response_model=PresentationRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def generate_from_transcript(
    request: Request,
    body: PresentationFromTranscript,
    current_user: User = Depends(require_ai_call_quota),
    session: AsyncSession = Depends(get_session),
):
    """
    Generate a presentation from an existing transcription.

    Rate limit: 5 requests/minute
    """
    if body.template not in VALID_TEMPLATES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid template '{body.template}'. Valid: {sorted(VALID_TEMPLATES)}",
        )

    service = PresentationGenService(session)
    presentation = await service.generate_from_transcript(
        user_id=current_user.id,
        transcript_id=body.transcript_id,
        title=body.title,
        num_slides=body.num_slides,
        style=body.style,
        template=body.template,
        language=body.language,
    )
    if not presentation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcription not found or has no text content",
        )

    await BillingService.consume_quota(current_user.id, "ai_call", 1, session)
    return _to_read(presentation)


@router.delete("/{presentation_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def delete_presentation(
    request: Request,
    presentation_id: UUID,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """
    Delete a presentation.

    Rate limit: 10 requests/minute
    """
    service = PresentationGenService(session)
    presentation = await service.get_presentation(current_user.id, presentation_id)
    if not presentation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Presentation not found",
        )

    await session.delete(presentation)
    await session.commit()
    return None
