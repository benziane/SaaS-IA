"""
Integration tests for the youtube_transcription module.

Tests route registration, schema validation, auth enforcement, and
graceful fallback behavior.
"""

import pytest
from unittest.mock import patch, AsyncMock


async def test_youtube_validate_requires_auth(client):
    """POST /api/youtube/validate returns 401 without auth token."""
    resp = await client.post(
        "/api/youtube/validate",
        json={"video_url": "https://youtube.com/watch?v=dQw4w9WgXcQ"}
    )
    assert resp.status_code == 401


async def test_youtube_validate_with_auth(client, auth_headers):
    """POST /api/youtube/validate returns 200 for valid YouTube URL."""
    resp = await client.post(
        "/api/youtube/validate",
        json={"video_url": "https://youtube.com/watch?v=dQw4w9WgXcQ"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "valid" in data
    assert data["valid"] is True
    assert data["video_id"] == "dQw4w9WgXcQ"


async def test_youtube_validate_invalid_url(client, auth_headers):
    """POST /api/youtube/validate returns valid=False for non-YouTube URL."""
    resp = await client.post(
        "/api/youtube/validate",
        json={"video_url": "https://example.com/not-youtube"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["valid"] is False


async def test_youtube_metadata_endpoint_exists(client, auth_headers):
    """POST /api/youtube/metadata is registered and reachable."""
    with patch(
        "app.transcription.youtube_transcript.get_youtube_metadata",
        new_callable=AsyncMock,
        return_value={
            "title": "Test Video",
            "uploader": "Test Channel",
            "duration_seconds": 120,
            "view_count": 1000,
            "like_count": 50,
            "thumbnail": "https://example.com/thumb.jpg",
            "is_live": False,
            "description": "Test description",
            "tags": ["test"],
            "chapters": [],
        }
    ):
        resp = await client.post(
            "/api/youtube/metadata",
            json={"video_url": "https://youtube.com/watch?v=dQw4w9WgXcQ"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Test Video"
        assert data["uploader"] == "Test Channel"


async def test_youtube_transcript_no_subtitles(client, auth_headers):
    """POST /api/youtube/transcript returns 422 when no subtitles available."""
    with patch(
        "app.transcription.youtube_transcript.get_youtube_transcript",
        new_callable=AsyncMock,
        return_value=None
    ):
        resp = await client.post(
            "/api/youtube/transcript",
            json={"video_url": "https://youtube.com/watch?v=dQw4w9WgXcQ", "language": "en"},
            headers=auth_headers,
        )
        assert resp.status_code == 422


async def test_youtube_module_manifest():
    """youtube_transcription manifest.json is valid and has correct prefix."""
    import json
    import os
    manifest_path = os.path.join(
        os.path.dirname(__file__),
        "../../app/modules/youtube_transcription/manifest.json"
    )
    with open(manifest_path) as f:
        manifest = json.load(f)
    assert manifest["name"] == "youtube_transcription"
    assert manifest["prefix"] == "/api/youtube"
    assert manifest["enabled"] is True
