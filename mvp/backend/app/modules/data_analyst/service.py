"""
Data Analyst service - AI-powered data analysis with NL queries and charts.

Processes CSV/JSON/Excel datasets, generates statistics, answers natural
language questions, and produces chart specifications for frontend rendering.
"""

import csv
import io
import json
from datetime import datetime
from typing import Optional
from uuid import UUID

import structlog
from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.data_analyst import DataAnalysis, AnalysisStatus, Dataset, DatasetStatus

logger = structlog.get_logger()


class DataAnalystService:
    """Service for AI-powered data analysis."""

    @staticmethod
    async def upload_dataset(
        user_id: UUID, filename: str, content: bytes,
        file_type: str, session: AsyncSession,
    ) -> Dataset:
        """Upload and process a dataset."""
        dataset = Dataset(
            user_id=user_id,
            name=filename.rsplit(".", 1)[0],
            filename=filename,
            file_type=file_type,
            file_size=len(content),
            status=DatasetStatus.PROCESSING,
        )
        session.add(dataset)
        await session.flush()

        try:
            # Try DuckDB first (100x faster on large CSVs), fallback to pandas parser
            parsed = None
            if file_type in ("csv", "tsv"):
                try:
                    from app.modules.data_analyst.duckdb_engine import is_duckdb_available, parse_csv_duckdb, auto_profile
                    if is_duckdb_available():
                        parsed = parse_csv_duckdb(content)
                        if parsed:
                            # Bonus: auto-profiling if ydata-profiling available
                            profile = auto_profile(content, filename)
                            if profile:
                                parsed["profile"] = profile
                            logger.info("dataset_parsed_duckdb", rows=parsed.get("row_count"))
                except Exception as e:
                    logger.debug("duckdb_fallback_to_pandas", error=str(e))

            if not parsed:
                if file_type == "csv":
                    parsed = DataAnalystService._parse_csv(content)
                elif file_type == "json":
                    parsed = DataAnalystService._parse_json(content)
                else:
                    parsed = DataAnalystService._parse_csv(content)  # fallback

            dataset.row_count = parsed["row_count"]
            dataset.column_count = parsed["column_count"]
            dataset.columns_json = json.dumps(parsed["columns"], ensure_ascii=False)
            dataset.preview_json = json.dumps(parsed["preview"], ensure_ascii=False)
            dataset.stats_json = json.dumps(parsed["stats"], ensure_ascii=False)
            dataset.status = DatasetStatus.READY

        except Exception as e:
            dataset.status = DatasetStatus.FAILED
            dataset.error = str(e)[:1000]
            logger.error("dataset_processing_failed", error=str(e))

        session.add(dataset)
        await session.commit()
        await session.refresh(dataset)

        logger.info(
            "dataset_uploaded",
            dataset_id=str(dataset.id),
            rows=dataset.row_count,
            cols=dataset.column_count,
        )
        return dataset

    @staticmethod
    def _parse_csv(content: bytes) -> dict:
        """Parse CSV content into structured data."""
        text = content.decode("utf-8", errors="replace")
        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)

        if not rows:
            return {"row_count": 0, "column_count": 0, "columns": [], "preview": [], "stats": {}}

        columns = []
        stats = {}
        headers = list(rows[0].keys())

        for col in headers:
            values = [r.get(col, "") for r in rows]
            non_null = sum(1 for v in values if v and v.strip())
            unique = len(set(v for v in values if v and v.strip()))
            sample = [v for v in values[:5] if v]

            # Try to detect numeric
            numeric_values = []
            for v in values:
                try:
                    numeric_values.append(float(v))
                except (ValueError, TypeError):
                    pass

            col_type = "numeric" if len(numeric_values) > len(values) * 0.5 else "text"

            columns.append({
                "name": col,
                "dtype": col_type,
                "non_null": non_null,
                "unique": unique,
                "sample_values": sample[:5],
            })

            if col_type == "numeric" and numeric_values:
                stats[col] = {
                    "min": min(numeric_values),
                    "max": max(numeric_values),
                    "mean": sum(numeric_values) / len(numeric_values),
                    "count": len(numeric_values),
                }

        preview = rows[:10]

        return {
            "row_count": len(rows),
            "column_count": len(headers),
            "columns": columns,
            "preview": preview,
            "stats": stats,
        }

    @staticmethod
    def _parse_json(content: bytes) -> dict:
        """Parse JSON content."""
        data = json.loads(content.decode("utf-8", errors="replace"))
        if isinstance(data, list) and data:
            rows = data
        elif isinstance(data, dict):
            # Try to find the array in the dict
            for v in data.values():
                if isinstance(v, list) and v:
                    rows = v
                    break
            else:
                rows = [data]
        else:
            rows = []

        if not rows or not isinstance(rows[0], dict):
            return {"row_count": 0, "column_count": 0, "columns": [], "preview": [], "stats": {}}

        headers = list(rows[0].keys())
        columns = []
        for col in headers:
            values = [str(r.get(col, "")) for r in rows]
            columns.append({
                "name": col,
                "dtype": "text",
                "non_null": sum(1 for v in values if v),
                "unique": len(set(values)),
                "sample_values": values[:5],
            })

        return {
            "row_count": len(rows),
            "column_count": len(headers),
            "columns": columns,
            "preview": [dict(r) for r in rows[:10]],
            "stats": {},
        }

    @staticmethod
    async def ask_question(
        dataset_id: UUID, user_id: UUID, question: str,
        analysis_type: str, provider: str, session: AsyncSession,
    ) -> DataAnalysis:
        """Ask a natural language question about a dataset."""
        dataset = await session.get(Dataset, dataset_id)
        if not dataset or dataset.user_id != user_id:
            analysis = DataAnalysis(
                dataset_id=dataset_id, user_id=user_id, question=question,
                status=AnalysisStatus.FAILED, error="Dataset not found",
            )
            session.add(analysis)
            await session.commit()
            await session.refresh(analysis)
            return analysis

        analysis = DataAnalysis(
            dataset_id=dataset_id,
            user_id=user_id,
            question=question,
            analysis_type=analysis_type,
            status=AnalysisStatus.ANALYZING,
            provider=provider,
        )
        session.add(analysis)
        await session.flush()

        try:
            columns = json.loads(dataset.columns_json)
            preview = json.loads(dataset.preview_json)
            stats = json.loads(dataset.stats_json)

            from app.ai_assistant.service import AIAssistantService

            prompt = f"""You are a data analyst. Analyze this dataset and answer the question.

Dataset: {dataset.name} ({dataset.row_count} rows, {dataset.column_count} columns)
Columns: {json.dumps(columns, indent=2)[:3000]}
Statistics: {json.dumps(stats, indent=2)[:2000]}
Sample data (first 5 rows): {json.dumps(preview[:5], indent=2)[:3000]}

Question: {question}

Respond with a JSON object:
{{
  "answer": "your detailed answer",
  "insights": [{{"insight": "key finding", "confidence": 0.9, "category": "trend|anomaly|correlation|distribution|summary"}}],
  "charts": [{{"type": "bar|line|pie|scatter|histogram|table|kpi", "title": "chart title", "data": {{"labels": [...], "values": [...]}}, "config": {{}}}}]
}}

Provide meaningful charts when relevant. Respond ONLY with the JSON object."""

            result = await AIAssistantService.process_text_with_provider(
                text=prompt,
                task="data_analysis",
                provider_name=provider,
                user_id=user_id,
                module="data_analyst",
            )

            response = result.get("processed_text", "{}")
            start = response.find("{")
            end = response.rfind("}") + 1

            if start >= 0 and end > start:
                parsed = json.loads(response[start:end])
                analysis.answer = parsed.get("answer", "")
                analysis.charts_json = json.dumps(parsed.get("charts", []), ensure_ascii=False)
                analysis.insights_json = json.dumps(parsed.get("insights", []), ensure_ascii=False)
            else:
                analysis.answer = response

            analysis.status = AnalysisStatus.COMPLETED

        except Exception as e:
            analysis.status = AnalysisStatus.FAILED
            analysis.error = str(e)[:1000]
            logger.error("data_analysis_failed", error=str(e))

        session.add(analysis)
        await session.commit()
        await session.refresh(analysis)
        return analysis

    @staticmethod
    async def auto_analyze(
        dataset_id: UUID, user_id: UUID, provider: str,
        depth: str, session: AsyncSession,
    ) -> DataAnalysis:
        """Automatically analyze a dataset and generate insights."""
        question = "Perform a comprehensive analysis of this dataset. Identify key trends, distributions, correlations, and anomalies. Provide actionable insights."
        if depth == "quick":
            question = "Provide a quick summary of this dataset with the 3 most important insights."
        elif depth == "deep":
            question = "Perform an exhaustive deep analysis. Cover distributions, correlations, outliers, trends, segments, and forecasts. Be very detailed."

        return await DataAnalystService.ask_question(
            dataset_id, user_id, question, "general", provider, session,
        )

    @staticmethod
    async def generate_report(
        dataset_id: UUID, user_id: UUID, analysis_ids: list[str],
        title: Optional[str], provider: str, session: AsyncSession,
    ) -> DataAnalysis:
        """Generate a comprehensive report from analyses."""
        dataset = await session.get(Dataset, dataset_id)
        if not dataset or dataset.user_id != user_id:
            report = DataAnalysis(
                dataset_id=dataset_id, user_id=user_id,
                question="Generate report", status=AnalysisStatus.FAILED,
                error="Dataset not found",
            )
            session.add(report)
            await session.commit()
            await session.refresh(report)
            return report

        # Gather previous analyses
        query = select(DataAnalysis).where(
            DataAnalysis.dataset_id == dataset_id,
            DataAnalysis.user_id == user_id,
            DataAnalysis.status == AnalysisStatus.COMPLETED,
        ).order_by(DataAnalysis.created_at.desc()).limit(10)
        prev = await session.execute(query)
        prev_analyses = list(prev.scalars().all())

        analyses_summary = "\n".join(
            f"Q: {a.question}\nA: {a.answer[:500]}" for a in prev_analyses
        )

        report_question = f"Generate a comprehensive data report titled '{title or dataset.name} Analysis Report}'. Previous analyses:\n{analyses_summary[:5000]}"

        return await DataAnalystService.ask_question(
            dataset_id, user_id, report_question, "general", provider, session,
        )

    @staticmethod
    async def list_datasets(user_id: UUID, session: AsyncSession) -> list[Dataset]:
        result = await session.execute(
            select(Dataset).where(Dataset.user_id == user_id)
            .order_by(Dataset.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_dataset(dataset_id: UUID, user_id: UUID, session: AsyncSession) -> Optional[Dataset]:
        d = await session.get(Dataset, dataset_id)
        if d and d.user_id != user_id:
            return None
        return d

    @staticmethod
    async def delete_dataset(dataset_id: UUID, user_id: UUID, session: AsyncSession) -> bool:
        d = await session.get(Dataset, dataset_id)
        if not d or d.user_id != user_id:
            return False
        # Delete analyses
        result = await session.execute(
            select(DataAnalysis).where(DataAnalysis.dataset_id == dataset_id)
        )
        for a in result.scalars().all():
            await session.delete(a)
        await session.delete(d)
        await session.commit()
        return True

    @staticmethod
    async def list_analyses(
        dataset_id: UUID, user_id: UUID, session: AsyncSession,
    ) -> list[DataAnalysis]:
        result = await session.execute(
            select(DataAnalysis).where(
                DataAnalysis.dataset_id == dataset_id,
                DataAnalysis.user_id == user_id,
            ).order_by(DataAnalysis.created_at.desc()).limit(20)
        )
        return list(result.scalars().all())
