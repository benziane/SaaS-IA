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
    "batch_crawl": "Batch-crawl multiple URLs in parallel with optional proxy rotation and memory-adaptive dispatcher",
    "deep_crawl": "Deep-crawl a website using BestFirst strategy with composite scoring, configurable depth and max pages",
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
    "create_integration_webhook": "Create a webhook connector to receive events from external services (Slack, GitHub, Stripe, etc.)",
    "deploy_chatbot": "Create and publish a custom AI chatbot with system prompt and optional RAG",
    "search_marketplace": "Search the marketplace for modules, templates, prompts, workflows, or datasets",
    "generate_presentation": "Generate a slide deck / presentation from a title and topic",
    "execute_code": "Execute code in a secure sandbox (Python)",
    "generate_form": "Generate an AI-powered form from a natural language prompt",
    "scrape_repos": "Scrape GitHub repositories and package them for AI consumption (Claude, ChatGPT, etc.)",
    "process_pdf": "Upload, parse, summarize, query, or export a PDF document",
    "batch_transcribe": "Batch transcribe multiple YouTube URLs concurrently (max 20)",
    "generate_summary": "Generate an AI-powered summary of a transcription (executive, detailed, bullet_points, action_items)",
    "edit_audio": "Edit an audio file (trim, fade, normalize, noise reduction, speed change, merge)",
    "generate_podcast": "Create a podcast episode with AI chapters, show notes, and RSS feed",
    "analyze_repo": "Analyze a GitHub repository: detect tech stack, score code quality, scan dependencies and security",
    "youtube_transcript": "Get instant YouTube subtitles/transcript without downloading (free, uses youtube-transcript-api)",
    "youtube_metadata": "Extract YouTube video metadata: title, channel, duration, views, description, chapters",
    "youtube_smart": "Smart YouTube transcription: tries free subtitles first, falls back to Whisper local transcription",
    "youtube_playlist": "Batch transcribe all videos in a YouTube playlist or channel (up to 50 videos)",
    "youtube_analyze": "Download YouTube video and analyze frames with AI Vision (content, scenes, objects)",
    "scrape_http": "Fast HTTP scrape of a URL without browser (lightweight, CSS selector, fit markdown)",
    "adaptive_crawl": "Self-tuning adaptive crawl with configurable strategy and confidence threshold",
    "hub_crawl": "Crawl using pre-built site profiles for known sites (e.g., GitHub, Reddit, Wikipedia)",
    "scrape_pdf": "Extract text content from a PDF URL",
    "extract_cosine": "Semantic clustering extraction from a URL using cosine similarity",
    "extract_lxml": "Structured JSON extraction from a URL using lxml and a schema",
    "docker_crawl": "Remote Docker-based crawl for multiple URLs",
    "chunk_regex": "Chunk text into segments using regex patterns",
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

    # YouTube-specific: smart transcript, metadata, playlist, analysis
    if any(w in instruction_lower for w in ["youtube.com", "youtu.be", "youtube playlist", "playlist youtube"]):
        if any(w in instruction_lower for w in ["playlist", "channel", "bulk", "batch", "multiple video"]):
            return [{"action": "youtube_playlist", "description": "Batch transcribe YouTube playlist", "input": {"url": "", "language": "auto", "max_videos": 20}}]
        if any(w in instruction_lower for w in ["metadata", "title", "channel", "views", "duration", "info"]):
            return [{"action": "youtube_metadata", "description": "Extract YouTube video metadata", "input": {"url": ""}}]
        if any(w in instruction_lower for w in ["analyz", "frame", "vision", "visual", "scene"]):
            return [{"action": "youtube_analyze", "description": "Analyze YouTube video frames with AI Vision", "input": {"url": ""}}]
        # Default for YouTube URLs: smart transcription
        return [{"action": "youtube_smart", "description": "Smart YouTube transcription (subtitles → Whisper)", "input": {"url": "", "language": "auto"}}]

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

    # ── Batch crawl (multiple URLs) ────────────────────
    if any(w in instruction_lower for w in ["batch crawl", "batch scrape", "crawl multiple", "scrape multiple", "crawl all", "scrape all"]):
        steps.append({
            "action": "batch_crawl",
            "description": "Batch-crawl multiple URLs in parallel",
            "input": {},
        })
        return steps

    # ── Deep crawl (site-wide) ─────────────────────────
    if any(w in instruction_lower for w in ["deep crawl", "crawl entire", "crawl site", "spider", "full site", "map site"]):
        steps.append({
            "action": "deep_crawl",
            "description": "Deep-crawl the website with BestFirst strategy",
            "input": {},
        })
        return steps

    # ── Adaptive crawl ─────────────────────────────────
    if any(w in instruction_lower for w in ["adaptive crawl", "adaptive scrape", "smart crawl", "self-tuning crawl", "auto crawl"]):
        steps.append({
            "action": "adaptive_crawl",
            "description": "Self-tuning adaptive crawl",
            "input": {},
        })
        return steps

    # ── Hub crawl (site profiles) ──────────────────────
    if any(w in instruction_lower for w in ["hub crawl", "site profile", "profile crawl"]):
        steps.append({
            "action": "hub_crawl",
            "description": "Crawl using pre-built site profile",
            "input": {},
        })
        return steps

    # ── HTTP scrape (fast, no browser) ─────────────────
    if any(w in instruction_lower for w in ["http scrape", "fast scrape", "lightweight scrape", "no browser", "scrape_http"]):
        steps.append({
            "action": "scrape_http",
            "description": "Fast HTTP scrape without browser",
            "input": {},
        })
        return steps

    # ── PDF URL scrape ─────────────────────────────────
    if any(w in instruction_lower for w in ["scrape pdf", "pdf url", "extract pdf from url", "download pdf"]):
        steps.append({
            "action": "scrape_pdf",
            "description": "Extract content from PDF URL",
            "input": {},
        })
        return steps

    # ── Cosine / semantic clustering extraction ────────
    if any(w in instruction_lower for w in ["cosine", "semantic cluster", "cluster extract", "similarity extract"]):
        steps.append({
            "action": "extract_cosine",
            "description": "Semantic clustering extraction from URL",
            "input": {},
        })
        return steps

    # ── lxml structured extraction ─────────────────────
    if any(w in instruction_lower for w in ["lxml", "structured extract", "json extract", "schema extract"]):
        steps.append({
            "action": "extract_lxml",
            "description": "Structured JSON extraction using lxml",
            "input": {},
        })
        return steps

    # ── Docker crawl ───────────────────────────────────
    if any(w in instruction_lower for w in ["docker crawl", "remote crawl", "docker scrape"]):
        steps.append({
            "action": "docker_crawl",
            "description": "Remote Docker-based crawl",
            "input": {},
        })
        return steps

    # ── Chunk text with regex ──────────────────────────
    if any(w in instruction_lower for w in ["chunk regex", "regex chunk", "split text", "chunk text", "text chunk"]):
        steps.append({
            "action": "chunk_regex",
            "description": "Chunk text using regex patterns",
            "input": {},
        })
        return steps

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

    if any(w in instruction_lower for w in ["webhook", "integration", "connect", "connecteur", "slack", "github", "stripe", "zapier"]):
        steps.append({
            "action": "create_integration_webhook",
            "description": "Create a webhook integration connector",
            "input": {},
        })

    if any(w in instruction_lower for w in ["chatbot", "bot", "deploy bot", "assistant widget", "embed chatbot", "widget chat"]):
        steps.append({
            "action": "deploy_chatbot",
            "description": "Create and deploy a custom chatbot",
            "input": {},
        })

    if any(w in instruction_lower for w in ["marketplace", "store", "boutique", "template store", "browse module", "plugin"]):
        steps.append({
            "action": "search_marketplace",
            "description": "Search the marketplace for listings",
            "input": {},
        })

    if any(w in instruction_lower for w in ["presentation", "slides", "pitch deck", "powerpoint", "diapositive"]):
        steps.append({
            "action": "generate_presentation",
            "description": "Generate a slide deck / presentation",
            "input": {},
        })

    if any(w in instruction_lower for w in ["execute code", "run code", "python", "sandbox", "script", "code"]):
        steps.append({
            "action": "execute_code",
            "description": "Execute code in a secure sandbox",
            "input": {},
        })

    if any(w in instruction_lower for w in ["form", "formulaire", "survey", "questionnaire", "sondage"]):
        steps.append({
            "action": "generate_form",
            "description": "Generate an AI-powered form",
            "input": {},
        })

    if any(w in instruction_lower for w in ["scrape repo", "skill seeker", "package repo", "github repo", "repo for claude", "repo for ai"]):
        steps.append({
            "action": "scrape_repos",
            "description": "Scrape GitHub repos and package for AI consumption",
            "input": {},
        })

    if any(w in instruction_lower for w in ["analyze repo", "repo analysis", "tech stack", "code quality", "audit repo", "scan repo", "review repo", "analyser repo", "analyse repo"]):
        steps.append({
            "action": "analyze_repo",
            "description": "Analyze GitHub repository: tech stack, quality, dependencies, security",
            "input": {},
        })

    if any(w in instruction_lower for w in ["pdf", "document pdf", "resume pdf", "analyze pdf", "summarize pdf", "parse pdf", "extract pdf"]):
        steps.append({
            "action": "process_pdf",
            "description": "Process, analyze, or summarize a PDF document",
            "input": {},
        })

    if any(w in instruction_lower for w in ["batch transcri", "multiple video", "bulk transcri", "several youtube", "many video", "liste video"]):
        steps.append({
            "action": "batch_transcribe",
            "description": "Batch transcribe multiple YouTube URLs concurrently",
            "input": {},
        })

    if any(w in instruction_lower for w in ["youtube playlist", "playlist youtube", "transcri.*playlist", "playlist.*transcri"]):
        steps.append({
            "action": "youtube_playlist",
            "description": "Transcribe YouTube playlist",
            "input": {"url": "", "max_videos": 20},
        })

    if any(w in instruction_lower for w in ["summary of transcri", "summarize transcri", "resume transcri", "executive summary", "action items from transcri", "bullet points from transcri"]):
        style = "executive"
        if any(w in instruction_lower for w in ["action item", "task", "next step"]):
            style = "action_items"
        elif any(w in instruction_lower for w in ["bullet", "point"]):
            style = "bullet_points"
        elif any(w in instruction_lower for w in ["detail"]):
            style = "detailed"
        steps.append({
            "action": "generate_summary",
            "description": f"Generate {style} summary of transcription",
            "input": {"style": style},
        })

    if not steps:
        steps.append({
            "action": "generate_text",
            "description": "Process the request with AI",
            "input": {"prompt": instruction},
        })

    return steps
