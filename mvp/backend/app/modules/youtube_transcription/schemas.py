"""
YouTube transcription module schemas.
"""

from typing import Optional

from pydantic import BaseModel


class YouTubeURLRequest(BaseModel):
    video_url: str
    language: str = "auto"


class PlaylistRequest(BaseModel):
    playlist_url: str
    language: str = "auto"
    max_videos: int = 50


class StreamRequest(BaseModel):
    stream_url: str
    duration_seconds: int = 300


class VideoAnalyzeRequest(BaseModel):
    video_url: str
    interval_seconds: int = 30
    max_frames: int = 10
    prompt: str = "Describe what is happening in this video frame"


class TranscriptResult(BaseModel):
    video_id: str
    text: str
    language: str
    duration_seconds: float
    provider: str
    is_manual: bool = False


class MetadataResult(BaseModel):
    video_id: str
    title: str
    uploader: str
    duration_seconds: float
    view_count: int
    like_count: int
    thumbnail: Optional[str]
    is_live: bool
    description: str
    tags: list[str]
    chapters: list[dict]


class PlaylistResult(BaseModel):
    success: bool
    total: int
    transcribed: int
    results: list[dict]


class StreamStatusResult(BaseModel):
    is_live: bool
    was_live: bool
    title: str
    uploader: str
    concurrent_viewers: Optional[int]
    url: str
    error: Optional[str]


class StreamCaptureResult(BaseModel):
    success: bool
    url: str
    title: str
    duration_seconds: float
    capture_method: str
    transcript: Optional[str]
    provider: Optional[str]
    error: Optional[str]


class VideoFrameResult(BaseModel):
    timestamp: float
    description: str


class VideoAnalyzeResult(BaseModel):
    video_id: str
    title: str
    frames_analyzed: int
    analyses: list[VideoFrameResult]
    summary: str


class ValidateResult(BaseModel):
    valid: bool
    video_id: Optional[str]
    url: str
