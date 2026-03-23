"""
YouTube transcript extraction using youtube-transcript-api.

Gets existing subtitles from YouTube videos instantly and for free,
without downloading audio or using paid APIs.
"""

import re
from typing import Optional

import structlog

logger = structlog.get_logger()


def extract_video_id(url: str) -> Optional[str]:
    """Extract YouTube video ID from various URL formats."""
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com/shorts/([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


async def get_youtube_transcript(
    video_url: str,
    language: str = "auto",
) -> Optional[dict]:
    """
    Try to get existing YouTube subtitles.
    Returns transcript data or None if not available.

    This is instant and free - no audio download needed.
    """
    video_id = extract_video_id(video_url)
    if not video_id:
        return None

    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        # Determine language preferences
        if language == "auto":
            lang_codes = ["fr", "en", "es", "de", "ar", "pt", "it", "ja", "ko", "zh"]
        else:
            lang_codes = [language, "en", "fr"]

        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

            # Try manual transcripts first (more accurate)
            transcript = None
            for lang in lang_codes:
                try:
                    transcript = transcript_list.find_manually_created_transcript([lang])
                    break
                except Exception:
                    continue

            # Fall back to auto-generated
            if transcript is None:
                for lang in lang_codes:
                    try:
                        transcript = transcript_list.find_generated_transcript([lang])
                        break
                    except Exception:
                        continue

            if transcript is None:
                # Try any available transcript
                for t in transcript_list:
                    transcript = t
                    break

            if transcript is None:
                return None

            entries = transcript.fetch()

            # Build full text
            full_text = " ".join(entry.get("text", "") for entry in entries if entry.get("text"))

            # Calculate duration from last entry
            duration = 0
            if entries:
                last = entries[-1]
                duration = int(last.get("start", 0) + last.get("duration", 0))

            # Detect if manual or auto-generated
            is_manual = transcript.is_generated is False

            return {
                "text": full_text,
                "segments": [
                    {
                        "text": e.get("text", ""),
                        "start": e.get("start", 0),
                        "duration": e.get("duration", 0),
                    }
                    for e in entries
                ],
                "language": transcript.language_code,
                "duration_seconds": duration,
                "is_manual": is_manual,
                "confidence": 0.95 if is_manual else 0.80,
                "provider": "youtube_subtitles",
            }

        except Exception as e:
            logger.debug("youtube_transcript_not_available", video_id=video_id, error=str(e))
            return None

    except ImportError:
        logger.warning("youtube_transcript_api_not_installed")
        return None


async def get_youtube_metadata(video_url: str) -> Optional[dict]:
    """
    Extract full metadata from a YouTube video using yt-dlp.
    Returns title, description, tags, chapters, thumbnail, duration, etc.
    """
    video_id = extract_video_id(video_url)
    if not video_id:
        return None

    try:
        import yt_dlp

        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "extract_flat": False,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)

            if not info:
                return None

            # Extract chapters
            chapters = []
            for ch in (info.get("chapters") or []):
                chapters.append({
                    "title": ch.get("title", ""),
                    "start_time": ch.get("start_time", 0),
                    "end_time": ch.get("end_time", 0),
                })

            return {
                "video_id": video_id,
                "title": info.get("title", ""),
                "description": info.get("description", ""),
                "uploader": info.get("uploader", ""),
                "uploader_id": info.get("uploader_id", ""),
                "channel_url": info.get("channel_url", ""),
                "duration_seconds": info.get("duration", 0),
                "view_count": info.get("view_count", 0),
                "like_count": info.get("like_count", 0),
                "upload_date": info.get("upload_date", ""),
                "thumbnail": info.get("thumbnail", ""),
                "tags": info.get("tags") or [],
                "categories": info.get("categories") or [],
                "chapters": chapters,
                "language": info.get("language", ""),
                "is_live": info.get("is_live", False),
                "was_live": info.get("was_live", False),
            }

    except Exception as e:
        logger.error("youtube_metadata_failed", url=video_url, error=str(e))
        return None


async def get_playlist_videos(playlist_url: str, max_videos: int = 50) -> list[dict]:
    """
    Extract all video URLs from a YouTube playlist or channel.
    """
    try:
        import yt_dlp

        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "extract_flat": True,
            "playlistend": max_videos,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(playlist_url, download=False)

            if not info:
                return []

            entries = info.get("entries") or []
            videos = []
            for entry in entries:
                if entry and entry.get("id"):
                    videos.append({
                        "video_id": entry.get("id", ""),
                        "title": entry.get("title", ""),
                        "url": f"https://www.youtube.com/watch?v={entry['id']}",
                        "duration": entry.get("duration", 0),
                    })

            return videos

    except Exception as e:
        logger.error("playlist_extraction_failed", url=playlist_url, error=str(e))
        return []


async def download_video(
    video_url: str,
    output_dir: str = "/tmp",
    format_type: str = "best[height<=720]",
) -> Optional[dict]:
    """
    Download a full video file for Vision AI analysis.
    Returns path to downloaded file.
    """
    video_id = extract_video_id(video_url)
    if not video_id:
        return None

    try:
        import yt_dlp
        import os

        output_path = os.path.join(output_dir, f"{video_id}.%(ext)s")

        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "format": format_type,
            "outtmpl": output_path,
            "merge_output_format": "mp4",
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            filename = ydl.prepare_filename(info)

            # Fix extension to mp4
            if not filename.endswith(".mp4"):
                base = os.path.splitext(filename)[0]
                if os.path.exists(base + ".mp4"):
                    filename = base + ".mp4"

            return {
                "file_path": filename,
                "video_id": video_id,
                "title": info.get("title", ""),
                "duration": info.get("duration", 0),
                "format": info.get("format", ""),
                "filesize": os.path.getsize(filename) if os.path.exists(filename) else 0,
            }

    except Exception as e:
        logger.error("video_download_failed", url=video_url, error=str(e))
        return None
