"""
Agent Planner - Decomposes natural language instructions into executable steps.

Uses AI to analyze the instruction and create a step-by-step plan
using available platform capabilities.
"""

import json

import structlog

logger = structlog.get_logger()

AVAILABLE_ACTIONS = {
    "transcribe": "Transcribe audio/video from a URL or file",
    "summarize": "Summarize text content",
    "translate": "Translate text to another language",
    "search_knowledge": "Search the knowledge base for relevant information",
    "ask_knowledge": "Ask a question using RAG on the knowledge base",
    "compare_models": "Compare AI model responses for a prompt",
    "generate_text": "Generate or process text with AI",
    "extract_info": "Extract specific information from text",
    "analyze_sentiment": "Analyze sentiment and emotions in text",
    "create_pipeline": "Create an AI processing pipeline",
}


async def create_plan(instruction: str) -> list[dict]:
    """
    Use AI to decompose an instruction into executable steps.

    Falls back to a simple heuristic if AI is unavailable.
    """
    try:
        from app.ai_assistant.service import AIAssistantService

        prompt = f"""You are a task planner for an AI platform. Decompose the following instruction into a sequence of steps.

Available actions: {json.dumps(AVAILABLE_ACTIONS, indent=2)}

Instruction: {instruction}

Respond with a JSON array of steps. Each step must have:
- "action": one of the available action keys
- "description": what this step does
- "input": parameters for the action (object)

Example response:
[
  {{"action": "transcribe", "description": "Transcribe the YouTube video", "input": {{"url": "https://..."}}}},
  {{"action": "summarize", "description": "Summarize the transcription", "input": {{"max_length": 500}}}}
]

Respond ONLY with the JSON array, no other text."""

        result = await AIAssistantService.process_text_with_provider(
            text=prompt,
            task="planning",
            provider_name="gemini",
        )

        response_text = result.get("processed_text", "[]")

        # Extract JSON from response
        start = response_text.find("[")
        end = response_text.rfind("]") + 1
        if start >= 0 and end > start:
            plan = json.loads(response_text[start:end])
            if isinstance(plan, list) and len(plan) > 0:
                return plan

    except Exception as e:
        logger.warning("agent_planner_ai_failed", error=str(e))

    # Fallback: simple heuristic planning
    return _heuristic_plan(instruction)


def _heuristic_plan(instruction: str) -> list[dict]:
    """Simple rule-based planning fallback."""
    instruction_lower = instruction.lower()
    steps = []

    if any(w in instruction_lower for w in ["transcri", "youtube", "video", "audio"]):
        steps.append({
            "action": "transcribe",
            "description": "Transcribe the audio/video content",
            "input": {},
        })

    if any(w in instruction_lower for w in ["resum", "summar", "synthes", "recap"]):
        steps.append({
            "action": "summarize",
            "description": "Summarize the content",
            "input": {},
        })

    if any(w in instruction_lower for w in ["tradui", "translat", "anglais", "english", "french", "francais"]):
        target = "en" if any(w in instruction_lower for w in ["anglais", "english"]) else "fr"
        steps.append({
            "action": "translate",
            "description": f"Translate to {target}",
            "input": {"target_language": target},
        })

    if any(w in instruction_lower for w in ["cherch", "search", "find", "trouv"]):
        steps.append({
            "action": "search_knowledge",
            "description": "Search the knowledge base",
            "input": {"query": instruction},
        })

    if any(w in instruction_lower for w in ["question", "demande", "ask", "quoi", "comment", "pourquoi"]):
        steps.append({
            "action": "ask_knowledge",
            "description": "Answer using RAG",
            "input": {"question": instruction},
        })

    if any(w in instruction_lower for w in ["sentiment", "emotion", "mood", "feeling", "tone", "positif", "negatif"]):
        steps.append({
            "action": "analyze_sentiment",
            "description": "Analyze sentiment and emotions",
            "input": {},
        })

    if any(w in instruction_lower for w in ["compar", "versus", "vs", "differ"]):
        steps.append({
            "action": "compare_models",
            "description": "Compare AI model responses",
            "input": {},
        })

    if not steps:
        steps.append({
            "action": "generate_text",
            "description": "Process the request with AI",
            "input": {"prompt": instruction},
        })

    return steps
