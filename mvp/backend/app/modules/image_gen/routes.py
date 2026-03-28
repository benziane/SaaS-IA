"""
Image Generation API routes.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth import get_current_user
from app.modules.auth_guards.middleware import require_verified_email
from app.database import get_session
from app.models.user import User
from app.modules.image_gen.schemas import (
    BulkGenerateRequest, EditImageRequest, GenerateImageRequest,
    ImageProjectCreate, ImageProjectRead, ImageRead, ThumbnailRequest,
    UpscaleRequest,
)
from app.modules.image_gen.service import ImageGenService
from app.rate_limit import limiter

router = APIRouter()


@router.post("/generate", response_model=ImageRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def generate_image(
    request: Request, body: GenerateImageRequest,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """Generate an image from a text prompt. Rate limit: 5/min"""
    return await ImageGenService.generate_image(
        user_id=current_user.id, prompt=body.prompt, style=body.style,
        provider=body.provider, width=body.width, height=body.height,
        session=session, negative_prompt=body.negative_prompt,
        project_id=body.project_id,
    )


@router.post("/thumbnail", response_model=ImageRead)
@limiter.limit("5/minute")
async def generate_thumbnail(
    request: Request, body: ThumbnailRequest,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """Generate a YouTube thumbnail from content. Rate limit: 5/min"""
    return await ImageGenService.generate_thumbnail(
        user_id=current_user.id, source_type=body.source_type,
        source_id=body.source_id, text=body.text,
        style=body.style, provider=body.provider, session=session,
    )


@router.post("/bulk", response_model=list[ImageRead])
@limiter.limit("2/minute")
async def bulk_generate(
    request: Request, body: BulkGenerateRequest,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """Generate multiple images at once. Rate limit: 2/min"""
    results = []
    for prompt in body.prompts:
        img = await ImageGenService.generate_image(
            user_id=current_user.id, prompt=prompt, style=body.style,
            provider=body.provider, width=body.width, height=body.height,
            session=session, project_id=body.project_id,
        )
        results.append(img)
    return results


@router.get("/", response_model=list[ImageRead])
@limiter.limit("20/minute")
async def list_images(
    request: Request, skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List generated images. Rate limit: 20/min"""
    return await ImageGenService.list_images(current_user.id, session, skip, limit)


@router.delete("/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def delete_image(
    request: Request, image_id: UUID,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """Delete an image. Rate limit: 10/min"""
    if not await ImageGenService.delete_image(image_id, current_user.id, session):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")


@router.post("/{image_id}/upscale", response_model=ImageRead)
@limiter.limit("3/minute")
async def upscale_image(
    request: Request, image_id: UUID, body: UpscaleRequest,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """Upscale an image using Real-ESRGAN (x2-x4). Rate limit: 3/min"""
    result = await ImageGenService.upscale_image(
        user_id=current_user.id, image_id=image_id,
        scale=body.scale, session=session,
    )
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=result["error"],
        )
    return result


@router.post("/projects", response_model=ImageProjectRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_project(
    request: Request, body: ImageProjectCreate,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """Create an image project. Rate limit: 10/min"""
    return await ImageGenService.create_project(current_user.id, body.name, body.description, session)


@router.get("/projects", response_model=list[ImageProjectRead])
@limiter.limit("20/minute")
async def list_projects(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List image projects. Rate limit: 20/min"""
    return await ImageGenService.list_projects(current_user.id, session)


@router.get("/styles")
async def list_styles():
    """List available image styles."""
    return {"styles": [
        {"id": "realistic", "name": "Realistic", "description": "Photorealistic quality"},
        {"id": "artistic", "name": "Artistic", "description": "Painterly, expressive style"},
        {"id": "cartoon", "name": "Cartoon", "description": "Fun, vibrant cartoon style"},
        {"id": "sketch", "name": "Sketch", "description": "Pencil sketch, hand-drawn"},
        {"id": "digital_art", "name": "Digital Art", "description": "Concept art, trending ArtStation"},
        {"id": "photography", "name": "Photography", "description": "Professional DSLR photography"},
        {"id": "watercolor", "name": "Watercolor", "description": "Soft watercolor painting"},
        {"id": "3d_render", "name": "3D Render", "description": "Octane render, CGI quality"},
        {"id": "flat_design", "name": "Flat Design", "description": "Modern vector style"},
        {"id": "minimalist", "name": "Minimalist", "description": "Clean, elegant, minimal"},
    ]}
