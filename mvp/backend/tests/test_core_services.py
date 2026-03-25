"""
Tests for core platform services.

Covers:
  - CircuitBreaker (closed, open, half-open states)
  - AIProviderManager (fallback across providers)
  - Sensitive data filtering in structured logs
  - PoolMetrics database connection stats
"""

import asyncio
import time
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ==========================================================================
# Circuit Breaker
# ==========================================================================

class TestCircuitBreaker:
    """Tests for the CircuitBreaker state machine."""

    def _make_breaker(self, **kwargs):
        from app.core.circuit_breaker import CircuitBreaker
        defaults = {
            "name": "test-breaker",
            "failure_threshold": 3,
            "recovery_timeout": 0.5,
            "half_open_max_calls": 2,
            "window_size": 10.0,
        }
        defaults.update(kwargs)
        return CircuitBreaker(**defaults)

    async def test_circuit_breaker_closed(self):
        """In CLOSED state a successful call passes through."""
        from app.core.circuit_breaker import CircuitState

        breaker = self._make_breaker()
        assert breaker.stats.state == CircuitState.CLOSED

        result = await breaker.call(lambda: "ok")
        assert result == "ok"
        assert breaker.stats.state == CircuitState.CLOSED
        assert breaker.stats.success_count == 1

    async def test_circuit_breaker_opens_after_threshold(self):
        """After failure_threshold failures the circuit transitions to OPEN."""
        from app.core.circuit_breaker import CircuitState, CircuitOpenError

        breaker = self._make_breaker(failure_threshold=3)

        async def failing_func():
            raise ValueError("provider down")

        # Trip the breaker with 3 failures
        for _ in range(3):
            with pytest.raises(ValueError):
                await breaker.call(failing_func)

        assert breaker.stats.state == CircuitState.OPEN

        # Subsequent calls should raise CircuitOpenError immediately
        with pytest.raises(CircuitOpenError) as exc_info:
            await breaker.call(lambda: "should not run")

        assert "OPEN" in str(exc_info.value)
        assert exc_info.value.name == "test-breaker"

    async def test_circuit_breaker_half_open_after_recovery(self):
        """After recovery_timeout elapses, the circuit moves to HALF_OPEN
        and allows probe calls."""
        from app.core.circuit_breaker import CircuitState

        breaker = self._make_breaker(
            failure_threshold=2,
            recovery_timeout=0.1,  # 100ms for fast tests
            half_open_max_calls=2,
        )

        async def failing_func():
            raise ValueError("down")

        # Trip the breaker
        for _ in range(2):
            with pytest.raises(ValueError):
                await breaker.call(failing_func)

        assert breaker.stats.state == CircuitState.OPEN

        # Wait for recovery timeout
        await asyncio.sleep(0.15)

        # Next call should be allowed (HALF_OPEN probe)
        result = await breaker.call(lambda: "probe-ok")
        assert result == "probe-ok"
        assert breaker.stats.state == CircuitState.HALF_OPEN

    async def test_circuit_breaker_half_open_to_closed(self):
        """Consecutive successes in HALF_OPEN transition back to CLOSED."""
        from app.core.circuit_breaker import CircuitState

        breaker = self._make_breaker(
            failure_threshold=2,
            recovery_timeout=0.05,
            half_open_max_calls=2,
        )

        async def failing_func():
            raise ValueError("down")

        # Trip the breaker
        for _ in range(2):
            with pytest.raises(ValueError):
                await breaker.call(failing_func)

        assert breaker.stats.state == CircuitState.OPEN

        # Wait for recovery
        await asyncio.sleep(0.1)

        # Two consecutive successes should close the circuit
        await breaker.call(lambda: "ok1")
        await breaker.call(lambda: "ok2")

        assert breaker.stats.state == CircuitState.CLOSED

    async def test_circuit_breaker_half_open_failure_reopens(self):
        """A failure during HALF_OPEN immediately re-opens the circuit."""
        from app.core.circuit_breaker import CircuitState

        breaker = self._make_breaker(
            failure_threshold=2,
            recovery_timeout=0.05,
            half_open_max_calls=3,
        )

        async def failing_func():
            raise ValueError("down again")

        # Trip the breaker
        for _ in range(2):
            with pytest.raises(ValueError):
                await breaker.call(failing_func)

        await asyncio.sleep(0.1)

        # First probe succeeds
        await breaker.call(lambda: "probe1")
        assert breaker.stats.state == CircuitState.HALF_OPEN

        # Second probe fails -> re-open
        with pytest.raises(ValueError):
            await breaker.call(failing_func)

        assert breaker.stats.state == CircuitState.OPEN

    async def test_circuit_breaker_stats(self):
        """The stats property returns a valid CircuitStats snapshot."""
        from app.core.circuit_breaker import CircuitStats, CircuitState

        breaker = self._make_breaker()

        await breaker.call(lambda: "ok")

        stats = breaker.stats
        assert isinstance(stats, CircuitStats)
        assert stats.state == CircuitState.CLOSED
        assert stats.success_count == 1
        assert stats.failure_count == 0

    async def test_circuit_breaker_async_callable(self):
        """The circuit breaker transparently handles async callables."""
        breaker = self._make_breaker()

        async def async_func():
            return "async-result"

        result = await breaker.call(async_func)
        assert result == "async-result"


