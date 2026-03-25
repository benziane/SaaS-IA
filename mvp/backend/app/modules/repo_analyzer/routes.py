"""
Repo Analyzer API routes
"""

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth import get_current_user
from app.database import get_session
from app.models.user import User
from app.modules.repo_analyzer.schemas import (
    AnalysisCreate,
    AnalysisRead,
    CompareRequest,
    CompareResult,
    PaginatedAnalyses,
)
from app.modules.repo_analyzer.service import RepoAnalyzerService
from app.rate_limit import limiter

router = APIRouter()


def get_service() -> RepoAnalyzerService:
    """Dependency to get the RepoAnalyzerService instance."""
    return RepoAnalyzerService()


# --------------------------------------------------------------------------
# POST /analyze - Create and launch a repo analysis
# --------------------------------------------------------------------------

@router.post("/analyze", response_model=AnalysisRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_analysis(
    request: Request,
    data: AnalysisCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    service: RepoAnalyzerService = Depends(get_service),
):
    """
    Create a new repo analysis and launch it in the background.

    Analysis types: structure, tech_stack, quality, documentation, dependencies, security, all.
    Depth: quick (README + package files), standard (+ source scan), deep (+ AI analysis).
    """
    try:
        analysis = await RepoAnalyzerService.create_analysis(
            user_id=current_user.id,
            data=data,
            session=session,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Launch background processing
    background_tasks.add_task(service.run_analysis, analysis.id)

    return AnalysisRead(**RepoAnalyzerService.analysis_to_read(analysis))


# --------------------------------------------------------------------------
# GET /analyses - List analyses (paginated)
# --------------------------------------------------------------------------

@router.get("/analyses", response_model=PaginatedAnalyses)
@limiter.limit("30/minute")
async def list_analyses(
    request: Request,
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List repo analyses for the current user with pagination."""
    analyses, total = await RepoAnalyzerService.list_analyses(
        user_id=current_user.id,
        session=session,
        skip=skip,
        limit=min(limit, 100),
    )

    items = [AnalysisRead(**RepoAnalyzerService.analysis_to_read(a)) for a in analyses]
    return PaginatedAnalyses(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
        has_more=(skip + limit) < total,
    )


# --------------------------------------------------------------------------
# GET /status - Git availability check (no auth required)
# --------------------------------------------------------------------------

@router.get("/status")
@limiter.limit("30/minute")
async def check_status(request: Request):
    """Check if git is installed and available."""
    return {
        "installed": RepoAnalyzerService.is_installed(),
        "mock_mode": not RepoAnalyzerService.is_installed(),
    }


# --------------------------------------------------------------------------
# GET /{analysis_id} - Analysis detail
# --------------------------------------------------------------------------

@router.get("/{analysis_id}", response_model=AnalysisRead)
@limiter.limit("30/minute")
async def get_analysis(
    request: Request,
    analysis_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get a single repo analysis by ID."""
    analysis = await RepoAnalyzerService.get_analysis(
        user_id=current_user.id,
        analysis_id=analysis_id,
        session=session,
    )
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")

    return AnalysisRead(**RepoAnalyzerService.analysis_to_read(analysis))


# --------------------------------------------------------------------------
# DELETE /{analysis_id} - Delete an analysis
# --------------------------------------------------------------------------

@router.delete("/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("5/minute")
async def delete_analysis(
    request: Request,
    analysis_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Delete a repo analysis."""
    deleted = await RepoAnalyzerService.delete_analysis(
        user_id=current_user.id,
        analysis_id=analysis_id,
        session=session,
    )
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")


# --------------------------------------------------------------------------
# POST /compare - Compare multiple repos
# --------------------------------------------------------------------------

@router.post("/compare", response_model=CompareResult)
@limiter.limit("3/minute")
async def compare_repos(
    request: Request,
    data: CompareRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    service: RepoAnalyzerService = Depends(get_service),
):
    """Compare 2-5 repositories side by side."""
    if len(data.repo_urls) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 2 repo URLs required for comparison",
        )

    result = await service.compare_repos(
        user_id=current_user.id,
        repo_urls=data.repo_urls,
        analysis_types=data.analysis_types,
        session=session,
    )
    return CompareResult(**result)
