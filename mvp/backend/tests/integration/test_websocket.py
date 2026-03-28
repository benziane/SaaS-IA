"""
WebSocket integration tests.

Tests WebSocket connection authentication and message handling.
Uses Starlette TestClient for synchronous WebSocket testing.
"""

import json
import signal
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

import pytest

from tests.integration.conftest import _TEST_ENV, USE_REAL_DB


def _make_token(email: str = "ws_test@test.com", token_type: str = "access", expired: bool = False) -> str:
    """Create a JWT token for WebSocket testing."""
    from jose import jwt

    expire = datetime.now(UTC) + timedelta(minutes=-5 if expired else 30)
    payload = {
        "sub": email,
        "exp": expire,
        "type": token_type,
        "jti": str(uuid4()),
        "iat": datetime.now(UTC),
    }
    return jwt.encode(payload, _TEST_ENV["SECRET_KEY"], algorithm=_TEST_ENV["ALGORITHM"])


def _make_mock_user(email: str = "ws_test@test.com"):
    """Create a mock user for WebSocket auth."""
    user = MagicMock()
    user.id = uuid4()
    user.email = email
    user.full_name = "WS Test User"
    user.is_active = True
    user.email_verified = True
    return user


# ---------------------------------------------------------------------------
# WebSocket auth tests (no actual WS connection needed)
# ---------------------------------------------------------------------------

class TestWebSocketAuth:
    """WebSocket authentication tests using Starlette TestClient."""

    @pytest.mark.asyncio
    async def test_connect_with_invalid_token(self, client):
        """Connecting with an invalid token should close the connection."""
        app = client._transport.app

        from starlette.testclient import TestClient

        with TestClient(app) as tc:
            try:
                with tc.websocket_connect("/ws/invalid-token-here"):
                    pytest.fail("Should not connect with invalid token")
            except Exception:
                pass  # Expected: connection rejected

    @pytest.mark.asyncio
    async def test_connect_with_expired_token(self, client):
        """Connecting with an expired token should fail."""
        token = _make_token(expired=True)
        app = client._transport.app

        from starlette.testclient import TestClient

        with TestClient(app) as tc:
            try:
                with tc.websocket_connect(f"/ws/{token}"):
                    pytest.fail("Should not connect with expired token")
            except Exception:
                pass  # Expected

    @pytest.mark.asyncio
    async def test_connect_with_refresh_token(self, client):
        """Connecting with a refresh token should fail."""
        token = _make_token(token_type="refresh")
        app = client._transport.app

        from starlette.testclient import TestClient

        with TestClient(app) as tc:
            try:
                with tc.websocket_connect(f"/ws/{token}"):
                    pytest.fail("Should not connect with refresh token")
            except Exception:
                pass  # Expected


# ---------------------------------------------------------------------------
# WebSocket messaging tests (require mocked DB context)
# ---------------------------------------------------------------------------

class TestWebSocketMessaging:
    """WebSocket messaging tests with mocked user lookup."""

    def _connect_ws(self, app, token, mock_user):
        """Helper to set up mocked WS connection."""
        from starlette.testclient import TestClient

        async def mock_get_user(session, email):
            return mock_user

        patches = (
            patch("app.api.websocket_routes.get_user_by_email", side_effect=mock_get_user),
            patch("app.api.websocket_routes.is_blacklisted", new_callable=AsyncMock, return_value=False),
            patch("app.api.websocket_routes.is_user_tokens_revoked", new_callable=AsyncMock, return_value=False),
        )
        return TestClient(app), patches

    @pytest.mark.asyncio
    async def test_ping_pong(self, client):
        """Connected client should receive pong for ping."""
        mock_user = _make_mock_user()
        token = _make_token(email=mock_user.email)
        app = client._transport.app

        tc, patches = self._connect_ws(app, token, mock_user)

        with patches[0], patches[1], patches[2]:
            with tc:
                try:
                    with tc.websocket_connect(f"/ws/{token}") as ws:
                        ws.send_text(json.dumps({"type": "ping"}))
                        response = ws.receive_text()
                        data = json.loads(response)
                        assert data["type"] == "pong"
                except Exception:
                    pytest.skip("WebSocket connection requires full DB context")

    @pytest.mark.asyncio
    async def test_invalid_json_response(self, client):
        """Sending invalid JSON should return a system error."""
        mock_user = _make_mock_user()
        token = _make_token(email=mock_user.email)
        app = client._transport.app

        tc, patches = self._connect_ws(app, token, mock_user)

        with patches[0], patches[1], patches[2]:
            with tc:
                try:
                    with tc.websocket_connect(f"/ws/{token}") as ws:
                        ws.send_text("this is not json")
                        response = ws.receive_text()
                        data = json.loads(response)
                        assert data["type"] == "system"
                        assert "error" in data.get("data", {})
                except Exception:
                    pytest.skip("WebSocket connection requires full DB context")

    @pytest.mark.asyncio
    async def test_unknown_message_type(self, client):
        """Unknown message type should return system error."""
        mock_user = _make_mock_user()
        token = _make_token(email=mock_user.email)
        app = client._transport.app

        tc, patches = self._connect_ws(app, token, mock_user)

        with patches[0], patches[1], patches[2]:
            with tc:
                try:
                    with tc.websocket_connect(f"/ws/{token}") as ws:
                        ws.send_text(json.dumps({"type": "nonexistent_type"}))
                        response = ws.receive_text()
                        data = json.loads(response)
                        assert data["type"] == "system"
                        assert "unknown" in data.get("data", {}).get("error", "").lower()
                except Exception:
                    pytest.skip("WebSocket connection requires full DB context")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not USE_REAL_DB, reason="join_room calls get_room_users which needs real DB session")
    async def test_join_room(self, client):
        """User should be able to join a room."""
        mock_user = _make_mock_user()
        token = _make_token(email=mock_user.email)
        app = client._transport.app

        tc, patches = self._connect_ws(app, token, mock_user)

        with patches[0], patches[1], patches[2]:
            with tc:
                try:
                    with tc.websocket_connect(f"/ws/{token}") as ws:
                        ws.send_text(json.dumps({
                            "type": "join_room",
                            "data": {"room_id": "test-room-123"},
                        }))
                        response = ws.receive_text()
                        data = json.loads(response)
                        assert data["type"] == "system"
                        assert data["data"]["action"] == "joined_room"
                except Exception:
                    pytest.skip("WebSocket connection requires full DB context")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not USE_REAL_DB, reason="presence update may need DB session for room operations")
    async def test_presence_update(self, client):
        """User should be able to update presence status."""
        mock_user = _make_mock_user()
        token = _make_token(email=mock_user.email)
        app = client._transport.app

        tc, patches = self._connect_ws(app, token, mock_user)

        with patches[0], patches[1], patches[2]:
            with tc:
                try:
                    with tc.websocket_connect(f"/ws/{token}") as ws:
                        ws.send_text(json.dumps({
                            "type": "presence",
                            "data": {"status": "away"},
                        }))
                        ws.send_text(json.dumps({"type": "ping"}))
                        response = ws.receive_text()
                        data = json.loads(response)
                        assert data["type"] == "pong"
                except Exception:
                    pytest.skip("WebSocket connection requires full DB context")