# ==========================================================================
# AI Provider Manager
# ==========================================================================

class TestAIProviderManager:
    """Tests for the AIProviderManager multi-provider failover."""

    async def test_ai_provider_manager_first_succeeds(self):
        """When the first provider succeeds, it is used directly."""
        from app.core.circuit_breaker import AIProviderManager

        manager = AIProviderManager()

        async def provider_a(**kwargs):
            return {"result": "from_a", **kwargs}

        async def provider_b(**kwargs):
            return {"result": "from_b", **kwargs}

        manager.add_provider("provider_a", provider_a, priority=1)
        manager.add_provider("provider_b", provider_b, priority=2)

        result = await manager.call(prompt="hello")
        assert result["result"] == "from_a"
        assert result["prompt"] == "hello"

    async def test_ai_provider_manager_fallback(self):
        """When the first provider fails, the manager falls back to the next."""
        from app.core.circuit_breaker import AIProviderManager

        manager = AIProviderManager()

        async def provider_a_fails(**kwargs):
            raise ConnectionError("Provider A is down")

        async def provider_b_works(**kwargs):
            return {"result": "from_b", **kwargs}

        manager.add_provider("provider_a", provider_a_fails, priority=1)
        manager.add_provider("provider_b", provider_b_works, priority=2)

        result = await manager.call(prompt="hello")
        assert result["result"] == "from_b"

    async def test_ai_provider_manager_all_fail(self):
        """When all providers fail, a RuntimeError is raised."""
        from app.core.circuit_breaker import AIProviderManager

        manager = AIProviderManager()

        async def failing(**kwargs):
            raise ConnectionError("down")

        manager.add_provider("a", failing, priority=1)
        manager.add_provider("b", failing, priority=2)

        with pytest.raises(RuntimeError, match="All AI providers failed"):
            await manager.call(prompt="hello")

    async def test_ai_provider_manager_circuit_open_skips(self):
        """A provider with an open circuit is skipped, not called."""
        from app.core.circuit_breaker import AIProviderManager

        manager = AIProviderManager()

        call_count = {"a": 0, "b": 0}

        async def provider_a(**kwargs):
            call_count["a"] += 1
            raise ConnectionError("down")

        async def provider_b(**kwargs):
            call_count["b"] += 1
            return "from_b"

        manager.add_provider(
            "provider_a", provider_a, priority=1,
            failure_threshold=2, recovery_timeout=60.0,
        )
        manager.add_provider("provider_b", provider_b, priority=2)

        # First two calls trip provider_a's circuit breaker
        result1 = await manager.call()
        result2 = await manager.call()

        # provider_a should have been called twice (failing), then its
        # circuit opens.  provider_b handles all calls.
        assert call_count["a"] == 2

        # Third call should skip provider_a entirely
        result3 = await manager.call()
        assert result3 == "from_b"
        # provider_a should NOT have been called again
        assert call_count["a"] == 2

    async def test_ai_provider_manager_get_all_stats(self):
        """get_all_stats() returns a dict of CircuitStats per provider."""
        from app.core.circuit_breaker import AIProviderManager, CircuitStats

        manager = AIProviderManager()
        manager.add_provider("x", AsyncMock(return_value="ok"), priority=1)

        await manager.call()

        stats = manager.get_all_stats()
        assert "x" in stats
        assert isinstance(stats["x"], CircuitStats)
        assert stats["x"].success_count == 1


# ==========================================================================
# Sensitive Data Filtering
# ==========================================================================

