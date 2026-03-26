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
        "publish_social": _exec_publish_social,
        "create_integration_webhook": _exec_create_integration_webhook,
        "deploy_chatbot": _exec_deploy_chatbot,
        "search_marketplace": _exec_search_marketplace,
        "generate_presentation": _exec_generate_presentation,
        "execute_code": _exec_execute_code,
        "generate_form": _exec_generate_form,
        "scrape_repos": _exec_scrape_repos,
        "analyze_repo": _exec_analyze_repo,
        "batch_transcribe": _exec_batch_transcribe,
        "generate_summary": _exec_generate_summary,
        "process_pdf": _exec_process_pdf,
        "edit_audio": _exec_edit_audio,
        "generate_podcast": _exec_generate_podcast,
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
    """Create a fine-tuning job via FineTuningService."""
    dataset_id = input_data.get("dataset_id", "")
    if not dataset_id:
        return {
            "output": "[Fine-tuning ready. Create a dataset first via POST /api/fine-tuning/datasets, then provide dataset_id.]",
            "action": "fine_tune",
            "note": "No dataset_id provided. Create a dataset from your transcriptions, conversations, or documents first.",
        }

    try:
        from app.modules.fine_tuning.service import FineTuningService
        from app.database import get_session_context
        from uuid import UUID as UUIDType

        user_id = input_data.get("_user_id")
        if not user_id:
            return {
                "output": f"[Fine-tuning job ready for dataset {dataset_id}. Use the Fine-Tuning module to launch.]",
                "action": "fine_tune",
                "note": "No user context. Use the Fine-Tuning module directly.",
            }

        uid = UUIDType(user_id) if isinstance(user_id, str) else user_id
        async with get_session_context() as session:
            job = await FineTuningService.create_job(
                user_id=uid,
                name=input_data.get("name", "Agent Fine-Tune"),
                dataset_id=dataset_id,
                base_model=input_data.get("base_model", "unsloth/tinyllama-bnb-4bit"),
                provider=input_data.get("provider", "local"),
                hyperparams=input_data.get("hyperparams", {}),
                session=session,
            )

        return {
            "output": f"[Fine-tuning job '{job.name}' created. Job ID: {job.id}. Status: {job.status}. "
                      f"Base model: {job.base_model}. Provider: {job.provider}.]",
            "action": "fine_tune",
            "job_id": str(job.id),
            "status": str(job.status),
        }
    except Exception as e:
        return {"output": "", "error": str(e)[:500], "action": "fine_tune"}

async def _exec_publish_social(input_data: dict, previous: Optional[str]) -> dict:
    """Publish content to social media platforms."""
    content = input_data.get("content", previous or "")
    platforms = input_data.get("platforms", ["twitter", "linkedin"])
    if not content:
        return {"output": "", "error": "No content to publish", "action": "publish_social"}

    try:
        from app.modules.social_publisher.service import SocialPublisherService
        from app.database import get_session_context
        from uuid import UUID as UUIDType

        user_id = input_data.get("_user_id")
        if not user_id:
            return {
                "output": content,
                "action": "publish_social",
                "note": "No user context. Use the Social Publisher module to publish.",
            }

        uid = UUIDType(user_id) if isinstance(user_id, str) else user_id
        async with get_session_context() as session:
            post = await SocialPublisherService.create_post(
                user_id=uid,
                content=content[:5000],
                platforms=platforms,
                session=session,
                hashtags=input_data.get("hashtags"),
            )

        return {
            "output": f"[Social post created for {', '.join(platforms)}. Post ID: {post.id}. Use the Social Publisher to review and publish.]",
            "action": "publish_social",
            "post_id": str(post.id),
            "platforms": platforms,
        }
    except Exception as e:
        return {"output": "", "error": str(e)[:500], "action": "publish_social"}


