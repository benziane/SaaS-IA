"""
YouTube transcription API routes — thin layer over existing utilities.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth import get_current_user
from app.database import get_session
from app.models.user import User
from app.modules.billing.service import BillingService
from app.modules.youtube_transcription.schemas import (
    MetadataResult,
    PlaylistRequest,
    PlaylistResult,
    StreamCaptureResult,
    StreamRequest,
    StreamStatusResult,
    TranscriptResult,
    ValidateResult,
    VideoAnalyzeRequest,
    VideoAnalyzeResult,
    VideoFrameResult,
    YouTubeURLRequest,
)
from app.rate_limit import limiter

router = APIRouter()


@router.post("/validate", response_model=ValidateResult)
@limiter.limit("30/minute")
async def validate_url(
    request: Request,
    body: YouTubeURLRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Validate a YouTube URL and extract the video ID.

    Rate limit: 30 requests/minute
    """
    try:
        from app.transcription.youtube_service import YouTubeService

        valid = YouTubeService.validate_url(body.video_url)
        video_id = YouTubeService.extract_video_id(body.video_url) if valid else None

        return ValidateResult(
            valid=valid,
            video_id=video_id,
            url=body.video_url,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/metadata", response_model=MetadataResult)
@limiter.limit("20/minute")
async def get_metadata(
    request: Request,
    body: YouTubeURLRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Extract YouTube video metadata.

    Returns title, description, tags, chapters, thumbnail, etc.

    Rate limit: 20 requests/minute
    """
    try:
        from app.transcription.youtube_transcript import get_youtube_metadata

        metadata = await get_youtube_metadata(body.video_url)
        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not extract metadata from URL",
            )

        return MetadataResult(
            video_id=metadata.get("video_id", ""),
            title=metadata.get("title", ""),
            uploader=metadata.get("uploader", ""),
            duration_seconds=float(metadata.get("duration_seconds", 0)),
            view_count=int(metadata.get("view_count", 0)),
            like_count=int(metadata.get("like_count", 0)),
            thumbnail=metadata.get("thumbnail"),
            is_live=bool(metadata.get("is_live", False)),
            description=metadata.get("description", ""),
            tags=metadata.get("tags", []),
            chapters=metadata.get("chapters", []),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/transcript", response_model=TranscriptResult)
@limiter.limit("10/minute")
async def get_transcript(
    request: Request,
    body: YouTubeURLRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Fetch YouTube subtitles/transcript directly (no download needed).

    Returns None if no subtitles are available — use /smart for fallback.

    Rate limit: 10 requests/minute
    """
    try:
        from app.transcription.youtube_transcript import extract_video_id, get_youtube_transcript

        result = await get_youtube_transcript(body.video_url, body.language)
        if not result or not result.get("text"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No subtitles available for this video. Use /smart for Whisper fallback.",
            )

        video_id = extract_video_id(body.video_url) or ""

        return TranscriptResult(
            video_id=video_id,
            text=result.get("text", ""),
            language=result.get("language", body.language),
            duration_seconds=float(result.get("duration_seconds", 0)),
            provider=result.get("provider", "youtube_subtitles"),
            is_manual=bool(result.get("is_manual", False)),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/smart", response_model=TranscriptResult)
@limiter.limit("10/minute")
async def smart_transcribe(
    request: Request,
    body: YouTubeURLRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Smart transcription with provider fallback.

    Tries in order:
    1. YouTube subtitles (instant, free)
    2. Whisper (download + local ASR)

    Rate limit: 10 requests/minute
    """
    try:
        from app.transcription.youtube_transcript import (
            download_video,
            extract_video_id,
            get_youtube_transcript,
        )

        video_id = extract_video_id(body.video_url) or ""

        # 1. Try YouTube subtitles first (free, instant)
        result = await get_youtube_transcript(body.video_url, body.language)
        if result and result.get("text"):
            return TranscriptResult(
                video_id=video_id,
                text=result.get("text", ""),
                language=result.get("language", body.language),
                duration_seconds=float(result.get("duration_seconds", 0)),
                provider="youtube_subtitles",
                is_manual=bool(result.get("is_manual", False)),
            )

        # 2. Fallback: download + Whisper
        try:
            from app.transcription.whisper_service import transcribe_with_whisper

            video_data = await download_video(body.video_url)
            if video_data and video_data.get("file_path"):
                whisper_result = await transcribe_with_whisper(video_data["file_path"])
                if whisper_result and whisper_result.get("text"):
                    await BillingService.consume_quota(current_user.id, "transcription", 1, session)
                    return TranscriptResult(
                        video_id=video_id,
                        text=whisper_result.get("text", ""),
                        language=whisper_result.get("language", body.language),
                        duration_seconds=float(whisper_result.get("duration_seconds", 0)),
                        provider="whisper",
                        is_manual=False,
                    )
        except Exception:
            pass

        # All providers failed
        return TranscriptResult(
            video_id=video_id,
            text="",
            language=body.language,
            duration_seconds=0.0,
            provider="failed",
            is_manual=False,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/playlist", response_model=PlaylistResult)
@limiter.limit("3/minute")
async def transcribe_playlist(
    request: Request,
    body: PlaylistRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Fetch transcripts for all videos in a YouTube playlist.

    Uses YouTube subtitles for each video (no download).
    Max 50 videos per request by default.

    Rate limit: 3 requests/minute
    """
    try:
        from app.transcription.youtube_transcript import get_playlist_videos, get_youtube_transcript

        videos = await get_playlist_videos(body.playlist_url, body.max_videos)
        if not videos:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not retrieve playlist or playlist is empty",
            )

        results = []
        transcribed = 0

        for video in videos:
            video_url = video.get("url", "")
            if not video_url:
                continue

            entry: dict = {
                "video_id": video.get("video_id", ""),
                "title": video.get("title", ""),
                "url": video_url,
                "success": False,
                "transcript": "",
                "provider": "",
                "language": body.language,
                "duration": video.get("duration_seconds", 0),
                "error": None,
            }

            try:
                transcript = await get_youtube_transcript(video_url, body.language)
                if transcript and transcript.get("text"):
                    entry["transcript"] = transcript.get("text", "")
                    entry["provider"] = transcript.get("provider", "youtube_subtitles")
                    entry["language"] = transcript.get("language", body.language)
                    entry["success"] = True
                    transcribed += 1
                else:
                    entry["error"] = "No subtitles available"
            except Exception as exc:
                entry["error"] = str(exc)

            results.append(entry)

        return PlaylistResult(
            success=transcribed > 0,
            total=len(results),
            transcribed=transcribed,
            results=results,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/stream/status", response_model=StreamStatusResult)
@limiter.limit("20/minute")
async def check_stream_status(
    request: Request,
    body: StreamRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Check if a URL is a live stream and return its current status.

    Rate limit: 20 requests/minute
    """
    try:
        from app.transcription.livestream_service import LiveStreamService

        result = await LiveStreamService.check_stream_status(body.stream_url)

        return StreamStatusResult(
            is_live=result.get("is_live", False),
            was_live=result.get("was_live", False),
            title=result.get("title", ""),
            uploader=result.get("uploader", ""),
            concurrent_viewers=result.get("concurrent_viewers"),
            url=result.get("url", body.stream_url),
            error=result.get("error"),
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/stream/capture", response_model=StreamCaptureResult)
@limiter.limit("2/minute")
async def capture_stream(
    request: Request,
    body: StreamRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Capture a live stream segment and transcribe it with Whisper.

    Rate limit: 2 requests/minute
    """
    try:
        from app.transcription.livestream_service import LiveStreamService

        capture = await LiveStreamService.capture_stream(
            stream_url=body.stream_url,
            duration_seconds=body.duration_seconds,
        )

        if not capture or not capture.get("success"):
            return StreamCaptureResult(
                success=False,
                url=body.stream_url,
                title="",
                duration_seconds=0.0,
                capture_method="",
                transcript=None,
                provider=None,
                error=capture.get("error", "Capture failed") if capture else "Capture failed",
            )

        transcript_text = None
        provider = None
        file_path = capture.get("file_path", "")

        if file_path:
            try:
                from app.transcription.whisper_service import transcribe_with_whisper

                whisper_result = await transcribe_with_whisper(file_path)
                if whisper_result:
                    transcript_text = whisper_result.get("text") or None
                    provider = whisper_result.get("provider", "whisper") or None
                    if transcript_text:
                        await BillingService.consume_quota(
                            current_user.id, "transcription", 1, session
                        )
            except Exception:
                pass

        return StreamCaptureResult(
            success=True,
            url=body.stream_url,
            title=capture.get("title", ""),
            duration_seconds=float(capture.get("duration_seconds", 0)),
            capture_method=capture.get("capture_method", ""),
            transcript=transcript_text,
            provider=provider,
            error=None,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/analyze", response_model=VideoAnalyzeResult)
@limiter.limit("3/minute")
async def analyze_video(
    request: Request,
    body: VideoAnalyzeRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Download a YouTube video, extract frames at regular intervals,
    and analyze each frame with Vision AI. Returns a per-frame
    description plus an overall AI summary.

    Rate limit: 3 requests/minute
    """
    try:
        from app.transcription.youtube_transcript import download_video, extract_video_id
        from app.transcription.video_tools import VideoToolsService

        video_data = await download_video(body.video_url)
        if not video_data or not video_data.get("file_path"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not download video",
            )

        analyses = await VideoToolsService.analyze_video_frames(
            video_path=video_data["file_path"],
            interval_seconds=body.interval_seconds,
            max_frames=body.max_frames,
            prompt=body.prompt,
        )

        frames = [
            VideoFrameResult(
                timestamp=float(a.get("timestamp", 0)),
                description=a.get("description", ""),
            )
            for a in analyses
        ]

        summary = ""
        if frames:
            all_descriptions = "\n".join(
                f"[{f.timestamp}s] {f.description}" for f in frames
            )
            try:
                from app.ai_assistant.service import AIAssistantService

                ai_result = await AIAssistantService.process_text_with_provider(
                    text=(
                        "Based on these video frame descriptions, provide a concise summary"
                        f" of the video content:\n\n{all_descriptions[:5000]}"
                    ),
                    task="summarize",
                    provider_name="gemini",
                )
                summary = ai_result.get("processed_text", "")
            except Exception:
                summary = all_descriptions[:500]

        await BillingService.consume_quota(current_user.id, "ai_call", 1, session)

        return VideoAnalyzeResult(
            video_id=extract_video_id(body.video_url) or "",
            title=video_data.get("title", ""),
            frames_analyzed=len(frames),
            analyses=frames,
            summary=summary,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
