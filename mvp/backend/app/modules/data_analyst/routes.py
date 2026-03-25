"""
Data Analyst API routes.
"""

import json
import os
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth import get_current_user
from app.database import get_session
from app.models.user import User
from app.modules.data_analyst.schemas import (
    AnalysisRead, AskDataRequest, AutoAnalyzeRequest, ChartSpec,
    DatasetRead, GenerateReportRequest, InsightItem,
)
from app.modules.data_analyst.service import DataAnalystService
from app.rate_limit import limiter

router = APIRouter()

ALLOWED_TYPES = {".csv": "csv", ".json": "json", ".xlsx": "xlsx", ".tsv": "csv"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


def _analysis_to_read(a) -> AnalysisRead:
    charts = json.loads(a.charts_json) if a.charts_json else []
    insights = json.loads(a.insights_json) if a.insights_json else []
    return AnalysisRead(
        id=a.id, dataset_id=a.dataset_id, user_id=a.user_id,
        question=a.question, analysis_type=a.analysis_type,
        answer=a.answer,
        charts=[ChartSpec(**c) for c in charts],
        insights=[InsightItem(**i) for i in insights],
        code_executed=a.code_executed,
        status=a.status.value if hasattr(a.status, "value") else a.status,
        provider=a.provider, error=a.error, created_at=a.created_at,
    )


@router.post("/datasets", response_model=DatasetRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def upload_dataset(
    request: Request,
    file: UploadFile = File(..., description="CSV, JSON, or Excel file"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Upload a dataset for analysis. Rate limit: 5/min"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="File must have a filename")

    _, ext = os.path.splitext(file.filename)
    ext = ext.lower()
    if ext not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed: {list(ALLOWED_TYPES.keys())}")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 50MB)")

    return await DataAnalystService.upload_dataset(
        user_id=current_user.id, filename=file.filename,
        content=content, file_type=ALLOWED_TYPES[ext], session=session,
    )


@router.get("/datasets", response_model=list[DatasetRead])
@limiter.limit("20/minute")
async def list_datasets(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List datasets. Rate limit: 20/min"""
    return await DataAnalystService.list_datasets(current_user.id, session)


@router.get("/datasets/{dataset_id}", response_model=DatasetRead)
@limiter.limit("30/minute")
async def get_dataset(
    request: Request, dataset_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get dataset details with preview. Rate limit: 30/min"""
    d = await DataAnalystService.get_dataset(dataset_id, current_user.id, session)
    if not d:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return d


@router.delete("/datasets/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def delete_dataset(
    request: Request, dataset_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Delete dataset and analyses. Rate limit: 10/min"""
    if not await DataAnalystService.delete_dataset(dataset_id, current_user.id, session):
        raise HTTPException(status_code=404, detail="Dataset not found")


@router.post("/datasets/{dataset_id}/ask", response_model=AnalysisRead)
@limiter.limit("5/minute")
async def ask_question(
    request: Request, dataset_id: UUID, body: AskDataRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Ask a natural language question about a dataset. Rate limit: 5/min"""
    analysis = await DataAnalystService.ask_question(
        dataset_id, current_user.id, body.question,
        body.analysis_type, body.provider, session,
    )
    return _analysis_to_read(analysis)


@router.post("/datasets/{dataset_id}/auto-analyze", response_model=AnalysisRead)
@limiter.limit("3/minute")
async def auto_analyze(
    request: Request, dataset_id: UUID, body: AutoAnalyzeRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Automatically analyze a dataset. Rate limit: 3/min"""
    analysis = await DataAnalystService.auto_analyze(
        dataset_id, current_user.id, body.provider, body.depth, session,
    )
    return _analysis_to_read(analysis)


@router.post("/datasets/{dataset_id}/report", response_model=AnalysisRead)
@limiter.limit("2/minute")
async def generate_report(
    request: Request, dataset_id: UUID, body: GenerateReportRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Generate a comprehensive report. Rate limit: 2/min"""
    analysis = await DataAnalystService.generate_report(
        dataset_id, current_user.id, body.analysis_ids,
        body.title, "gemini", session,
    )
    return _analysis_to_read(analysis)


@router.get("/datasets/{dataset_id}/analyses", response_model=list[AnalysisRead])
@limiter.limit("20/minute")
async def list_analyses(
    request: Request, dataset_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List analyses for a dataset. Rate limit: 20/min"""
    analyses = await DataAnalystService.list_analyses(dataset_id, current_user.id, session)
    return [_analysis_to_read(a) for a in analyses]
