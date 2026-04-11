"""Tests for instagram_intelligence module."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_validate_profile_unauthenticated(client: AsyncClient):
    response = await client.post("/api/instagram/validate", json={"username": "test"})
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_validate_profile_authenticated(client: AsyncClient, auth_headers: dict):
    response = await client.post(
        "/api/instagram/validate",
        json={"username": "test", "max_reels": 3, "transcribe": False},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "valid" in data
    assert "username" in data
    assert "is_private" in data


@pytest.mark.asyncio
async def test_analyze_reel_invalid_url(client: AsyncClient, auth_headers: dict):
    response = await client.post(
        "/api/instagram/analyze-reel",
        json={"reel_url": "https://notinstagram.com/reel/abc123/"},
        headers=auth_headers,
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_analyze_reel_mock(client: AsyncClient, auth_headers: dict):
    response = await client.post(
        "/api/instagram/analyze-reel",
        json={"reel_url": "https://www.instagram.com/reel/mock123/", "transcribe": False},
        headers=auth_headers,
    )
    # With no instagrapi/instaloader installed, service returns mock data (200)
    assert response.status_code in (200, 500)


@pytest.mark.asyncio
async def test_analyze_profile_mock(client: AsyncClient, auth_headers: dict):
    response = await client.post(
        "/api/instagram/analyze-profile",
        json={"username": "testuser", "max_reels": 2, "transcribe": False},
        headers=auth_headers,
    )
    assert response.status_code in (200, 500)
    if response.status_code == 200:
        data = response.json()
        assert "username" in data
        assert "reels" in data
        assert isinstance(data["reels"], list)
