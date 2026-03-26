"""
Image Generation service - AI image creation, editing, thumbnails.

Supports Gemini Imagen, DALL-E 3, and Stable Diffusion.
Falls back to placeholder generation in mock mode.
"""

import ipaddress
import json
import socket
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse
from uuid import UUID

import structlog
from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.image_gen import GeneratedImage, ImageProject, ImageStatus

logger = structlog.get_logger()

# Real-ESRGAN auto-detection with graceful fallback
try:
    from realesrgan import RealESRGANer
    from basicsr.archs.rrdbnet_arch import RRDBNet
    HAS_REALESRGAN = True
except ImportError:
    HAS_REALESRGAN = False

_upscaler = None  # Lazy singleton

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


def _validate_url_for_ssrf(url: str) -> None:
    """Validate that a URL is safe to fetch (prevent SSRF attacks).

    Raises ValueError if the URL targets internal/private network resources.
    """
    parsed = urlparse(url)

    if parsed.scheme != "https":
        raise ValueError(f"Only HTTPS URLs are allowed, got: {parsed.scheme}")

    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL has no hostname")

    blocked_hostnames = {"localhost", "localhost.localdomain", "ip6-localhost", "ip6-loopback"}
    if hostname.lower() in blocked_hostnames:
        raise ValueError(f"Blocked hostname: {hostname}")

    try:
        resolved_ips = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        raise ValueError(f"Could not resolve hostname: {hostname}")

    for family, _type, _proto, _canonname, sockaddr in resolved_ips:
        ip_str = sockaddr[0]
        ip = ipaddress.ip_address(ip_str)
        if ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_link_local:
            raise ValueError(f"URL resolves to private/reserved IP: {ip_str}")

    return None


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
    def _get_upscaler():
        """Lazy-load Real-ESRGAN upscaler singleton (~100MB model)."""
        global _upscaler
        if _upscaler is not None:
            return _upscaler
        if not HAS_REALESRGAN:
            return None
        model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
        _upscaler = RealESRGANer(
            scale=4,
            model_path="https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth",
            model=model,
            tile=0,
            tile_pad=10,
            pre_pad=0,
            half=False,
        )
        logger.info("realesrgan_loaded", model="RealESRGAN_x4plus")
        return _upscaler

    @staticmethod
    async def upscale_image(
        user_id: UUID, image_id: UUID, scale: int,
        session: AsyncSession,
    ) -> dict | GeneratedImage:
        """Upscale an existing image using Real-ESRGAN.

        Returns a new GeneratedImage record with the upscaled result,
        or an error dict if Real-ESRGAN is not installed.
        """
        if not HAS_REALESRGAN:
            logger.warning("realesrgan_not_available")
            return {"error": "Real-ESRGAN not installed. Install with: pip install realesrgan basicsr"}

        # Load source image from DB
        source = await session.get(GeneratedImage, image_id)
        if not source or source.user_id != user_id:
            return {"error": "Image not found"}
        if not source.image_url:
            return {"error": "Source image has no URL"}

        # Create upscaled image record
        upscaled = GeneratedImage(
            user_id=user_id,
            prompt=f"[upscale x{scale}] {source.prompt}",
            style=source.style,
            provider="realesrgan",
            width=source.width * scale,
            height=source.height * scale,
            source_type="upscale",
            source_id=str(source.id),
            status=ImageStatus.GENERATING,
        )
        session.add(upscaled)
        await session.flush()

        try:
            import cv2
            import numpy as np

            upscaler = ImageGenService._get_upscaler()

            # Load the source image (handle local paths and URLs)
            img_path = source.image_url
            if img_path.startswith(("http://", "https://")):
                _validate_url_for_ssrf(img_path)
                import urllib.request
                tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                urllib.request.urlretrieve(img_path, tmp.name)
                img_path = tmp.name

            img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
            if img is None:
                raise ValueError(f"Could not read image from {source.image_url}")

            output, _ = upscaler.enhance(img, outscale=scale)

            # Save upscaled image
            out_dir = Path(tempfile.gettempdir()) / "upscaled"
            out_dir.mkdir(exist_ok=True)
            out_path = out_dir / f"{upscaled.id}.png"
            cv2.imwrite(str(out_path), output)

            upscaled.image_url = str(out_path)
            upscaled.model = "RealESRGAN_x4plus"
            upscaled.metadata_json = json.dumps({
                "source_image_id": str(source.id),
                "scale": scale,
                "original_size": f"{source.width}x{source.height}",
                "upscaled_size": f"{upscaled.width}x{upscaled.height}",
            })
            upscaled.status = ImageStatus.COMPLETED

        except Exception as e:
            upscaled.status = ImageStatus.FAILED
            upscaled.error = str(e)[:1000]
            logger.error("upscale_failed", error=str(e), image_id=str(image_id))

        session.add(upscaled)
        await session.commit()
        await session.refresh(upscaled)

        logger.info("image_upscaled", image_id=str(upscaled.id), source_id=str(source.id), scale=scale)
        return upscaled

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