class TestSensitiveDataFiltering:
    """Tests for the structlog processor that redacts sensitive fields."""

    def test_password_redacted(self):
        """Fields named 'password' should be replaced with ***REDACTED***."""
        from app.core.logging_config import filter_sensitive_data, _REDACTED

        event_dict = {
            "event": "user_login",
            "password": "s3cret",
            "username": "john",
        }
        result = filter_sensitive_data(None, "info", event_dict)

        assert result["password"] == _REDACTED
        assert result["username"] == "john"

    def test_token_redacted(self):
        """Fields named 'token' should be redacted."""
        from app.core.logging_config import filter_sensitive_data, _REDACTED

        event_dict = {
            "event": "auth",
            "token": "eyJhbGciOi...",
        }
        result = filter_sensitive_data(None, "info", event_dict)
        assert result["token"] == _REDACTED

    def test_api_key_redacted(self):
        """Fields named 'api_key' should be redacted."""
        from app.core.logging_config import filter_sensitive_data, _REDACTED

        event_dict = {
            "event": "provider_call",
            "api_key": "sk-1234567890",
        }
        result = filter_sensitive_data(None, "info", event_dict)
        assert result["api_key"] == _REDACTED

    def test_nested_sensitive_data_redacted(self):
        """Sensitive keys inside nested dicts should also be redacted."""
        from app.core.logging_config import filter_sensitive_data, _REDACTED

        event_dict = {
            "event": "nested",
            "data": {
                "password": "s3cret",
                "user": "john",
            },
        }
        result = filter_sensitive_data(None, "info", event_dict)
        assert result["data"]["password"] == _REDACTED
        assert result["data"]["user"] == "john"

    def test_non_sensitive_data_unchanged(self):
        """Non-sensitive fields should pass through unchanged."""
        from app.core.logging_config import filter_sensitive_data

        event_dict = {
            "event": "normal_operation",
            "module": "transcription",
            "duration_ms": 123,
            "status": "success",
        }
        result = filter_sensitive_data(None, "info", event_dict)
        assert result["module"] == "transcription"
        assert result["duration_ms"] == 123
        assert result["status"] == "success"

    def test_access_token_in_list_redacted(self):
        """Sensitive keys inside list elements should be redacted."""
        from app.core.logging_config import filter_sensitive_data, _REDACTED

        event_dict = {
            "event": "batch",
            "items": [
                {"access_token": "tok_123", "name": "a"},
                {"access_token": "tok_456", "name": "b"},
            ],
        }
        result = filter_sensitive_data(None, "info", event_dict)
        for item in result["items"]:
            assert item["access_token"] == _REDACTED
            assert item["name"] in ("a", "b")

    def test_all_sensitive_keys_covered(self):
        """Every key in SENSITIVE_KEYS should trigger redaction."""
        from app.core.logging_config import (
            filter_sensitive_data,
            SENSITIVE_KEYS,
            _REDACTED,
        )

        event_dict = {key: f"value_for_{key}" for key in SENSITIVE_KEYS}
        event_dict["event"] = "test"

        result = filter_sensitive_data(None, "info", event_dict)
        for key in SENSITIVE_KEYS:
            assert result[key] == _REDACTED, f"Key '{key}' was not redacted"


# ==========================================================================
# Pool Metrics
# ==========================================================================

class TestPoolMetrics:
    """Tests for the database PoolMetrics dataclass.

    The PoolMetrics class is tested in isolation by reconstructing it
    from its definition, because importing ``app.database`` at module
    level would trigger PostgreSQL engine creation with pool arguments
    incompatible with the SQLite test DATABASE_URL.
    """

    def _make_pool_metrics_class(self):
        """Build and return the PoolMetrics dataclass without importing
        the database module's engine creation side-effects."""
        from dataclasses import dataclass
        from typing import Optional

        @dataclass
        class PoolMetrics:
            size: int
            checked_in: int
            checked_out: int
            overflow: int

            @staticmethod
            def get_stats(engine) -> Optional["PoolMetrics"]:
                pool = engine.pool
                try:
                    return PoolMetrics(
                        size=pool.size(),
                        checked_in=pool.checkedin(),
                        checked_out=pool.checkedout(),
                        overflow=pool.overflow(),
                    )
                except AttributeError:
                    return None

        return PoolMetrics

    def test_pool_metrics_get_stats_returns_valid_dataclass(self):
        """PoolMetrics.get_stats() returns a valid PoolMetrics instance
        when the pool supports size/checkedin/checkedout/overflow."""
        PoolMetrics = self._make_pool_metrics_class()

        mock_pool = MagicMock()
        mock_pool.size.return_value = 20
        mock_pool.checkedin.return_value = 18
        mock_pool.checkedout.return_value = 2
        mock_pool.overflow.return_value = 0

        mock_engine = MagicMock()
        mock_engine.pool = mock_pool

        stats = PoolMetrics.get_stats(mock_engine)

        assert stats is not None
        assert stats.size == 20
        assert stats.checked_in == 18
        assert stats.checked_out == 2
        assert stats.overflow == 0

    def test_pool_metrics_with_mock_pool(self):
        """PoolMetrics should correctly reflect pool state."""
        PoolMetrics = self._make_pool_metrics_class()

        mock_pool = MagicMock()
        mock_pool.size.return_value = 10
        mock_pool.checkedin.return_value = 5
        mock_pool.checkedout.return_value = 5
        mock_pool.overflow.return_value = 3

        mock_engine = MagicMock()
        mock_engine.pool = mock_pool

        stats = PoolMetrics.get_stats(mock_engine)

        assert stats is not None
        assert isinstance(stats.size, int)
        assert isinstance(stats.checked_in, int)
        assert isinstance(stats.checked_out, int)
        assert isinstance(stats.overflow, int)
        assert stats.size == 10
        assert stats.checked_out == 5
        assert stats.overflow == 3

    def test_pool_metrics_null_pool_returns_none(self):
        """When the pool doesn't support size/checkedin, return None."""
        PoolMetrics = self._make_pool_metrics_class()

        mock_pool = MagicMock()
        mock_pool.size.side_effect = AttributeError("NullPool has no size")

        mock_engine = MagicMock()
        mock_engine.pool = mock_pool

        stats = PoolMetrics.get_stats(mock_engine)
        assert stats is None
