"""
Multi-Agent Crew service - Orchestrates teams of specialized AI agents.

Supports sequential, parallel, and hierarchical process types,
inter-agent communication, and tool usage.
"""

import asyncio
import json
import time
from datetime import UTC, datetime
from typing import Optional
from uuid import UUID

import structlog
from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.multi_agent import Crew, CrewRun, CrewRunStatus, CrewStatus

logger = structlog.get_logger()

# Pre-built crew templates
CREW_TEMPLATES = [
    {
        "id": "research_writing",
        "name": "Research & Writing Team",
        "description": "Research a topic, write an article, then review for quality",
        "category": "content",
        "goal": "Produce high-quality, well-researched content",
        "icon": "Groups",
        "process_type": "sequential",
        "agents": [
            {"id": "a1", "role": "researcher", "name": "Research Analyst", "goal": "Find comprehensive information on the topic using web and knowledge base", "backstory": "Expert researcher with access to web crawling and knowledge base search", "tools": ["crawl_web", "search_knowledge"], "max_iterations": 3},
            {"id": "a2", "role": "writer", "name": "Content Writer", "goal": "Write engaging, well-structured content based on research findings", "backstory": "Professional writer specializing in clear, compelling content", "tools": ["generate", "content_studio"], "max_iterations": 2},
            {"id": "a3", "role": "reviewer", "name": "Quality Reviewer", "goal": "Review content for accuracy, clarity, and engagement", "backstory": "Editor with keen eye for quality and readability", "tools": ["generate"], "max_iterations": 2},
        ],
    },
    {
        "id": "market_analysis",
        "name": "Market Analysis Team",
        "description": "Analyze competitors, market trends, and generate strategic insights",
        "category": "research",
        "goal": "Provide comprehensive market intelligence",
        "icon": "Analytics",
        "process_type": "sequential",
        "agents": [
            {"id": "a1", "role": "researcher", "name": "Market Researcher", "goal": "Gather market data and competitor information", "tools": ["crawl_web", "search_knowledge"], "max_iterations": 3},
            {"id": "a2", "role": "analyst", "name": "Data Analyst", "goal": "Analyze gathered data for patterns and insights", "tools": ["generate", "sentiment"], "max_iterations": 2},
            {"id": "a3", "role": "creative", "name": "Strategy Advisor", "goal": "Synthesize analysis into actionable strategic recommendations", "tools": ["generate"], "max_iterations": 2},
        ],
    },
    {
        "id": "multilingual_content",
        "name": "Multilingual Content Team",
        "description": "Create content and translate to multiple languages with cultural adaptation",
        "category": "content",
        "goal": "Produce localized content for global audiences",
        "icon": "Translate",
        "process_type": "sequential",
        "agents": [
            {"id": "a1", "role": "writer", "name": "Content Creator", "goal": "Write the original content piece", "tools": ["generate", "content_studio"], "max_iterations": 2},
            {"id": "a2", "role": "translator", "name": "Localization Expert", "goal": "Translate and culturally adapt content", "tools": ["translate", "generate"], "max_iterations": 3},
            {"id": "a3", "role": "reviewer", "name": "Quality Checker", "goal": "Ensure translation accuracy and cultural sensitivity", "tools": ["generate"], "max_iterations": 1},
        ],
    },
    {
        "id": "social_media_team",
        "name": "Social Media Team",
        "description": "Research trending topics, create viral content, and optimize for engagement",
        "category": "marketing",
        "goal": "Create viral social media content",
        "icon": "TrendingUp",
        "process_type": "sequential",
        "agents": [
            {"id": "a1", "role": "researcher", "name": "Trend Scout", "goal": "Research current trends and viral content patterns", "tools": ["crawl_web"], "max_iterations": 2},
            {"id": "a2", "role": "creative", "name": "Creative Director", "goal": "Generate creative content ideas and hooks", "tools": ["generate", "content_studio"], "max_iterations": 2},
            {"id": "a3", "role": "analyst", "name": "Engagement Optimizer", "goal": "Optimize content for maximum engagement with hashtags, timing, and CTAs", "tools": ["generate", "sentiment"], "max_iterations": 1},
        ],
    },
]


