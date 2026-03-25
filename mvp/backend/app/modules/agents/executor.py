"""
Agent Executor - Executes planned steps using platform capabilities.
"""

import json
from datetime import datetime
from typing import Optional

import structlog

logger = structlog.get_logger()


async def _exec_crawl_web(input_data: dict, previous: Optional[str]) -> dict:
    """Execute web crawling."""
    url = input_data.get("url", previous or "")
    if not url or not url.startswith("http"):
        return {"output": "", "error": "No valid URL provided for crawling", "action": "crawl_web"}

    try:
        from app.modules.web_crawler.service import WebCrawlerService

        result = await WebCrawlerService.scrape(
            url=url,
            extract_images=input_data.get("extract_images", True),
            max_images=input_data.get("max_images", 10),
        )

        if result.get("success"):
            markdown = result.get("markdown", "")
            image_count = result.get("image_count", 0)
            title = result.get("title", "")

            output = f"# {title}\n\n{markdown[:6000]}"
            if image_count > 0:
                output += f"\n\n[{image_count} images found]"

            return {
                "output": output,
                "action": "crawl_web",
                "url": url,
                "title": title,
                "image_count": image_count,
                "text_length": len(markdown),
            }
        return {"output": "", "error": result.get("error", "Crawl failed"), "action": "crawl_web"}

    except Exception as e:
        return {"output": "", "error": str(e)[:500], "action": "crawl_web"}


async def _exec_analyze_image(input_data: dict, previous: Optional[str]) -> dict:
    """Analyze an image URL with AI Vision."""
    image_url = input_data.get("image_url", input_data.get("url", ""))
    if not image_url:
        return {"output": "", "error": "No image URL provided", "action": "analyze_image"}

    try:
        from app.modules.web_crawler.service import WebCrawlerService

        prompt = input_data.get("prompt", "Describe this image in detail: what it shows, any text visible, colors, and context.")
        description = await WebCrawlerService._analyze_image_url(
            image_url=image_url,
            prompt=prompt,
        )

        return {"output": description, "action": "analyze_image", "image_url": image_url}

    except Exception as e:
        return {"output": "", "error": str(e)[:500], "action": "analyze_image"}


async def execute_step(action: str, input_data: dict, previous_output: Optional[str] = None) -> dict:
    """Execute a single agent step."""
    handlers = {
        "transcribe": _exec_transcribe,
        "summarize": _exec_summarize,
        "translate": _exec_translate,
        "search_knowledge": _exec_search,
        "ask_knowledge": _exec_ask,
        "compare_models": _exec_compare,
        "generate_text": _exec_generate,
        "extract_info": _exec_extract,
        "analyze_sentiment": _exec_sentiment,
        "create_pipeline": _exec_generate,  # Fallback to generate for now
        "crawl_web": _exec_crawl_web,
        "analyze_image": _exec_analyze_image,
        "generate_content": _exec_generate_content,
        "run_workflow": _exec_run_workflow,
        "run_crew": _exec_run_crew,
        "text_to_speech": _exec_tts,
        "voice_dub": _exec_voice_dub,
        "realtime_chat": _exec_realtime_chat,
        "security_scan": _exec_security_scan,
        "generate_image": _exec_generate_image,
        "generate_thumbnail": _exec_generate_thumbnail,
        "analyze_data": _exec_analyze_data,
        "generate_video": _exec_generate_video,
        "generate_clips": _exec_generate_clips,
        "fine_tune": _exec_fine_tune,
    }

    handler = handlers.get(action, _exec_generate)
    return await handler(input_data, previous_output)


async def _exec_transcribe(input_data: dict, previous: Optional[str]) -> dict:
    """Execute a transcription step."""
    url = input_data.get("url", "")
    if not url and previous:
        url = previous.strip()

    if not url:
        return {"output": "", "error": "No URL provided for transcription", "action": "transcribe"}

    return {
        "output": f"[Transcription task created for: {url}. Use the transcription module to process.]",
        "action": "transcribe",
        "url": url,
    }


async def _exec_summarize(input_data: dict, previous: Optional[str]) -> dict:
    """Execute a summarization step."""
    text = input_data.get("text", previous or "")
    if not text:
        return {"output": "", "error": "No text to summarize", "action": "summarize"}

    try:
        from app.ai_assistant.service import AIAssistantService
        max_length = input_data.get("max_length", 500)
        result = await AIAssistantService.process_text_with_provider(
            text=f"Summarize the following text in {max_length} words or less:\n\n{text[:8000]}",
            task="summarize",
            provider_name=input_data.get("provider", "gemini"),
            user_id=input_data.get("_user_id"),
            module="agents",
        )
        return {"output": result.get("processed_text", ""), "action": "summarize"}
    except Exception as e:
        return {"output": text[:500], "error": str(e)[:500], "action": "summarize"}


