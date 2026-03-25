"""
Circuit Breaker for AI Providers
=================================

Zero-external-dependency circuit breaker implementation designed for
resilient AI provider failover.

States:
  CLOSED   -> normal operation, requests pass through
  OPEN     -> provider is down, requests are rejected immediately
  HALF_OPEN -> recovery probe: a limited number of requests are allowed
               through; consecutive successes transition back to CLOSED

The AIProviderManager wraps multiple providers with individual circuit
breakers and routes calls to the first healthy provider by priority.
"""

import asyncio
import inspect
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

import structlog

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# Circuit state & stats
# ---------------------------------------------------------------------------


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitStats:
    """Read-only snapshot of a circuit breaker's current status."""

    state: CircuitState
    failure_count: int
    success_count: int
    last_failure_time: Optional[float]
    last_state_change: float
    consecutive_successes_in_half_open: int


# ---------------------------------------------------------------------------
# Custom exception
# ---------------------------------------------------------------------------


class CircuitOpenError(Exception):
    """Raised when a call is attempted on an OPEN circuit."""

    def __init__(self, name: str, recovery_remaining: float):
        self.name = name
        self.recovery_remaining = recovery_remaining
        super().__init__(
            f"Circuit breaker '{name}' is OPEN. "
            f"Recovery in {recovery_remaining:.1f}s."
        )


# ---------------------------------------------------------------------------
# Circuit Breaker
# ---------------------------------------------------------------------------


