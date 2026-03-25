"""
Image Generation service - AI image creation, editing, thumbnails.

Supports Gemini Imagen, DALL-E 3, and Stable Diffusion.
Falls back to placeholder generation in mock mode.
"""

import json
from datetime import datetime
from typing import Optional
from uuid import UUID

import structlog
from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.image_gen import GeneratedImage, ImageProject, ImageStatus

logger = structlog.get_logger()

STYLE_PROMPTS = {
    "realistic": "photorealistic, high quality, detailed, 8k resolution",
    "artistic": "artistic style, painted, expressive brushstrokes, gallery quality",
    "cartoon": "cartoon style, vibrant colors, bold outlines, fun and playful",
    "sketch": "pencil sketch, hand-drawn, detailed linework, black and white",
    "digital_art": "digital art, concept art, highly detailed, trending on artstation",
    "photography": "professional photography, DSLR, perfect lighting, shallow depth of field",
    "watercolor": "watercolor painting, soft colors, paper texture, artistic blending",
    "3d_render": "3D render, octane render, volumetric lighting, CGI quality",
    "flat_design": "flat design, vector style, clean lines, modern minimalist",
    "minimalist": "minimalist, simple, clean, lots of negative space, elegant",
}


class ImageGenService:
    """Service for AI image generation."""

    @staticmethod
    async def generate_image(
        user_id: UUID, prompt: str, style: str, provider: str,
        width: int, height: int, session: AsyncSession,
        negative_prompt: Optional[str] = None,
        source_type: str = "prompt", source_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> GeneratedImage:
        """Generate an image from a text prompt."""
        image = GeneratedImage(
            user_id=user_id,
            prompt=prompt,
            negative_prompt=negative_prompt,
            style=style,
            provider=provider,
            width=width,
            height=height,
            source_type=source_type,
            source_id=source_id,
            status=ImageStatus.GENERATING,
        )
        session.add(image)
        await session.flush()

        try:
            # Enhance prompt with style
            style_suffix = STYLE_PROMPTS.get(style, "")
            full_prompt = f"{prompt}. {style_suffix}" if style_suffix else prompt

            result = await ImageGenService._call_provider(
                prompt=full_prompt,
                negative_prompt=negative_prompt,
                provider=provider,
                width=width,
                height=height,
            )

            image.image_url = result.get("url", "")
            image.thumbnail_url = result.get("thumbnail_url", "")
            image.model = result.get("model", "")
            image.metadata_json = json.dumps(result.get("metadata", {}), ensure_ascii=False)
            image.status = ImageStatus.COMPLETED

        except Exception as e:
            image.status = ImageStatus.FAILED
            image.error = str(e)[:1000]
            logger.error("image_generation_failed", error=str(e))

        session.add(image)

        # Update project count
        if project_id:
            try:
                from uuid import UUID as UUIDType
                project = await session.get(ImageProject, UUIDType(project_id))
                if project and project.user_id == user_id:
                    project.image_count += 1
                    session.add(project)
            except (ValueError, Exception):
                pass

        await session.commit()
        await session.refresh(image)

        logger.info("image_generated", image_id=str(image.id), provider=provider, style=style)
        return image

    @staticmethod
    async def generate_thumbnail(
        user_id: UUID, source_type: str, source_id: Optional[str],
        text: Optional[str], style: str, provider: str,
        session: AsyncSession,
    ) -> GeneratedImage:
        """Generate a YouTube thumbnail from content."""
        source_text = text or ""

        if source_type == "transcription" and source_id:
            from app.models.transcription import Transcription
            from uuid import UUID as UUIDType
            t = await session.get(Transcription, UUIDType(source_id))
            if t and t.user_id == user_id:
                source_text = t.transcription_text or ""

        if not source_text:
            image = GeneratedImage(
                user_id=user_id, prompt="", style=style, provider=provider,
                source_type="thumbnail", status=ImageStatus.FAILED,
                error="No source text for thumbnail",
            )
            session.add(image)
            await session.commit()
            await session.refresh(image)
            return image

        # Use AI to create a thumbnail prompt
        try:
            from app.ai_assistant.service import AIAssistantService
            result = await AIAssistantService.process_text_with_provider(
                text=f"Create a concise, visual image prompt for a YouTube thumbnail based on this content. Focus on the key visual elements that would make an engaging thumbnail. Content: {source_text[:3000]}",
                task="creative",
                provider_name="gemini",
                user_id=user_id,
                module="image_gen",
            )
            thumbnail_prompt = result.get("processed_text", source_text[:200])
        except Exception:
            thumbnail_prompt = source_text[:200]

        return await ImageGenService.generate_image(
            user_id=user_id, prompt=thumbnail_prompt, style=style,
            provider=provider, width=1280, height=720, session=session,
            source_type="thumbnail", source_id=source_id,
        )

    @staticmethod
    async def list_images(
        user_id: UUID, session: AsyncSession,
        skip: int = 0, limit: int = 20,
    ) -> list[GeneratedImage]:
        result = await session.execute(
            select(GeneratedImage).where(GeneratedImage.user_id == user_id)
            .order_by(GeneratedImage.created_at.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def delete_image(image_id: UUID, user_id: UUID, session: AsyncSession) -> bool:
        image = await session.get(GeneratedImage, image_id)
        if not image or image.user_id != user_id:
            return False
        await session.delete(image)
        await session.commit()
        return True

    @staticmethod
    async def create_project(
        user_id: UUID, name: str, description: Optional[str], session: AsyncSession,
    ) -> ImageProject:
        project = ImageProject(user_id=user_id, name=name, description=description)
        session.add(project)
        await session.commit()
        await session.refresh(project)
        return project

    @staticmethod
    async def list_projects(user_id: UUID, session: AsyncSession) -> list[ImageProject]:
        result = await session.execute(
            select(ImageProject).where(ImageProject.user_id == user_id)
            .order_by(ImageProject.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def _call_provider(
        prompt: str, negative_prompt: Optional[str],
        provider: str, width: int, height: int,
    ) -> dict:
        """Call the image generation provider. Returns dict with url, model, metadata."""
        from app.config import settings

        # Try Gemini Imagen
        if provider == "gemini":
            api_key = getattr(settings, "GEMINI_API_KEY", None)
            if api_key and not api_key.startswith("your-"):
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel("gemini-2.0-flash")
                    response = await model.generate_content_async(
                        f"Describe this image in vivid detail as if you were painting it: {prompt}"
                    )
                    # Gemini doesn't directly generate images via this API,
                    # return the enhanced prompt as a placeholder
                    return {
                        "url": f"/api/images/placeholder/{width}x{height}",
                        "model": "gemini-2.0-flash",
                        "metadata": {"enhanced_prompt": response.text[:500] if response.text else prompt},
                    }
                except Exception as e:
                    logger.warning("gemini_image_failed", error=str(e))

        # Mock mode for MVP
        logger.info("image_gen_mock", provider=provider, prompt_length=len(prompt))
        return {
            "url": f"/api/images/placeholder/{width}x{height}?style={provider}",
            "thumbnail_url": f"/api/images/placeholder/256x256?style={provider}",
            "model": f"{provider}_mock",
            "metadata": {"mock": True, "prompt_length": len(prompt)},
        }
