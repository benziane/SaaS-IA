"""
Agent Executor - Executes planned steps using platform capabilities.
"""

import json
from datetime import datetime
from typing import Optional

import structlog

logger = structlog.get_logger()


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
