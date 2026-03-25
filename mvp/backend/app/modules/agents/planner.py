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
    "compare": "Compare AI model responses (pipeline step)",
    "generate_text": "Generate or process text with AI",
    "extract_info": "Extract specific information from text",
    "analyze_sentiment": "Analyze sentiment and emotions in text",
    "sentiment": "Analyze sentiment and emotions (pipeline step)",
    "create_pipeline": "Create an AI processing pipeline",
    "crawl_web": "Crawl a web page and extract text and images",
    "crawl_and_index": "Crawl a web page and auto-index content to the Knowledge Base",
    "analyze_image": "Analyze an image using AI Vision",
    "generate_content": "Generate multi-format content (blog, Twitter thread, LinkedIn post, newsletter, etc.) from text",
    "run_workflow": "Execute an AI automation workflow",
    "run_crew": "Run a multi-agent crew to collaboratively solve a complex task",
    "text_to_speech": "Convert text to speech audio using AI voice synthesis",
    "voice_dub": "Dub/translate audio to another language with AI voice",
    "realtime_chat": "Start a real-time AI conversation session",
    "security_scan": "Scan text for PII, prompt injection, and safety issues",
    "generate_image": "Generate an AI image from a text description",
    "generate_thumbnail": "Generate a YouTube thumbnail from content",
    "analyze_data": "Analyze a dataset and answer questions with charts and insights",
    "generate_video": "Generate an AI video from text or image",
    "generate_clips": "Generate highlight clips from a transcription",
    "fine_tune": "Create a training dataset or fine-tune a custom AI model",
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

    if any(w in instruction_lower for w in ["crawl", "scrape", "web", "website", "page", "site", "url"]):
        # Prefer crawl_and_index when user also mentions indexing or knowledge base
        if any(w in instruction_lower for w in ["index", "knowledge", "base", "kb", "save"]):
            steps.append({
                "action": "crawl_and_index",
                "description": "Crawl the web page and index to Knowledge Base",
                "input": {},
            })
        else:
            steps.append({
                "action": "crawl_web",
                "description": "Crawl the web page",
                "input": {},
            })

    if any(w in instruction_lower for w in ["image", "photo", "picture", "screenshot", "visual"]):
        steps.append({
            "action": "analyze_image",
            "description": "Analyze the image with AI Vision",
            "input": {},
        })

    if any(w in instruction_lower for w in ["compar", "versus", "vs", "differ"]):
        steps.append({
            "action": "compare_models",
            "description": "Compare AI model responses",
            "input": {},
        })

    if any(w in instruction_lower for w in ["blog", "article", "twitter", "thread", "linkedin", "newsletter", "instagram", "carousel", "content", "social media", "post", "seo"]):
        fmt = "blog_article"
        if any(w in instruction_lower for w in ["twitter", "thread", "tweet"]):
            fmt = "twitter_thread"
        elif any(w in instruction_lower for w in ["linkedin"]):
            fmt = "linkedin_post"
        elif any(w in instruction_lower for w in ["newsletter", "email"]):
            fmt = "newsletter"
        elif any(w in instruction_lower for w in ["instagram", "carousel"]):
            fmt = "instagram_carousel"
        elif any(w in instruction_lower for w in ["seo", "meta"]):
            fmt = "seo_meta"
        steps.append({
            "action": "generate_content",
            "description": f"Generate {fmt.replace('_', ' ')} content",
            "input": {"format": fmt},
        })

    if any(w in instruction_lower for w in ["workflow", "automat", "pipeline", "chain"]):
        steps.append({
            "action": "run_workflow",
            "description": "Execute AI automation workflow",
            "input": {},
        })

    if any(w in instruction_lower for w in ["crew", "team", "equipe", "multi-agent", "collaborat", "ensemble"]):
        steps.append({
            "action": "run_crew",
            "description": "Run multi-agent crew for collaborative task",
            "input": {},
        })

    if any(w in instruction_lower for w in ["voice", "voix", "speak", "parle", "tts", "text to speech", "audio", "narrat", "podcast"]):
        steps.append({
            "action": "text_to_speech",
            "description": "Convert text to speech audio",
            "input": {},
        })

    if any(w in instruction_lower for w in ["dub", "doubl", "doublage", "voice over"]):
        steps.append({
            "action": "voice_dub",
            "description": "Dub content to another language",
            "input": {},
        })

    if any(w in instruction_lower for w in ["realtime", "real-time", "live", "en direct", "conversation live", "assistant vocal"]):
        steps.append({
            "action": "realtime_chat",
            "description": "Start real-time AI conversation",
            "input": {},
        })

    if any(w in instruction_lower for w in ["secur", "pii", "rgpd", "gdpr", "scan", "guardrail", "injection", "safety", "compliance", "audit"]):
        steps.append({
            "action": "security_scan",
            "description": "Scan content for security and privacy issues",
            "input": {},
        })

    if any(w in instruction_lower for w in ["genere image", "generate image", "creer image", "create image", "illustration", "visuel", "banner", "affiche", "poster"]):
        steps.append({
            "action": "generate_image",
            "description": "Generate an AI image",
            "input": {},
        })

    if any(w in instruction_lower for w in ["thumbnail", "miniature", "vignette"]):
        steps.append({
            "action": "generate_thumbnail",
            "description": "Generate a thumbnail",
            "input": {},
        })

    if any(w in instruction_lower for w in ["data", "donnee", "csv", "excel", "analyse", "analyz", "chart", "graph", "statistiq", "rapport", "report", "dataset"]):
        steps.append({
            "action": "analyze_data",
            "description": "Analyze data with AI",
            "input": {},
        })

    if any(w in instruction_lower for w in ["video", "clip", "short", "reel", "tiktok", "avatar", "explainer", "animation"]):
        if any(w in instruction_lower for w in ["clip", "highlight", "moment", "extrait"]):
            steps.append({
                "action": "generate_clips",
                "description": "Generate highlight clips",
                "input": {},
            })
        else:
            steps.append({
                "action": "generate_video",
                "description": "Generate an AI video",
                "input": {},
            })

    if any(w in instruction_lower for w in ["fine-tun", "finetun", "train model", "custom model", "entrainer", "fine tun", "lora", "dataset train"]):
        steps.append({
            "action": "fine_tune",
            "description": "Create training dataset or fine-tune model",
            "input": {},
        })

    if not steps:
        steps.append({
            "action": "generate_text",
            "description": "Process the request with AI",
            "input": {"prompt": instruction},
        })

    return steps
