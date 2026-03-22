"""
YouTube Service - Grade S++
Handles YouTube video processing and audio extraction
"""

import re
import os
import tempfile
import structlog
from typing import Optional, Tuple

logger = structlog.get_logger()

# ========================================================================
# YOUTUBE URL PATTERNS
# ========================================================================

# Regex patterns for YouTube URLs
YOUTUBE_PATTERNS = [
    r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?v=([a-zA-Z0-9_-]{11})',
    r'(?:https?:\/\/)?(?:www\.)?youtu\.be\/([a-zA-Z0-9_-]{11})',
    r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/embed\/([a-zA-Z0-9_-]{11})',
]


# ========================================================================
# YOUTUBE SERVICE
# ========================================================================

class YouTubeService:
    """Service for processing YouTube videos"""
    
    @staticmethod
    def extract_video_id(url: str) -> Optional[str]:
        """
        Extract YouTube video ID from URL
        
        Args:
            url: YouTube video URL
        
        Returns:
            str: Video ID (11 characters) or None if invalid
        
        Examples:
            >>> YouTubeService.extract_video_id("https://youtube.com/watch?v=pAwRgHoBHR0")
            'pAwRgHoBHR0'
            >>> YouTubeService.extract_video_id("https://youtu.be/pAwRgHoBHR0?si=xyz")
            'pAwRgHoBHR0'
        """
        for pattern in YOUTUBE_PATTERNS:
            match = re.search(pattern, url)
            if match:
                video_id = match.group(1)
                logger.info(
                    "youtube_video_id_extracted",
                    url=url,
                    video_id=video_id
                )
                return video_id
        
        logger.warning("youtube_invalid_url", url=url)
        return None
    
    @staticmethod
    def get_audio_url(video_url: str) -> str:
        """
        Get audio URL for AssemblyAI transcription
        
        AssemblyAI can directly transcribe YouTube videos by passing the video URL.
        No need to extract audio separately.
        
        Args:
            video_url: YouTube video URL
        
        Returns:
            str: The same URL (AssemblyAI handles YouTube URLs directly)
        
        Note:
            AssemblyAI supports direct YouTube URLs, so we just validate and return it.
        """
        video_id = YouTubeService.extract_video_id(video_url)
        
        if not video_id:
            raise ValueError(f"Invalid YouTube URL: {video_url}")
        
        # Normalize to standard YouTube URL format
        normalized_url = f"https://www.youtube.com/watch?v={video_id}"
        
        logger.info(
            "youtube_audio_url_prepared",
            original_url=video_url,
            normalized_url=normalized_url,
            video_id=video_id
        )
        
        return normalized_url
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """
        Validate if URL is a valid YouTube URL
        
        Args:
            url: URL to validate
        
        Returns:
            bool: True if valid YouTube URL, False otherwise
        """
        return YouTubeService.extract_video_id(url) is not None
    
    @staticmethod
    def download_audio(video_url: str) -> Tuple[str, dict]:
        """
        Download audio from YouTube video using yt-dlp
        
        Args:
            video_url: YouTube video URL
        
        Returns:
            Tuple[str, dict]: (audio_file_path, metadata)
        
        Raises:
            RuntimeError: If download fails
        """
        from .debug_logger import get_debug_logger
        debug = get_debug_logger()
        
        try:
            import yt_dlp
            
            video_id = YouTubeService.extract_video_id(video_url)
            if not video_id:
                raise ValueError(f"Invalid YouTube URL: {video_url}")
            
            # Create temp directory for audio file
            temp_dir = tempfile.mkdtemp(prefix="youtube_audio_")
            output_template = os.path.join(temp_dir, f"{video_id}.%(ext)s")
            
            # yt-dlp options (download best audio, no conversion)
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': output_template,
                'quiet': True,
                'no_warnings': True,
            }
            
            logger.info(
                "youtube_download_start",
                video_url=video_url,
                video_id=video_id,
                temp_dir=temp_dir
            )
            
            if debug:
                debug.log_youtube_download_start(temp_dir)
            
            # Download audio
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                
                # Get metadata
                metadata = {
                    'title': info.get('title'),
                    'duration': info.get('duration'),
                    'uploader': info.get('uploader'),
                    'upload_date': info.get('upload_date'),
                }
                
                # Find the downloaded file (extension can vary: webm, m4a, opus, etc.)
                downloaded_file = ydl.prepare_filename(info)
                
                if not os.path.exists(downloaded_file):
                    # Try to find any file in temp_dir
                    files = [f for f in os.listdir(temp_dir) if f.startswith(video_id)]
                    if not files:
                        raise RuntimeError(f"Audio file not found in: {temp_dir}")
                    downloaded_file = os.path.join(temp_dir, files[0])
                
                audio_file = downloaded_file
                
                file_size = os.path.getsize(audio_file)
                
                logger.info(
                    "youtube_download_success",
                    video_id=video_id,
                    audio_file=audio_file,
                    file_size=file_size,
                    duration=metadata.get('duration')
                )
                
                # Note: log_youtube_download_complete is called in service.py with job_id
                
                return audio_file, metadata
                
        except Exception as e:
            logger.error(
                "youtube_download_error",
                video_url=video_url,
                error=str(e)
            )
            raise RuntimeError(f"YouTube audio download failed: {str(e)}")


# ========================================================================
# EXPORTS
# ========================================================================

__all__ = ["YouTubeService"]

