"""
Pipeline service - Business logic for creating and executing AI pipelines.
"""

import json
from datetime import datetime
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

        pipeline.updated_at = datetime.utcnow()
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
            started_at=datetime.utcnow(),
        )
        session.add(execution)
        await session.commit()
        await session.refresh(execution)

        # Process steps sequentially
        results = []
        previous_output = None

        try:
            for i, step in enumerate(steps):
                execution.current_step = i + 1
                session.add(execution)
                await session.commit()

                step_result = await PipelineService._execute_step(
                    step, previous_output
                )
                results.append(step_result)
                previous_output = step_result.get("output", "")

            execution.status = ExecutionStatus.COMPLETED
            execution.results_json = json.dumps(results, ensure_ascii=False)
            execution.completed_at = datetime.utcnow()

        except Exception as e:
            execution.status = ExecutionStatus.FAILED
            execution.error = str(e)[:2000]
            execution.results_json = json.dumps(results, ensure_ascii=False)
            execution.completed_at = datetime.utcnow()
            logger.error(
                "pipeline_execution_failed",
                execution_id=str(execution.id),
                error=str(e),
            )

        session.add(execution)
        await session.commit()
        await session.refresh(execution)

        logger.info(
            "pipeline_execution_finished",
            execution_id=str(execution.id),
            status=execution.status.value,
            steps_completed=execution.current_step,
        )

        return execution

    @staticmethod
    async def _execute_step(step: dict, previous_output: Optional[str]) -> dict:
        """Execute a single pipeline step."""
        step_type = step.get("type", "unknown")
        config = step.get("config", {})

        if step_type == "summarize":
            return await PipelineService._step_summarize(previous_output or "", config)
        elif step_type == "translate":
            return await PipelineService._step_translate(previous_output or "", config)
        elif step_type == "transcription":
            return {"type": "transcription", "output": previous_output or "", "note": "Transcription step requires external input"}
        elif step_type == "export":
            return {"type": "export", "output": previous_output or "", "format": config.get("format", "txt")}
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
