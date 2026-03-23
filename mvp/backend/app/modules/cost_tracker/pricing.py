"""
AI provider pricing configuration.

Prices in USD cents per 1M tokens (as of March 2026).
"""

PRICING = {
    "gemini": {
        "model": "gemini-2.5-flash",
        "input_per_1m": 0,
        "output_per_1m": 0,
        "label": "Free tier",
    },
    "groq": {
        "model": "llama-3.3-70b",
        "input_per_1m": 59,
        "output_per_1m": 79,
        "label": "Very cheap",
    },
    "claude": {
        "model": "claude-sonnet-4",
        "input_per_1m": 300,
        "output_per_1m": 1500,
        "label": "Premium",
    },
}


def estimate_cost_cents(provider: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate cost in cents for a given provider and token count."""
    pricing = PRICING.get(provider)
    if not pricing:
        return 0.0

    input_cost = (input_tokens / 1_000_000) * pricing["input_per_1m"]
    output_cost = (output_tokens / 1_000_000) * pricing["output_per_1m"]
    return round(input_cost + output_cost, 4)
