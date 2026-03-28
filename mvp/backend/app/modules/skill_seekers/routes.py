"""
Skill Seekers API routes
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, status
from fastapi.responses import FileResponse
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth import get_current_user
from app.modules.auth_guards.middleware import require_verified_email
from app.database import get_session
from app.models.user import User
from app.models.skill_seekers import ScrapeJob
from app.modules.skill_seekers.schemas import CancelJobResponse, ScrapeJobCreate, ScrapeJobRead, PaginatedJobs, ScrapeJobStats
from app.modules.skill_seekers.service import SkillSeekersService
from app.rate_limit import limiter

router = APIRouter()


MAX_CONCURRENT_JOBS_PER_USER = 5


def get_service() -> SkillSeekersService:
    """Dependency to get the SkillSeekersService instance."""
    return SkillSeekersService()


def _celery_available() -> bool:
    """Check if Celery workers are available."""
    try:
        from app.celery_app import celery_app
        result = celery_app.control.ping(timeout=1.0)
        return bool(result)
    except Exception:
        return False


def _launch_job(service: SkillSeekersService, job_id, background_tasks: BackgroundTasks):
    """Dispatch job to Celery if available, else BackgroundTasks."""
    if _celery_available():
        from app.modules.skill_seekers.tasks import process_scrape_job_task
        process_scrape_job_task.delay(str(job_id))
    else:
        background_tasks.add_task(service.run_job, job_id)


# --------------------------------------------------------------------------
# POST /jobs - Create and launch a scrape job
# --------------------------------------------------------------------------

@router.post("/jobs", response_model=ScrapeJobRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def create_job(
    request: Request,
    data: ScrapeJobCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
    service: SkillSeekersService = Depends(get_service),
):
    """
    Create a new scrape job and launch it in the background.

    Accepts a list of GitHub repos (owner/repo format), target platforms,
    and an optional enhance flag.  The job runs asynchronously; poll
    GET /jobs/{job_id} for progress.
    """
    # Check concurrent job limit
    from app.models.skill_seekers import ScrapeJobStatus as SJS
    active_jobs, _ = await SkillSeekersService.get_jobs(
        user_id=current_user.id,
        session=session,
        status_filter=SJS.RUNNING,
    )
    pending_jobs, _ = await SkillSeekersService.get_jobs(
        user_id=current_user.id,
        session=session,
        status_filter=SJS.PENDING,
    )
    if len(active_jobs) + len(pending_jobs) >= MAX_CONCURRENT_JOBS_PER_USER:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Maximum {MAX_CONCURRENT_JOBS_PER_USER} concurrent jobs allowed. Wait for current jobs to complete.",
        )

    try:
        job = await SkillSeekersService.create_job(
            user_id=current_user.id,
            repos=data.repos,
            targets=data.targets,
            enhance=data.enhance,
            session=session,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Launch via Celery or BackgroundTasks fallback
    _launch_job(service, job.id, background_tasks)

    return ScrapeJobRead(**SkillSeekersService.job_to_read(job))


# --------------------------------------------------------------------------
# GET /jobs - List scrape jobs (paginated)
# --------------------------------------------------------------------------

@router.get("/jobs", response_model=PaginatedJobs)
@limiter.limit("30/minute")
async def list_jobs(
    request: Request,
    skip: int = 0,
    limit: int = 20,
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List scrape jobs for the current user with pagination and optional status filter."""
    from app.models.skill_seekers import ScrapeJobStatus as SJS
    parsed_status = None
    if status_filter:
        try:
            parsed_status = SJS(status_filter)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status_filter}")

    jobs, total = await SkillSeekersService.get_jobs(
        user_id=current_user.id,
        session=session,
        skip=skip,
        limit=min(limit, 100),
        status_filter=parsed_status,
    )

    items = [ScrapeJobRead(**SkillSeekersService.job_to_read(j)) for j in jobs]
    return PaginatedJobs(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
        has_more=(skip + limit) < total,
    )


# --------------------------------------------------------------------------
# GET /jobs/stats - User statistics (BEFORE /{job_id} to avoid path conflict)
# --------------------------------------------------------------------------

