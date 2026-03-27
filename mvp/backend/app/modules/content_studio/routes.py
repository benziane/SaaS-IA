"""
Content Studio API routes - Multi-format content generation.
"""

import json
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
from app.modules.content_studio.schemas import (
    ContentRead,
    ContentUpdate,
    GenerateFromURLRequest,
    GenerateRequest,
    ProjectCreate,
    ProjectRead,
    RegenerateRequest,
)
from app.modules.content_studio.service import ContentStudioService
from app.rate_limit import limiter

router = APIRouter()


@router.post("/projects", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_project(
    request: Request,
    body: ProjectCreate,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """
    Create a content project from a source (text, transcription, document, or URL).

    Rate limit: 10 requests/minute
    """
    if body.source_type not in ("text", "transcription", "document", "url"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="source_type must be one of: text, transcription, document, url",
        )

    if body.source_type == "text" and not body.source_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="source_text is required when source_type is 'text'",
        )

    if body.source_type in ("transcription", "document") and not body.source_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"source_id is required when source_type is '{body.source_type}'",
        )

    project = await ContentStudioService.create_project(
        user_id=current_user.id,
        title=body.title,
        source_type=body.source_type,
        source_text=body.source_text,
        source_id=body.source_id,
        session=session,
        language=body.language,
        tone=body.tone,
        target_audience=body.target_audience,
        keywords=body.keywords,
    )
    return project


@router.get("/projects", response_model=list[ProjectRead])
@limiter.limit("20/minute")
async def list_projects(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    List user's content projects.

    Rate limit: 20 requests/minute
    """
    projects, _ = await ContentStudioService.list_projects(
        current_user.id, session, skip, limit
    )
    return projects


@router.post("/projects/{project_id}/generate", response_model=list[ContentRead])
@limiter.limit("5/minute")
async def generate_contents(
    request: Request,
    project_id: UUID,
    body: GenerateRequest,
    current_user: User = Depends(require_ai_call_quota),
    session: AsyncSession = Depends(get_session),
):
    """
    Generate content in multiple formats for a project.

    Available formats: blog_article, twitter_thread, linkedin_post, newsletter,
    instagram_carousel, youtube_description, seo_meta, press_release,
    email_campaign, podcast_notes.

    Rate limit: 5 requests/minute
    """
    valid_formats = [
        "blog_article", "twitter_thread", "linkedin_post", "newsletter",
        "instagram_carousel", "youtube_description", "seo_meta",
        "press_release", "email_campaign", "podcast_notes",
    ]
    invalid = [f for f in body.formats if f not in valid_formats]
    if invalid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid formats: {invalid}. Valid: {valid_formats}",
        )

    contents = await ContentStudioService.generate_contents(
        project_id=project_id,
        user_id=current_user.id,
        formats=body.formats,
        session=session,
        provider=body.provider,
        custom_instructions=body.custom_instructions,
    )

    if not contents:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or no source text available",
        )

    # Consume AI quota per format generated
    await BillingService.consume_quota(
        current_user.id, "ai_call", len(body.formats), session
    )

    return contents


@router.get("/projects/{project_id}/contents", response_model=list[ContentRead])
@limiter.limit("20/minute")
async def get_project_contents(
    request: Request,
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Get all generated content for a project.

    Rate limit: 20 requests/minute
    """
    return await ContentStudioService.get_project_contents(
        project_id, current_user.id, session
    )


@router.put("/contents/{content_id}", response_model=ContentRead)
@limiter.limit("10/minute")
async def update_content(
    request: Request,
    content_id: UUID,
    body: ContentUpdate,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """
    Update a generated content piece (edit text, change status, schedule).

    Rate limit: 10 requests/minute
    """
    content = await ContentStudioService.update_content(
        content_id, current_user.id, body.model_dump(exclude_unset=True), session
    )
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found",
        )
    return content


@router.post("/contents/{content_id}/regenerate", response_model=ContentRead)
@limiter.limit("5/minute")
async def regenerate_content(
    request: Request,
    content_id: UUID,
    body: RegenerateRequest,
    current_user: User = Depends(require_ai_call_quota),
    session: AsyncSession = Depends(get_session),
):
    """
    Regenerate a specific content piece with optional custom instructions.

    Rate limit: 5 requests/minute
    """
    content = await ContentStudioService.regenerate_content(
        content_id, current_user.id, session,
        custom_instructions=body.custom_instructions,
        provider=body.provider,
    )
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found",
        )

    await BillingService.consume_quota(current_user.id, "ai_call", 1, session)
    return content


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def delete_project(
    request: Request,
    project_id: UUID,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """
    Delete a content project and all its generated content.

    Rate limit: 10 requests/minute
    """
    deleted = await ContentStudioService.delete_project(
        project_id, current_user.id, session
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    return None


@router.post("/from-url", response_model=list[ContentRead])
@limiter.limit("3/minute")
async def generate_from_url(
    request: Request,
    body: GenerateFromURLRequest,
    current_user: User = Depends(require_ai_call_quota),
    session: AsyncSession = Depends(get_session),
):
    """
    One-shot: crawl a URL and generate content in multiple formats.

    Rate limit: 3 requests/minute
    """
    project = await ContentStudioService.create_project(
        user_id=current_user.id,
        title=body.title or f"Content from {body.url[:50]}",
        source_type="url",
        source_text=body.url,
        source_id=None,
        session=session,
        tone=body.tone,
        target_audience=body.target_audience,
        keywords=body.keywords,
    )

    contents = await ContentStudioService.generate_contents(
        project_id=project.id,
        user_id=current_user.id,
        formats=body.formats,
        session=session,
        provider=body.provider,
    )

    await BillingService.consume_quota(
        current_user.id, "ai_call", len(body.formats), session
    )

    return contents


@router.get("/formats")
async def list_formats():
    """List all available content formats with descriptions."""
    return {
        "formats": [
            {"id": "blog_article", "name": "Blog Article", "description": "Full-length blog post with SEO structure", "icon": "Article"},
            {"id": "twitter_thread", "name": "Twitter/X Thread", "description": "Viral thread with 8-15 tweets", "icon": "Twitter"},
            {"id": "linkedin_post", "name": "LinkedIn Post", "description": "Professional post with engagement hooks", "icon": "LinkedIn"},
            {"id": "newsletter", "name": "Newsletter", "description": "Email newsletter with subject line", "icon": "Email"},
            {"id": "instagram_carousel", "name": "Instagram Carousel", "description": "8-10 slide carousel with captions", "icon": "Instagram"},
            {"id": "youtube_description", "name": "YouTube Description", "description": "Optimized video description with timestamps", "icon": "YouTube"},
            {"id": "seo_meta", "name": "SEO Metadata", "description": "Meta title, description, keywords, Open Graph", "icon": "Search"},
            {"id": "press_release", "name": "Press Release", "description": "Professional press release format", "icon": "Newspaper"},
            {"id": "email_campaign", "name": "Email Campaign", "description": "3-email marketing sequence", "icon": "Campaign"},
            {"id": "podcast_notes", "name": "Podcast Show Notes", "description": "Episode notes with timestamps and resources", "icon": "Podcasts"},
        ]
    }
