"""Instagram intelligence API routes."""

import asyncio
import os
import tempfile

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth import get_current_user
from app.database import get_session
from app.modules.auth_guards.middleware import require_verified_email
from app.models.user import User
from app.modules.instagram_intelligence.schemas import (
    ProfileAnalyzeRequest,
    ProfileReport,
    ReelDownloadRequest,
    ReelResult,
    ValidateProfileResult,
)
from app.modules.instagram_intelligence.service import InstagramIntelligenceService
from app.rate_limit import limiter

router = APIRouter()


@router.post("/validate", response_model=ValidateProfileResult)
@limiter.limit("30/minute")
async def validate_profile(
    request: Request,
    body: ProfileAnalyzeRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Validate an Instagram profile username — check it exists and is public.

    Rate limit: 30 requests/minute
    """
    try:
        svc = InstagramIntelligenceService()
        result = await svc.validate_profile(body.username)
        return ValidateProfileResult(**result)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/analyze-profile", response_model=ProfileReport)
@limiter.limit("5/minute")
async def analyze_profile(
    request: Request,
    body: ProfileAnalyzeRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Analyze a public Instagram profile: fetch Reels metadata, transcribe
    audio with Whisper, score sentiment with RoBERTa, return insights.

    Rate limit: 5 requests/minute
    """
    try:
        svc = InstagramIntelligenceService(session=session)
        result = await svc.analyze_profile(
            username=body.username,
            max_reels=min(body.max_reels, 20),
            transcribe=body.transcribe,
            language=body.language,
        )
        # Save all reels to database
        for reel in result.get("reels", []):
            await svc.save_reel(reel, current_user.id)
        return ProfileReport(**result)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/analyze-reel", response_model=ReelResult)
@limiter.limit("10/minute")
async def analyze_reel(
    request: Request,
    body: ReelDownloadRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Analyze a single public Instagram Reel by URL.
    Transcribes audio and scores sentiment.

    Rate limit: 10 requests/minute
    """
    if "instagram.com" not in body.reel_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL must be an instagram.com URL",
        )
    try:
        svc = InstagramIntelligenceService(session=session)
        result = await svc.analyze_reel(
            reel_url=body.reel_url,
            transcribe=body.transcribe,
            language=body.language,
        )
        await svc.save_reel(result, current_user.id)
        return ReelResult(**result)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/download-video")
@limiter.limit("5/minute")
async def download_video(
    request: Request,
    reel_url: str = Query(..., description="Instagram reel URL"),
    current_user: User = Depends(get_current_user),
):
    """
    Download a public Instagram Reel video and stream it to the client.
    Uses yt-dlp to handle Instagram's DASH streams.

    Rate limit: 5 requests/minute
    """
    if "instagram.com" not in reel_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL must be an instagram.com URL",
        )

    tmp_dir = tempfile.mkdtemp()
    tmp_path = os.path.join(tmp_dir, "reel.%(ext)s")

    try:
        import yt_dlp

        ydl_opts = {
            "outtmpl": tmp_path,
            "format": "best",
            "quiet": True,
            "no_warnings": True,
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120",
            },
        }

        loop = asyncio.get_event_loop()

        def _download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(reel_url, download=True)

        await loop.run_in_executor(None, _download)

        import glob
        files = glob.glob(os.path.join(tmp_dir, "*"))
        if not files:
            raise HTTPException(status_code=500, detail="Download failed")

        file_path = files[0]
        ext = os.path.splitext(file_path)[1] or ".mp4"
        filename = f"instagram_reel{ext}"

        def iter_file():
            try:
                with open(file_path, "rb") as f:
                    while chunk := f.read(65536):
                        yield chunk
            finally:
                import shutil
                shutil.rmtree(tmp_dir, ignore_errors=True)

        media_type = "video/mp4" if ext == ".mp4" else "application/octet-stream"
        return StreamingResponse(
            iter_file(),
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    except HTTPException:
        raise
    except Exception as e:
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/download-thumbnail")
@limiter.limit("20/minute")
async def download_thumbnail(
    request: Request,
    reel_url: str = Query(..., description="Instagram reel or post URL"),
    current_user: User = Depends(get_current_user),
):
    """
    Download the thumbnail/cover image of a public Instagram Reel.

    Rate limit: 20 requests/minute
    """
    if "instagram.com" not in reel_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL must be an instagram.com URL",
        )

    try:
        import yt_dlp
        import httpx

        ydl_opts = {
            "skip_download": True,
            "quiet": True,
            "no_warnings": True,
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120",
            },
        }

        loop = asyncio.get_event_loop()

        def _extract():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(reel_url, download=False)

        info = await loop.run_in_executor(None, _extract)
        thumbnail_url = info.get("thumbnail") if info else None

        if not thumbnail_url:
            raise HTTPException(status_code=404, detail="No thumbnail found")

        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            resp = await client.get(
                thumbnail_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120"},
            )
            resp.raise_for_status()

        content_type = resp.headers.get("content-type", "image/jpeg")
        return StreamingResponse(
            iter([resp.content]),
            media_type=content_type,
            headers={"Content-Disposition": 'attachment; filename="thumbnail.jpg"'},
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/download-carousel")
@limiter.limit("10/minute")
async def download_carousel(
    request: Request,
    post_url: str = Query(..., description="Instagram post URL (carousel /p/...)"),
    current_user: User = Depends(get_current_user),
):
    """
    Download all slides from an Instagram carousel/sidecar post.

    Fallback chain:
      1. instaloader get_sidecar_nodes() — anonymous, works on public posts
      2. Playwright DOM scraping — headless browser fallback

    Returns JSON with slide URLs + metadata (slide_count, username, caption, likes).

    Rate limit: 10/minute
    """
    if "instagram.com" not in post_url:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="URL must be an instagram.com URL")

    try:
        svc = InstagramIntelligenceService()
        result = await svc.download_carousel(post_url)
        if not result.get("slides"):
            raise HTTPException(status_code=404, detail=result.get("error", "No slides found"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/analyze-carousel")
@limiter.limit("5/minute")
async def analyze_carousel(
    request: Request,
    post_url: str = Query(..., description="Instagram carousel/post URL (/p/...)"),
    mode: str = Query("claude_vision", description="OCR mode: local_ocr | claude_vision | both"),
    current_user: User = Depends(get_current_user),
):
    """
    Download all slides from an Instagram carousel and extract text/structure
    from each image using OCR or Claude Vision.

    Modes:
      - local_ocr: PaddleOCR → Surya → EasyOCR (best available, fully offline)
      - claude_vision: Claude Haiku Vision (best for infographics/schemas)
      - both: run both in parallel and merge results

    Rate limit: 5 requests/minute
    """
    if "instagram.com" not in post_url:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="URL must be an instagram.com URL")
    if mode not in ("local_ocr", "claude_vision", "both"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="mode must be local_ocr | claude_vision | both")
    try:
        import shutil
        svc = InstagramIntelligenceService()
        tmp_dir = tempfile.mkdtemp(prefix="ig_carousel_")
        try:
            carousel = await svc.download_carousel_files(post_url, tmp_dir)
            saved = carousel.get("saved_files", [])
            if not saved:
                raise HTTPException(status_code=404, detail=carousel.get("error", "No slides downloaded"))
            paths = [f["path"] for f in sorted(saved, key=lambda x: x["index"])]
            transcriptions = await svc.transcribe_carousel_images(paths, mode=mode)
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)
        return {
            "post_url": post_url,
            "provider": carousel.get("provider"),
            "username": carousel.get("username"),
            "likes": carousel.get("likes"),
            "slide_count": carousel.get("slide_count"),
            "caption": carousel.get("caption"),
            "ocr_mode": mode,
            "slides": transcriptions,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
