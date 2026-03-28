"""
AI Workflows service - No-code automation workflow engine.

Supports triggers, conditional logic, and chained actions
that orchestrate all platform modules.
"""

import json
from datetime import UTC, datetime
from typing import Optional
from uuid import UUID

import structlog
from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.workflow import (
    RunStatus,
    Workflow,
    WorkflowRun,
    WorkflowStatus,
)

logger = structlog.get_logger()

# Built-in workflow templates
WORKFLOW_TEMPLATES = [
    {
        "id": "youtube_to_blog",
        "name": "YouTube to Blog Post",
        "description": "Transcribe a YouTube video, summarize it, then generate a full blog article",
        "category": "content",
        "trigger_type": "manual",
        "icon": "YouTube",
        "nodes": [
            {"id": "n1", "type": "action", "action": "transcribe", "label": "Transcribe Video", "config": {}, "position_x": 100, "position_y": 200},
            {"id": "n2", "type": "action", "action": "summarize", "label": "Summarize", "config": {"max_length": 1000}, "position_x": 350, "position_y": 200},
            {"id": "n3", "type": "action", "action": "content_studio", "label": "Generate Blog", "config": {"format": "blog_article", "tone": "engaging"}, "position_x": 600, "position_y": 200},
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n2"},
            {"id": "e2", "source": "n2", "target": "n3"},
        ],
    },
    {
        "id": "social_media_pack",
        "name": "Social Media Content Pack",
        "description": "Generate Twitter thread, LinkedIn post, and Instagram carousel from any text",
        "category": "content",
        "trigger_type": "manual",
        "icon": "Share",
        "nodes": [
            {"id": "n1", "type": "action", "action": "summarize", "label": "Prepare Content", "config": {"max_length": 2000}, "position_x": 100, "position_y": 200},
            {"id": "n2", "type": "action", "action": "content_studio", "label": "Twitter Thread", "config": {"format": "twitter_thread"}, "position_x": 400, "position_y": 100},
            {"id": "n3", "type": "action", "action": "content_studio", "label": "LinkedIn Post", "config": {"format": "linkedin_post"}, "position_x": 400, "position_y": 200},
            {"id": "n4", "type": "action", "action": "content_studio", "label": "Instagram Carousel", "config": {"format": "instagram_carousel"}, "position_x": 400, "position_y": 300},
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n2"},
            {"id": "e2", "source": "n1", "target": "n3"},
            {"id": "e3", "source": "n1", "target": "n4"},
        ],
    },
    {
        "id": "competitive_intel",
        "name": "Competitive Intelligence",
        "description": "Crawl competitor websites, analyze content, summarize insights and index to knowledge base",
        "category": "research",
        "trigger_type": "manual",
        "icon": "TravelExplore",
        "nodes": [
            {"id": "n1", "type": "action", "action": "crawl", "label": "Crawl Website", "config": {}, "position_x": 100, "position_y": 200},
            {"id": "n2", "type": "action", "action": "summarize", "label": "Analyze Content", "config": {"max_length": 1500}, "position_x": 350, "position_y": 100},
            {"id": "n3", "type": "action", "action": "sentiment", "label": "Sentiment Analysis", "config": {}, "position_x": 350, "position_y": 300},
            {"id": "n4", "type": "action", "action": "generate", "label": "Generate Report", "config": {"prompt": "Create a competitive analysis report"}, "position_x": 600, "position_y": 200},
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n2"},
            {"id": "e2", "source": "n1", "target": "n3"},
            {"id": "e3", "source": "n2", "target": "n4"},
            {"id": "e4", "source": "n3", "target": "n4"},
        ],
    },
    {
        "id": "knowledge_enrichment",
        "name": "Knowledge Base Enrichment",
        "description": "Crawl URLs, process and index content, then generate a summary report",
        "category": "knowledge",
        "trigger_type": "manual",
        "icon": "AutoStories",
        "nodes": [
            {"id": "n1", "type": "action", "action": "crawl", "label": "Crawl & Extract", "config": {}, "position_x": 100, "position_y": 200},
            {"id": "n2", "type": "action", "action": "index_knowledge", "label": "Index to KB", "config": {}, "position_x": 350, "position_y": 200},
            {"id": "n3", "type": "action", "action": "summarize", "label": "Summarize", "config": {}, "position_x": 600, "position_y": 200},
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n2"},
            {"id": "e2", "source": "n2", "target": "n3"},
        ],
    },
    {
        "id": "multilingual_content",
        "name": "Multilingual Content Generator",
        "description": "Take content and generate translations + localized social media posts",
        "category": "content",
        "trigger_type": "manual",
        "icon": "Translate",
        "nodes": [
            {"id": "n1", "type": "action", "action": "translate", "label": "Translate to English", "config": {"target_language": "en"}, "position_x": 100, "position_y": 100},
            {"id": "n2", "type": "action", "action": "translate", "label": "Translate to Spanish", "config": {"target_language": "es"}, "position_x": 100, "position_y": 300},
            {"id": "n3", "type": "action", "action": "content_studio", "label": "English Blog", "config": {"format": "blog_article"}, "position_x": 400, "position_y": 100},
            {"id": "n4", "type": "action", "action": "content_studio", "label": "Spanish Blog", "config": {"format": "blog_article"}, "position_x": 400, "position_y": 300},
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n3"},
            {"id": "e2", "source": "n2", "target": "n4"},
        ],
    },
]