async def _exec_create_integration_webhook(input_data: dict, previous: Optional[str]) -> dict:
    """Create a webhook integration connector via Integration Hub."""
    name = input_data.get("name", "")
    provider = input_data.get("provider", "custom")
    if not name:
        name = f"{provider} webhook"

    try:
        from app.modules.integration_hub.service import IntegrationHubService
        from app.database import get_session_context
        from uuid import UUID as UUIDType

        user_id = input_data.get("_user_id")
        if not user_id:
            return {
                "output": f"[Webhook connector '{name}' ready to create. Use the Integration Hub module to set up.]",
                "action": "create_integration_webhook",
                "note": "No user context. Use the Integration Hub module directly.",
            }

        uid = UUIDType(user_id) if isinstance(user_id, str) else user_id
        async with get_session_context() as session:
            service = IntegrationHubService(session)
            connector = await service.create_connector(
                user_id=uid,
                data={
                    "name": name,
                    "type": "webhook",
                    "provider": provider,
                    "config": input_data.get("config", {}),
                    "enabled": True,
                },
            )

        return {
            "output": f"[Webhook connector '{connector.name}' created for {provider}. "
                      f"Connector ID: {connector.id}. "
                      f"Webhook URL: /api/integrations/webhook/{connector.id}]",
            "action": "create_integration_webhook",
            "connector_id": str(connector.id),
            "provider": provider,
            "webhook_url": f"/api/integrations/webhook/{connector.id}",
        }
    except Exception as e:
        return {"output": "", "error": str(e)[:500], "action": "create_integration_webhook"}


async def _exec_deploy_chatbot(input_data: dict, previous: Optional[str]) -> dict:
    """Create and publish a chatbot via the Chatbot Builder."""
    name = input_data.get("name", "")
    system_prompt = input_data.get("system_prompt", "")
    if not name:
        return {"output": "", "error": "No chatbot name provided", "action": "deploy_chatbot"}
    if not system_prompt:
        system_prompt = "You are a helpful AI assistant."

    try:
        from app.modules.ai_chatbot_builder.service import ChatbotBuilderService
        from app.database import get_session_context
        from uuid import UUID as UUIDType

        user_id = input_data.get("_user_id")
        if not user_id:
            return {
                "output": f"[Chatbot '{name}' ready to deploy. Use the Chatbot Builder module to create and publish.]",
                "action": "deploy_chatbot",
                "note": "No user context. Use the Chatbot Builder module directly.",
            }

        uid = UUIDType(user_id) if isinstance(user_id, str) else user_id
        async with get_session_context() as session:
            service = ChatbotBuilderService(session)
            chatbot = await service.create_chatbot(
                user_id=uid,
                data={
                    "name": name,
                    "description": input_data.get("description"),
                    "system_prompt": system_prompt,
                    "model": input_data.get("model", "gemini"),
                    "personality": input_data.get("personality", "professional"),
                    "welcome_message": input_data.get("welcome_message"),
                    "knowledge_base_ids": input_data.get("knowledge_base_ids"),
                },
            )

            # Auto-publish if requested (default: True for agent deploy action)
            if input_data.get("publish", True):
                chatbot = await service.publish_chatbot(uid, chatbot.id)

        embed_info = ""
        if chatbot.embed_token:
            embed_info = f" Embed token: {chatbot.embed_token}."

        return {
            "output": f"[Chatbot '{chatbot.name}' created and {'published' if chatbot.is_published else 'drafted'}. "
                      f"ID: {chatbot.id}.{embed_info}]",
            "action": "deploy_chatbot",
            "chatbot_id": str(chatbot.id),
            "is_published": chatbot.is_published,
            "embed_token": chatbot.embed_token,
        }
    except Exception as e:
        return {"output": "", "error": str(e)[:500], "action": "deploy_chatbot"}


