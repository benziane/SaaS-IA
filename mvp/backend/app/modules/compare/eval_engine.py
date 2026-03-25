"""
Promptfoo-style Evaluation Engine for LLM comparison.

Provides automated LLM-as-judge evaluation, scoring, and ELO ranking.
Inspired by promptfoo (12K+ stars) but integrated natively.

Works without any external dependency - uses our existing AI providers.
"""

import json
from typing import Optional
from uuid import UUID

import structlog

logger = structlog.get_logger()


async def evaluate_responses(
    prompt: str,
    responses: list[dict],
    user_id: Optional[UUID] = None,
    judge_provider: str = "gemini",
) -> list[dict]:
    """Evaluate multiple LLM responses using LLM-as-judge pattern.

    Args:
        prompt: Original user prompt
        responses: List of {provider, response, response_time_ms}
        judge_provider: Provider to use as judge (default: gemini, free)

    Returns:
        List of responses enriched with: score (0-10), reasoning, rank
    """
    if len(responses) < 2:
        for r in responses:
            r["eval_score"] = 7.0
            r["eval_reasoning"] = "Single response, no comparison"
            r["eval_rank"] = 1
        return responses

    # Build judge prompt
    response_texts = "\n\n".join(
        f"--- Response {i+1} (Provider: {r['provider']}) ---\n{r.get('response', '')[:2000]}"
        for i, r in enumerate(responses)
        if r.get("response")
    )

    judge_prompt = f"""You are an expert evaluator. Score each AI response to the user's prompt.

User Prompt: "{prompt[:1000]}"

{response_texts}

For each response, provide a JSON array with:
- provider: the provider name
- score: 0-10 (10 = perfect)
- reasoning: 1-2 sentences explaining the score
- strengths: key strengths
- weaknesses: key weaknesses

Consider: accuracy, completeness, clarity, relevance, helpfulness.

Respond ONLY with a JSON array: [{{"provider": "...", "score": 8, "reasoning": "...", "strengths": "...", "weaknesses": "..."}}]"""

    try:
        from app.ai_assistant.service import AIAssistantService
        result = await AIAssistantService.process_text_with_provider(
            text=judge_prompt,
            task="evaluation",
            provider_name=judge_provider,
            user_id=user_id,
            module="compare",
        )

        text = result.get("processed_text", "[]")
        start = text.find("[")
        end = text.rfind("]") + 1
        if start >= 0 and end > start:
            evals = json.loads(text[start:end])

            # Merge evaluations into responses
            eval_map = {e.get("provider", ""): e for e in evals if isinstance(e, dict)}
            for r in responses:
                ev = eval_map.get(r["provider"], {})
                r["eval_score"] = ev.get("score", 5.0)
                r["eval_reasoning"] = ev.get("reasoning", "")
                r["eval_strengths"] = ev.get("strengths", "")
                r["eval_weaknesses"] = ev.get("weaknesses", "")

            # Assign ranks
            sorted_responses = sorted(responses, key=lambda x: x.get("eval_score", 0), reverse=True)
            for rank, r in enumerate(sorted_responses):
                r["eval_rank"] = rank + 1

            logger.info("llm_judge_complete", responses=len(responses))
            return responses

    except Exception as e:
        logger.warning("llm_judge_failed", error=str(e))

    # Fallback: rank by response length (crude but works)
    for r in responses:
        r["eval_score"] = min(10, len(r.get("response", "")) / 200)
        r["eval_reasoning"] = "Auto-scored by length (judge unavailable)"
        r["eval_rank"] = 0
    sorted_r = sorted(responses, key=lambda x: x.get("eval_score", 0), reverse=True)
    for rank, r in enumerate(sorted_r):
        r["eval_rank"] = rank + 1
    return responses


def compute_elo_update(
    winner_elo: float,
    loser_elo: float,
    k_factor: float = 32.0,
) -> tuple[float, float]:
    """Compute ELO rating update after a comparison.

    Returns (new_winner_elo, new_loser_elo).
    """
    expected_winner = 1.0 / (1.0 + 10 ** ((loser_elo - winner_elo) / 400))
    expected_loser = 1.0 - expected_winner

    new_winner = winner_elo + k_factor * (1 - expected_winner)
    new_loser = loser_elo + k_factor * (0 - expected_loser)

    return round(new_winner, 1), round(new_loser, 1)
