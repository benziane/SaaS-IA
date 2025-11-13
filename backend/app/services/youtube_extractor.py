"""
Service for extracting audio from YouTube videos
"""
import os
import re
import asyncio
from typing import Dict, Optional, Tuple
from pathlib import Path
import yt_dlp
from app.core.config import settings


class YouTubeExtractor:
    """Service for downloading and extracting audio from YouTube videos"""

    def __init__(self, upload_dir: str = None):
        """
        Initialize YouTube extractor

        Args:
            upload_dir: Directory to store downloaded audio files
        """
        self.upload_dir = Path(upload_dir or settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def extract_video_id(url: str) -> Optional[str]:
        """
        Extract video ID from YouTube URL

        Args:
            url: YouTube video URL

        Returns:
            Video ID or None if invalid
        """
        patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
            r'(?:embed\/)([0-9A-Za-z_-]{11})',
            r'(?:watch\?v=)([0-9A-Za-z_-]{11})',
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return None

    async def get_video_info(self, url: str) -> Dict:
        """
        Get video metadata without downloading

        Args:
            url: YouTube video URL

        Returns:
            Dictionary with video information

        Raises:
            Exception: If video info cannot be retrieved
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
        }

        try:
            loop = asyncio.get_event_loop()
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = await loop.run_in_executor(
                    None,
                    lambda: ydl.extract_info(url, download=False)
                )

                return {
                    'video_id': info.get('id'),
                    'title': info.get('title'),
                    'duration': info.get('duration'),
                    'channel': info.get('uploader') or info.get('channel'),
                    'description': info.get('description'),
                    'thumbnail': info.get('thumbnail'),
                    'upload_date': info.get('upload_date'),
                    'view_count': info.get('view_count'),
                }

        except Exception as e:
            raise Exception(f"Failed to get video info: {str(e)}")

    async def download_audio(
        self,
        url: str,
        video_id: Optional[str] = None,
        progress_callback=None
    ) -> Tuple[str, Dict]:
        """
        Download audio from YouTube video

        Args:
            url: YouTube video URL
            video_id: Optional video ID (will be extracted if not provided)
            progress_callback: Optional callback for download progress

        Returns:
            Tuple of (audio_file_path, video_info)

        Raises:
            Exception: If download fails
        """
        if not video_id:
            video_id = self.extract_video_id(url)

        if not video_id:
            raise ValueError("Invalid YouTube URL")

        output_path = self.upload_dir / f"{video_id}.%(ext)s"

        def progress_hook(d):
            if progress_callback and d['status'] == 'downloading':
                try:
                    percent = d.get('_percent_str', '0%').strip('%')
                    progress_callback(float(percent))
                except:
                    pass

        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': str(output_path),
            'quiet': False,
            'no_warnings': True,
            'progress_hooks': [progress_hook] if progress_callback else [],
        }

        try:
            loop = asyncio.get_event_loop()

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Download and extract info
                info = await loop.run_in_executor(
                    None,
                    lambda: ydl.extract_info(url, download=True)
                )

                # Get the actual output file path
                audio_file = self.upload_dir / f"{video_id}.mp3"

                if not audio_file.exists():
                    raise Exception("Audio file not found after download")

                video_info = {
                    'video_id': info.get('id'),
                    'title': info.get('title'),
                    'duration': info.get('duration'),
                    'channel': info.get('uploader') or info.get('channel'),
                    'description': info.get('description'),
                    'thumbnail': info.get('thumbnail'),
                }

                return str(audio_file), video_info

        except Exception as e:
            raise Exception(f"Failed to download audio: {str(e)}")

    async def cleanup_audio(self, file_path: str) -> None:
        """
        Delete audio file

        Args:
            file_path: Path to audio file
        """
        try:
            if os.path.exists(file_path):
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    os.remove,
                    file_path
                )
        except Exception as e:
            print(f"Failed to cleanup audio file: {str(e)}")

    def get_supported_formats(self) -> list:
        """
        Get list of supported audio formats

        Returns:
            List of supported formats
        """
        return ['mp3', 'wav', 'm4a', 'webm', 'ogg']