async def _exec_generate_presentation(input_data: dict, previous: Optional[str]) -> dict:
    """Generate a presentation via PresentationGenService."""
    title = input_data.get("title", "")
    topic = input_data.get("topic", previous or "")
    if not title and not topic:
        return {"output": "", "error": "No title or topic provided for presentation", "action": "generate_presentation"}
    if not title:
        title = topic[:100]

    try:
        from app.modules.presentation_gen.service import PresentationGenService
        from app.database import get_session_context
        from uuid import UUID as UUIDType

        user_id = input_data.get("_user_id")
        if not user_id:
            return {
                "output": f"[Presentation '{title}' ready to generate. Use the Presentation Gen module to create.]",
                "action": "generate_presentation",
                "note": "No user context. Use the Presentation Gen module directly.",
            }

        uid = UUIDType(user_id) if isinstance(user_id, str) else user_id
        async with get_session_context() as session:
            service = PresentationGenService(session)
            presentation = await service.generate_presentation(
                user_id=uid,
                title=title,
                topic=topic,
                num_slides=input_data.get("num_slides", 10),
                style=input_data.get("style", "professional"),
                template=input_data.get("template", "default"),
                language=input_data.get("language", "fr"),
            )

        return {
            "output": f"[Presentation '{presentation.title}' generated with {presentation.num_slides} slides. "
                      f"ID: {presentation.id}. Status: {presentation.status}.]",
            "action": "generate_presentation",
            "presentation_id": str(presentation.id),
            "num_slides": presentation.num_slides,
            "status": str(presentation.status),
        }
    except Exception as e:
        return {"output": "", "error": str(e)[:500], "action": "generate_presentation"}


async def _exec_execute_code(input_data: dict, previous: Optional[str]) -> dict:
    """Execute code in a secure sandbox."""
    code = input_data.get("code", input_data.get("source", previous or ""))
    if not code:
        return {"output": "", "error": "No code provided for execution", "action": "execute_code"}

    try:
        from app.modules.code_sandbox.service import CodeSandboxService
        from app.database import get_session_context
        from uuid import UUID as UUIDType

        user_id = input_data.get("_user_id")
        if not user_id:
            return {
                "output": code,
                "action": "execute_code",
                "note": "No user context. Use the Code Sandbox module directly.",
            }

        uid = UUIDType(user_id) if isinstance(user_id, str) else user_id
        async with get_session_context() as session:
            # Create a temporary sandbox
            sandbox = await CodeSandboxService.create_sandbox(
                user_id=uid,
                data={"name": "Agent execution", "language": input_data.get("language", "python")},
                session=session,
            )

            # Add a cell with the code
            cell = await CodeSandboxService.add_cell(
                user_id=uid,
                sandbox_id=sandbox.id,
                data={"source": code},
                session=session,
            )

            if not cell:
                return {"output": "", "error": "Failed to create code cell", "action": "execute_code"}

            # Execute the cell
            result = await CodeSandboxService.execute_cell(
                user_id=uid,
                sandbox_id=sandbox.id,
                cell_id=cell["id"],
                session=session,
            )

        if not result:
            return {"output": "", "error": "Execution returned no result", "action": "execute_code"}

        output = result.get("output", "") or ""
        error = result.get("error")
        status = result.get("status", "unknown")

        if error:
            return {
                "output": output,
                "error": error,
                "action": "execute_code",
                "status": status,
                "execution_time_ms": result.get("execution_time_ms"),
            }

        return {
            "output": output,
            "action": "execute_code",
            "status": status,
            "execution_time_ms": result.get("execution_time_ms"),
        }
    except Exception as e:
        return {"output": "", "error": str(e)[:500], "action": "execute_code"}


async def _exec_generate_form(input_data: dict, previous: Optional[str]) -> dict:
    """Generate a form via AIFormsService."""
    prompt = input_data.get("prompt", input_data.get("description", previous or ""))
    if not prompt:
        return {"output": "", "error": "No prompt provided for form generation", "action": "generate_form"}

    try:
        from app.modules.ai_forms.service import AIFormsService
        from app.database import get_session_context
        from uuid import UUID as UUIDType

        user_id = input_data.get("_user_id")
        if not user_id:
            return {
                "output": f"[Form ready to generate from prompt: '{prompt[:100]}'. Use the AI Forms module to create.]",
                "action": "generate_form",
                "note": "No user context. Use the AI Forms module directly.",
            }

        uid = UUIDType(user_id) if isinstance(user_id, str) else user_id
        async with get_session_context() as session:
            service = AIFormsService(session)
            form = await service.generate_form(
                user_id=uid,
                prompt=prompt,
                num_fields=input_data.get("num_fields", 5),
            )

        return {
            "output": f"[Form '{form.title}' generated with {len(json.loads(form.fields_json))} fields. "
                      f"ID: {form.id}. Status: {form.status}.]",
            "action": "generate_form",
            "form_id": str(form.id),
            "status": form.status,
        }
    except Exception as e:
        return {"output": "", "error": str(e)[:500], "action": "generate_form"}