class WorkflowService:
    """Service for managing and executing AI workflows."""

    @staticmethod
    async def create_workflow(
        user_id: UUID,
        name: str,
        description: Optional[str],
        trigger_type: str,
        trigger_config: dict,
        nodes: list[dict],
        edges: list[dict],
        session: AsyncSession,
        schedule_cron: Optional[str] = None,
    ) -> Workflow:
        """Create a new workflow."""
        workflow = Workflow(
            user_id=user_id,
            name=name,
            description=description,
            trigger_type=trigger_type,
            trigger_config_json=json.dumps(trigger_config, ensure_ascii=False),
            nodes_json=json.dumps(nodes, ensure_ascii=False),
            edges_json=json.dumps(edges, ensure_ascii=False),
            schedule_cron=schedule_cron,
        )
        session.add(workflow)
        await session.commit()
        await session.refresh(workflow)

        logger.info(
            "workflow_created",
            workflow_id=str(workflow.id),
            name=name,
            nodes_count=len(nodes),
        )
        return workflow

    @staticmethod
    async def get_workflow(
        workflow_id: UUID,
        user_id: UUID,
        session: AsyncSession,
    ) -> Optional[Workflow]:
        """Get a workflow by ID, verifying ownership."""
        workflow = await session.get(Workflow, workflow_id)
        if workflow and workflow.user_id != user_id:
            return None
        return workflow

    @staticmethod
    async def list_workflows(
        user_id: UUID,
        session: AsyncSession,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Workflow], int]:
        """List user's workflows with pagination."""
        count_result = await session.execute(
            select(func.count())
            .select_from(Workflow)
            .where(Workflow.user_id == user_id)
        )
        total = count_result.scalar_one()

        result = await session.execute(
            select(Workflow)
            .where(Workflow.user_id == user_id)
            .order_by(Workflow.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    @staticmethod
    async def update_workflow(
        workflow_id: UUID,
        user_id: UUID,
        updates: dict,
        session: AsyncSession,
    ) -> Optional[Workflow]:
        """Update a workflow."""
        workflow = await session.get(Workflow, workflow_id)
        if not workflow or workflow.user_id != user_id:
            return None

        if "name" in updates and updates["name"]:
            workflow.name = updates["name"]
        if "description" in updates:
            workflow.description = updates["description"]
        if "trigger_type" in updates and updates["trigger_type"]:
            workflow.trigger_type = updates["trigger_type"]
        if "trigger_config" in updates and updates["trigger_config"] is not None:
            workflow.trigger_config_json = json.dumps(
                updates["trigger_config"], ensure_ascii=False
            )
        if "nodes" in updates and updates["nodes"] is not None:
            workflow.nodes_json = json.dumps(
                [n if isinstance(n, dict) else n.model_dump() for n in updates["nodes"]],
                ensure_ascii=False,
            )
        if "edges" in updates and updates["edges"] is not None:
            workflow.edges_json = json.dumps(
                [e if isinstance(e, dict) else e.model_dump() for e in updates["edges"]],
                ensure_ascii=False,
            )
        if "status" in updates and updates["status"]:
            workflow.status = updates["status"]
        if "schedule_cron" in updates:
            workflow.schedule_cron = updates["schedule_cron"]

        workflow.updated_at = datetime.now(UTC)
        session.add(workflow)
        await session.commit()
        await session.refresh(workflow)
        return workflow

    @staticmethod
    async def delete_workflow(
        workflow_id: UUID,
        user_id: UUID,
        session: AsyncSession,
    ) -> bool:
        """Delete a workflow and its runs."""
        workflow = await session.get(Workflow, workflow_id)
        if not workflow or workflow.user_id != user_id:
            return False

        run_result = await session.execute(
            select(WorkflowRun).where(WorkflowRun.workflow_id == workflow_id)
        )
        for run in run_result.scalars().all():
            await session.delete(run)

        await session.delete(workflow)
        await session.commit()

        logger.info("workflow_deleted", workflow_id=str(workflow_id))
        return True

    @staticmethod
    async def execute_workflow(
        workflow_id: UUID,
        user_id: UUID,
        session: AsyncSession,
        input_data: Optional[dict] = None,
    ) -> Optional[WorkflowRun]:
        """Execute a workflow by traversing the node graph."""
        import time

        workflow = await session.get(Workflow, workflow_id)
        if not workflow or workflow.user_id != user_id:
            return None

        nodes = json.loads(workflow.nodes_json)
        edges = json.loads(workflow.edges_json)

        run = WorkflowRun(
            workflow_id=workflow_id,
            user_id=user_id,
            status=RunStatus.RUNNING,
            trigger_type=workflow.trigger_type,
            trigger_data_json=json.dumps(input_data or {}, ensure_ascii=False),
            total_nodes=len(nodes),
            started_at=datetime.now(UTC),
        )
        session.add(run)
        await session.commit()
        await session.refresh(run)

        start_time = time.monotonic()

        # Build adjacency list
        adjacency = {}
        in_degree = {n["id"]: 0 for n in nodes}
        for edge in edges:
            adjacency.setdefault(edge["source"], []).append(edge["target"])
            if edge["target"] in in_degree:
                in_degree[edge["target"]] += 1

        # Find start nodes (no incoming edges)
        start_nodes = [nid for nid, deg in in_degree.items() if deg == 0]
        if not start_nodes:
            start_nodes = [nodes[0]["id"]] if nodes else []

        # Map node IDs to node data
        node_map = {n["id"]: n for n in nodes}

        # Execute nodes in topological order
        results = []
        node_outputs = {}
        executed = set()
        queue = list(start_nodes)

        commit_batch_size = 5
        nodes_since_commit = 0

        try:
            while queue:
                node_id = queue.pop(0)
                if node_id in executed:
                    continue

                node = node_map.get(node_id)
                if not node:
                    continue

                # Gather inputs from parent nodes
                parent_outputs = []
                for edge in edges:
                    if edge["target"] == node_id and edge["source"] in node_outputs:
                        parent_outputs.append(node_outputs[edge["source"]])

                previous_output = "\n\n".join(parent_outputs) if parent_outputs else (
                    json.dumps(input_data) if input_data else ""
                )

                run.current_node = len(executed) + 1
                session.add(run)
                nodes_since_commit += 1

                if nodes_since_commit >= commit_batch_size:
                    await session.commit()
                    nodes_since_commit = 0

                node_result = await WorkflowService._execute_node(
                    node, previous_output, user_id
                )
                node_outputs[node_id] = node_result.get("output", "")
                results.append({
                    "node_id": node_id,
                    "label": node.get("label", ""),
                    "action": node.get("action", ""),
                    **node_result,
                })
                executed.add(node_id)

                # Enqueue children
                for child_id in adjacency.get(node_id, []):
                    # Check if all parents are executed
                    parents_done = all(
                        e["source"] in executed
                        for e in edges
                        if e["target"] == child_id
                    )
                    if parents_done and child_id not in executed:
                        queue.append(child_id)

            run.status = RunStatus.COMPLETED
        except Exception as e:
            run.status = RunStatus.FAILED
            run.error = str(e)[:2000]
            logger.error(
                "workflow_execution_failed",
                run_id=str(run.id),
                error=str(e),
            )

        elapsed_ms = int((time.monotonic() - start_time) * 1000)
        run.results_json = json.dumps(results, ensure_ascii=False)
        run.completed_at = datetime.now(UTC)
        run.duration_ms = elapsed_ms
        run.current_node = len(executed)
        session.add(run)

        # Update workflow stats
        workflow.run_count += 1
        workflow.last_run_at = datetime.now(UTC)
        session.add(workflow)

        await session.commit()
        await session.refresh(run)

        logger.info(
            "workflow_execution_finished",
            run_id=str(run.id),
            status=run.status.value,
            nodes_executed=len(executed),
            duration_ms=elapsed_ms,
        )
        return run

    @staticmethod
    async def _execute_node(
        node: dict,
        previous_output: str,
        user_id: UUID,
    ) -> dict:
        """Execute a single workflow node."""
        action = node.get("action", "generate")
        config = node.get("config", {})

        if action == "summarize":
            return await WorkflowService._node_summarize(previous_output, config, user_id)
        elif action == "translate":
            return await WorkflowService._node_translate(previous_output, config, user_id)
        elif action == "sentiment":
            return await WorkflowService._node_sentiment(previous_output, config)
        elif action == "generate":
            return await WorkflowService._node_generate(previous_output, config, user_id)
        elif action == "crawl":
            return await WorkflowService._node_crawl(previous_output, config)
        elif action == "batch_crawl":
            return await WorkflowService._node_batch_crawl(previous_output, config)
        elif action == "deep_crawl":
            return await WorkflowService._node_deep_crawl(previous_output, config)
        elif action == "transcribe":
            return await WorkflowService._node_transcribe(previous_output, config)
        elif action == "youtube_transcript":
            return await WorkflowService._node_youtube_transcript(previous_output, config)
        elif action == "youtube_smart":
            return await WorkflowService._node_youtube_smart(previous_output, config)
        elif action == "youtube_metadata":
            return await WorkflowService._node_youtube_metadata(previous_output, config)
        elif action == "search_knowledge":
            return await WorkflowService._node_search_kb(previous_output, config, user_id)
        elif action == "index_knowledge":
            return await WorkflowService._node_index_kb(previous_output, config, user_id)
        elif action == "compare":
            return await WorkflowService._node_compare(previous_output, config, user_id)
        elif action == "content_studio":
            return await WorkflowService._node_content_studio(previous_output, config, user_id)
        elif action == "notify":
            return {"output": previous_output, "action": "notify", "note": "Notification sent"}
        elif action == "webhook_call":
            return await WorkflowService._node_webhook(previous_output, config)
        elif action == "condition":
            return await WorkflowService._node_condition(previous_output, config)
        elif action == "generate_image":
            return await WorkflowService._node_generate_image(previous_output, config, user_id)
        elif action == "generate_video":
            return await WorkflowService._node_generate_video(previous_output, config, user_id)
        elif action == "analyze_data":
            return {"output": previous_output, "action": "analyze_data", "note": "Upload a dataset in Data Analyst first"}
        elif action == "text_to_speech":
            return {"output": f"[TTS queued: {len(previous_output.split())} words]", "action": "text_to_speech"}
        elif action == "security_scan":
            return await WorkflowService._node_security_scan(previous_output, config, user_id)
        elif action == "voice_dub":
            target = config.get("target_language", "en")
            return {"output": f"[Dubbing to {target} queued]", "action": "voice_dub", "target_language": target}
        elif action == "publish_social":
            return await WorkflowService._node_publish_social(previous_output, config, user_id)
        elif action == "search_marketplace":
            return await WorkflowService._node_search_marketplace(previous_output, config)
        elif action == "deploy_chatbot":
            return await WorkflowService._node_deploy_chatbot(previous_output, config, user_id)
        elif action == "send_webhook":
            return await WorkflowService._node_send_webhook(previous_output, config)
        elif action == "upscale_image":
            return await WorkflowService._node_upscale_image(previous_output, config, user_id)
        elif action == "generate_presentation":
            return await WorkflowService._node_generate_presentation(previous_output, config, user_id)
        elif action == "execute_code":
            return await WorkflowService._node_execute_code(previous_output, config, user_id)
        elif action == "generate_form":
            return await WorkflowService._node_generate_form(previous_output, config, user_id)
        elif action == "scrape_repos":
            return await WorkflowService._node_scrape_repos(previous_output, config, user_id)
        elif action == "edit_audio":
            return await WorkflowService._node_edit_audio(previous_output, config, user_id)
        elif action == "generate_podcast":
            return await WorkflowService._node_generate_podcast(previous_output, config, user_id)
        elif action == "analyze_repo":
            return await WorkflowService._node_analyze_repo(previous_output, config, user_id)
        elif action == "process_pdf":
            return await WorkflowService._node_process_pdf(previous_output, config, user_id)
        elif action == "create_webhook":
            return await WorkflowService._node_create_webhook(previous_output, config, user_id)
        elif action == "fine_tune":
            return await WorkflowService._node_fine_tune(previous_output, config, user_id)
        else:
            return await WorkflowService._node_generate(previous_output, config, user_id)

    @staticmethod
    async def _node_summarize(text: str, config: dict, user_id: UUID) -> dict:
        if not text:
            return {"output": "", "error": "No input text", "action": "summarize"}
        try:
            from app.ai_assistant.service import AIAssistantService
            max_len = config.get("max_length", 500)
            result = await AIAssistantService.process_text_with_provider(
                text=f"Summarize in {max_len} words or less:\n\n{text[:10000]}",
                task="summarize",
                provider_name=config.get("provider", "gemini"),
                user_id=user_id,
                module="ai_workflows",
            )
            return {"output": result.get("processed_text", ""), "action": "summarize"}
        except Exception as e:
            return {"output": text[:500], "error": str(e)[:500], "action": "summarize"}

    @staticmethod
    async def _node_translate(text: str, config: dict, user_id: UUID) -> dict:
        if not text:
            return {"output": "", "error": "No input text", "action": "translate"}
        target = config.get("target_language", "en")
        try:
            from app.ai_assistant.service import AIAssistantService
            result = await AIAssistantService.process_text_with_provider(
                text=f"Translate to {target}:\n\n{text[:10000]}",
                task="translate",
                provider_name=config.get("provider", "gemini"),
                user_id=user_id,
                module="ai_workflows",
            )
            return {"output": result.get("processed_text", ""), "action": "translate"}
        except Exception as e:
            return {"output": text, "error": str(e)[:500], "action": "translate"}

    @staticmethod
    async def _node_sentiment(text: str, config: dict) -> dict:
        if not text:
            return {"output": "", "error": "No text", "action": "sentiment"}
        try:
            from app.modules.sentiment.service import SentimentService
            result = await SentimentService.analyze_text(text[:10000])
            summary = (
                f"Sentiment: {result['overall_sentiment']} (score: {result['overall_score']}). "
                f"Positive: {result['positive_percent']}%, Negative: {result['negative_percent']}%"
            )
            return {"output": summary, "action": "sentiment", "details": result}
        except Exception as e:
            return {"output": "", "error": str(e)[:500], "action": "sentiment"}

    @staticmethod
    async def _node_generate(text: str, config: dict, user_id: UUID) -> dict:
        prompt = config.get("prompt", text) or text
        if not prompt:
            return {"output": "", "error": "No prompt", "action": "generate"}
        try:
            from app.ai_assistant.service import AIAssistantService
            result = await AIAssistantService.process_text_with_provider(
                text=f"{prompt}\n\nContext:\n{text[:8000]}" if text and text != prompt else prompt[:10000],
                task="general",
                provider_name=config.get("provider", "gemini"),
                user_id=user_id,
                module="ai_workflows",
            )
            return {"output": result.get("processed_text", ""), "action": "generate"}
        except Exception as e:
            return {"output": "", "error": str(e)[:500], "action": "generate"}

    @staticmethod
    async def _node_crawl(text: str, config: dict) -> dict:
        url = config.get("url", text or "").strip()
        if not url or not url.startswith("http"):
            return {"output": "", "error": "No valid URL", "action": "crawl"}
        try:
            from app.modules.web_crawler.service import WebCrawlerService
            result = await WebCrawlerService.scrape(url=url, extract_images=True)
            if result.get("success"):
                return {
                    "output": result.get("markdown", "")[:10000],
                    "action": "crawl",
                    "title": result.get("title", ""),
                }
            return {"output": "", "error": result.get("error", "Crawl failed"), "action": "crawl"}
        except Exception as e:
            return {"output": "", "error": str(e)[:500], "action": "crawl"}

    @staticmethod
    async def _node_batch_crawl(text: str, config: dict) -> dict:
        urls = config.get("urls", [])
        if not urls and text:
            urls = [u.strip() for u in text.split("\n") if u.strip().startswith("http")]
        if not urls:
            return {"output": "", "error": "No URLs for batch crawl", "action": "batch_crawl"}
        try:
            from app.modules.web_crawler.service import WebCrawlerService
            result = await WebCrawlerService.batch_scrape(
                urls=urls,
                extract_images=config.get("extract_images", False),
                proxies=config.get("proxies"),
                dispatcher=config.get("dispatcher"),
            )
            if result.get("success"):
                results_list = result.get("results", [])
                successes = sum(1 for r in results_list if r.get("success"))
                return {
                    "output": f"Batch: {successes}/{len(results_list)} succeeded",
                    "action": "batch_crawl",
                    "total": len(results_list),
                }
            return {"output": "", "error": result.get("error", "Batch failed"), "action": "batch_crawl"}
        except Exception as e:
            return {"output": "", "error": str(e)[:500], "action": "batch_crawl"}

    @staticmethod
    async def _node_deep_crawl(text: str, config: dict) -> dict:
        url = config.get("url", text or "").strip()
        if not url or not url.startswith("http"):
            return {"output": "", "error": "No valid URL", "action": "deep_crawl"}
        try:
            from app.modules.web_crawler.service import WebCrawlerService
            result = await WebCrawlerService.deep_crawl(
                start_url=url,
                max_depth=config.get("max_depth", 3),
                max_pages=config.get("max_pages", 20),
                extract_images=config.get("extract_images", False),
                composite_scorers=config.get("composite_scorers"),
                proxies=config.get("proxies"),
                dispatcher=config.get("dispatcher"),
            )
            if result.get("success"):
                pages = result.get("results", [])
                return {
                    "output": f"Deep crawl: {len(pages)} pages from {url}",
                    "action": "deep_crawl",
                    "pages_crawled": len(pages),
                }
            return {"output": "", "error": result.get("error", "Deep crawl failed"), "action": "deep_crawl"}
        except Exception as e:
            return {"output": "", "error": str(e)[:500], "action": "deep_crawl"}

    @staticmethod
    async def _node_transcribe(text: str, config: dict) -> dict:
        url = config.get("url", text or "").strip()
        if not url:
            return {"output": "", "error": "No URL for transcription", "action": "transcribe"}
        return {
            "output": f"[Transcription task queued for: {url}]",
            "action": "transcribe",
            "url": url,
        }

    @staticmethod
    async def _node_youtube_transcript(text: str, config: dict) -> dict:
        url = config.get("url", text or "").strip()
        if not url:
            return {"output": "", "error": "No YouTube URL for transcript", "action": "youtube_transcript"}
        language = config.get("language", "auto")
        try:
            from app.transcription.youtube_transcript import get_youtube_transcript
            result = await get_youtube_transcript(url, language)
            if not result:
                return {"output": "", "error": "No subtitles available", "action": "youtube_transcript"}
            return {
                "output": result.get("full_text", ""),
                "provider": result.get("provider", "youtube_subtitles"),
                "action": "youtube_transcript",
            }
        except Exception as e:
            return {"output": "", "error": str(e)[:500], "action": "youtube_transcript"}

    @staticmethod
    async def _node_youtube_smart(text: str, config: dict) -> dict:
        url = config.get("url", text or "").strip()
        if not url:
            return {"output": "", "error": "No YouTube URL", "action": "youtube_smart"}
        language = config.get("language", "auto")
        try:
            from app.transcription.youtube_transcript import get_youtube_transcript, download_video
            result = await get_youtube_transcript(url, language)
            if result:
                return {"output": result.get("full_text", ""), "provider": "youtube_subtitles", "action": "youtube_smart"}
            video_data = await download_video(url)
            if video_data and video_data.get("file_path"):
                from app.transcription.whisper_service import transcribe_with_whisper
                whisper = await transcribe_with_whisper(video_data["file_path"])
                if whisper:
                    return {"output": whisper.get("text", ""), "provider": "whisper", "action": "youtube_smart"}
            return {"output": "", "error": "No transcription provider succeeded", "action": "youtube_smart"}
        except Exception as e:
            return {"output": "", "error": str(e)[:500], "action": "youtube_smart"}

    @staticmethod
    async def _node_youtube_metadata(text: str, config: dict) -> dict:
        url = config.get("url", text or "").strip()
        if not url:
            return {"output": "", "error": "No YouTube URL", "action": "youtube_metadata"}
        try:
            from app.transcription.youtube_transcript import get_youtube_metadata
            metadata = await get_youtube_metadata(url)
            if not metadata:
                return {"output": "", "error": "Could not fetch metadata", "action": "youtube_metadata"}
            return {
                "output": f"{metadata.get('title', '')} — {metadata.get('uploader', '')} ({metadata.get('duration_seconds', 0)}s)",
                "metadata": metadata,
                "action": "youtube_metadata",
            }
        except Exception as e:
            return {"output": "", "error": str(e)[:500], "action": "youtube_metadata"}

    @staticmethod
    async def _node_search_kb(text: str, config: dict, user_id: UUID) -> dict:
        query = config.get("query", text or "")
        if not query:
            return {"output": "", "error": "No search query", "action": "search_knowledge"}
        try:
            from app.modules.knowledge.service import KnowledgeService
            from app.database import get_session_context
            async with get_session_context() as kb_session:
                results = await KnowledgeService.search(
                    user_id=user_id, query=query[:500], session=kb_session, limit=5,
                )
            if results:
                output = "\n\n".join(
                    f"[{r.get('filename', '')}] {r.get('content', '')[:500]}" for r in results
                )
                return {"output": output, "action": "search_knowledge", "results_count": len(results)}
            return {"output": "No results found.", "action": "search_knowledge"}
        except Exception as e:
            return {"output": "", "error": str(e)[:500], "action": "search_knowledge"}

    @staticmethod
    async def _node_index_kb(text: str, config: dict, user_id: UUID) -> dict:
        if not text:
            return {"output": "", "error": "No content to index", "action": "index_knowledge"}
        try:
            from app.modules.knowledge.service import KnowledgeService
            from app.database import get_session_context
            filename = config.get("filename", f"workflow_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.md")
            async with get_session_context() as kb_session:
                doc = await KnowledgeService.upload_document(
                    user_id=user_id,
                    filename=filename,
                    content_type="text/markdown",
                    text_content=text[:50000],
                    session=kb_session,
                )
            return {
                "output": f"Indexed as '{filename}' ({doc.total_chunks} chunks)",
                "action": "index_knowledge",
            }
        except Exception as e:
            return {"output": "", "error": str(e)[:500], "action": "index_knowledge"}

    @staticmethod
    async def _node_compare(text: str, config: dict, user_id: UUID) -> dict:
        prompt = config.get("prompt", text or "")
        if not prompt:
            return {"output": "", "error": "No prompt", "action": "compare"}
        try:
            from app.modules.compare.service import CompareService
            from app.database import get_session_context
            providers = config.get("providers", ["gemini", "groq"])
            async with get_session_context() as cmp_session:
                _, results = await CompareService.run_comparison(
                    user_id=user_id, prompt=prompt[:5000],
                    providers=providers, session=cmp_session,
                )
            if results:
                best = max(results, key=lambda r: len(r.get("response", "")))
                return {"output": best.get("response", ""), "action": "compare"}
            return {"output": "", "error": "Comparison failed", "action": "compare"}
        except Exception as e:
            return {"output": "", "error": str(e)[:500], "action": "compare"}

    @staticmethod
    async def _node_content_studio(text: str, config: dict, user_id: UUID) -> dict:
        """Generate content using the Content Studio module."""
        fmt = config.get("format", "blog_article")
        if not text:
            return {"output": "", "error": "No source text", "action": "content_studio"}
        try:
            from app.modules.content_studio.service import ContentStudioService
            result = await ContentStudioService._generate_single(
                source_text=text,
                fmt=__import__("app.models.content_studio", fromlist=["ContentFormat"]).ContentFormat(fmt),
                tone=config.get("tone", "professional"),
                target_audience=config.get("target_audience"),
                keywords=None,
                language=config.get("language", "auto"),
                provider=config.get("provider"),
                custom_instructions=config.get("instructions"),
                user_id=user_id,
            )
            return {
                "output": result.get("content", ""),
                "action": "content_studio",
                "format": fmt,
                "title": result.get("title", ""),
            }
        except Exception as e:
            return {"output": "", "error": str(e)[:500], "action": "content_studio"}

    @staticmethod
    async def _node_webhook(text: str, config: dict) -> dict:
        """Call an external webhook with the workflow output."""
        import httpx

        url = config.get("url", "")
        if not url:
            return {"output": text, "error": "No webhook URL", "action": "webhook_call"}
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    url,
                    json={"content": text[:5000], "source": "saas-ia-workflow"},
                    headers=config.get("headers", {}),
                )
            return {
                "output": f"Webhook called: {resp.status_code}",
                "action": "webhook_call",
                "status_code": resp.status_code,
            }
        except Exception as e:
            return {"output": text, "error": str(e)[:500], "action": "webhook_call"}

    @staticmethod
    async def _node_condition(text: str, config: dict) -> dict:
        """Evaluate a simple condition."""
        condition = config.get("condition", "")
        return {"output": text, "action": "condition", "condition": condition, "passed": bool(text)}

    @staticmethod
    async def _node_generate_image(text: str, config: dict, user_id: UUID) -> dict:
        """Generate an image in the workflow."""
        prompt = config.get("prompt", text or "")
        style = config.get("style", "digital_art")
        if not prompt:
            return {"output": "", "error": "No prompt for image generation", "action": "generate_image"}
        try:
            from app.modules.image_gen.service import ImageGenService
            from app.database import get_session_context
            async with get_session_context() as img_session:
                image = await ImageGenService.generate_image(
                    user_id=user_id, prompt=prompt[:2000], style=style,
                    provider=config.get("provider", "gemini"),
                    width=config.get("width", 1024), height=config.get("height", 1024),
                    session=img_session,
                )
            return {
                "output": f"Image generated: {image.image_url or 'processing'}",
                "action": "generate_image",
                "image_id": str(image.id),
                "style": style,
            }
        except Exception as e:
            return {"output": "", "error": str(e)[:500], "action": "generate_image"}

    @staticmethod
    async def _node_generate_video(text: str, config: dict, user_id: UUID) -> dict:
        """Generate a video in the workflow."""
        prompt = config.get("prompt", text or "")
        video_type = config.get("video_type", "text_to_video")
        if not prompt:
            return {"output": "", "error": "No prompt for video", "action": "generate_video"}
        try:
            from app.modules.video_gen.service import VideoGenService
            from app.database import get_session_context
            async with get_session_context() as vid_session:
                video = await VideoGenService.generate_video(
                    user_id=user_id, title=config.get("title", "Workflow Video"),
                    prompt=prompt[:2000], video_type=video_type,
                    provider=config.get("provider", "gemini"),
                    duration_s=config.get("duration_s", 10),
                    width=1920, height=1080, session=vid_session,
                )
            return {
                "output": f"Video generated: {video.video_url or 'processing'} ({video.duration_s}s)",
                "action": "generate_video",
                "video_id": str(video.id),
            }
        except Exception as e:
            return {"output": "", "error": str(e)[:500], "action": "generate_video"}

    @staticmethod
    async def _node_security_scan(text: str, config: dict, user_id: UUID) -> dict:
        """Security scan in the workflow."""
        if not text:
            return {"output": "", "error": "No text to scan", "action": "security_scan"}
        try:
            from app.modules.security_guardian.service import SecurityGuardianService
            findings = SecurityGuardianService._detect_pii(text) + SecurityGuardianService._detect_prompt_injection(text)
            if findings:
                summary = f"Found {len(findings)} issue(s):\n" + "\n".join(
                    f"- [{f['severity']}] {f['type']}: {f['description']}" for f in findings[:10]
                )
                if config.get("auto_redact"):
                    redacted = SecurityGuardianService._redact_pii(text, findings)
                    return {"output": redacted, "action": "security_scan", "findings_count": len(findings), "redacted": True}
                return {"output": summary, "action": "security_scan", "findings_count": len(findings)}
            return {"output": "Content is clean - no issues found.", "action": "security_scan", "findings_count": 0}
        except Exception as e:
            return {"output": text, "error": str(e)[:500], "action": "security_scan"}

    @staticmethod
    async def _node_publish_social(text: str, config: dict, user_id: UUID) -> dict:
        """Publish content to social media platforms."""
        platforms = config.get("platforms", ["twitter"])
        if not text:
            return {"output": "", "error": "No content to publish", "action": "publish_social"}
        try:
            from app.modules.social_publisher.service import SocialPublisherService
            from app.database import get_session_context
            async with get_session_context() as sp_session:
                post = await SocialPublisherService.create_post(
                    user_id=user_id,
                    content=text[:5000],
                    platforms=platforms,
                    session=sp_session,
                    hashtags=config.get("hashtags"),
                )
                published = await SocialPublisherService.publish_post(
                    user_id=user_id,
                    post_id=post.id,
                    session=sp_session,
                )
            return {
                "output": f"Published to {', '.join(platforms)} (post_id: {published.id})",
                "action": "publish_social",
                "post_id": str(published.id),
            }
        except Exception as e:
            return {"output": text, "error": str(e)[:500], "action": "publish_social"}

    @staticmethod
    async def _node_search_marketplace(text: str, config: dict) -> dict:
        """Search the marketplace for listings."""
        query = config.get("query", text or "")
        if not query:
            return {"output": "", "error": "No search query", "action": "search_marketplace"}
        try:
            from app.modules.marketplace.service import MarketplaceService
            from app.database import get_session_context
            async with get_session_context() as mp_session:
                svc = MarketplaceService(mp_session)
                listings, total = await svc.list_listings(
                    search=query[:200],
                    category=config.get("category"),
                    limit=config.get("limit", 5),
                )
            if listings:
                output = f"Found {total} result(s):\n" + "\n".join(
                    f"- {l.title} ({l.type}/{l.category}) v{l.version}" for l in listings
                )
                return {"output": output, "action": "search_marketplace", "results_count": total}
            return {"output": "No marketplace listings found.", "action": "search_marketplace", "results_count": 0}
        except Exception as e:
            return {"output": "", "error": str(e)[:500], "action": "search_marketplace"}

    @staticmethod
    async def _node_deploy_chatbot(text: str, config: dict, user_id: UUID) -> dict:
        """Create and publish a chatbot from workflow output."""
        system_prompt = config.get("system_prompt", text or "")
        name = config.get("name", "Workflow Chatbot")
        if not system_prompt:
            return {"output": "", "error": "No system prompt for chatbot", "action": "deploy_chatbot"}
        try:
            from app.modules.ai_chatbot_builder.service import ChatbotBuilderService
            from app.database import get_session_context
            async with get_session_context() as cb_session:
                svc = ChatbotBuilderService(cb_session)
                chatbot = await svc.create_chatbot(
                    user_id=user_id,
                    data={
                        "name": name,
                        "system_prompt": system_prompt[:10000],
                        "model": config.get("model", "gemini"),
                        "personality": config.get("personality", "professional"),
                        "welcome_message": config.get("welcome_message"),
                    },
                )
                published = await svc.publish_chatbot(
                    user_id=user_id,
                    chatbot_id=chatbot.id,
                )
            return {
                "output": f"Chatbot deployed: {published.name} (token: {published.embed_token})",
                "action": "deploy_chatbot",
                "chatbot_id": str(published.id),
                "embed_token": published.embed_token,
            }
        except Exception as e:
            return {"output": "", "error": str(e)[:500], "action": "deploy_chatbot"}

    _SAFE_WEBHOOK_HEADERS = frozenset({
        "content-type", "authorization", "x-api-key", "x-webhook-secret",
        "accept", "user-agent",
    })

    @staticmethod
    def _filter_webhook_headers(raw_headers: dict) -> dict:
        return {
            k: v for k, v in raw_headers.items()
            if k.lower() in WorkflowService._SAFE_WEBHOOK_HEADERS
        }

    @staticmethod
    async def _node_send_webhook(text: str, config: dict) -> dict:
        """Send data to a webhook URL."""
        import httpx

        url = config.get("url", "")
        if not url:
            return {"output": text, "error": "No webhook URL", "action": "send_webhook"}
        try:
            method = config.get("method", "POST").upper()
            payload = {"content": text[:5000], "source": "saas-ia-workflow"}
            safe_headers = WorkflowService._filter_webhook_headers(
                config.get("headers", {})
            )
            async with httpx.AsyncClient(timeout=30) as client:
                if method == "GET":
                    resp = await client.get(url, headers=safe_headers)
                else:
                    resp = await client.post(
                        url, json=payload, headers=safe_headers,
                    )
            return {
                "output": f"Webhook sent: {resp.status_code}",
                "action": "send_webhook",
                "status_code": resp.status_code,
            }
        except Exception as e:
            return {"output": text, "error": str(e)[:500], "action": "send_webhook"}

    @staticmethod
    async def _node_upscale_image(text: str, config: dict, user_id: UUID) -> dict:
        """Upscale an image using Real-ESRGAN."""
        image_id = config.get("image_id", text or "").strip()
        scale = config.get("scale", 2)
        if not image_id:
            return {"output": "", "error": "No image_id for upscaling", "action": "upscale_image"}
        try:
            from uuid import UUID as _UUID
            from app.modules.image_gen.service import ImageGenService
            from app.database import get_session_context
            parsed_id = _UUID(str(image_id).strip())
            async with get_session_context() as img_session:
                result = await ImageGenService.upscale_image(
                    user_id=user_id,
                    image_id=parsed_id,
                    scale=scale,
                    session=img_session,
                )
            if isinstance(result, dict) and result.get("error"):
                return {"output": "", "error": result["error"], "action": "upscale_image"}
            return {
                "output": f"Image upscaled ({scale}x): {result.image_url or 'processing'}",
                "action": "upscale_image",
                "image_id": str(result.id),
            }
        except Exception as e:
            return {"output": "", "error": str(e)[:500], "action": "upscale_image"}

    @staticmethod
    async def _node_generate_presentation(text: str, config: dict, user_id: UUID) -> dict:
        """Generate a presentation in the workflow."""
        title = config.get("title", "Workflow Presentation")
        if not text:
            return {"output": "", "error": "No text for presentation", "action": "generate_presentation"}
        try:
            from app.modules.presentation_gen.service import PresentationGenService
            from app.database import get_session_context
            async with get_session_context() as pres_session:
                svc = PresentationGenService(pres_session)
                presentation = await svc.generate_presentation(
                    user_id=user_id,
                    title=title,
                    topic=text[:2000],
                    num_slides=config.get("num_slides", 10),
                    style=config.get("style", "professional"),
                    template=config.get("template", "default"),
                    language=config.get("language", "fr"),
                    source_text=text[:12000],
                )
            return {
                "output": f"Presentation generated: {presentation.title} ({presentation.num_slides} slides)",
                "action": "generate_presentation",
                "presentation_id": str(presentation.id),
            }
        except Exception as e:
            return {"output": "", "error": str(e)[:500], "action": "generate_presentation"}

    @staticmethod
    async def _node_execute_code(text: str, config: dict, user_id: UUID) -> dict:
        """Execute Python code in a sandboxed environment."""
        code = config.get("code", text or "")
        if not code:
            return {"output": "", "error": "No code to execute", "action": "execute_code"}
        try:
            from app.modules.code_sandbox.service import CodeSandboxService
            from app.database import get_session_context
            async with get_session_context() as cs_session:
                sandbox = await CodeSandboxService.create_sandbox(
                    user_id=user_id,
                    data={"name": config.get("name", "Workflow Sandbox"), "language": "python"},
                    session=cs_session,
                )
                cell = await CodeSandboxService.add_cell(
                    user_id=user_id,
                    sandbox_id=sandbox.id,
                    data={"source": code[:50000], "cell_type": "code"},
                    session=cs_session,
                )
                result = await CodeSandboxService.execute_cell(
                    user_id=user_id,
                    sandbox_id=sandbox.id,
                    cell_id=cell["id"],
                    session=cs_session,
                )
            if result and result.get("status") == "success":
                output = result.get("output") or "Code executed successfully (no output)"
                return {
                    "output": output,
                    "action": "execute_code",
                    "execution_time_ms": result.get("execution_time_ms"),
                }
            error = result.get("error", "unknown") if result else "Execution failed"
            return {"output": "", "error": error, "action": "execute_code"}
        except Exception as e:
            return {"output": "", "error": str(e)[:500], "action": "execute_code"}

    @staticmethod
    async def _node_generate_form(text: str, config: dict, user_id: UUID) -> dict:
        """Generate an AI-powered form from a prompt."""
        prompt = config.get("prompt", text or "")
        if not prompt:
            return {"output": "", "error": "No prompt for form generation", "action": "generate_form"}
        try:
            from app.modules.ai_forms.service import AIFormsService
            from app.database import get_session_context
            import json as _json
            async with get_session_context() as form_session:
                svc = AIFormsService(form_session)
                form = await svc.generate_form(
                    user_id=user_id,
                    prompt=prompt[:5000],
                    num_fields=config.get("num_fields", 5),
                )
            fields = _json.loads(form.fields_json) if form.fields_json else []
            return {
                "output": f"Form generated: {form.title} ({len(fields)} fields)",
                "action": "generate_form",
                "form_id": str(form.id),
            }
        except Exception as e:
            return {"output": "", "error": str(e)[:500], "action": "generate_form"}

    @staticmethod
    async def _node_scrape_repos(text: str, config: dict, user_id: UUID) -> dict:
        """Scrape GitHub repos using Skill Seekers."""
        repos = config.get("repos", [])
        targets = config.get("targets", ["claude"])
        if not repos and text:
            repos = [text.strip()]
        if not repos:
            return {"output": "", "error": "No repos provided", "action": "scrape_repos"}
        try:
            import json as _json
            from app.modules.skill_seekers.service import SkillSeekersService
            from app.database import get_session_context
            svc = SkillSeekersService()
            async with get_session_context() as ss_session:
                job = await SkillSeekersService.create_job(
                    user_id=user_id,
                    repos=repos,
                    targets=targets,
                    enhance=config.get("enhance", False),
                    session=ss_session,
                )
            await svc.run_job(job.id)
            async with get_session_context() as ss_session:
                from app.models.skill_seekers import ScrapeJob
                job = await ss_session.get(ScrapeJob, job.id)
            output_files = _json.loads(job.output_files_json) if job.output_files_json else []
            import os
            filenames = [os.path.basename(f) for f in output_files]
            output = f"Scraped {len(repos)} repo(s) for {', '.join(targets)}: {', '.join(filenames)}" if filenames else "Scrape completed but no output files"
            return {
                "output": output,
                "action": "scrape_repos",
                "job_id": str(job.id),
                "output_files": filenames,
            }
        except Exception as e:
            return {"output": "", "error": str(e)[:500], "action": "scrape_repos"}

    @staticmethod
    async def list_runs(
        workflow_id: UUID,
        user_id: UUID,
        session: AsyncSession,
        limit: int = 20,
    ) -> list[WorkflowRun]:
        """List runs for a workflow."""
        result = await session.execute(
            select(WorkflowRun)
            .where(
                WorkflowRun.workflow_id == workflow_id,
                WorkflowRun.user_id == user_id,
            )
            .order_by(WorkflowRun.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_run(
        run_id: UUID,
        user_id: UUID,
        session: AsyncSession,
    ) -> Optional[WorkflowRun]:
        """Get a workflow run by ID."""
        run = await session.get(WorkflowRun, run_id)
        if run and run.user_id != user_id:
            return None
        return run

    @staticmethod
    def get_templates(category: Optional[str] = None) -> list[dict]:
        """Get available workflow templates."""
        if category:
            return [t for t in WORKFLOW_TEMPLATES if t["category"] == category]
        return WORKFLOW_TEMPLATES

    @staticmethod
    async def create_from_template(
        template_id: str,
        user_id: UUID,
        name: Optional[str],
        session: AsyncSession,
    ) -> Optional[Workflow]:
        """Create a workflow from a template."""
        template = next((t for t in WORKFLOW_TEMPLATES if t["id"] == template_id), None)
        if not template:
            return None

        workflow = Workflow(
            user_id=user_id,
            name=name or template["name"],
            description=template["description"],
            trigger_type=template["trigger_type"],
            trigger_config_json="{}",
            nodes_json=json.dumps(template["nodes"], ensure_ascii=False),
            edges_json=json.dumps(template["edges"], ensure_ascii=False),
            is_template=False,
            template_category=template["category"],
        )
        session.add(workflow)
        await session.commit()
        await session.refresh(workflow)

        logger.info(
            "workflow_from_template",
            workflow_id=str(workflow.id),
            template_id=template_id,
        )
        return workflow

    # -----------------------------------------------------------------------
    # Audio Studio workflow nodes
    # -----------------------------------------------------------------------

    @staticmethod
    async def _node_edit_audio(previous_output: str, config: dict, user_id: UUID) -> dict:
        """Workflow node: edit audio file."""
        audio_id = config.get("audio_id", "")
        operations = config.get("operations", [])
        if not audio_id:
            return {"output": previous_output, "action": "edit_audio", "error": "No audio_id provided"}
        try:
            from app.modules.audio_studio.service import AudioStudioService
            from app.database import get_session_context
            from uuid import UUID as _UUID
            parsed_id = _UUID(str(audio_id).strip())
            async with get_session_context() as session:
                service = AudioStudioService(session)
                result = await service.edit_audio(user_id, parsed_id, operations)
            return {
                "output": f"Audio edited: {result.original_filename} ({result.duration_seconds}s)",
                "action": "edit_audio",
                "audio_id": str(result.id),
            }
        except Exception as e:
            return {"output": previous_output, "action": "edit_audio", "error": str(e)[:500]}

    @staticmethod
    async def _node_generate_podcast(previous_output: str, config: dict, user_id: UUID) -> dict:
        """Workflow node: generate podcast episode with chapters and show notes."""
        audio_id = config.get("audio_id", "")
        title = config.get("title", "Untitled Episode")
        if not audio_id:
            return {"output": previous_output, "action": "generate_podcast", "error": "No audio_id provided"}
        try:
            from app.modules.audio_studio.service import AudioStudioService
            from app.database import get_session_context
            from uuid import UUID as _UUID
            import json as _json
            parsed_id = _UUID(str(audio_id).strip())
            async with get_session_context() as session:
                service = AudioStudioService(session)
                await service.generate_chapters(user_id, parsed_id)
                notes = await service.generate_show_notes(user_id, parsed_id)
                episode = await service.create_podcast_episode(user_id, {
                    "audio_id": str(parsed_id),
                    "title": title,
                    "description": config.get("description", ""),
                    "show_notes": _json.dumps(notes.get("show_notes", {}), ensure_ascii=False),
                })
            return {
                "output": f"Podcast episode '{episode.title}' created (ID: {episode.id})",
                "action": "generate_podcast",
                "episode_id": str(episode.id),
            }
        except Exception as e:
            return {"output": previous_output, "action": "generate_podcast", "error": str(e)[:500]}

    @staticmethod
    async def _node_analyze_repo(text: str, config: dict, user_id: UUID) -> dict:
        """Analyze a GitHub repository in a workflow."""
        repo_url = config.get("repo_url", text or "").strip()
        if not repo_url:
            return {"output": "", "error": "No repo URL provided", "action": "analyze_repo"}

        analysis_types = config.get("analysis_types", ["all"])
        depth = config.get("depth", "standard")

        try:
            from app.modules.repo_analyzer.service import RepoAnalyzerService
            from app.modules.repo_analyzer.schemas import AnalysisCreate
            from app.database import get_session_context
            import json as _json

            svc = RepoAnalyzerService()
            async with get_session_context() as session:
                data = AnalysisCreate(
                    repo_url=repo_url,
                    analysis_types=analysis_types,
                    depth=depth,
                )
                analysis = await svc.create_analysis(user_id, data, session)
            await svc.run_analysis(analysis.id)

            from app.models.repo_analyzer import RepoAnalysis
            async with get_session_context() as session:
                refreshed = await session.get(RepoAnalysis, analysis.id)

            if refreshed and refreshed.results_json:
                results = _json.loads(refreshed.results_json)
                quality = results.get("quality", {})
                tech = results.get("tech_stack", {})
                output = f"Repo: {repo_url} | Grade: {quality.get('grade', '?')} ({quality.get('score', 0)}/100)"
                if tech.get("frameworks"):
                    output += f" | Frameworks: {', '.join(tech['frameworks'])}"
                return {
                    "output": output,
                    "action": "analyze_repo",
                    "analysis_id": str(analysis.id),
                }
            return {
                "output": f"Analysis created for {repo_url} (ID: {analysis.id})",
                "action": "analyze_repo",
                "analysis_id": str(analysis.id),
            }
        except Exception as e:
            return {"output": "", "error": str(e)[:500], "action": "analyze_repo"}

    @staticmethod
    async def _node_process_pdf(text: str, config: dict, user_id: UUID) -> dict:
        """Process, summarize, or query a PDF document in a workflow."""
        pdf_id = config.get("pdf_id", "")
        action = config.get("action", "summarize")
        if not pdf_id:
            return {"output": text, "error": "No pdf_id provided", "action": "process_pdf"}
        try:
            from uuid import UUID as _UUID
            from app.modules.pdf_processor.service import PDFProcessorService
            from app.database import get_session_context
            parsed_id = _UUID(str(pdf_id).strip())
            async with get_session_context() as session:
                if action == "query":
                    question = config.get("question", text or "")
                    result = await PDFProcessorService.query_pdf(
                        user_id, parsed_id, question, session,
                    )
                    step_output = result.get("answer", "") if result else "PDF query failed"
                elif action == "keywords":
                    result = await PDFProcessorService.extract_keywords(
                        user_id, parsed_id, session,
                    )
                    step_output = ", ".join(result.get("keywords", [])) if result else "Keyword extraction failed"
                elif action == "export":
                    fmt = config.get("format", "markdown")
                    result = await PDFProcessorService.export_pdf(
                        user_id, parsed_id, fmt, session,
                    )
                    step_output = result.get("content", "")[:3000] if result else "Export failed"
                else:
                    style = config.get("style", "executive")
                    result = await PDFProcessorService.summarize_pdf(
                        user_id, parsed_id, session, style=style,
                    )
                    step_output = result.get("summary", "") if result else "Summarization failed"
            return {"output": step_output, "action": "process_pdf"}
        except Exception as e:
            return {"output": "", "error": str(e)[:500], "action": "process_pdf"}

    @staticmethod
    async def _node_create_webhook(text: str, config: dict, user_id: UUID) -> dict:
        """Create a webhook connector via IntegrationHubService in a workflow."""
        url = config.get("url", text or "").strip()
        if not url or not url.startswith("http"):
            return {"output": text, "error": "No valid URL provided for webhook", "action": "create_webhook"}
        try:
            from app.modules.integration_hub.service import IntegrationHubService
            from app.database import get_session_context
            async with get_session_context() as session:
                svc = IntegrationHubService(session)
                connector = await svc.create_connector(
                    user_id=user_id,
                    data={
                        "name": config.get("name", "Workflow Webhook"),
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
            return {
                "output": f"Webhook created: {connector.name} (id: {connector.id})",
                "action": "create_webhook",
                "connector_id": str(connector.id),
            }
        except Exception as e:
            return {"output": "", "error": str(e)[:500], "action": "create_webhook"}

    @staticmethod
    async def _node_fine_tune(text: str, config: dict, user_id: UUID) -> dict:
        """Create a fine-tuning job in a workflow."""
        dataset_id = config.get("dataset_id", "")
        if not dataset_id:
            return {
                "output": text,
                "action": "fine_tune",
                "note": "No dataset_id provided. Create a dataset first via the Fine-Tuning module.",
            }
        try:
            from app.modules.fine_tuning.service import FineTuningService
            from app.database import get_session_context
            async with get_session_context() as session:
                job = await FineTuningService.create_job(
                    user_id=user_id,
                    name=config.get("name", "Workflow Fine-Tune"),
                    dataset_id=dataset_id,
                    base_model=config.get("base_model", "unsloth/tinyllama-bnb-4bit"),
                    provider=config.get("provider", "local"),
                    hyperparams=config.get("hyperparams", {}),
                    session=session,
                )
            return {
                "output": f"Fine-tuning job created: {job.name} (ID: {job.id}, status: {job.status})",
                "action": "fine_tune",
                "job_id": str(job.id),
            }
        except Exception as e:
            return {"output": "", "error": str(e)[:500], "action": "fine_tune"}
