"""
Pipeline service - Business logic for creating and executing AI pipelines.
"""

import json
from datetime import UTC, datetime
from typing import Optional
from uuid import UUID

import structlog
from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.pipeline import Pipeline, PipelineExecution, PipelineStatus, ExecutionStatus

logger = structlog.get_logger()


class PipelineService:
    """Service for managing AI pipelines and their executions."""

    @staticmethod
    async def create_pipeline(
        user_id: UUID,
        name: str,
        description: Optional[str],
        steps: list[dict],
        is_template: bool,
        session: AsyncSession,
    ) -> Pipeline:
        """Create a new pipeline."""
        pipeline = Pipeline(
            user_id=user_id,
            name=name,
            description=description,
            steps_json=json.dumps(steps, ensure_ascii=False),
            is_template=is_template,
        )
        session.add(pipeline)
        await session.commit()
        await session.refresh(pipeline)

        logger.info(
            "pipeline_created",
            pipeline_id=str(pipeline.id),
            user_id=str(user_id),
            steps_count=len(steps),
        )
        return pipeline

    @staticmethod
    async def get_pipeline(
        pipeline_id: UUID,
        user_id: UUID,
        session: AsyncSession,
    ) -> Optional[Pipeline]:
        """Get a pipeline by ID, verifying ownership."""
        pipeline = await session.get(Pipeline, pipeline_id)
        if pipeline and pipeline.user_id != user_id:
            return None
        return pipeline

    @staticmethod
    async def list_pipelines(
        user_id: UUID,
        session: AsyncSession,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Pipeline], int]:
        """List user's pipelines with pagination."""
        count_result = await session.execute(
            select(func.count()).select_from(Pipeline).where(
                Pipeline.user_id == user_id
            )
        )
        total = count_result.scalar_one()

        result = await session.execute(
            select(Pipeline)
            .where(Pipeline.user_id == user_id)
            .order_by(Pipeline.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        pipelines = list(result.scalars().all())

        return pipelines, total

    @staticmethod
    async def update_pipeline(
        pipeline_id: UUID,
        user_id: UUID,
        updates: dict,
        session: AsyncSession,
    ) -> Optional[Pipeline]:
        """Update a pipeline."""
        pipeline = await session.get(Pipeline, pipeline_id)
        if not pipeline or pipeline.user_id != user_id:
            return None

        if "name" in updates and updates["name"]:
            pipeline.name = updates["name"]
        if "description" in updates:
            pipeline.description = updates["description"]
        if "steps" in updates and updates["steps"] is not None:
            pipeline.steps_json = json.dumps(
                [s if isinstance(s, dict) else s.model_dump() for s in updates["steps"]],
                ensure_ascii=False,
            )
        if "status" in updates and updates["status"]:
            pipeline.status = updates["status"]

        pipeline.updated_at = datetime.now(UTC)
        session.add(pipeline)
        await session.commit()
        await session.refresh(pipeline)

        return pipeline

    @staticmethod
    async def delete_pipeline(
        pipeline_id: UUID,
        user_id: UUID,
        session: AsyncSession,
    ) -> bool:
        """Delete a pipeline and its executions."""
        pipeline = await session.get(Pipeline, pipeline_id)
        if not pipeline or pipeline.user_id != user_id:
            return False

        # Delete executions first
        exec_result = await session.execute(
            select(PipelineExecution).where(
                PipelineExecution.pipeline_id == pipeline_id
            )
        )
        for execution in exec_result.scalars().all():
            await session.delete(execution)

        await session.delete(pipeline)
        await session.commit()

        logger.info("pipeline_deleted", pipeline_id=str(pipeline_id))
        return True

    @staticmethod
    async def execute_pipeline(
        pipeline_id: UUID,
        user_id: UUID,
        session: AsyncSession,
    ) -> Optional[PipelineExecution]:
        """Start executing a pipeline."""
        pipeline = await session.get(Pipeline, pipeline_id)
        if not pipeline or pipeline.user_id != user_id:
            return None

        steps = json.loads(pipeline.steps_json)

        execution = PipelineExecution(
            pipeline_id=pipeline_id,
            user_id=user_id,
            status=ExecutionStatus.RUNNING,
            current_step=0,
            total_steps=len(steps),
            started_at=datetime.now(UTC),
        )
        session.add(execution)
        await session.flush()

        results = []
        previous_output = None

        try:
            for i, step in enumerate(steps):
                execution.current_step = i + 1
                session.add(execution)
                await session.flush()

                step_result = await PipelineService._execute_step(
                    step, previous_output, pipeline=pipeline, session=session
                )
                results.append(step_result)
                previous_output = step_result.get("output", "")

            execution.status = ExecutionStatus.COMPLETED
            execution.results_json = json.dumps(results, ensure_ascii=False)
            execution.completed_at = datetime.now(UTC)
            session.add(execution)
            await session.commit()

        except Exception as e:
            await session.rollback()
            execution.status = ExecutionStatus.FAILED
            execution.error = str(e)[:2000]
            execution.results_json = json.dumps(results, ensure_ascii=False)
            execution.completed_at = datetime.now(UTC)
            session.add(execution)
            await session.commit()
            logger.error(
                "pipeline_execution_failed",
                execution_id=str(execution.id),
                error=str(e),
            )

        await session.refresh(execution)

        logger.info(
            "pipeline_execution_finished",
            execution_id=str(execution.id),
            status=execution.status.value,
            steps_completed=execution.current_step,
        )

        return execution

    @staticmethod
    async def _execute_step(
        step: dict,
        previous_output: Optional[str],
        pipeline: Optional["Pipeline"] = None,
        session: Optional[AsyncSession] = None,
    ) -> dict:
        """Execute a single pipeline step."""
        step_type = step.get("type", "unknown")
        config = step.get("config", {})

        if step_type == "summarize":
            return await PipelineService._step_summarize(previous_output or "", config)
        elif step_type == "translate":
            return await PipelineService._step_translate(previous_output or "", config)
        elif step_type == "transcription":
            return {"type": "transcription", "output": previous_output or "", "note": "Transcription step requires external input"}
        elif step_type == "web_crawl":
            from app.modules.web_crawler.service import WebCrawlerService
            url = config.get("url", previous_output or "")
            if url:
                result = await WebCrawlerService.scrape(url=url, extract_images=True)
                if result.get("success"):
                    step_output = result.get("markdown", "")
                else:
                    step_output = f"Crawl failed: {result.get('error', 'unknown')}"
            else:
                step_output = "No URL provided for web crawl"
            return {"type": "web_crawl", "output": step_output}
        elif step_type == "export":
            return {"type": "export", "output": previous_output or "", "format": config.get("format", "txt")}

        # ---- Sentiment analysis step ----
        elif step_type == "sentiment":
            text = config.get("text", previous_output or "")
            if text:
                from app.modules.sentiment.service import SentimentService
                result = await SentimentService.analyze_text(text[:10000])
                overall = result.get("overall_sentiment", "neutral")
                score = result.get("overall_score", 0)
                pos = result.get("positive_percent", 0)
                neg = result.get("negative_percent", 0)
                step_output = f"Sentiment: {overall} (score: {score})\nPositive: {pos}%\nNegative: {neg}%"

                emotions = result.get("emotion_summary", {})
                if emotions:
                    step_output += "\nEmotions: " + ", ".join(
                        f"{k}({v})" for k, v in emotions.items()
                    )
            else:
                step_output = "No text to analyze"
            return {"type": "sentiment", "output": step_output}

        # ---- Knowledge Base search step ----
        elif step_type == "search_knowledge":
            query = config.get("query", previous_output or "")
            if query and pipeline:
                from app.modules.knowledge.service import KnowledgeService
                results = await KnowledgeService.search(
                    user_id=pipeline.user_id,
                    query=query[:500],
                    session=session,
                    limit=config.get("limit", 5),
                )
                if results:
                    step_output = "\n\n".join(
                        f"[{r.get('filename', '')}] {r.get('content', '')}"
                        for r in results
                    )
                else:
                    step_output = "No results found"
            else:
                step_output = "No query provided" if not query else "No pipeline context"
            return {"type": "search_knowledge", "output": step_output}

        # ---- RAG question step ----
        elif step_type == "ask_knowledge":
            question = config.get("question", previous_output or "")
            if question and pipeline:
                from app.modules.knowledge.service import KnowledgeService
                result = await KnowledgeService.rag_query(
                    user_id=pipeline.user_id,
                    question=question[:1000],
                    session=session,
                )
                step_output = result.get("answer", "") if result else "No answer found"
            else:
                step_output = "No question provided" if not question else "No pipeline context"
            return {"type": "ask_knowledge", "output": step_output}

        # ---- AI model comparison step ----
        elif step_type == "compare":
            prompt = config.get("prompt", previous_output or "")
            providers = config.get("providers", ["gemini", "groq"])
            if prompt and pipeline:
                from app.modules.compare.service import CompareService
                _, results = await CompareService.run_comparison(
                    user_id=pipeline.user_id,
                    prompt=prompt[:5000],
                    providers=providers,
                    session=session,
                )
                if results:
                    step_output = "\n\n".join(
                        f"[{r.get('provider', '?')}] ({r.get('response_time_ms', 0)}ms)\n{r.get('response', '')}"
                        for r in results
                    )
                else:
                    step_output = "Comparison failed"
            else:
                step_output = "No prompt for comparison" if not prompt else "No pipeline context"
            return {"type": "compare", "output": step_output}

        # ---- Crawl and auto-index to Knowledge Base step ----
        elif step_type == "crawl_and_index":
            url = config.get("url", previous_output or "")
            if url and url.startswith("http") and pipeline:
                from app.modules.web_crawler.service import WebCrawlerService
                result = await WebCrawlerService.index_to_knowledge_base(
                    url=url,
                    user_id=pipeline.user_id,
                    crawl_subpages=config.get("crawl_subpages", False),
                    max_pages=config.get("max_pages", 3),
                    include_images=True,
                    session=session,
                )
                if result.get("success"):
                    step_output = f"Indexed {result.get('pages_crawled', 0)} pages, {result.get('chunks_indexed', 0)} chunks"
                else:
                    step_output = f"Indexing failed: {result.get('error', 'unknown')}"
            else:
                if not url or not url.startswith("http"):
                    step_output = "No valid URL provided"
                else:
                    step_output = "No pipeline context"
            return {"type": "crawl_and_index", "output": step_output}

        # ---- Content Studio step ----
        elif step_type == "content_studio":
            text = config.get("text", previous_output or "")
            fmt = config.get("format", "blog_article")
            if text:
                try:
                    from app.models.content_studio import ContentFormat
                    from app.modules.content_studio.service import ContentStudioService
                    result = await ContentStudioService._generate_single(
                        source_text=text[:12000],
                        fmt=ContentFormat(fmt),
                        tone=config.get("tone", "professional"),
                        target_audience=config.get("target_audience"),
                        keywords=None,
                        language=config.get("language", "auto"),
                        provider=config.get("provider"),
                        custom_instructions=config.get("instructions"),
                        user_id=getattr(pipeline, "user_id", None),
                    )
                    step_output = result.get("content", "")
                except Exception as e:
                    step_output = f"Content generation failed: {str(e)[:500]}"
            else:
                step_output = "No text for content generation"
            return {"type": "content_studio", "output": step_output, "format": fmt}

        # ---- Generate image step ----
        elif step_type == "generate_image":
            prompt = config.get("prompt", previous_output or "")
            style = config.get("style", "digital_art")
            if prompt and pipeline:
                try:
                    from app.modules.image_gen.service import ImageGenService
                    image = await ImageGenService.generate_image(
                        user_id=pipeline.user_id, prompt=prompt[:2000], style=style,
                        provider=config.get("provider", "gemini"),
                        width=config.get("width", 1024), height=config.get("height", 1024),
                        session=session,
                    )
                    step_output = f"Image generated: {image.image_url or 'processing'} (style: {style})"
                except Exception as e:
                    step_output = f"Image generation failed: {str(e)[:500]}"
            else:
                step_output = "No prompt for image generation"
            return {"type": "generate_image", "output": step_output}

        # ---- Generate video step ----
        elif step_type == "generate_video":
            prompt = config.get("prompt", previous_output or "")
            if prompt and pipeline:
                try:
                    from app.modules.video_gen.service import VideoGenService
                    video = await VideoGenService.generate_video(
                        user_id=pipeline.user_id,
                        title=config.get("title", "Pipeline Video"),
                        prompt=prompt[:2000],
                        video_type=config.get("video_type", "text_to_video"),
                        provider=config.get("provider", "gemini"),
                        duration_s=config.get("duration_s", 10),
                        width=1920, height=1080, session=session,
                    )
                    step_output = f"Video generated: {video.video_url or 'processing'}"
                except Exception as e:
                    step_output = f"Video generation failed: {str(e)[:500]}"
            else:
                step_output = "No prompt for video generation"
            return {"type": "generate_video", "output": step_output}

        # ---- Text-to-speech step ----
        elif step_type == "text_to_speech":
            text = config.get("text", previous_output or "")
            if text and pipeline:
                try:
                    from app.modules.voice_clone.service import VoiceCloneService
                    synthesis = await VoiceCloneService.synthesize(
                        user_id=pipeline.user_id, text=text[:5000],
                        voice_id=config.get("voice_id"),
                        provider=config.get("provider", "openai"),
                        output_format="mp3", language=config.get("language", "auto"),
                        session=session,
                    )
                    step_output = f"Audio generated: {synthesis.audio_url or 'processing'} ({synthesis.duration_s}s)"
                except Exception as e:
                    step_output = f"TTS failed: {str(e)[:500]}"
            else:
                step_output = "No text for TTS"
            return {"type": "text_to_speech", "output": step_output}

        # ---- Security scan step ----
        elif step_type == "security_scan":
            text = config.get("text", previous_output or "")
            if text:
                try:
                    from app.modules.security_guardian.service import SecurityGuardianService
                    findings = SecurityGuardianService._detect_pii(text) + SecurityGuardianService._detect_prompt_injection(text)
                    if findings:
                        step_output = f"Found {len(findings)} issue(s):\n" + "\n".join(
                            f"- [{f['severity']}] {f['type']}: {f['description']}" for f in findings[:10]
                        )
                    else:
                        step_output = "Content is clean - no security issues found."
                except Exception as e:
                    step_output = f"Scan failed: {str(e)[:500]}"
            else:
                step_output = "No text to scan"
            return {"type": "security_scan", "output": step_output}

        # ---- Publish to social platforms step ----
        elif step_type == "publish_social":
            text = config.get("text", previous_output or "")
            platforms = config.get("platforms", ["twitter"])
            if text and pipeline:
                try:
                    from app.modules.social_publisher.service import SocialPublisherService
                    post = await SocialPublisherService.create_post(
                        user_id=pipeline.user_id,
                        content=text[:5000],
                        platforms=platforms,
                        session=session,
                        hashtags=config.get("hashtags"),
                    )
                    published = await SocialPublisherService.publish_post(
                        user_id=pipeline.user_id,
                        post_id=post.id,
                        session=session,
                    )
                    step_output = f"Published to {', '.join(platforms)} (post_id: {published.id})"
                except Exception as e:
                    step_output = f"Social publish failed: {str(e)[:500]}"
            else:
                step_output = "No content to publish" if not text else "No pipeline context"
            return {"type": "publish_social", "output": step_output}

        # ---- Search marketplace step ----
        elif step_type == "search_marketplace":
            query = config.get("query", previous_output or "")
            if query:
                try:
                    from app.modules.marketplace.service import MarketplaceService
                    svc = MarketplaceService(session)
                    listings, total = await svc.list_listings(
                        search=query[:200],
                        category=config.get("category"),
                        limit=config.get("limit", 5),
                    )
                    if listings:
                        step_output = f"Found {total} result(s):\n" + "\n".join(
                            f"- {l.title} ({l.type}/{l.category}) v{l.version}" for l in listings
                        )
                    else:
                        step_output = "No marketplace listings found"
                except Exception as e:
                    step_output = f"Marketplace search failed: {str(e)[:500]}"
            else:
                step_output = "No search query provided"
            return {"type": "search_marketplace", "output": step_output}

        # ---- Deploy chatbot step ----
        elif step_type == "deploy_chatbot":
            text = config.get("system_prompt", previous_output or "")
            name = config.get("name", "Pipeline Chatbot")
            if text and pipeline:
                try:
                    from app.modules.ai_chatbot_builder.service import ChatbotBuilderService
                    svc = ChatbotBuilderService(session)
                    chatbot = await svc.create_chatbot(
                        user_id=pipeline.user_id,
                        data={
                            "name": name,
                            "system_prompt": text[:10000],
                            "model": config.get("model", "gemini"),
                            "personality": config.get("personality", "professional"),
                            "welcome_message": config.get("welcome_message"),
                        },
                    )
                    published = await svc.publish_chatbot(
                        user_id=pipeline.user_id,
                        chatbot_id=chatbot.id,
                    )
                    step_output = f"Chatbot deployed: {published.name} (token: {published.embed_token})"
                except Exception as e:
                    step_output = f"Chatbot deploy failed: {str(e)[:500]}"
            else:
                step_output = "No system prompt for chatbot" if not text else "No pipeline context"
            return {"type": "deploy_chatbot", "output": step_output}

        # ---- Create webhook connector step ----
        elif step_type == "create_webhook":
            url = config.get("url", previous_output or "")
            if url and url.startswith("http") and pipeline:
                try:
                    from app.modules.integration_hub.service import IntegrationHubService
                    svc = IntegrationHubService(session)
                    connector = await svc.create_connector(
                        user_id=pipeline.user_id,
                        data={
                            "name": config.get("name", "Pipeline Webhook"),
                            "type": "webhook",
                            "provider": "custom",
                            "config": {
                                "url": url,
                                "method": config.get("method", "POST"),
                                "headers": config.get("headers", {}),
                            },
                            "enabled": True,
                        },
                    )
                    step_output = f"Webhook created: {connector.name} (id: {connector.id})"
                except Exception as e:
                    step_output = f"Webhook creation failed: {str(e)[:500]}"
            else:
                if not url or not url.startswith("http"):
                    step_output = "No valid URL provided for webhook"
                else:
                    step_output = "No pipeline context"
            return {"type": "create_webhook", "output": step_output}

        # ---- Sentiment analysis with RoBERTa step ----
        elif step_type == "analyze_sentiment_roberta":
            text = config.get("text", previous_output or "")
            if text:
                try:
                    from app.modules.sentiment.service import SentimentService
                    result = await SentimentService.analyze_text(text[:10000])
                    method = result.get("sentiment_method", "llm")
                    overall = result.get("overall_sentiment", "neutral")
                    score = result.get("overall_score", 0)
                    pos = result.get("positive_percent", 0)
                    neg = result.get("negative_percent", 0)
                    step_output = (
                        f"Sentiment ({method}): {overall} (score: {score})\n"
                        f"Positive: {pos}%\nNegative: {neg}%"
                    )
                    emotions = result.get("emotion_summary", {})
                    if emotions:
                        step_output += "\nEmotions: " + ", ".join(
                            f"{k}({v})" for k, v in emotions.items()
                        )
                except Exception as e:
                    step_output = f"RoBERTa sentiment failed: {str(e)[:500]}"
            else:
                step_output = "No text to analyze"
            return {"type": "analyze_sentiment_roberta", "output": step_output}

        # ---- Upscale image step ----
        elif step_type == "upscale_image":
            image_id = config.get("image_id", previous_output or "")
            scale = config.get("scale", 2)
            if image_id and pipeline:
                try:
                    from uuid import UUID as _UUID
                    from app.modules.image_gen.service import ImageGenService
                    parsed_id = _UUID(str(image_id).strip())
                    result = await ImageGenService.upscale_image(
                        user_id=pipeline.user_id,
                        image_id=parsed_id,
                        scale=scale,
                        session=session,
                    )
                    if isinstance(result, dict) and result.get("error"):
                        step_output = f"Upscale failed: {result['error']}"
                    else:
                        step_output = f"Image upscaled ({scale}x): {result.image_url or 'processing'}"
                except Exception as e:
                    step_output = f"Image upscale failed: {str(e)[:500]}"
            else:
                step_output = "No image_id for upscaling" if not image_id else "No pipeline context"
            return {"type": "upscale_image", "output": step_output}

        # ---- Generate presentation step ----
        elif step_type == "generate_presentation":
            text = config.get("text", previous_output or "")
            title = config.get("title", "Pipeline Presentation")
            if text and pipeline:
                try:
                    from app.modules.presentation_gen.service import PresentationGenService
                    svc = PresentationGenService(session)
                    presentation = await svc.generate_presentation(
                        user_id=pipeline.user_id,
                        title=title,
                        topic=text[:2000],
                        num_slides=config.get("num_slides", 10),
                        style=config.get("style", "professional"),
                        template=config.get("template", "default"),
                        language=config.get("language", "fr"),
                        source_text=text[:12000],
                    )
                    step_output = f"Presentation generated: {presentation.title} ({presentation.num_slides} slides, id: {presentation.id})"
                except Exception as e:
                    step_output = f"Presentation generation failed: {str(e)[:500]}"
            else:
                step_output = "No text for presentation" if not text else "No pipeline context"
            return {"type": "generate_presentation", "output": step_output}

        # ---- Execute code step ----
        elif step_type == "execute_code":
            code = config.get("code", previous_output or "")
            if code and pipeline:
                try:
                    from app.modules.code_sandbox.service import CodeSandboxService
                    sandbox = await CodeSandboxService.create_sandbox(
                        user_id=pipeline.user_id,
                        data={"name": config.get("name", "Pipeline Sandbox"), "language": "python"},
                        session=session,
                    )
                    cell = await CodeSandboxService.add_cell(
                        user_id=pipeline.user_id,
                        sandbox_id=sandbox.id,
                        data={"source": code[:50000], "cell_type": "code"},
                        session=session,
                    )
                    result = await CodeSandboxService.execute_cell(
                        user_id=pipeline.user_id,
                        sandbox_id=sandbox.id,
                        cell_id=cell["id"],
                        session=session,
                    )
                    if result and result.get("status") == "success":
                        step_output = result.get("output") or "Code executed successfully (no output)"
                    else:
                        step_output = f"Code error: {result.get('error', 'unknown')}" if result else "Execution failed"
                except Exception as e:
                    step_output = f"Code execution failed: {str(e)[:500]}"
            else:
                step_output = "No code to execute" if not code else "No pipeline context"
            return {"type": "execute_code", "output": step_output}

        # ---- Generate form step ----
        elif step_type == "generate_form":
            prompt = config.get("prompt", previous_output or "")
            if prompt and pipeline:
                try:
                    from app.modules.ai_forms.service import AIFormsService
                    svc = AIFormsService(session)
                    form = await svc.generate_form(
                        user_id=pipeline.user_id,
                        prompt=prompt[:5000],
                        num_fields=config.get("num_fields", 5),
                    )
                    step_output = f"Form generated: {form.title} ({len(json.loads(form.fields_json))} fields, id: {form.id})"
                except Exception as e:
                    step_output = f"Form generation failed: {str(e)[:500]}"
            else:
                step_output = "No prompt for form generation" if not prompt else "No pipeline context"
            return {"type": "generate_form", "output": step_output}

        # ---- Scrape repos step (Skill Seekers) ----
        elif step_type == "scrape_repos":
            repos = config.get("repos", [])
            targets = config.get("targets", ["claude"])
            if not repos and previous_output:
                repos = [previous_output.strip()]
            if repos and pipeline:
                try:
                    from app.modules.skill_seekers.service import SkillSeekersService
                    svc = SkillSeekersService()
                    job = await SkillSeekersService.create_job(
                        user_id=pipeline.user_id,
                        repos=repos,
                        targets=targets,
                        enhance=config.get("enhance", False),
                        session=session,
                    )
                    await svc.run_job(job.id)
                    await session.refresh(job)
                    output_files = json.loads(job.output_files_json) if job.output_files_json else []
                    filenames = [__import__("os").path.basename(f) for f in output_files]
                    step_output = f"Scraped {len(repos)} repo(s) for {', '.join(targets)}: {', '.join(filenames)}" if filenames else "Scrape completed but no output files"
                except Exception as e:
                    step_output = f"Repo scrape failed: {str(e)[:500]}"
            else:
                step_output = "No repos provided" if not repos else "No pipeline context"
            return {"type": "scrape_repos", "output": step_output}

        # ---- Analyze repo step (Repo Analyzer) ----
        elif step_type == "analyze_repo":
            repo_url = config.get("repo_url", previous_output or "").strip()
            analysis_types = config.get("analysis_types", ["all"])
            depth = config.get("depth", "standard")
            if repo_url and pipeline:
                try:
                    from app.modules.repo_analyzer.service import RepoAnalyzerService
                    from app.modules.repo_analyzer.schemas import AnalysisCreate
                    svc = RepoAnalyzerService()
                    data = AnalysisCreate(
                        repo_url=repo_url,
                        analysis_types=analysis_types,
                        depth=depth,
                    )
                    analysis = await svc.create_analysis(pipeline.user_id, data, session)
                    await svc.run_analysis(analysis.id)
                    await session.refresh(analysis)
                    refreshed = analysis
                    if refreshed and refreshed.results_json:
                        results = json.loads(refreshed.results_json)
                        quality = results.get("quality", {})
                        tech = results.get("tech_stack", {})
                        step_output = f"Repo: {repo_url} | Grade: {quality.get('grade', '?')} ({quality.get('score', 0)}/100)"
                        if tech.get("frameworks"):
                            step_output += f" | Frameworks: {', '.join(tech['frameworks'])}"
                    else:
                        step_output = f"Analysis created for {repo_url} but results not available"
                except Exception as e:
                    step_output = f"Repo analysis failed: {str(e)[:500]}"
            else:
                step_output = "No repo URL provided" if not repo_url else "No pipeline context"
            return {"type": "analyze_repo", "output": step_output}

        # ---- PDF processing step ----
        elif step_type == "process_pdf":
            pdf_id = config.get("pdf_id", "")
            action = config.get("action", "summarize")
            if pdf_id and pipeline:
                try:
                    from uuid import UUID as _UUID
                    from app.modules.pdf_processor.service import PDFProcessorService
                    parsed_id = _UUID(str(pdf_id).strip())
                    if action == "query":
                        question = config.get("question", previous_output or "")
                        result = await PDFProcessorService.query_pdf(
                            pipeline.user_id, parsed_id, question, session,
                        )
                        step_output = result.get("answer", "") if result else "PDF query failed"
                    elif action == "keywords":
                        result = await PDFProcessorService.extract_keywords(
                            pipeline.user_id, parsed_id, session,
                        )
                        step_output = ", ".join(result.get("keywords", [])) if result else "Keyword extraction failed"
                    elif action == "export":
                        fmt = config.get("format", "markdown")
                        result = await PDFProcessorService.export_pdf(
                            pipeline.user_id, parsed_id, fmt, session,
                        )
                        step_output = result.get("content", "")[:3000] if result else "Export failed"
                    else:
                        style = config.get("style", "executive")
                        result = await PDFProcessorService.summarize_pdf(
                            pipeline.user_id, parsed_id, session, style=style,
                        )
                        step_output = result.get("summary", "") if result else "Summarization failed"
                except Exception as e:
                    step_output = f"PDF processing failed: {str(e)[:500]}"
            else:
                step_output = "No pdf_id provided" if not pdf_id else "No pipeline context"
            return {"type": "process_pdf", "output": step_output}

        # ---- Audio editing step ----
        elif step_type == "edit_audio":
            audio_id = config.get("audio_id", "")
            operations = config.get("operations", [])
            if audio_id and pipeline:
                try:
                    from uuid import UUID as _UUID
                    from app.modules.audio_studio.service import AudioStudioService
                    parsed_id = _UUID(str(audio_id).strip())
                    service = AudioStudioService(session)
                    result = await service.edit_audio(pipeline.user_id, parsed_id, operations)
                    step_output = f"Audio edited: {result.original_filename} ({result.duration_seconds}s)"
                except Exception as e:
                    step_output = f"Audio edit failed: {str(e)[:500]}"
            else:
                step_output = "No audio_id provided" if not audio_id else "No pipeline context"
            return {"type": "edit_audio", "output": step_output}

        # ---- Audio transcription step ----
        elif step_type == "transcribe_audio":
            audio_id = config.get("audio_id", "")
            if audio_id and pipeline:
                try:
                    from uuid import UUID as _UUID
                    from app.modules.audio_studio.service import AudioStudioService
                    parsed_id = _UUID(str(audio_id).strip())
                    service = AudioStudioService(session)
                    result = await service.transcribe_audio(pipeline.user_id, parsed_id)
                    step_output = result.transcript or "Transcription empty"
                except Exception as e:
                    step_output = f"Audio transcription failed: {str(e)[:500]}"
            else:
                step_output = "No audio_id provided" if not audio_id else "No pipeline context"
            return {"type": "transcribe_audio", "output": step_output}

        # ---- Generate podcast step ----
        elif step_type == "generate_podcast":
            audio_id = config.get("audio_id", "")
            title = config.get("title", "Untitled Episode")
            if audio_id and pipeline:
                try:
                    from uuid import UUID as _UUID
                    from app.modules.audio_studio.service import AudioStudioService
                    parsed_id = _UUID(str(audio_id).strip())
                    service = AudioStudioService(session)
                    await service.generate_chapters(pipeline.user_id, parsed_id)
                    notes = await service.generate_show_notes(pipeline.user_id, parsed_id)
                    import json as _json
                    episode = await service.create_podcast_episode(pipeline.user_id, {
                        "audio_id": str(parsed_id),
                        "title": title,
                        "description": config.get("description", ""),
                        "show_notes": _json.dumps(notes.get("show_notes", {}), ensure_ascii=False),
                    })
                    step_output = f"Podcast episode '{episode.title}' created (ID: {episode.id})"
                except Exception as e:
                    step_output = f"Podcast generation failed: {str(e)[:500]}"
            else:
                step_output = "No audio_id provided" if not audio_id else "No pipeline context"
            return {"type": "generate_podcast", "output": step_output}


        # ---- Fine-tune model step ----
        elif step_type == "fine_tune":
            dataset_id = config.get("dataset_id", "")
            if dataset_id and pipeline:
                try:
                    from app.modules.fine_tuning.service import FineTuningService
                    job = await FineTuningService.create_job(
                        user_id=pipeline.user_id,
                        name=config.get("name", "Pipeline Fine-Tune"),
                        dataset_id=dataset_id,
                        base_model=config.get("base_model", "unsloth/tinyllama-bnb-4bit"),
                        provider=config.get("provider", "local"),
                        hyperparams=config.get("hyperparams", {}),
                        session=session,
                    )
                    step_output = f"Fine-tuning job created: {job.name} (ID: {job.id}, status: {job.status})"
                except Exception as e:
                    step_output = f"Fine-tuning failed: {str(e)[:500]}"
            else:
                step_output = "No dataset_id provided" if not dataset_id else "No pipeline context"
            return {"type": "fine_tune", "output": step_output}
        else:
            return {"type": step_type, "output": previous_output or "", "note": "Unknown step type"}

    @staticmethod
    async def _step_summarize(text: str, config: dict) -> dict:
        """Execute a summarize step using AI."""
        if not text:
            return {"type": "summarize", "output": "", "error": "No input text"}

        try:
            from app.ai_assistant.service import AIAssistantService
            result = await AIAssistantService.process_text_with_provider(
                text=f"Summarize the following text concisely:\n\n{text}",
                task="summarize",
                provider_name=config.get("provider", "gemini"),
            )
            return {
                "type": "summarize",
                "output": result.get("processed_text", ""),
                "provider": result.get("provider", "gemini"),
            }
        except Exception as e:
            return {"type": "summarize", "output": text, "error": str(e)[:500]}

    @staticmethod
    async def _step_translate(text: str, config: dict) -> dict:
        """Execute a translate step using AI."""
        if not text:
            return {"type": "translate", "output": "", "error": "No input text"}

        target_lang = config.get("target_language", "en")
        try:
            from app.ai_assistant.service import AIAssistantService
            result = await AIAssistantService.process_text_with_provider(
                text=f"Translate the following text to {target_lang}:\n\n{text}",
                task="translate",
                provider_name=config.get("provider", "gemini"),
            )
            return {
                "type": "translate",
                "output": result.get("processed_text", ""),
                "target_language": target_lang,
                "provider": result.get("provider", "gemini"),
            }
        except Exception as e:
            return {"type": "translate", "output": text, "error": str(e)[:500]}

    @staticmethod
    async def get_execution(
        execution_id: UUID,
        user_id: UUID,
        session: AsyncSession,
    ) -> Optional[PipelineExecution]:
        """Get a pipeline execution by ID."""
        execution = await session.get(PipelineExecution, execution_id)
        if execution and execution.user_id != user_id:
            return None
        return execution

    @staticmethod
    async def list_executions(
        pipeline_id: UUID,
        user_id: UUID,
        session: AsyncSession,
    ) -> list[PipelineExecution]:
        """List executions for a pipeline."""
        result = await session.execute(
            select(PipelineExecution)
            .where(
                PipelineExecution.pipeline_id == pipeline_id,
                PipelineExecution.user_id == user_id,
            )
            .order_by(PipelineExecution.created_at.desc())
            .limit(20)
        )
        return list(result.scalars().all())