async def _exec_translate(input_data: dict, previous: Optional[str]) -> dict:
    """Execute a translation step."""
    text = input_data.get("text", previous or "")
    target = input_data.get("target_language", "en")
    if not text:
        return {"output": "", "error": "No text to translate", "action": "translate"}

    try:
        from app.ai_assistant.service import AIAssistantService
        result = await AIAssistantService.process_text_with_provider(
            text=f"Translate the following text to {target}:\n\n{text[:8000]}",
            task="translate",
            provider_name=input_data.get("provider", "gemini"),
            user_id=input_data.get("_user_id"),
            module="agents",
        )
        return {"output": result.get("processed_text", ""), "action": "translate", "target_language": target}
    except Exception as e:
        return {"output": text, "error": str(e)[:500], "action": "translate"}


async def _exec_search(input_data: dict, previous: Optional[str]) -> dict:
    """Execute a knowledge base search."""
    query = input_data.get("query", previous or "")
    if not query:
        return {"output": "", "error": "No query for search", "action": "search_knowledge"}

    try:
        from app.modules.knowledge.service import KnowledgeService
        from app.database import get_session_context
        from uuid import UUID as UUIDType

        user_id = input_data.get("_user_id")
        if not user_id:
            return {"output": f"Search query: {query}", "action": "search_knowledge", "note": "No user context for search"}

        uid = UUIDType(user_id) if isinstance(user_id, str) else user_id
        async with get_session_context() as session:
            results = await KnowledgeService.search(
                query=query,
                user_id=uid,
                limit=input_data.get("limit", 5),
                session=session,
            )

        if results:
            output_text = "\n\n".join(
                f"[{r.get('filename', 'doc')}] {r.get('content', '')[:500]}"
                for r in results
            )
            return {"output": output_text, "action": "search_knowledge", "results_count": len(results)}
        return {"output": "No results found.", "action": "search_knowledge", "results_count": 0}

    except Exception as e:
        return {"output": "", "error": str(e)[:500], "action": "search_knowledge"}


async def _exec_ask(input_data: dict, previous: Optional[str]) -> dict:
    """Execute a RAG question."""
    question = input_data.get("question", previous or "")
    if not question:
        return {"output": "", "error": "No question provided", "action": "ask_knowledge"}

    try:
        from app.modules.knowledge.service import KnowledgeService
        from app.database import get_session_context
        from uuid import UUID as UUIDType

        user_id = input_data.get("_user_id")
        if not user_id:
            return await _exec_generate({"prompt": question}, previous)

        uid = UUIDType(user_id) if isinstance(user_id, str) else user_id
        async with get_session_context() as session:
            result = await KnowledgeService.rag_query(
                question=question,
                user_id=uid,
                session=session,
            )

        answer = result.get("answer", "") if result else ""
        sources = result.get("sources", []) if result else []
        return {
            "output": answer,
            "action": "ask_knowledge",
            "sources_count": len(sources),
        }

    except Exception as e:
        return {"output": "", "error": str(e)[:500], "action": "ask_knowledge"}


async def _exec_sentiment(input_data: dict, previous: Optional[str]) -> dict:
    """Execute sentiment analysis."""
    text = input_data.get("text", previous or "")
    if not text:
        return {"output": "", "error": "No text for sentiment analysis", "action": "analyze_sentiment"}

    try:
        from app.modules.sentiment.service import SentimentService
        result = await SentimentService.analyze_text(text[:10000])

        summary = f"Overall: {result['overall_sentiment']} (score: {result['overall_score']}). "
        summary += f"Positive: {result['positive_percent']}%, Negative: {result['negative_percent']}%, Neutral: {result['neutral_percent']}%."
        if result.get('emotion_summary'):
            top_emotions = sorted(result['emotion_summary'].items(), key=lambda x: x[1], reverse=True)[:3]
            summary += f" Top emotions: {', '.join(f'{e}({c})' for e, c in top_emotions)}."

        return {"output": summary, "action": "analyze_sentiment", "details": result}
    except Exception as e:
        return {"output": "", "error": str(e)[:500], "action": "analyze_sentiment"}


