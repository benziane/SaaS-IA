"""
Video Generation service - AI video creation, clips, avatars.

Supports text-to-video, highlight clips from transcriptions,
talking avatars, and explainer videos.
"""

import asyncio
import json
import os
import tempfile
from datetime import datetime
from typing import Optional
from uuid import UUID

import structlog
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.video_gen import GeneratedVideo, VideoProject, VideoStatus, VideoType

try:
    import ffmpeg
    HAS_FFMPEG = True
except ImportError:
    HAS_FFMPEG = False

logger = structlog.get_logger()


class VideoGenService:
    """Service for AI video generation."""

    @staticmethod
    async def generate_video(
        user_id: UUID, title: str, prompt: str, video_type: str,
        provider: str, duration_s: float, width: int, height: int,
        session: AsyncSession, style: Optional[str] = None,
        source_type: Optional[str] = None, source_id: Optional[str] = None,
        project_id: Optional[str] = None, settings: Optional[dict] = None,
    ) -> GeneratedVideo:
        """Generate a video from text prompt."""
        vtype = VideoType(video_type) if video_type in [v.value for v in VideoType] else VideoType.TEXT_TO_VIDEO

        video = GeneratedVideo(
            user_id=user_id,
            title=title,
            video_type=vtype,
            prompt=prompt[:5000],
            provider=provider,
            source_type=source_type,
            source_id=source_id,
            width=width,
            height=height,
            status=VideoStatus.GENERATING,
            settings_json=json.dumps(settings or {}, ensure_ascii=False),
        )
        session.add(video)
        await session.flush()

        try:
            result = await VideoGenService._call_provider(
                prompt=prompt, provider=provider, video_type=video_type,
                duration_s=duration_s, width=width, height=height,
                style=style, settings=settings,
            )
            video.video_url = result.get("url", "")
            video.thumbnail_url = result.get("thumbnail_url", "")
            video.duration_s = result.get("duration_s", duration_s)
            video.description = result.get("description", "")
            video.status = VideoStatus.COMPLETED

        except Exception as e:
            video.status = VideoStatus.FAILED
            video.error = str(e)[:1000]
            logger.error("video_generation_failed", error=str(e))

        session.add(video)

        if project_id:
            try:
                from uuid import UUID as UUIDType
                project = await session.get(VideoProject, UUIDType(project_id))
                if project and project.user_id == user_id:
                    project.video_count += 1
                    project.total_duration_s += video.duration_s or 0
                    session.add(project)
            except (ValueError, Exception) as e:
                logger.warning("project_id_parse_failed", project_id=project_id, error=str(e))

        await session.commit()
        await session.refresh(video)

        logger.info("video_generated", video_id=str(video.id), type=video_type)
        return video

    @staticmethod
    async def generate_clips(
        user_id: UUID, transcription_id: str, max_clips: int,
        clip_duration_s: float, format_type: str, provider: str,
        session: AsyncSession,
    ) -> list[GeneratedVideo]:
        """Generate highlight clips from a transcription."""
        from app.models.transcription import Transcription
        from uuid import UUID as UUIDType

        t = await session.get(Transcription, UUIDType(transcription_id))
        if not t or t.user_id != user_id:
            return []

        text = t.transcription_text or ""
        if not text:
            return []

        # Use AI to identify key moments
        try:
            from app.ai_assistant.service import AIAssistantService
            result = await AIAssistantService.process_text_with_provider(
                text=f"""Identify the {max_clips} most interesting/viral moments from this transcription.
For each moment, provide:
- A short title (max 50 chars)
- A visual description for video generation (max 200 chars)
- Why it's interesting

Transcription: {text[:8000]}

Respond with a JSON array: [{{"title": "...", "visual_prompt": "...", "reason": "..."}}]""",
                task="analysis",
                provider_name="gemini",
                user_id=user_id,
                module="video_gen",
            )

            response = result.get("processed_text", "[]")
            start = response.find("[")
            end = response.rfind("]") + 1
            moments = json.loads(response[start:end]) if start >= 0 and end > start else []

        except Exception:
            moments = [{"title": f"Highlight {i+1}", "visual_prompt": text[:200], "reason": ""} for i in range(min(max_clips, 3))]

        clips = []
        for moment in moments[:max_clips]:
            clip = await VideoGenService.generate_video(
                user_id=user_id,
                title=moment.get("title", "Clip"),
                prompt=moment.get("visual_prompt", ""),
                video_type="clip_highlights",
                provider=provider,
                duration_s=clip_duration_s,
                width=1080,
                height=1920 if format_type == "short_form" else 1080,
                session=session,
                source_type="transcription",
                source_id=transcription_id,
            )
            clips.append(clip)

        return clips

    @staticmethod
    async def generate_avatar_video(
        user_id: UUID, text: str, avatar_style: str,
        voice_id: Optional[str], background: str, provider: str,
        session: AsyncSession,
    ) -> GeneratedVideo:
        """Generate a talking avatar video."""
        return await VideoGenService.generate_video(
            user_id=user_id,
            title=f"Avatar: {text[:50]}",
            prompt=text,
            video_type="avatar_talking",
            provider=provider,
            duration_s=len(text.split()) * 0.4,  # rough estimate
            width=1080,
            height=1080,
            session=session,
            settings={"avatar_style": avatar_style, "voice_id": voice_id, "background": background},
        )

    @staticmethod
    async def generate_from_source(
        user_id: UUID, source_type: str, source_id: str,
        video_type: str, title: Optional[str], provider: str,
        duration_s: float, session: AsyncSession,
    ) -> GeneratedVideo:
        """Generate video from transcription, document, or content."""
        text = ""
        if source_type == "transcription":
            from app.models.transcription import Transcription
            from uuid import UUID as UUIDType
            t = await session.get(Transcription, UUIDType(source_id))
            if t and t.user_id == user_id:
                text = t.transcription_text or ""
        elif source_type == "document":
            from app.models.knowledge import DocumentChunk
            from uuid import UUID as UUIDType
            result = await session.execute(
                select(DocumentChunk).where(DocumentChunk.document_id == UUIDType(source_id))
                .order_by(DocumentChunk.chunk_index)
            )
            chunks = result.scalars().all()
            text = "\n\n".join(c.content for c in chunks)

        if not text:
            video = GeneratedVideo(
                user_id=user_id, title=title or "Video", video_type=VideoType(video_type),
                provider=provider, status=VideoStatus.FAILED,
                error="No source content found",
            )
            session.add(video)
            await session.commit()
            await session.refresh(video)
            return video

        # Generate visual prompt from text
        try:
            from app.ai_assistant.service import AIAssistantService
            result = await AIAssistantService.process_text_with_provider(
                text=f"Create a visual scene description for a {video_type.replace('_', ' ')} video based on: {text[:3000]}",
                task="creative",
                provider_name="gemini",
                user_id=user_id,
                module="video_gen",
            )
            visual_prompt = result.get("processed_text", text[:500])
        except Exception:
            visual_prompt = text[:500]

        return await VideoGenService.generate_video(
            user_id=user_id, title=title or f"Video from {source_type}",
            prompt=visual_prompt, video_type=video_type, provider=provider,
            duration_s=duration_s, width=1920, height=1080, session=session,
            source_type=source_type, source_id=source_id,
        )

    @staticmethod
    async def list_videos(
        user_id: UUID, session: AsyncSession, skip: int = 0, limit: int = 20,
    ) -> list[GeneratedVideo]:
        result = await session.execute(
            select(GeneratedVideo).where(GeneratedVideo.user_id == user_id)
            .order_by(GeneratedVideo.created_at.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def delete_video(video_id: UUID, user_id: UUID, session: AsyncSession) -> bool:
        v = await session.get(GeneratedVideo, video_id)
        if not v or v.user_id != user_id:
            return False
        await session.delete(v)
        await session.commit()
        return True

    @staticmethod
    async def create_project(
        user_id: UUID, name: str, description: Optional[str], session: AsyncSession,
    ) -> VideoProject:
        project = VideoProject(user_id=user_id, name=name, description=description)
        session.add(project)
        await session.commit()
        await session.refresh(project)
        return project

    @staticmethod
    async def list_projects(user_id: UUID, session: AsyncSession) -> list[VideoProject]:
        result = await session.execute(
            select(VideoProject).where(VideoProject.user_id == user_id)
            .order_by(VideoProject.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def _call_provider(
        prompt: str, provider: str, video_type: str,
        duration_s: float, width: int, height: int,
        style: Optional[str] = None, settings: Optional[dict] = None,
    ) -> dict:
        """Call video generation provider. Mock for MVP."""
        logger.info("video_gen_mock", provider=provider, type=video_type, duration=duration_s)
        return {
            "url": f"/api/videos/placeholder/{width}x{height}/{duration_s}s.mp4",
            "thumbnail_url": f"/api/videos/placeholder/{width}x{height}/thumb.jpg",
            "duration_s": duration_s,
            "description": f"Generated {video_type} video ({duration_s}s)",
        }

    # ── ffmpeg-python processing methods ──────────────────────────

    @staticmethod
    async def _add_subtitles(video_path: str, srt_path: str, output_path: str) -> str:
        """Burn subtitles onto a video using ffmpeg. Returns output path or original if unavailable."""
        if not HAS_FFMPEG:
            logger.warning("ffmpeg_not_available", method="_add_subtitles")
            return video_path
        try:
            escaped_srt = srt_path.replace("\\", "/").replace(":", "\\:")
            stream = (
                ffmpeg
                .input(video_path)
                .output(output_path, vf=f"subtitles={escaped_srt}")
                .overwrite_output()
            )
            await asyncio.to_thread(stream.run, quiet=True)
            logger.info("subtitles_added", video=video_path, srt=srt_path, output=output_path)
            return output_path
        except Exception as e:
            logger.error("add_subtitles_failed", error=str(e), video=video_path)
            return video_path

    @staticmethod
    async def _extract_clip(video_path: str, start_s: float, duration_s: float, output_path: str) -> str:
        """Extract a clip from a video using ffmpeg. Returns output path."""
        if not HAS_FFMPEG:
            logger.warning("ffmpeg_not_available", method="_extract_clip")
            return video_path
        try:
            stream = (
                ffmpeg
                .input(video_path, ss=start_s, t=duration_s)
                .output(output_path, c="copy")
                .overwrite_output()
            )
            await asyncio.to_thread(stream.run, quiet=True)
            logger.info("clip_extracted", video=video_path, start=start_s, duration=duration_s, output=output_path)
            return output_path
        except Exception as e:
            logger.error("extract_clip_failed", error=str(e), video=video_path)
            return video_path

    @staticmethod
    async def _concat_clips(clip_paths: list[str], output_path: str) -> str:
        """Concatenate multiple clips into one video using ffmpeg concat demuxer."""
        if not HAS_FFMPEG:
            logger.warning("ffmpeg_not_available", method="_concat_clips")
            return clip_paths[0] if clip_paths else ""
        try:
            concat_file = os.path.join(tempfile.gettempdir(), "ffmpeg_concat_list.txt")

            def _run_concat():
                with open(concat_file, "w") as f:
                    for path in clip_paths:
                        safe = path.replace("\\", "/").replace("'", "'\\''")
                        f.write(f"file '{safe}'\n")
                (
                    ffmpeg
                    .input(concat_file, format="concat", safe=0)
                    .output(output_path, c="copy")
                    .overwrite_output()
                    .run(quiet=True)
                )
                os.remove(concat_file)

            await asyncio.to_thread(_run_concat)
            logger.info("clips_concatenated", count=len(clip_paths), output=output_path)
            return output_path
        except Exception as e:
            logger.error("concat_clips_failed", error=str(e))
            return clip_paths[0] if clip_paths else ""

    @staticmethod
    async def _add_audio_track(video_path: str, audio_path: str, output_path: str) -> str:
        """Mix an audio track onto a video (e.g. TTS dubbing) using ffmpeg."""
        if not HAS_FFMPEG:
            logger.warning("ffmpeg_not_available", method="_add_audio_track")
            return video_path
        try:
            video_in = ffmpeg.input(video_path)
            audio_in = ffmpeg.input(audio_path)
            stream = (
                ffmpeg
                .output(video_in.video, audio_in.audio, output_path, vcodec="copy", acodec="aac", shortest=None)
                .overwrite_output()
            )
            await asyncio.to_thread(stream.run, quiet=True)
            logger.info("audio_track_added", video=video_path, audio=audio_path, output=output_path)
            return output_path
        except Exception as e:
            logger.error("add_audio_track_failed", error=str(e), video=video_path)
            return video_path

    @staticmethod
    async def _get_video_info(video_path: str) -> dict:
        """Get video metadata using ffmpeg.probe(). Returns duration, dimensions, codec, fps, file_size."""
        if not HAS_FFMPEG:
            logger.warning("ffmpeg_not_available", method="_get_video_info")
            return {}
        try:
            probe = await asyncio.to_thread(ffmpeg.probe, video_path)
            video_stream = next(
                (s for s in probe.get("streams", []) if s.get("codec_type") == "video"),
                {},
            )
            format_info = probe.get("format", {})

            fps_raw = video_stream.get("r_frame_rate", "0/1")
            try:
                num, den = fps_raw.split("/")
                fps = round(int(num) / int(den), 2) if int(den) else 0.0
            except (ValueError, ZeroDivisionError):
                fps = 0.0

            info = {
                "duration": float(format_info.get("duration", 0)),
                "width": int(video_stream.get("width", 0)),
                "height": int(video_stream.get("height", 0)),
                "codec": video_stream.get("codec_name", "unknown"),
                "fps": fps,
                "file_size": int(format_info.get("size", 0)),
            }
            logger.info("video_info_retrieved", path=video_path, info=info)
            return info
        except Exception as e:
            logger.error("get_video_info_failed", error=str(e), path=video_path)
            return {}