@dataclass
class CircuitBreaker:
    """
    Async-safe circuit breaker with sliding failure window.

    Parameters:
        name: human-readable label (e.g. provider name)
        failure_threshold: failures within *window_size* to trip the breaker
        recovery_timeout: seconds to wait in OPEN before transitioning to HALF_OPEN
        half_open_max_calls: consecutive successes required in HALF_OPEN to close
        window_size: sliding window (seconds) for counting failures
    """

    name: str
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    half_open_max_calls: int = 3
    window_size: float = 60.0

    # -- internal state (not part of the public constructor) --
    _state: CircuitState = field(default=CircuitState.CLOSED, init=False, repr=False)
    _failures: deque = field(default_factory=deque, init=False, repr=False)
    _last_failure_time: Optional[float] = field(default=None, init=False, repr=False)
    _last_state_change: float = field(default_factory=time.monotonic, init=False, repr=False)
    _half_open_successes: int = field(default=0, init=False, repr=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False, repr=False)
    _total_successes: int = field(default=0, init=False, repr=False)
    _total_failures: int = field(default=0, init=False, repr=False)

    # -- helpers --

    def _clean_old_failures(self) -> None:
        """Remove failures older than the sliding window."""
        cutoff = time.monotonic() - self.window_size
        while self._failures and self._failures[0] < cutoff:
            self._failures.popleft()

    def _transition(self, new_state: CircuitState) -> None:
        """Transition to *new_state* and log the change."""
        old = self._state
        self._state = new_state
        self._last_state_change = time.monotonic()

        if new_state == CircuitState.HALF_OPEN:
            self._half_open_successes = 0

        logger.info(
            "circuit_breaker_transition",
            name=self.name,
            from_state=old.value,
            to_state=new_state.value,
        )

    async def _record_success(self) -> None:
        async with self._lock:
            self._total_successes += 1

            if self._state == CircuitState.HALF_OPEN:
                self._half_open_successes += 1
                if self._half_open_successes >= self.half_open_max_calls:
                    self._transition(CircuitState.CLOSED)
                    self._failures.clear()

    async def _record_failure(self, error: Exception) -> None:
        async with self._lock:
            now = time.monotonic()
            self._total_failures += 1
            self._last_failure_time = now
            self._failures.append(now)
            self._clean_old_failures()

            logger.warning(
                "circuit_breaker_failure",
                name=self.name,
                state=self._state.value,
                failure_count=len(self._failures),
                error=str(error),
            )

            if self._state == CircuitState.HALF_OPEN:
                # Any failure in half-open immediately re-opens
                self._transition(CircuitState.OPEN)
            elif (
                self._state == CircuitState.CLOSED
                and len(self._failures) >= self.failure_threshold
            ):
                self._transition(CircuitState.OPEN)

    def _should_allow_request(self) -> bool:
        """Determine whether a request should be allowed (non-locking read)."""
        if self._state == CircuitState.CLOSED:
            return True

        if self._state == CircuitState.OPEN:
            elapsed = time.monotonic() - self._last_state_change
            if elapsed >= self.recovery_timeout:
                self._transition(CircuitState.HALF_OPEN)
                return True
            return False

        # HALF_OPEN -- allow through for probing
        return True

    async def call(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """
        Execute *func* through the circuit breaker.

        Handles both sync and async callables transparently.

        Raises:
            CircuitOpenError: if the circuit is OPEN and recovery has not elapsed
        """
        async with self._lock:
            if not self._should_allow_request():
                elapsed = time.monotonic() - self._last_state_change
                remaining = max(0.0, self.recovery_timeout - elapsed)
                raise CircuitOpenError(self.name, remaining)

        # Execute the function (support both sync and async)
        try:
            result = func(*args, **kwargs)
            if inspect.isawaitable(result):
                result = await result
        except Exception as exc:
            await self._record_failure(exc)
            raise

        await self._record_success()
        return result

    @property
    def stats(self) -> CircuitStats:
        """Return a read-only snapshot of the breaker's current status."""
        return CircuitStats(
            state=self._state,
            failure_count=self._total_failures,
            success_count=self._total_successes,
            last_failure_time=self._last_failure_time,
            last_state_change=self._last_state_change,
            consecutive_successes_in_half_open=self._half_open_successes,
        )


# ---------------------------------------------------------------------------
# AI Provider Manager (multi-provider failover)
# ---------------------------------------------------------------------------


class AIProviderManager:
    """
    Routes AI calls across multiple providers with circuit-breaker protection.

    Providers are tried in priority order (lower number = higher priority).
    If a provider's circuit breaker is open, it is skipped. If a provider
    raises an exception, the failure is recorded and the next provider
    is attempted.

    Usage::

        manager = AIProviderManager()
        manager.add_provider("gemini", gemini_call, priority=1)
        manager.add_provider("claude", claude_call, priority=2)
        manager.add_provider("groq",   groq_call,   priority=3)

        result = await manager.call(prompt="Hello")
    """

    def __init__(self) -> None:
        # list of (priority, name, call_func, breaker), kept sorted
        self._providers: list[tuple[int, str, Callable, CircuitBreaker]] = []

    def add_provider(
        self,
        name: str,
        call_func: Callable,
        priority: int = 10,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
    ) -> None:
        """
        Register a provider with its own circuit breaker.

        Args:
            name: human-readable label
            call_func: callable(**kwargs) -> result
            priority: lower = tried first
            failure_threshold: failures to trip the breaker
            recovery_timeout: seconds before HALF_OPEN probe
        """
        breaker = CircuitBreaker(
            name=name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
        )
        self._providers.append((priority, name, call_func, breaker))
        self._providers.sort(key=lambda t: t[0])

        logger.info(
            "circuit_breaker_provider_added",
            name=name,
            priority=priority,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
        )

    async def call(self, **kwargs: Any) -> Any:
        """
        Attempt to call providers in priority order.

        Raises:
            RuntimeError: if every provider is unavailable or errored
        """
        errors: list[tuple[str, Exception]] = []

        for _priority, name, func, breaker in self._providers:
            try:
                return await breaker.call(func, **kwargs)
            except CircuitOpenError:
                logger.debug("circuit_breaker_skip_open", provider=name)
                continue
            except Exception as exc:
                logger.warning(
                    "circuit_breaker_provider_error",
                    provider=name,
                    error=str(exc),
                )
                errors.append((name, exc))
                continue

        # All providers failed
        summary = "; ".join(f"{n}: {e}" for n, e in errors)
        raise RuntimeError(
            f"All AI providers failed. Errors: {summary}"
            if errors
            else "All AI providers are circuit-broken (OPEN)."
        )

    def get_all_stats(self) -> dict[str, CircuitStats]:
        """Return circuit stats for every registered provider."""
        return {name: breaker.stats for _, name, _, breaker in self._providers}
