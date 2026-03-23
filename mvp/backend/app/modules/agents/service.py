"""
Agent service - Orchestrates planning and execution of autonomous agents.
"""

import json
from datetime import datetime
from typing import Optional
from uuid import UUID

import structlog
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.agent import AgentRun, AgentStep, AgentStatus
from app.modules.agents.planner import create_plan
from app.modules.agents.executor import execute_step

logger = structlog.get_logger()


class AgentService:
    """Service for autonomous AI agent operations."""

    @staticmethod
    async def create_and_run(
        user_id: UUID,
        instruction: str,
        session: AsyncSession,
    ) -> AgentRun:
        """Create an agent run, plan steps, and execute them."""
        # Create the run
        run = AgentRun(
            user_id=user_id,
            instruction=instruction,
            status=AgentStatus.PLANNING,
        )
        session.add(run)
        await session.flush()

        logger.info("agent_run_created", run_id=str(run.id), instruction=instruction[:100])

        try:
            # Plan the steps
            plan = await create_plan(instruction)
            run.plan_json = json.dumps(plan, ensure_ascii=False)
            run.total_steps = len(plan)

            # Create step records
            steps = []
            for i, step_data in enumerate(plan):
                step = AgentStep(
                    run_id=run.id,
                    step_index=i,
                    action=step_data.get("action", "generate_text"),
                    description=step_data.get("description", ""),
                    input_json=json.dumps(step_data.get("input", {}), ensure_ascii=False),
                )
                session.add(step)
                steps.append(step)

            run.status = AgentStatus.EXECUTING
            await session.commit()

            logger.info("agent_plan_created", run_id=str(run.id), steps=len(plan))

            # Execute steps sequentially
            previous_output = None
            results = []

            for i, (step, step_data) in enumerate(zip(steps, plan)):
                step.status = AgentStatus.EXECUTING
                step.started_at = datetime.utcnow()
                run.current_step = i + 1
                session.add(step)
                session.add(run)
                await session.commit()

                try:
                    step_input = step_data.get("input", {})
                    step_input["_user_id"] = str(user_id)

                    result = await execute_step(
                        action=step_data.get("action", "generate_text"),
                        input_data=step_input,
                        previous_output=previous_output,
                    )

                    step.output_json = json.dumps(result, ensure_ascii=False)
                    step.status = AgentStatus.COMPLETED
                    step.completed_at = datetime.utcnow()

                    previous_output = result.get("output", "")
                    results.append(result)

                    if result.get("error"):
                        step.error = result["error"][:1000]

                    # Track cost for this step
                    try:
                        from app.modules.cost_tracker.tracker import track_ai_usage
                        await track_ai_usage(
                            user_id=user_id,
                            provider=result.get("provider", "unknown"),
                            model="agent",
                            module="agents",
                            action=step.action,
                            input_tokens=0,
                            output_tokens=len(result.get("output", "")),
                            latency_ms=int((step.completed_at - step.started_at).total_seconds() * 1000) if step.completed_at and step.started_at else 0,
                            success=step.status == AgentStatus.COMPLETED,
                            session=session,
                        )
                    except Exception:
                        pass

                except Exception as e:
                    step.status = AgentStatus.FAILED
                    step.error = str(e)[:1000]
                    step.completed_at = datetime.utcnow()
                    results.append({"error": str(e), "action": step.action})
                    logger.error("agent_step_failed", run_id=str(run.id), step=i, error=str(e))

                session.add(step)
                await session.commit()

            # Finalize
            run.status = AgentStatus.COMPLETED
            run.results_json = json.dumps(results, ensure_ascii=False)
            run.completed_at = datetime.utcnow()

        except Exception as e:
            run.status = AgentStatus.FAILED
            run.error = str(e)[:2000]
            run.completed_at = datetime.utcnow()
            logger.error("agent_run_failed", run_id=str(run.id), error=str(e))

        session.add(run)
        await session.commit()
        await session.refresh(run)

        logger.info(
            "agent_run_finished",
            run_id=str(run.id),
            status=run.status.value,
            steps_completed=run.current_step,
        )

        return run

    @staticmethod
    async def get_run(
        run_id: UUID,
        user_id: UUID,
        session: AsyncSession,
    ) -> Optional[dict]:
        """Get an agent run with its steps."""
        run = await session.get(AgentRun, run_id)
        if not run or run.user_id != user_id:
            return None

        result = await session.execute(
            select(AgentStep)
            .where(AgentStep.run_id == run_id)
            .order_by(AgentStep.step_index.asc())
        )
        steps = list(result.scalars().all())

        return {
            "run": run,
            "steps": steps,
        }

    @staticmethod
    async def list_runs(
        user_id: UUID,
        session: AsyncSession,
        limit: int = 20,
    ) -> list[AgentRun]:
        """List agent runs for a user."""
        result = await session.execute(
            select(AgentRun)
            .where(AgentRun.user_id == user_id)
            .order_by(AgentRun.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def cancel_run(
        run_id: UUID,
        user_id: UUID,
        session: AsyncSession,
    ) -> bool:
        """Cancel a running agent."""
        run = await session.get(AgentRun, run_id)
        if not run or run.user_id != user_id:
            return False
        if run.status in [AgentStatus.COMPLETED, AgentStatus.FAILED, AgentStatus.CANCELLED]:
            return False

        run.status = AgentStatus.CANCELLED
        run.completed_at = datetime.utcnow()
        session.add(run)
        await session.commit()
        return True