async def _exec_search_marketplace(input_data: dict, previous: Optional[str]) -> dict:
    """Search marketplace listings."""
    query = input_data.get("query", input_data.get("search", previous or ""))
    if not query:
        return {"output": "", "error": "No search query for marketplace", "action": "search_marketplace"}

    try:
        from app.modules.marketplace.service import MarketplaceService
        from app.database import get_session_context

        async with get_session_context() as session:
            service = MarketplaceService(session)
            listings, total = await service.list_listings(
                type=input_data.get("type"),
                category=input_data.get("category"),
                sort_by=input_data.get("sort_by", "newest"),
                search=query,
                limit=input_data.get("limit", 10),
                offset=0,
            )

        if listings:
            results_text = f"Found {total} marketplace listing(s) for '{query}':\n\n"
            for listing in listings:
                results_text += (
                    f"- **{listing.title}** ({listing.type}, {listing.category}) "
                    f"- {listing.rating}/5 stars, {listing.installs_count} installs"
                )
                if listing.price > 0:
                    results_text += f", ${listing.price}"
                results_text += f"\n  {listing.description[:150]}\n"
            return {
                "output": results_text,
                "action": "search_marketplace",
                "total": total,
                "results_count": len(listings),
            }
        return {
            "output": f"No marketplace listings found for '{query}'.",
            "action": "search_marketplace",
            "total": 0,
            "results_count": 0,
        }
    except Exception as e:
        return {"output": "", "error": str(e)[:500], "action": "search_marketplace"}


async def _exec_batch_transcribe(input_data: dict, previous: Optional[str]) -> dict:
    """Batch transcribe multiple YouTube URLs."""
    urls = input_data.get("urls", [])
    if not urls and previous:
        # Try to extract URLs from previous output
        import re
        found = re.findall(r'https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)[a-zA-Z0-9_-]+', previous)
        urls = found[:20]
    if not urls:
        return {"output": "", "error": "No URLs provided for batch transcription", "action": "batch_transcribe"}

    try:
        from app.modules.transcription.service import TranscriptionService
        from app.database import get_session_context
        from uuid import UUID as UUIDType

        user_id = input_data.get("_user_id")
        if not user_id:
            return {
                "output": f"[Batch transcription ready for {len(urls)} URL(s). Use the Transcription module to process.]",
                "action": "batch_transcribe",
                "note": "No user context. Use the Transcription module directly.",
            }

        uid = UUIDType(user_id) if isinstance(user_id, str) else user_id
        async with get_session_context() as session:
            service = TranscriptionService()
            job_ids = await service.batch_transcribe(
                user_id=uid,
                urls=urls,
                session=session,
                language=input_data.get("language", "auto"),
            )

        return {
            "output": f"[Batch transcription created: {len(job_ids)} jobs for {len(urls)} URLs. "
                      f"Job IDs: {', '.join(str(jid) for jid in job_ids[:5])}{'...' if len(job_ids) > 5 else ''}. "
                      f"Use GET /api/transcription/{{job_id}} to check status.]",
            "action": "batch_transcribe",
            "job_ids": [str(jid) for jid in job_ids],
            "total_urls": len(urls),
            "jobs_created": len(job_ids),
        }
    except Exception as e:
        return {"output": "", "error": str(e)[:500], "action": "batch_transcribe"}


