"""
LiteLLM Proxy - Unified LLM gateway with auto cost tracking and routing.

Wraps all AI provider calls through LiteLLM for:
- Unified API across all providers (OpenAI-compatible)
- Automatic token counting and cost calculation
- Intelligent routing (cheapest provider for the task)
- Automatic fallback on provider errors

Falls back gracefully to direct providers if litellm is not installed.
The existing GeminiProvider/ClaudeProvider/GroqProvider are PRESERVED as fallback.
"""

import time
from typing import Optional
from uuid import UUID

import structlog

logger = structlog.get_logger()

# LiteLLM model mapping to our provider names
MODEL_MAP = {
    "gemini": "gemini/gemini-2.0-flash",
    "claude": "claude-sonnet-4-20250514",
    "groq": "groq/llama-3.3-70b-versatile",
}

# Reverse mapping
PROVIDER_FROM_MODEL = {v: k for k, v in MODEL_MAP.items()}

_litellm_available = None


def is_available() -> bool:
    """Check if litellm is installed and usable."""
    global _litellm_available
    if _litellm_available is not None:
        return _litellm_available
    try:
        import litellm  # noqa: F401
        _litellm_available = True
        logger.info("litellm_available", msg="LiteLLM proxy enabled for unified LLM access")
    except ImportError:
        _litellm_available = False
        logger.info("litellm_not_installed", msg="Using direct providers (pip install litellm to enable proxy)")
    return _litellm_available


async def complete(
    text: str,
    provider_name: str = "gemini",
    user_id: Optional[UUID] = None,
    module: str = "general",
    task: str = "general",
) -> dict:
    """Call LLM via LiteLLM proxy with automatic cost tracking.

    Returns dict with: processed_text, model, provider, tokens, cost_usd
    Falls back to direct provider if litellm unavailable.
    """
    if not is_available():
        return await _fallback_direct(text, provider_name, user_id, module, task)

    import litellm

    model = MODEL_MAP.get(provider_name, MODEL_MAP["gemini"])

    start_time = time.monotonic()
    try:
        response = await litellm.acompletion(
            model=model,
            messages=[{"role": "user", "content": text}],
            metadata={
                "user_id": str(user_id) if user_id else None,
                "module": module,
                "task": task,
            },
        )

        elapsed_ms = int((time.monotonic() - start_time) * 1000)
        content = response.choices[0].message.content or ""
        usage = response.usage

        # LiteLLM gives us exact token counts and cost
        input_tokens = usage.prompt_tokens if usage else 0
        output_tokens = usage.completion_tokens if usage else 0
        total_tokens = usage.total_tokens if usage else 0

        # LiteLLM cost calculation (exact, not estimated)
        try:
            cost_usd = litellm.completion_cost(completion_response=response)
        except Exception:
            cost_usd = 0.0

        # Track cost
        await _track_cost(
            user_id=user_id, provider=provider_name,
            model=response.model or model,
            module=module, task=task,
            input_tokens=input_tokens, output_tokens=output_tokens,
            latency_ms=elapsed_ms, success=True,
        )

        logger.info(
            "litellm_completion",
            provider=provider_name, model=response.model,
            input_tokens=input_tokens, output_tokens=output_tokens,
            cost_usd=round(cost_usd, 6), latency_ms=elapsed_ms,
        )

        return {
            "processed_text": content,
            "model": response.model or model,
            "provider": provider_name,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "cost_usd": round(cost_usd, 6),
            "latency_ms": elapsed_ms,
            "via": "litellm",
        }

    except Exception as e:
        elapsed_ms = int((time.monotonic() - start_time) * 1000)
        logger.warning("litellm_failed_fallback", provider=provider_name, error=str(e))

        await _track_cost(
            user_id=user_id, provider=provider_name, model=model,
            module=module, task=task, input_tokens=0, output_tokens=0,
            latency_ms=elapsed_ms, success=False, error=str(e),
        )

        # Fallback to direct provider
        return await _fallback_direct(text, provider_name, user_id, module, task)


async def complete_with_routing(
    text: str,
    user_id: Optional[UUID] = None,
    module: str = "general",
    task: str = "general",
    prefer_free: bool = True,
) -> dict:
    """Intelligent routing: tries cheapest provider first, falls back on error.

    Order: groq (free/fast) -> gemini (free) -> claude (paid, best quality)
    """
    order = ["groq", "gemini", "claude"] if prefer_free else ["gemini", "claude", "groq"]

    last_error = None
    for provider in order:
        try:
            result = await complete(text, provider, user_id, module, task)
            if result.get("processed_text"):
                return result
        except Exception as e:
            last_error = e
            logger.debug("routing_provider_failed", provider=provider, error=str(e))
            continue

    raise last_error or RuntimeError("All providers failed")


def get_model_costs() -> dict:
    """Get exact costs per model from LiteLLM's model database."""
    if not is_available():
        from app.modules.cost_tracker.pricing import PRICING
        return PRICING

    try:
        import litellm
        costs = {}
        for name, model in MODEL_MAP.items():
            try:
                info = litellm.get_model_cost_map(url="").get(model, {})
                costs[name] = {
                    "model": model,
                    "input_per_1m": info.get("input_cost_per_token", 0) * 1_000_000,
                    "output_per_1m": info.get("output_cost_per_token", 0) * 1_000_000,
                    "label": "litellm",
                }
            except Exception:
                pass
        return costs if costs else None
    except Exception:
        return None


async def _fallback_direct(
    text: str, provider_name: str, user_id: Optional[UUID],
    module: str, task: str,
) -> dict:
    """Fallback: use original direct providers."""
    from app.ai_assistant.providers.gemini import GeminiProvider
    from app.ai_assistant.providers.claude import ClaudeProvider
    from app.ai_assistant.providers.groq import GroqProvider

    providers_map = {
        "gemini": GeminiProvider,
        "claude": ClaudeProvider,
        "groq": GroqProvider,
    }

    provider_class = providers_map.get(provider_name, GeminiProvider)
    provider = provider_class()
    prompt = f"Task: {task}\n\n{text}"

    start_time = time.monotonic()
    result = await provider.complete(prompt)
    elapsed_ms = int((time.monotonic() - start_time) * 1000)

    est_input = max(len(prompt) // 4, 1)
    est_output = max(len(result) // 4, 1) if result else 0

    await _track_cost(
        user_id=user_id, provider=provider_name,
        model=provider.model_name, module=module, task=task,
        input_tokens=est_input, output_tokens=est_output,
        latency_ms=elapsed_ms, success=True,
    )

    return {
        "processed_text": result,
        "model": provider.model_name,
        "provider": provider_name,
        "input_tokens": est_input,
        "output_tokens": est_output,
        "total_tokens": est_input + est_output,
        "cost_usd": 0.0,
        "latency_ms": elapsed_ms,
        "via": "direct",
    }


async def _track_cost(
    user_id: Optional[UUID], provider: str, model: str,
    module: str, task: str, input_tokens: int, output_tokens: int,
    latency_ms: int, success: bool, error: str = None,
) -> None:
    """Track AI usage cost (never blocks main flow)."""
    try:
        from app.modules.cost_tracker.tracker import track_ai_usage
        await track_ai_usage(
            user_id=user_id or __import__("uuid").UUID("00000000-0000-0000-0000-000000000000"),
            provider=provider, model=model, module=module, action=task,
            input_tokens=input_tokens, output_tokens=output_tokens,
            latency_ms=latency_ms, success=success, error=error,
        )
    except Exception:
        pass
