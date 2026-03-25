"""
Live stream capture and recording service.

Uses yt-dlp and streamlink to capture live streams from YouTube, Twitch, etc.
Records a segment and returns the file path for transcription.
"""

import asyncio
import os
import tempfile
from datetime import UTC, datetime
from typing import Optional

import structlog

logger = structlog.get_logger()


class LiveStreamService:
    """Service for capturing and processing live streams."""

    @staticmethod
    async def capture_stream(
        stream_url: str,
        duration_seconds: int = 300,
        output_dir: str = "/tmp",
    ) -> Optional[dict]:
        """
        Capture a segment of a live stream.

        Tries yt-dlp first (YouTube Live), then streamlink (Twitch, etc.).

        Args:
            stream_url: URL of the live stream
            duration_seconds: How many seconds to record (default: 5 min, max: 30 min)
            output_dir: Where to save the recording
        """
        duration_seconds = min(duration_seconds, 1800)  # Max 30 min

        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"livestream_{timestamp}.mp4")

        # Try yt-dlp first (works great for YouTube Live)
        result = await LiveStreamService._capture_with_ytdlp(
            stream_url, duration_seconds, output_file
        )
        if result:
            return result

        # Fallback to streamlink (Twitch, other platforms)
        result = await LiveStreamService._capture_with_streamlink(
            stream_url, duration_seconds, output_file
        )
        if result:
            return result

        return {
            "success": False,
            "error": "Could not capture stream. Ensure the URL is a valid live stream.",
        }

    @staticmethod
    async def _capture_with_ytdlp(
        url: str, duration: int, output_file: str
    ) -> Optional[dict]:
        """Capture live stream using yt-dlp."""
        try:
            import yt_dlp

            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "format": "best[height<=720]",
                "outtmpl": output_file,
                "live_from_start": False,
                "match_filter": None,
            }

            # Check if it's actually a live stream
            with yt_dlp.YoutubeDL({"quiet": True, "skip_download": True}) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info:
                    return None
                is_live = info.get("is_live", False)
                if not is_live:
                    return None
                title = info.get("title", "")

            # Use ffmpeg to limit duration
            # yt-dlp doesn't have native duration limit for live
            # So we use a subprocess with timeout
            loop = asyncio.get_event_loop()

            def _download():
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url])
                except Exception:
                    pass

            # Run download with timeout
            try:
                await asyncio.wait_for(
                    loop.run_in_executor(None, _download),
                    timeout=duration + 10,
                )
            except asyncio.TimeoutError:
                pass  # Expected - we stop after duration

            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                return {
                    "success": True,
                    "file_path": output_file,
                    "title": title,
                    "duration_seconds": duration,
                    "file_size": file_size,
                    "capture_method": "yt-dlp",
                    "url": url,
                }

            # Try with .mkv extension
            mkv_file = output_file.replace(".mp4", ".mkv")
            webm_file = output_file.replace(".mp4", ".webm")
            for alt_file in [mkv_file, webm_file]:
                if os.path.exists(alt_file):
                    return {
                        "success": True,
                        "file_path": alt_file,
                        "title": title,
                        "duration_seconds": duration,
                        "file_size": os.path.getsize(alt_file),
                        "capture_method": "yt-dlp",
                        "url": url,
                    }

            return None

        except Exception as e:
            logger.debug("ytdlp_livestream_failed", url=url, error=str(e))
            return None

    @staticmethod
    async def _capture_with_streamlink(
        url: str, duration: int, output_file: str
    ) -> Optional[dict]:
        """Capture live stream using streamlink."""
        try:
            import streamlink

            streams = streamlink.streams(url)
            if not streams:
                return None

            # Get best available quality (prefer 720p)
            quality = None
            for q in ["720p", "480p", "best", "worst"]:
                if q in streams:
                    quality = q
                    break

            if not quality:
                quality = list(streams.keys())[0]

            stream = streams[quality]
            fd = stream.open()

            # Read stream data for specified duration
            loop = asyncio.get_event_loop()

            def _record():
                chunk_size = 8192
                bytes_written = 0
                max_bytes = 50 * 1024 * 1024  # 50MB max

                with open(output_file, "wb") as f:
                    import time
                    start = time.time()
                    while time.time() - start < duration and bytes_written < max_bytes:
                        try:
                            data = fd.read(chunk_size)
                            if not data:
                                break
                            f.write(data)
                            bytes_written += len(data)
                        except Exception:
                            break
                fd.close()
                return bytes_written

            bytes_written = await asyncio.wait_for(
                loop.run_in_executor(None, _record),
                timeout=duration + 30,
            )

            if os.path.exists(output_file) and bytes_written > 0:
                return {
                    "success": True,
                    "file_path": output_file,
                    "title": f"Live stream from {url}",
                    "duration_seconds": duration,
                    "file_size": bytes_written,
                    "capture_method": "streamlink",
                    "quality": quality,
                    "url": url,
                }

            return None

        except ImportError:
            logger.debug("streamlink_not_installed")
            return None
        except Exception as e:
            logger.debug("streamlink_capture_failed", url=url, error=str(e))
            return None

    @staticmethod
    async def check_stream_status(url: str) -> dict:
        """
        Check if a URL is a live stream and return its status.
        """
        try:
            import yt_dlp

            with yt_dlp.YoutubeDL({"quiet": True, "skip_download": True}) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info:
                    return {"is_live": False, "error": "Could not extract info"}

                return {
                    "is_live": info.get("is_live", False),
                    "was_live": info.get("was_live", False),
                    "title": info.get("title", ""),
                    "uploader": info.get("uploader", ""),
                    "concurrent_viewers": info.get("concurrent_view_count"),
                    "url": url,
                }

        except Exception as e:
            return {"is_live": False, "error": str(e)[:200]}
