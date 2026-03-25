"""
Skill Seekers API routes
"""

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth import get_current_user
from app.database import get_session
from app.models.user import User
from app.modules.skill_seekers.schemas import ScrapeJobCreate, ScrapeJobRead, PaginatedJobs, ScrapeJobStats
from app.modules.skill_seekers.service import SkillSeekersService
from app.rate_limit import limiter

router = APIRouter()


def get_service() -> SkillSeekersService:
    """Dependency to get the SkillSeekersService instance."""
    return SkillSeekersService()


# --------------------------------------------------------------------------
# POST /jobs - Create and launch a scrape job
# --------------------------------------------------------------------------

@router.post("/jobs", response_model=ScrapeJobRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def create_job(
    request: Request,
    data: ScrapeJobCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    service: SkillSeekersService = Depends(get_service),
):
    """
    Create a new scrape job and launch it in the background.

    Accepts a list of GitHub repos (owner/repo format), target platforms,
    and an optional enhance flag.  The job runs asynchronously; poll
    GET /jobs/{job_id} for progress.
    """
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

    # Launch background processing
    background_tasks.add_task(service.run_job, job.id)

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
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List scrape jobs for the current user with pagination."""
    jobs, total = await SkillSeekersService.get_jobs(
        user_id=current_user.id,
        session=session,
        skip=skip,
        limit=min(limit, 100),
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
    current_user: User = Depends(get_current_user),
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
# GET /status - CLI availability check (no auth required)
# --------------------------------------------------------------------------

@router.get("/status")
@limiter.limit("30/minute")
async def check_status(request: Request):
    """Check if the skill-seekers CLI is installed and available."""
    return {
        "installed": SkillSeekersService.is_installed(),
        "mock_mode": not SkillSeekersService.is_installed(),
    }
