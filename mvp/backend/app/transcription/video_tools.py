"""
Video processing tools.

Extract frames, audio tracks, and process video files
for Vision AI analysis and transcription.
"""

import asyncio
import os
import tempfile
from typing import Optional

import structlog

logger = structlog.get_logger()


class VideoToolsService:
    """Service for video processing and frame extraction."""

    @staticmethod
    async def extract_frames(
        video_path: str,
        interval_seconds: int = 30,
        max_frames: int = 20,
        output_dir: Optional[str] = None,
    ) -> list[dict]:
        """
        Extract key frames from a video at regular intervals.

        Useful for Vision AI analysis of video content.
        Uses moviepy for cross-platform compatibility.

        Returns list of {path, timestamp, index} dicts.
        """
        if not os.path.exists(video_path):
            return []

        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix="frames_")

        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                lambda: VideoToolsService._do_extract_frames(
                    video_path, interval_seconds, max_frames, output_dir
                ),
            )
        except Exception as e:
            logger.error("frame_extraction_failed", error=str(e))
            return []

    @staticmethod
    def _do_extract_frames(
        video_path: str,
        interval: int,
        max_frames: int,
        output_dir: str,
    ) -> list[dict]:
        """Synchronous frame extraction (runs in thread pool)."""
        try:
            from moviepy import VideoFileClip
        except ImportError:
            try:
                from moviepy.editor import VideoFileClip
            except ImportError:
                logger.warning("moviepy_not_installed")
                return []

        frames = []
        clip = VideoFileClip(video_path)

        try:
            duration = clip.duration
            timestamps = []
            t = 0
            while t < duration and len(timestamps) < max_frames:
                timestamps.append(t)
                t += interval

            for i, ts in enumerate(timestamps):
                frame_path = os.path.join(output_dir, f"frame_{i:04d}_{int(ts)}s.jpg")
                frame = clip.get_frame(ts)

                # Save frame using PIL
                try:
                    from PIL import Image
                    import numpy as np
                    img = Image.fromarray(frame.astype(np.uint8))
                    img.save(frame_path, "JPEG", quality=85)
                except ImportError:
                    # Fallback without PIL
                    import struct
                    # Skip if PIL not available
                    continue

                frames.append({
                    "path": frame_path,
                    "timestamp": round(ts, 2),
                    "index": i,
                })

        finally:
            clip.close()

        return frames

    @staticmethod
    async def extract_audio(
        video_path: str,
        output_format: str = "mp3",
        output_dir: Optional[str] = None,
    ) -> Optional[str]:
        """
        Extract audio track from a video file.

        Returns path to the extracted audio file.
        """
        if not os.path.exists(video_path):
            return None

        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix="audio_")

        base_name = os.path.splitext(os.path.basename(video_path))[0]
        output_path = os.path.join(output_dir, f"{base_name}.{output_format}")

        try:
            loop = asyncio.get_event_loop()

            def _extract():
                try:
                    from moviepy import VideoFileClip
                except ImportError:
                    from moviepy.editor import VideoFileClip

                clip = VideoFileClip(video_path)
                try:
                    clip.audio.write_audiofile(
                        output_path,
                        logger=None,
                    )
                finally:
                    clip.close()

            await loop.run_in_executor(None, _extract)

            if os.path.exists(output_path):
                return output_path
            return None

        except Exception as e:
            logger.error("audio_extraction_failed", error=str(e))
            return None

    @staticmethod
    async def analyze_video_frames(
        video_path: str,
        interval_seconds: int = 60,
        max_frames: int = 10,
        prompt: str = "Describe what is shown in this video frame.",
    ) -> list[dict]:
        """
        Extract frames from a video and analyze each with Gemini Vision.

        Returns list of {timestamp, description} dicts.
        """
        # Extract frames
        frames = await VideoToolsService.extract_frames(
            video_path,
            interval_seconds=interval_seconds,
            max_frames=max_frames,
        )

        if not frames:
            return []

        # Analyze each frame with Vision AI
        results = []
        for frame in frames:
            try:
                from app.modules.web_crawler.service import WebCrawlerService
                import base64

                # Read frame file
                with open(frame["path"], "rb") as f:
                    image_bytes = f.read()

                from app.config import settings
                if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "MOCK":
                    results.append({
                        "timestamp": frame["timestamp"],
                        "description": "[Vision analysis requires GEMINI_API_KEY]",
                    })
                    continue

                import google.generativeai as genai
                genai.configure(api_key=settings.GEMINI_API_KEY)

                model = genai.GenerativeModel("gemini-2.0-flash")
                image_part = {
                    "mime_type": "image/jpeg",
                    "data": base64.b64encode(image_bytes).decode("utf-8"),
                }

                response = model.generate_content([prompt, image_part])
                description = response.text if response.text else "No description"

                results.append({
                    "timestamp": frame["timestamp"],
                    "description": description,
                    "frame_path": frame["path"],
                })

            except Exception as e:
                results.append({
                    "timestamp": frame["timestamp"],
                    "description": f"Analysis failed: {str(e)[:100]}",
                })

        return results

    @staticmethod
    async def split_audio_by_chapters(
        audio_path: str,
        chapters: list[dict],
        output_dir: Optional[str] = None,
    ) -> list[dict]:
        """
        Split an audio file into segments based on chapter timestamps.

        Uses pydub for audio manipulation.
        """
        if not os.path.exists(audio_path):
            return []

        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix="chapters_")

        try:
            from pydub import AudioSegment

            loop = asyncio.get_event_loop()

            def _split():
                audio = AudioSegment.from_file(audio_path)
                segments = []

                for i, ch in enumerate(chapters):
                    start_ms = int(ch.get("start_time", 0) * 1000)
                    end_ms = int(ch.get("end_time", len(audio) / 1000) * 1000)

                    segment = audio[start_ms:end_ms]
                    segment_path = os.path.join(
                        output_dir,
                        f"chapter_{i:02d}_{ch.get('title', 'untitled')[:30]}.mp3"
                    )
                    segment.export(segment_path, format="mp3")

                    segments.append({
                        "path": segment_path,
                        "title": ch.get("title", ""),
                        "start_time": ch.get("start_time", 0),
                        "end_time": ch.get("end_time", 0),
                        "duration_ms": end_ms - start_ms,
                    })

                return segments

            return await loop.run_in_executor(None, _split)

        except ImportError:
            logger.warning("pydub_not_installed")
            return []
        except Exception as e:
            logger.error("audio_split_failed", error=str(e))
            return []