class MultiAgentCrewService:
    """Service for managing and executing multi-agent crews."""

    @staticmethod
    async def create_crew(
        user_id: UUID,
        name: str,
        description: Optional[str],
        goal: Optional[str],
        agents: list[dict],
        process_type: str,
        session: AsyncSession,
    ) -> Crew:
        """Create a new crew."""
        crew = Crew(
            user_id=user_id,
            name=name,
            description=description,
            goal=goal,
            agents_json=json.dumps(agents, ensure_ascii=False),
            process_type=process_type,
        )
        session.add(crew)
        await session.commit()
        await session.refresh(crew)

        logger.info("crew_created", crew_id=str(crew.id), agents_count=len(agents))
        return crew

    @staticmethod
    async def get_crew(crew_id: UUID, user_id: UUID, session: AsyncSession) -> Optional[Crew]:
        crew = await session.get(Crew, crew_id)
        if crew and crew.user_id != user_id:
            return None
        return crew

    @staticmethod
    async def list_crews(
        user_id: UUID, session: AsyncSession, skip: int = 0, limit: int = 20,
    ) -> tuple[list[Crew], int]:
        count_result = await session.execute(
            select(func.count()).select_from(Crew).where(Crew.user_id == user_id)
        )
        total = count_result.scalar_one()
        result = await session.execute(
            select(Crew).where(Crew.user_id == user_id)
            .order_by(Crew.updated_at.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all()), total

    @staticmethod
    async def update_crew(crew_id: UUID, user_id: UUID, updates: dict, session: AsyncSession) -> Optional[Crew]:
        crew = await session.get(Crew, crew_id)
        if not crew or crew.user_id != user_id:
            return None
        if "name" in updates and updates["name"]:
            crew.name = updates["name"]
        if "description" in updates:
            crew.description = updates["description"]
        if "goal" in updates:
            crew.goal = updates["goal"]
        if "agents" in updates and updates["agents"] is not None:
            crew.agents_json = json.dumps(
                [a if isinstance(a, dict) else a.model_dump() for a in updates["agents"]],
                ensure_ascii=False,
            )
        if "process_type" in updates and updates["process_type"]:
            crew.process_type = updates["process_type"]
        if "status" in updates and updates["status"]:
            crew.status = updates["status"]
        crew.updated_at = datetime.now(UTC)
        session.add(crew)
        await session.commit()
        await session.refresh(crew)
        return crew

    @staticmethod
    async def delete_crew(crew_id: UUID, user_id: UUID, session: AsyncSession) -> bool:
        crew = await session.get(Crew, crew_id)
        if not crew or crew.user_id != user_id:
            return False
        run_result = await session.execute(
            select(CrewRun).where(CrewRun.crew_id == crew_id)
        )
        for run in run_result.scalars().all():
            await session.delete(run)
        await session.delete(crew)
        await session.commit()
        return True

    @staticmethod
    async def run_crew(
        crew_id: UUID, user_id: UUID, instruction: str,
        session: AsyncSession, input_data: Optional[dict] = None,
    ) -> Optional[CrewRun]:
        """Execute a crew by running agents sequentially or in parallel."""
        crew = await session.get(Crew, crew_id)
        if not crew or crew.user_id != user_id:
            return None

        agents = json.loads(crew.agents_json)
        start_time = time.monotonic()

        run = CrewRun(
            crew_id=crew_id,
            user_id=user_id,
            status=CrewRunStatus.RUNNING,
            instruction=instruction[:5000],
            total_agents=len(agents),
            started_at=datetime.now(UTC),
        )
        session.add(run)
        await session.commit()
        await session.refresh(run)

        messages = []
        context = instruction
        if input_data:
            context += f"\n\nInput data: {json.dumps(input_data, ensure_ascii=False)[:3000]}"

        total_tokens = 0

        process_type = crew.process_type or "sequential"
        if process_type == "hierarchical":
            logger.warning(
                "hierarchical_not_implemented",
                run_id=str(run.id),
                fallback="sequential",
            )
            process_type = "sequential"

        try:
            if process_type == "parallel":
                messages, total_tokens = await MultiAgentCrewService._run_parallel(
                    agents=agents,
                    context=context,
                    crew_goal=crew.goal or "",
                    user_id=user_id,
                    run=run,
                    session=session,
                )
            else:
                for i, agent_def in enumerate(agents):
                    run.current_agent = i + 1
                    session.add(run)
                    await session.commit()

                    agent_result = await MultiAgentCrewService._run_agent(
                        agent_def=agent_def,
                        context=context,
                        crew_goal=crew.goal or "",
                        previous_messages=messages,
                        user_id=user_id,
                    )

                    msg = {
                        "agent_id": agent_def["id"],
                        "agent_name": agent_def.get("name", agent_def["role"]),
                        "role": agent_def["role"],
                        "content": agent_result.get("output", ""),
                        "tool_used": agent_result.get("tool_used"),
                        "iteration": agent_result.get("iterations", 1),
                        "timestamp": datetime.now(UTC).isoformat(),
                    }
                    messages.append(msg)
                    context = agent_result.get("output", context)
                    total_tokens += agent_result.get("tokens", 0)

            run.status = CrewRunStatus.COMPLETED
            run.final_output = messages[-1]["content"] if messages else ""

        except Exception as e:
            run.status = CrewRunStatus.FAILED
            run.error = str(e)[:2000]
            logger.error("crew_run_failed", run_id=str(run.id), error=str(e))

        elapsed_ms = int((time.monotonic() - start_time) * 1000)
        run.messages_json = json.dumps(messages, ensure_ascii=False)
        run.duration_ms = elapsed_ms
        run.tokens_used = total_tokens
        run.completed_at = datetime.now(UTC)
        session.add(run)

        crew.run_count += 1
        session.add(crew)

        await session.commit()
        await session.refresh(run)

        logger.info(
            "crew_run_finished", run_id=str(run.id),
            status=run.status.value, duration_ms=elapsed_ms,
        )
        return run

    @staticmethod
    async def _run_parallel(
        agents: list[dict], context: str, crew_goal: str,
        user_id: UUID, run: "CrewRun", session: AsyncSession,
    ) -> tuple[list[dict], int]:
        run.current_agent = 0
        session.add(run)
        await session.commit()

        completed_count = 0
        progress_lock = asyncio.Lock()

        async def _safe_run(agent_def: dict) -> dict:
            nonlocal completed_count
            try:
                result = await MultiAgentCrewService._run_agent(
                    agent_def=agent_def,
                    context=context,
                    crew_goal=crew_goal,
                    previous_messages=[],
                    user_id=user_id,
                )
                return {"ok": True, "agent_def": agent_def, "result": result}
            except Exception as exc:
                logger.error(
                    "parallel_agent_failed",
                    agent_id=agent_def.get("id"),
                    error=str(exc),
                )
                return {"ok": False, "agent_def": agent_def, "error": str(exc)}
            finally:
                async with progress_lock:
                    completed_count += 1
                    run.current_agent = completed_count
                    session.add(run)
                    await session.commit()

        raw_results = await asyncio.gather(*[_safe_run(a) for a in agents])

        messages: list[dict] = []
        total_tokens = 0
        for item in raw_results:
            agent_def = item["agent_def"]
            if item["ok"]:
                agent_result = item["result"]
                content = agent_result.get("output", "")
                total_tokens += agent_result.get("tokens", 0)
                tool_used = agent_result.get("tool_used")
                iteration = agent_result.get("iterations", 1)
            else:
                content = f"[Agent error: {item['error'][:500]}]"
                tool_used = None
                iteration = 0
            messages.append({
                "agent_id": agent_def["id"],
                "agent_name": agent_def.get("name", agent_def["role"]),
                "role": agent_def["role"],
                "content": content,
                "tool_used": tool_used,
                "iteration": iteration,
                "timestamp": datetime.now(UTC).isoformat(),
            })

        return messages, total_tokens

    @staticmethod
    async def _run_agent(
        agent_def: dict, context: str, crew_goal: str,
        previous_messages: list[dict], user_id: UUID,
    ) -> dict:
        """Run a single agent with its tools and persona."""
        from app.ai_assistant.service import AIAssistantService

        role = agent_def.get("role", "assistant")
        name = agent_def.get("name", role)
        goal = agent_def.get("goal", "")
        backstory = agent_def.get("backstory", "")
        tools = agent_def.get("tools", [])
        provider = agent_def.get("provider", "gemini")
        max_iter = agent_def.get("max_iterations", 3)

        # Build conversation history from previous agents
        history = ""
        if previous_messages:
            history = "\n\n".join(
                f"[{m['agent_name']} ({m['role']})]:\n{m['content'][:2000]}"
                for m in previous_messages[-5:]
            )

        # Build tool descriptions
        tool_descriptions = []
        for tool in tools:
            tool_descriptions.append(f"- {tool}")

        prompt = f"""You are {name}, a {role} agent in an AI crew.

Crew Goal: {crew_goal}
Your Goal: {goal}
{f'Backstory: {backstory}' if backstory else ''}
Available Tools: {', '.join(tools) if tools else 'none (text generation only)'}

Previous agent outputs:
{history if history else '(You are the first agent)'}

Current task/context:
{context[:8000]}

Instructions:
1. Analyze the context and previous agent outputs
2. Execute your role to achieve your goal
3. Produce a clear, comprehensive output for the next agent

Respond with your output directly. Be thorough and specific."""

        # Execute with tool usage if needed
        tool_used = None
        tool_output = ""

        if "crawl_web" in tools and ("http" in context.lower() or "url" in context.lower()):
            try:
                import re
                urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', context)
                if urls:
                    from app.modules.web_crawler.service import WebCrawlerService
                    result = await WebCrawlerService.scrape(url=urls[0], extract_images=False)
                    if result.get("success"):
                        tool_output = f"\n\n[Web Research from {urls[0]}]:\n{result.get('markdown', '')[:4000]}"
                        tool_used = "crawl_web"
            except Exception:
                pass

        if "search_knowledge" in tools and not tool_output:
            try:
                from app.modules.knowledge.service import KnowledgeService
                from app.database import get_session_context
                async with get_session_context() as kb_session:
                    results = await KnowledgeService.search(
                        user_id=user_id, query=context[:200], session=kb_session, limit=3,
                    )
                if results:
                    tool_output = "\n\n[Knowledge Base Results]:\n" + "\n".join(
                        f"- [{r.get('filename', '')}] {r.get('content', '')[:300]}" for r in results
                    )
                    tool_used = "search_knowledge"
            except Exception:
                pass

        if "sentiment" in tools and not tool_output:
            try:
                from app.modules.sentiment.service import SentimentService
                result = await SentimentService.analyze_text(context[:5000])
                tool_output = f"\n\n[Sentiment Analysis]: {result.get('overall_sentiment', 'neutral')} (score: {result.get('overall_score', 0)})"
                tool_used = "sentiment"
            except Exception:
                pass

        full_prompt = prompt + tool_output

        result = await AIAssistantService.process_text_with_provider(
            text=full_prompt,
            task="agent",
            provider_name=provider,
            user_id=user_id,
            module="multi_agent_crew",
        )

        return {
            "output": result.get("processed_text", ""),
            "tool_used": tool_used,
            "iterations": 1,
            "tokens": 0,
        }

    @staticmethod
    async def list_runs(
        crew_id: UUID, user_id: UUID, session: AsyncSession,
        skip: int = 0, limit: int = 20,
    ) -> list[CrewRun]:
        result = await session.execute(
            select(CrewRun).where(
                CrewRun.crew_id == crew_id, CrewRun.user_id == user_id,
            ).order_by(CrewRun.created_at.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_run(run_id: UUID, user_id: UUID, session: AsyncSession) -> Optional[CrewRun]:
        run = await session.get(CrewRun, run_id)
        if run and run.user_id != user_id:
            return None
        return run

    @staticmethod
    def get_templates(category: Optional[str] = None) -> list[dict]:
        if category:
            return [t for t in CREW_TEMPLATES if t["category"] == category]
        return CREW_TEMPLATES

    @staticmethod
    async def create_from_template(
        template_id: str, user_id: UUID, name: Optional[str], session: AsyncSession,
    ) -> Optional[Crew]:
        template = next((t for t in CREW_TEMPLATES if t["id"] == template_id), None)
        if not template:
            return None
        crew = Crew(
            user_id=user_id,
            name=name or template["name"],
            description=template["description"],
            goal=template["goal"],
            agents_json=json.dumps(template["agents"], ensure_ascii=False),
            process_type=template["process_type"],
            is_template=False,
            template_category=template["category"],
        )
        session.add(crew)
        await session.commit()
        await session.refresh(crew)
        return crew