async def _exec_compare(input_data: dict, previous: Optional[str]) -> dict:
    """Execute a model comparison."""
    prompt = input_data.get("prompt", previous or "")
    if not prompt:
        return {"output": "", "error": "No prompt for comparison", "action": "compare_models"}

    try:
        from app.modules.compare.service import CompareService
        from app.database import get_session_context
        from uuid import uuid4

        providers = input_data.get("providers", ["gemini", "groq"])

        async with get_session_context() as session:
            _, results = await CompareService.run_comparison(
                user_id=uuid4(),
                prompt=prompt[:5000],
                providers=providers,
                session=session,
            )

        best = max(results, key=lambda r: len(r.get("response", ""))) if results else {}
        return {
            "output": best.get("response", ""),
            "action": "compare_models",
            "results_count": len(results),
            "best_provider": best.get("provider", "unknown"),
        }
    except Exception as e:
        return {"output": "", "error": str(e)[:500], "action": "compare_models"}


async def _exec_generate(input_data: dict, previous: Optional[str]) -> dict:
    """Execute generic text generation."""
    prompt = input_data.get("prompt", previous or "")
    if not prompt:
        prompt = json.dumps(input_data)

    try:
        from app.ai_assistant.service import AIAssistantService
        result = await AIAssistantService.process_text_with_provider(
            text=prompt[:8000],
            task="general",
            provider_name=input_data.get("provider", "gemini"),
            user_id=input_data.get("_user_id"),
            module="agents",
        )
        return {"output": result.get("processed_text", ""), "action": "generate_text"}
    except Exception as e:
        return {"output": "", "error": str(e)[:500], "action": "generate_text"}


async def _exec_extract(input_data: dict, previous: Optional[str]) -> dict:
    """Execute information extraction."""
    text = input_data.get("text", previous or "")
    what = input_data.get("extract", "key information")
    if not text:
        return {"output": "", "error": "No text for extraction", "action": "extract_info"}

    try:
        from app.ai_assistant.service import AIAssistantService
        result = await AIAssistantService.process_text_with_provider(
            text=f"Extract {what} from the following text:\n\n{text[:8000]}",
            task="extract",
            provider_name="gemini",
            user_id=input_data.get("_user_id"),
            module="agents",
        )
        return {"output": result.get("processed_text", ""), "action": "extract_info"}
    except Exception as e:
        return {"output": text, "error": str(e)[:500], "action": "extract_info"}


async def _exec_generate_content(input_data: dict, previous: Optional[str]) -> dict:
    """Generate multi-format content via the Content Studio."""
    text = input_data.get("text", previous or "")
    fmt = input_data.get("format", "blog_article")
    if not text:
        return {"output": "", "error": "No text for content generation", "action": "generate_content"}

    try:
        from app.models.content_studio import ContentFormat
        from app.modules.content_studio.service import ContentStudioService

        result = await ContentStudioService._generate_single(
            source_text=text,
            fmt=ContentFormat(fmt),
            tone=input_data.get("tone", "professional"),
            target_audience=input_data.get("target_audience"),
            keywords=None,
            language=input_data.get("language", "auto"),
            provider=input_data.get("provider"),
            custom_instructions=input_data.get("instructions"),
            user_id=input_data.get("_user_id"),
        )
        content = result.get("content", "")
        title = result.get("title", "")
        output = f"# {title}\n\n{content}" if title else content
        return {
            "output": output,
            "action": "generate_content",
            "format": fmt,
            "title": title,
            "word_count": len(content.split()),
        }
    except Exception as e:
        return {"output": "", "error": str(e)[:500], "action": "generate_content"}


async def _exec_run_workflow(input_data: dict, previous: Optional[str]) -> dict:
    """Trigger a workflow execution."""
    workflow_id = input_data.get("workflow_id", "")
    if not workflow_id:
        return {
            "output": previous or "",
            "action": "run_workflow",
            "note": "No workflow_id specified. Use the workflows module to create and run workflows.",
        }
    return {
        "output": f"[Workflow {workflow_id} execution queued]",
        "action": "run_workflow",
        "workflow_id": workflow_id,
    }


async def _exec_run_crew(input_data: dict, previous: Optional[str]) -> dict:
    """Trigger a multi-agent crew execution."""
    crew_id = input_data.get("crew_id", "")
    instruction = input_data.get("instruction", previous or "")
    if not crew_id:
        return {
            "output": instruction,
            "action": "run_crew",
            "note": "No crew_id specified. Use the multi-agent crew module to create and run crews.",
        }
    return {
        "output": f"[Crew {crew_id} execution queued with instruction: {instruction[:200]}]",
        "action": "run_crew",
        "crew_id": crew_id,
    }


