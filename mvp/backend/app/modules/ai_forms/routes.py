"""
AI Forms API routes - CRUD, publish/close, public submission, responses, AI analysis.
"""

import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth import get_current_user
from app.database import get_session
from app.models.user import User
from app.modules.ai_forms.schemas import (
    FormAnalysisRead,
    FormCreate,
    FormGenerateRequest,
    FormRead,
    FormResponseCreate,
    FormResponseRead,
    FormUpdate,
)
from app.modules.ai_forms.service import AIFormsService
from app.rate_limit import limiter

router = APIRouter()


def _form_to_read(form) -> dict:
    """Convert AIForm model to FormRead-compatible dict."""
    fields_raw = json.loads(form.fields_json) if form.fields_json else []
    return {
        "id": form.id,
        "user_id": form.user_id,
        "title": form.title,
        "description": form.description,
        "fields": fields_raw,
        "style": form.style,
        "thank_you_message": form.thank_you_message,
        "is_public": form.is_public,
        "share_token": form.share_token,
        "responses_count": form.responses_count,
        "status": form.status,
        "created_at": form.created_at,
        "updated_at": form.updated_at,
    }


def _response_to_read(resp) -> dict:
    """Convert FormResponse model to FormResponseRead-compatible dict."""
    return {
        "id": resp.id,
        "form_id": resp.form_id,
        "answers": json.loads(resp.answers_json) if resp.answers_json else {},
        "score": resp.score,
        "analysis": resp.analysis,
        "submitted_at": resp.submitted_at,
    }


# ─── Authenticated CRUD endpoints ──────────────────────────────────────────────


@router.post("", response_model=FormRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_form(
    request: Request,
    body: FormCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a new form with fields and configuration."""
    service = AIFormsService(session)
    form = await service.create_form(current_user.id, body.model_dump())
    return _form_to_read(form)


@router.get("", response_model=list[FormRead])
@limiter.limit("20/minute")
async def list_forms(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List all forms for the current user."""
    service = AIFormsService(session)
    forms = await service.list_forms(current_user.id)
    return [_form_to_read(f) for f in forms]


@router.get("/{form_id}", response_model=FormRead)
@limiter.limit("20/minute")
async def get_form(
    request: Request,
    form_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get form details."""
    service = AIFormsService(session)
    form = await service.get_form(current_user.id, form_id)
    if not form:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form not found")
    return _form_to_read(form)


@router.put("/{form_id}", response_model=FormRead)
@limiter.limit("10/minute")
async def update_form(
    request: Request,
    form_id: UUID,
    body: FormUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Update form settings and fields."""
    service = AIFormsService(session)
    form = await service.update_form(
        current_user.id, form_id, body.model_dump(exclude_unset=True)
    )
    if not form:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form not found")
    return _form_to_read(form)


@router.delete("/{form_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def delete_form(
    request: Request,
    form_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Soft delete a form."""
    service = AIFormsService(session)
    deleted = await service.delete_form(current_user.id, form_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form not found")
    return None


# ─── Publish / Close ──────────────────────────────────────────────────────────


@router.post("/{form_id}/publish", response_model=FormRead)
@limiter.limit("5/minute")
async def publish_form(
    request: Request,
    form_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Publish form and generate share token."""
    service = AIFormsService(session)
    form = await service.publish_form(current_user.id, form_id)
    if not form:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form not found")
    return _form_to_read(form)


@router.post("/{form_id}/close", response_model=FormRead)
@limiter.limit("5/minute")
async def close_form(
    request: Request,
    form_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Close form to new responses."""
    service = AIFormsService(session)
    form = await service.close_form(current_user.id, form_id)
    if not form:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form not found")
    return _form_to_read(form)


# ─── Responses (authenticated) ────────────────────────────────────────────────


@router.get("/{form_id}/responses", response_model=list[FormResponseRead])
@limiter.limit("20/minute")
async def list_responses(
    request: Request,
    form_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List all responses for a form."""
    service = AIFormsService(session)
    responses = await service.list_responses(current_user.id, form_id)
    if responses is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form not found")
    return [_response_to_read(r) for r in responses]


@router.get("/{form_id}/responses/{response_id}", response_model=FormResponseRead)
@limiter.limit("20/minute")
async def get_response(
    request: Request,
    form_id: UUID,
    response_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get a single response."""
    service = AIFormsService(session)
    response = await service.get_response(current_user.id, form_id, response_id)
    if not response:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Response not found")
    return _response_to_read(response)


# ─── AI Analysis & Scoring ─────────────────────────────────────────────────────


@router.get("/{form_id}/analytics", response_model=FormAnalysisRead)
@limiter.limit("10/minute")
async def analyze_responses(
    request: Request,
    form_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """AI analysis of all form responses with insights."""
    service = AIFormsService(session)
    analysis = await service.analyze_responses(current_user.id, form_id)
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form not found")
    return analysis


@router.post("/{form_id}/responses/{response_id}/score", response_model=FormResponseRead)
@limiter.limit("10/minute")
async def score_response(
    request: Request,
    form_id: UUID,
    response_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """AI scoring of an individual response."""
    service = AIFormsService(session)
    response = await service.score_response(current_user.id, form_id, response_id)
    if not response:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Response not found")
    return _response_to_read(response)


# ─── AI Form Generation ───────────────────────────────────────────────────────


@router.post("/generate", response_model=FormRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def generate_form(
    request: Request,
    body: FormGenerateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Generate a form from natural language description using AI."""
    service = AIFormsService(session)
    form = await service.generate_form(current_user.id, body.prompt, body.num_fields)
    return _form_to_read(form)


# ─── Public endpoints (no auth, validate share_token) ──────────────────────────


@router.get("/public/{share_token}", response_model=FormRead)
@limiter.limit("30/minute")
async def public_get_form(
    request: Request,
    share_token: str,
    session: AsyncSession = Depends(get_session),
):
    """Get a published form by share token. No auth required."""
    service = AIFormsService(session)
    form = await service._get_form_by_token(share_token)
    if not form:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Form not found or not published",
        )
    return _form_to_read(form)


@router.post("/public/{share_token}/submit", response_model=FormResponseRead)
@limiter.limit("20/minute")
async def public_submit_response(
    request: Request,
    share_token: str,
    body: FormResponseCreate,
    session: AsyncSession = Depends(get_session),
):
    """Submit a response to a published form. No auth required."""
    service = AIFormsService(session)

    form = await service._get_form_by_token(share_token)
    if not form:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Form not found or not published",
        )

    try:
        response = await service.submit_response(form.id, share_token, body.answers)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    if not response:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to submit response",
        )
    return _response_to_read(response)
