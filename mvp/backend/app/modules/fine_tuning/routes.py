"""
Fine-Tuning Studio API routes.
"""

import json
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth import get_current_user
from app.database import get_session
from app.models.user import User
from app.modules.fine_tuning.schemas import (
    AddSamplesRequest, AvailableModel, DatasetCreate, DatasetFromSourceRequest,
    DatasetRead, EvalRead, EvalRequest, FineTuneCreate, FineTuneJobRead,
)
from app.modules.fine_tuning.service import FineTuningService
from app.rate_limit import limiter

router = APIRouter()


@router.post("/datasets", response_model=DatasetRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_dataset(
    request: Request, body: DatasetCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a training dataset with manual samples. Rate limit: 10/min"""
    return await FineTuningService.create_dataset(
        user_id=current_user.id, name=body.name, description=body.description,
        dataset_type=body.dataset_type,
        samples=[s.model_dump() for s in body.samples],
        validation_split=body.validation_split, session=session,
    )


@router.post("/datasets/from-source", response_model=DatasetRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/minute")
async def create_from_source(
    request: Request, body: DatasetFromSourceRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a dataset from platform data (transcriptions, conversations, documents). Rate limit: 3/min"""
    return await FineTuningService.create_dataset_from_source(
        user_id=current_user.id, name=body.name, source_type=body.source_type,
        dataset_type=body.dataset_type, max_samples=body.max_samples,
        filters=body.filters, session=session,
    )


@router.get("/datasets", response_model=list[DatasetRead])
@limiter.limit("20/minute")
async def list_datasets(
    request: Request, current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List training datasets. Rate limit: 20/min"""
    return await FineTuningService.list_datasets(current_user.id, session)


@router.get("/datasets/{dataset_id}", response_model=DatasetRead)
@limiter.limit("30/minute")
async def get_dataset(
    request: Request, dataset_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get dataset details. Rate limit: 30/min"""
    ds = await FineTuningService.get_dataset(dataset_id, current_user.id, session)
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return ds


@router.post("/datasets/{dataset_id}/samples", response_model=DatasetRead)
@limiter.limit("10/minute")
async def add_samples(
    request: Request, dataset_id: UUID, body: AddSamplesRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Add samples to a dataset. Rate limit: 10/min"""
    ds = await FineTuningService.add_samples(
        dataset_id, current_user.id, [s.model_dump() for s in body.samples], session,
    )
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return ds


@router.post("/datasets/{dataset_id}/assess-quality", response_model=DatasetRead)
@limiter.limit("3/minute")
async def assess_quality(
    request: Request, dataset_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """AI quality assessment of a dataset. Rate limit: 3/min"""
    ds = await FineTuningService.assess_quality(dataset_id, current_user.id, session)
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return ds


@router.delete("/datasets/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def delete_dataset(
    request: Request, dataset_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Delete a dataset. Rate limit: 10/min"""
    if not await FineTuningService.delete_dataset(dataset_id, current_user.id, session):
        raise HTTPException(status_code=404, detail="Dataset not found")


@router.post("/jobs", response_model=FineTuneJobRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/minute")
async def create_job(
    request: Request, body: FineTuneCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create and start a fine-tuning job. Rate limit: 3/min"""
    return await FineTuningService.create_job(
        user_id=current_user.id, name=body.name, dataset_id=body.dataset_id,
        base_model=body.base_model, provider=body.provider,
        hyperparams=body.hyperparams, session=session,
    )


@router.get("/jobs", response_model=list[FineTuneJobRead])
@limiter.limit("20/minute")
async def list_jobs(
    request: Request, current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List fine-tuning jobs. Rate limit: 20/min"""
    return await FineTuningService.list_jobs(current_user.id, session)


@router.get("/jobs/{job_id}", response_model=FineTuneJobRead)
@limiter.limit("30/minute")
async def get_job(
    request: Request, job_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get job details. Rate limit: 30/min"""
    job = await FineTuningService.get_job(job_id, current_user.id, session)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/jobs/{job_id}/evaluate", response_model=EvalRead)
@limiter.limit("3/minute")
async def evaluate_model(
    request: Request, job_id: UUID, body: EvalRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Evaluate a fine-tuned model. Rate limit: 3/min"""
    ev = await FineTuningService.evaluate_model(
        job_id, current_user.id, body.test_prompts, body.eval_type, session,
    )
    if not ev:
        raise HTTPException(status_code=404, detail="Job not found")
    return ev


@router.get("/jobs/{job_id}/evaluations", response_model=list[EvalRead])
@limiter.limit("20/minute")
async def list_evaluations(
    request: Request, job_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List evaluations for a job. Rate limit: 20/min"""
    return await FineTuningService.list_evaluations(job_id, current_user.id, session)


@router.get("/models", response_model=list[AvailableModel])
async def list_models():
    """List available base models for fine-tuning."""
    return [AvailableModel(**m) for m in FineTuningService.get_available_models()]