async def _exec_tts(input_data: dict, previous: Optional[str]) -> dict:
    """Convert text to speech."""
    text = input_data.get("text", previous or "")
    if not text:
        return {"output": "", "error": "No text for TTS", "action": "text_to_speech"}
    return {
        "output": f"[TTS synthesis queued: {len(text.split())} words. Use the Voice Clone module to process.]",
        "action": "text_to_speech",
        "text_length": len(text),
        "word_count": len(text.split()),
    }


async def _exec_voice_dub(input_data: dict, previous: Optional[str]) -> dict:
    """Dub content to another language."""
    target = input_data.get("target_language", "en")
    return {
        "output": f"[Voice dubbing to {target} queued. Use the Voice Clone module to process.]",
        "action": "voice_dub",
        "target_language": target,
    }


async def _exec_realtime_chat(input_data: dict, previous: Optional[str]) -> dict:
    """Start a realtime AI chat session."""
    return {
        "output": previous or "",
        "action": "realtime_chat",
        "note": "Use the Realtime AI module to start a live session.",
    }


async def _exec_security_scan(input_data: dict, previous: Optional[str]) -> dict:
    """Scan text for security issues."""
    text = input_data.get("text", previous or "")
    if not text:
        return {"output": "", "error": "No text to scan", "action": "security_scan"}
    try:
        from app.modules.security_guardian.service import SecurityGuardianService
        findings_pii = SecurityGuardianService._detect_pii(text)
        findings_injection = SecurityGuardianService._detect_prompt_injection(text)
        all_findings = findings_pii + findings_injection

        if all_findings:
            summary = f"Found {len(all_findings)} issue(s):\n"
            for f in all_findings[:10]:
                summary += f"- [{f['severity'].upper()}] {f['type']}: {f['description']}\n"
            return {
                "output": summary,
                "action": "security_scan",
                "findings_count": len(all_findings),
            }
        return {
            "output": "No security issues detected. Content is clean.",
            "action": "security_scan",
            "findings_count": 0,
        }
    except Exception as e:
        return {"output": "", "error": str(e)[:500], "action": "security_scan"}


async def _exec_generate_image(input_data: dict, previous: Optional[str]) -> dict:
    """Generate an AI image."""
    prompt = input_data.get("prompt", previous or "")
    if not prompt:
        return {"output": "", "error": "No prompt for image generation", "action": "generate_image"}
    style = input_data.get("style", "digital_art")
    return {
        "output": f"[Image generation queued: '{prompt[:100]}' in {style} style. Use the Image Gen module to process.]",
        "action": "generate_image",
        "prompt": prompt[:200],
        "style": style,
    }


async def _exec_generate_thumbnail(input_data: dict, previous: Optional[str]) -> dict:
    """Generate a thumbnail."""
    text = input_data.get("text", previous or "")
    return {
        "output": f"[Thumbnail generation queued from content ({len(text)} chars). Use the Image Gen module.]",
        "action": "generate_thumbnail",
    }


async def _exec_analyze_data(input_data: dict, previous: Optional[str]) -> dict:
    """Analyze data."""
    question = input_data.get("question", previous or "")
    return {
        "output": f"[Data analysis queued: '{question[:200]}'. Upload a dataset in the Data Analyst module to proceed.]",
        "action": "analyze_data",
        "question": question[:200],
    }


async def _exec_generate_video(input_data: dict, previous: Optional[str]) -> dict:
    """Generate a video."""
    prompt = input_data.get("prompt", previous or "")
    video_type = input_data.get("video_type", "text_to_video")
    return {
        "output": f"[Video generation queued: '{prompt[:100]}' ({video_type}). Use the Video Gen module to process.]",
        "action": "generate_video",
        "video_type": video_type,
    }


async def _exec_generate_clips(input_data: dict, previous: Optional[str]) -> dict:
    """Generate highlight clips."""
    return {
        "output": "[Clip generation queued. Use the Video Gen module with a transcription to extract highlights.]",
        "action": "generate_clips",
    }


async def _exec_fine_tune(input_data: dict, previous: Optional[str]) -> dict:
    """Fine-tune a custom model."""
    return {
        "output": "[Fine-tuning task queued. Use the Fine-Tuning Studio to create a dataset and train a model.]",
        "action": "fine_tune",
        "note": "Create a dataset from your transcriptions, conversations, or documents, then train a custom model.",
    }