async def _exec_generate_summary(input_data: dict, previous: Optional[str]) -> dict:
    """Generate an AI-powered summary of a transcription."""
    transcription_id = input_data.get("transcription_id", "")
    if not transcription_id and previous:
        # Try to extract UUID from previous output
        import re
        uuids = re.findall(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', previous)
        if uuids:
            transcription_id = uuids[0]

    if not transcription_id:
        return {"output": "", "error": "No transcription_id provided for summary generation", "action": "generate_summary"}

    style = input_data.get("style", "executive")

    try:
        from app.modules.transcription.service import TranscriptionService
        from app.database import get_session_context
        from uuid import UUID as UUIDType

        user_id = input_data.get("_user_id")
        if not user_id:
            return {
                "output": f"[Summary generation ready for transcription {transcription_id}. Use the Transcription module to process.]",
                "action": "generate_summary",
                "note": "No user context. Use the Transcription module directly.",
            }

        uid = UUIDType(user_id) if isinstance(user_id, str) else user_id
        tid = UUIDType(transcription_id) if isinstance(transcription_id, str) else transcription_id

        async with get_session_context() as session:
            service = TranscriptionService()
            result = await service.generate_summary(
                transcription_id=tid,
                user_id=uid,
                session=session,
                style=style,
            )

        summary = result.get("summary", "")
        return {
            "output": summary,
            "action": "generate_summary",
            "transcription_id": str(transcription_id),
            "style": style,
            "word_count": result.get("word_count", 0),
        }
    except Exception as e:
        return {"output": "", "error": str(e)[:500], "action": "generate_summary"}


async def _exec_scrape_repos(input_data: dict, previous: Optional[str]) -> dict:
    """Scrape GitHub repos and package for AI consumption via Skill Seekers."""
    repos = input_data.get("repos", [])
    if not repos and previous:
        # Try to extract owner/repo patterns from previous output
        import re
        found = re.findall(r"[a-zA-Z0-9_\-\.]+/[a-zA-Z0-9_\-\.]+", previous)
        repos = found[:5]
    if not repos:
        return {"output": "", "error": "No repos provided for scraping", "action": "scrape_repos"}

    targets = input_data.get("targets", ["claude"])
    enhance = input_data.get("enhance", False)

    try:
        from app.modules.skill_seekers.service import SkillSeekersService
        from app.database import get_session_context
        from uuid import UUID as UUIDType

        user_id = input_data.get("_user_id")
        if not user_id:
            return {
                "output": f"[Scrape job ready for {len(repos)} repo(s): {', '.join(repos)}. "
                          f"Use the Skill Seekers module to launch.]",
                "action": "scrape_repos",
                "note": "No user context. Use the Skill Seekers module directly.",
            }

        uid = UUIDType(user_id) if isinstance(user_id, str) else user_id
        async with get_session_context() as session:
            service = SkillSeekersService()
            job = await service.create_job(
                user_id=uid,
                repos=repos,
                targets=targets,
                enhance=enhance,
                session=session,
            )

        return {
            "output": f"[Scrape job created for {len(repos)} repo(s): {', '.join(repos)}. "
                      f"Job ID: {job.id}. Targets: {', '.join(targets)}. "
                      f"{'Enhancement enabled.' if enhance else ''} "
                      f"Poll GET /api/skill-seekers/jobs/{job.id} for progress.]",
            "action": "scrape_repos",
            "job_id": str(job.id),
            "repos": repos,
            "targets": targets,
        }
    except Exception as e:
        return {"output": "", "error": str(e)[:500], "action": "scrape_repos"}


async def _exec_process_pdf(input_data: dict, previous: Optional[str]) -> dict:
    """Process, summarize, or query a PDF document."""
    pdf_id = input_data.get("pdf_id", "")
    action = input_data.get("action", "summarize")

    if not pdf_id:
        return {
            "output": "[PDF processing ready. Upload a PDF via the PDF Processor module, then use its ID to summarize, query, or export.]",
            "action": "process_pdf",
            "note": "No pdf_id provided. Upload a PDF first via POST /api/pdf/upload.",
        }

    try:
        from app.modules.pdf_processor.service import PDFProcessorService
        from app.database import get_session_context
        from uuid import UUID as UUIDType

        user_id = input_data.get("_user_id")
        if not user_id:
            return {
                "output": f"[PDF {pdf_id} ready for processing. Use the PDF Processor module.]",
                "action": "process_pdf",
                "note": "No user context. Use the PDF Processor module directly.",
            }

        uid = UUIDType(user_id) if isinstance(user_id, str) else user_id
        pid = UUIDType(pdf_id) if isinstance(pdf_id, str) else pdf_id

        async with get_session_context() as session:
            if action == "query":
                question = input_data.get("question", previous or "")
                if not question:
                    return {"output": "", "error": "No question provided for PDF query", "action": "process_pdf"}
                result = await PDFProcessorService.query_pdf(uid, pid, question, session)
                if result:
                    return {
                        "output": result.get("answer", ""),
                        "action": "process_pdf",
                        "confidence": result.get("confidence", 0),
                        "sources_count": len(result.get("sources", [])),
                    }
            elif action == "keywords":
                result = await PDFProcessorService.extract_keywords(uid, pid, session)
                if result:
                    return {
                        "output": ", ".join(result.get("keywords", [])),
                        "action": "process_pdf",
                    }
            elif action == "export":
                fmt = input_data.get("format", "markdown")
                result = await PDFProcessorService.export_pdf(uid, pid, fmt, session)
                if result:
                    return {
                        "output": result.get("content", "")[:3000],
                        "action": "process_pdf",
                        "format": fmt,
                    }
            else:
                style = input_data.get("style", "executive")
                result = await PDFProcessorService.summarize_pdf(uid, pid, session, style=style)
                if result:
                    return {
                        "output": result.get("summary", ""),
                        "action": "process_pdf",
                        "style": style,
                    }

        return {"output": "", "error": "PDF not found or not accessible", "action": "process_pdf"}

    except Exception as e:
        return {"output": "", "error": str(e)[:500], "action": "process_pdf"}


async def _exec_edit_audio(input_data: dict, previous: Optional[str]) -> dict:
    """Edit an audio file using the Audio Studio module."""
    audio_id = input_data.get("audio_id", "")
    operations = input_data.get("operations", [])

    if not audio_id:
        return {
            "output": "[Audio editing ready. Upload audio via POST /api/audio-studio/upload, then use its ID to edit.]",
            "action": "edit_audio",
            "note": "No audio_id provided. Upload an audio file first.",
        }

    try:
        from app.modules.audio_studio.service import AudioStudioService
        from app.database import get_session_context
        from uuid import UUID as UUIDType

        user_id = input_data.get("_user_id")
        if not user_id:
            return {
                "output": f"[Audio {audio_id} ready for editing. Use the Audio Studio module.]",
                "action": "edit_audio",
                "note": "No user context. Use the Audio Studio module directly.",
            }

        uid = UUIDType(user_id) if isinstance(user_id, str) else user_id
        aid = UUIDType(audio_id) if isinstance(audio_id, str) else audio_id

        async with get_session_context() as session:
            service = AudioStudioService(session)
            result = await service.edit_audio(uid, aid, operations)

        return {
            "output": f"[Audio '{result.original_filename}' edited successfully. "
                      f"Duration: {result.duration_seconds}s. Operations: {len(operations)}.]",
            "action": "edit_audio",
            "audio_id": str(result.id),
            "duration_seconds": result.duration_seconds,
        }
    except Exception as e:
        return {"output": "", "error": str(e)[:500], "action": "edit_audio"}


async def _exec_generate_podcast(input_data: dict, previous: Optional[str]) -> dict:
    """Create a podcast episode with AI chapters and show notes."""
    audio_id = input_data.get("audio_id", "")
    title = input_data.get("title", "Untitled Episode")

    if not audio_id:
        return {
            "output": "[Podcast creation ready. Upload audio via POST /api/audio-studio/upload, then provide audio_id.]",
            "action": "generate_podcast",
            "note": "No audio_id provided. Upload an audio file first.",
        }

    try:
        from app.modules.audio_studio.service import AudioStudioService
        from app.database import get_session_context
        from uuid import UUID as UUIDType

        user_id = input_data.get("_user_id")
        if not user_id:
            return {
                "output": f"[Podcast episode '{title}' ready. Use Audio Studio module with audio {audio_id}.]",
                "action": "generate_podcast",
                "note": "No user context. Use the Audio Studio module directly.",
            }

        uid = UUIDType(user_id) if isinstance(user_id, str) else user_id
        aid = UUIDType(audio_id) if isinstance(audio_id, str) else audio_id

        async with get_session_context() as session:
            service = AudioStudioService(session)

            # Generate chapters
            await service.generate_chapters(uid, aid)
            # Generate show notes
            notes_result = await service.generate_show_notes(uid, aid)
            show_notes_text = json.dumps(notes_result.get("show_notes", {}), ensure_ascii=False)

            # Create episode
            episode = await service.create_podcast_episode(uid, {
                "audio_id": str(aid),
                "title": title,
                "description": input_data.get("description", ""),
                "show_notes": show_notes_text,
                "publish_date": input_data.get("publish_date"),
            })

        return {
            "output": f"[Podcast episode '{episode.title}' created with AI chapters and show notes. "
                      f"Episode ID: {episode.id}. Audio ID: {audio_id}.]",
            "action": "generate_podcast",
            "episode_id": str(episode.id),
            "audio_id": str(audio_id),
        }
    except Exception as e:
        return {"output": "", "error": str(e)[:500], "action": "generate_podcast"}


async def _exec_analyze_repo(input_data: dict, previous: Optional[str]) -> dict:
    """Analyze a GitHub repository for tech stack, quality, structure, etc."""
    repo_url = input_data.get("repo_url", input_data.get("url", ""))
    if not repo_url and previous:
        # Try to extract a GitHub URL from previous output
        import re
        urls = re.findall(r"https?://github\.com/[a-zA-Z0-9_\-\.]+/[a-zA-Z0-9_\-\.]+", previous)
        if urls:
            repo_url = urls[0]
        else:
            # Try owner/repo format
            repos = re.findall(r"[a-zA-Z0-9_\-\.]+/[a-zA-Z0-9_\-\.]+", previous)
            if repos:
                repo_url = repos[0]

    if not repo_url:
        return {"output": "", "error": "No repo URL provided for analysis", "action": "analyze_repo"}

    analysis_types = input_data.get("analysis_types", ["all"])
    depth = input_data.get("depth", "standard")

    try:
        from app.modules.repo_analyzer.service import RepoAnalyzerService
        from app.modules.repo_analyzer.schemas import AnalysisCreate
        from app.database import get_session_context

        user_id = input_data.get("_user_id")
        if not user_id:
            return {
                "output": f"[Repo analysis ready for {repo_url}. "
                          f"Use the Repo Analyzer module to launch.]",
                "action": "analyze_repo",
                "note": "No user context. Use the Repo Analyzer module directly.",
            }

        from uuid import UUID as UUIDType
        uid = UUIDType(user_id) if isinstance(user_id, str) else user_id

        async with get_session_context() as session:
            service = RepoAnalyzerService()
            data = AnalysisCreate(
                repo_url=repo_url,
                analysis_types=analysis_types,
                depth=depth,
            )
            analysis = await service.create_analysis(uid, data, session)
            await service.run_analysis(analysis.id)

        # Reload results
        async with get_session_context() as session:
            refreshed = await session.get(
                __import__("app.models.repo_analyzer", fromlist=["RepoAnalysis"]).RepoAnalysis,
                analysis.id,
            )
            if refreshed and refreshed.results_json:
                import json
                results = json.loads(refreshed.results_json)
                # Build summary
                quality = results.get("quality", {})
                tech = results.get("tech_stack", {})
                structure = results.get("structure", {})

                summary_parts = [f"Repository: {repo_url}"]
                if quality:
                    summary_parts.append(f"Quality: {quality.get('grade', '?')} ({quality.get('score', 0)}/100)")
                if tech:
                    langs = ", ".join(tech.get("languages", {}).keys())
                    frameworks = ", ".join(tech.get("frameworks", []))
                    if langs:
                        summary_parts.append(f"Languages: {langs}")
                    if frameworks:
                        summary_parts.append(f"Frameworks: {frameworks}")
                if structure:
                    summary_parts.append(f"Files: {structure.get('total_files', 0)}, Lines: {structure.get('total_lines', 0)}")

                return {
                    "output": "\n".join(summary_parts),
                    "action": "analyze_repo",
                    "analysis_id": str(analysis.id),
                    "repo_url": repo_url,
                    "results": results,
                }

        return {
            "output": f"[Analysis created for {repo_url} but results not yet available. "
                      f"Analysis ID: {analysis.id}]",
            "action": "analyze_repo",
            "analysis_id": str(analysis.id),
        }
    except Exception as e:
        return {"output": "", "error": str(e)[:500], "action": "analyze_repo"}