@router.get("/jobs/stats", response_model=ScrapeJobStats)
@limiter.limit("20/minute")
async def get_stats(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get scrape job statistics for the current user."""
    return await SkillSeekersService.get_user_stats(
        user_id=current_user.id,
        session=session,
    )


# --------------------------------------------------------------------------
# GET /jobs/{job_id} - Job detail
# --------------------------------------------------------------------------

@router.get("/jobs/{job_id}", response_model=ScrapeJobRead)
@limiter.limit("30/minute")
async def get_job(
    request: Request,
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get a single scrape job by ID."""
    job = await SkillSeekersService.get_job(
        job_id=job_id,
        user_id=current_user.id,
        session=session,
    )
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scrape job not found")

    return ScrapeJobRead(**SkillSeekersService.job_to_read(job))


# --------------------------------------------------------------------------
# DELETE /jobs/{job_id} - Delete a scrape job
# --------------------------------------------------------------------------

@router.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("5/minute")
async def delete_job(
    request: Request,
    job_id: UUID,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """Delete a scrape job and its output files."""
    deleted = await SkillSeekersService.delete_job(
        job_id=job_id,
        user_id=current_user.id,
        session=session,
    )
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scrape job not found")


# --------------------------------------------------------------------------
# GET /jobs/{job_id}/download/{filename} - Download output file
# --------------------------------------------------------------------------

@router.get("/jobs/{job_id}/download/{filename}")
@limiter.limit("30/minute")
async def download_file(
    request: Request,
    job_id: UUID,
    filename: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Download an output file from a completed scrape job."""
    job = await SkillSeekersService.get_job(
        job_id=job_id,
        user_id=current_user.id,
        session=session,
    )
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scrape job not found")

    filepath = SkillSeekersService.get_output_file(job, filename)
    if not filepath:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="text/markdown",
    )


# --------------------------------------------------------------------------
# POST /jobs/{job_id}/retry - Retry a failed job
# --------------------------------------------------------------------------

@router.post("/jobs/{job_id}/retry", response_model=ScrapeJobRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def retry_job(
    request: Request,
    job_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
    service: SkillSeekersService = Depends(get_service),
):
    """Retry a failed scrape job by cloning it and re-launching."""
    # Check concurrent job limit (same as create_job)
    from app.models.skill_seekers import ScrapeJobStatus as SJS
    active_jobs, _ = await SkillSeekersService.get_jobs(
        user_id=current_user.id, session=session, status_filter=SJS.RUNNING,
    )
    pending_jobs, _ = await SkillSeekersService.get_jobs(
        user_id=current_user.id, session=session, status_filter=SJS.PENDING,
    )
    if len(active_jobs) + len(pending_jobs) >= MAX_CONCURRENT_JOBS_PER_USER:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Maximum {MAX_CONCURRENT_JOBS_PER_USER} concurrent jobs allowed. Wait for current jobs to complete.",
        )

    new_job = await SkillSeekersService.retry_job(
        job_id=job_id,
        user_id=current_user.id,
        session=session,
    )
    if not new_job:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job not found, not owned by you, or not in failed state",
        )

    _launch_job(service, new_job.id, background_tasks)
    return ScrapeJobRead(**SkillSeekersService.job_to_read(new_job))


# --------------------------------------------------------------------------
# POST /jobs/{job_id}/cancel - Cancel a running/pending job
# --------------------------------------------------------------------------

@router.post("/jobs/{job_id}/cancel", response_model=CancelJobResponse)
@limiter.limit("5/minute")
async def cancel_job(
    request: Request,
    job_id: UUID,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """Cancel a running or pending scrape job."""
    cancelled = await SkillSeekersService.cancel_job(
        job_id=job_id,
        user_id=current_user.id,
        session=session,
    )
    if not cancelled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job not found, not owned by you, or not in a cancellable state",
        )
    return {"status": "cancelled", "job_id": str(job_id)}


# --------------------------------------------------------------------------
# GET /jobs/{job_id}/preview/{filename} - Preview output file content
# --------------------------------------------------------------------------

@router.get("/jobs/{job_id}/preview/{filename}")
@limiter.limit("30/minute")
async def preview_file(
    request: Request,
    job_id: UUID,
    filename: str,
    max_chars: int = 5000,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Preview the first N characters of an output file from a completed scrape job."""
    job = await SkillSeekersService.get_job(
        job_id=job_id,
        user_id=current_user.id,
        session=session,
    )
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scrape job not found")

    capped = min(max_chars, 50000)
    content = SkillSeekersService.get_file_preview(job, filename, max_chars=capped)
    if content is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    truncated = len(content) > capped
    return {"filename": filename, "content": content[:capped], "truncated": truncated}


# --------------------------------------------------------------------------
# GET /status - CLI availability check (no auth required)
# --------------------------------------------------------------------------

@router.get("/status")
@limiter.limit("30/minute")
async def check_status(request: Request):
    """Check if the skill-seekers CLI is installed and available."""
    return {
        "installed": SkillSeekersService.is_installed(),
        "mock_mode": not SkillSeekersService.is_installed(),
        "version": await SkillSeekersService.get_cli_version(),
    }


# --------------------------------------------------------------------------
# GET /jobs/{job_id}/download-token/{filename} - Generate signed download URL
# --------------------------------------------------------------------------

@router.get("/jobs/{job_id}/download-token/{filename}")
@limiter.limit("30/minute")
async def get_download_token(
    request: Request,
    job_id: UUID,
    filename: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Generate a signed token for downloading an output file (valid 5 min)."""
    job = await SkillSeekersService.get_job(job_id=job_id, user_id=current_user.id, session=session)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    filepath = SkillSeekersService.get_output_file(job, filename)
    if not filepath:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    token = SkillSeekersService.generate_download_token(job_id, filename)
    return {"token": token, "url": f"/api/skill-seekers/jobs/{job_id}/dl/{filename}?token={token}"}


# --------------------------------------------------------------------------
# GET /jobs/{job_id}/dl/{filename} - Public download with signed token (no JWT)
# --------------------------------------------------------------------------

@router.get("/jobs/{job_id}/dl/{filename}")
@limiter.limit("30/minute")
async def download_with_token(
    request: Request,
    job_id: UUID,
    filename: str,
    token: str = Query(..., description="Signed download token"),
    session: AsyncSession = Depends(get_session),
):
    """Download an output file using a signed token (no JWT required)."""
    if not SkillSeekersService.verify_download_token(job_id, filename, token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid or expired token")

    job = await session.get(ScrapeJob, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    filepath = SkillSeekersService.get_output_file(job, filename)
    if not filepath:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    return FileResponse(path=filepath, filename=filename, media_type="text/markdown")


# --------------------------------------------------------------------------
# POST /cleanup - Clean up old completed/failed jobs (admin/maintenance)
# --------------------------------------------------------------------------

@router.post("/cleanup")
@limiter.limit("2/minute")
async def cleanup_old_jobs(
    request: Request,
    max_age_hours: int = 24,
    current_user: User = Depends(require_verified_email),
):
    """Remove completed/failed jobs older than max_age_hours and their output files. Admin only."""
    if not getattr(current_user, "is_superuser", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can run cleanup operations",
        )
    count = await SkillSeekersService.cleanup_old_jobs(max_age_hours=max_age_hours)
    return {"cleaned": count, "max_age_hours": max_age_hours}
