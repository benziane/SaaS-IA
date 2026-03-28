"""
Code Sandbox API routes.
"""

import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth import get_current_user
from app.modules.auth_guards.middleware import require_verified_email
from app.database import get_session
from app.models.user import User
from app.modules.code_sandbox.schemas import (
    CellCreate, CellResult, CellUpdate,
    CodeDebugRequest, CodeDebugResponse,
    CodeExplainRequest, CodeExplainResponse,
    CodeGenerateRequest, CodeGenerateResponse,
    SandboxCreate, SandboxRead,
)
from app.modules.code_sandbox.service import CodeSandboxService
from app.rate_limit import limiter

router = APIRouter()


def _sandbox_to_read(s) -> SandboxRead:
    cells = json.loads(s.cells_json) if s.cells_json else []
    return SandboxRead(
        id=s.id,
        user_id=s.user_id,
        name=s.name,
        language=s.language,
        description=s.description,
        cells=cells,
        status=s.status.value if hasattr(s.status, "value") else s.status,
        created_at=s.created_at,
        updated_at=s.updated_at,
    )


# ─── Sandbox CRUD ───────────────────────────────────────────────

@router.post("/sandboxes", response_model=SandboxRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_sandbox(
    request: Request,
    body: SandboxCreate,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """Create a new code sandbox. Rate limit: 10/min"""
    sandbox = await CodeSandboxService.create_sandbox(
        user_id=current_user.id,
        data=body.model_dump(),
        session=session,
    )
    return _sandbox_to_read(sandbox)


@router.get("/sandboxes", response_model=list[SandboxRead])
@limiter.limit("30/minute")
async def list_sandboxes(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List user's sandboxes. Rate limit: 30/min"""
    sandboxes = await CodeSandboxService.list_sandboxes(current_user.id, session)
    return [_sandbox_to_read(s) for s in sandboxes]


@router.get("/sandboxes/{sandbox_id}", response_model=SandboxRead)
@limiter.limit("30/minute")
async def get_sandbox(
    request: Request,
    sandbox_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get sandbox with cells. Rate limit: 30/min"""
    sandbox = await CodeSandboxService.get_sandbox(current_user.id, sandbox_id, session)
    if not sandbox:
        raise HTTPException(status_code=404, detail="Sandbox not found")
    return _sandbox_to_read(sandbox)


@router.delete("/sandboxes/{sandbox_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def delete_sandbox(
    request: Request,
    sandbox_id: UUID,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """Delete (archive) a sandbox. Rate limit: 10/min"""
    if not await CodeSandboxService.delete_sandbox(current_user.id, sandbox_id, session):
        raise HTTPException(status_code=404, detail="Sandbox not found")


# ─── Cell operations ────────────────────────────────────────────

@router.post("/sandboxes/{sandbox_id}/cells", status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def add_cell(
    request: Request,
    sandbox_id: UUID,
    body: CellCreate,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """Add a cell to a sandbox. Rate limit: 20/min"""
    cell = await CodeSandboxService.add_cell(
        user_id=current_user.id,
        sandbox_id=sandbox_id,
        data=body.model_dump(),
        session=session,
    )
    if cell is None:
        raise HTTPException(status_code=404, detail="Sandbox not found")
    return cell


@router.put("/sandboxes/{sandbox_id}/cells/{cell_id}")
@limiter.limit("30/minute")
async def update_cell(
    request: Request,
    sandbox_id: UUID,
    cell_id: str,
    body: CellUpdate,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """Update cell source code. Rate limit: 30/min"""
    cell = await CodeSandboxService.update_cell(
        user_id=current_user.id,
        sandbox_id=sandbox_id,
        cell_id=cell_id,
        source=body.source,
        session=session,
    )
    if cell is None:
        raise HTTPException(status_code=404, detail="Cell or sandbox not found")
    return cell


@router.delete("/sandboxes/{sandbox_id}/cells/{cell_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("20/minute")
async def delete_cell(
    request: Request,
    sandbox_id: UUID,
    cell_id: str,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """Remove a cell from a sandbox. Rate limit: 20/min"""
    if not await CodeSandboxService.delete_cell(current_user.id, sandbox_id, cell_id, session):
        raise HTTPException(status_code=404, detail="Cell or sandbox not found")


@router.post("/sandboxes/{sandbox_id}/cells/{cell_id}/execute", response_model=CellResult)
@limiter.limit("10/minute")
async def execute_cell(
    request: Request,
    sandbox_id: UUID,
    cell_id: str,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """Execute a cell in a safe sandbox. Rate limit: 10/min"""
    result = await CodeSandboxService.execute_cell(
        user_id=current_user.id,
        sandbox_id=sandbox_id,
        cell_id=cell_id,
        session=session,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Cell or sandbox not found")
    return result


# ─── AI-powered features ────────────────────────────────────────

@router.post("/generate", response_model=CodeGenerateResponse)
@limiter.limit("5/minute")
async def generate_code(
    request: Request,
    body: CodeGenerateRequest,
    current_user: User = Depends(require_verified_email),
):
    """Generate code from natural language. Rate limit: 5/min"""
    result = await CodeSandboxService.generate_code(
        user_id=current_user.id,
        prompt=body.prompt,
        language=body.language,
        context=body.context,
    )
    return CodeGenerateResponse(**result)


@router.post("/explain", response_model=CodeExplainResponse)
@limiter.limit("10/minute")
async def explain_code(
    request: Request,
    body: CodeExplainRequest,
    current_user: User = Depends(require_verified_email),
):
    """Explain code using AI. Rate limit: 10/min"""
    result = await CodeSandboxService.explain_code(
        user_id=current_user.id,
        code=body.code,
    )
    return CodeExplainResponse(**result)


@router.post("/debug", response_model=CodeDebugResponse)
@limiter.limit("5/minute")
async def debug_code(
    request: Request,
    body: CodeDebugRequest,
    current_user: User = Depends(require_verified_email),
):
    """Debug code with AI assistance. Rate limit: 5/min"""
    result = await CodeSandboxService.debug_code(
        user_id=current_user.id,
        code=body.code,
        error=body.error,
    )
    return CodeDebugResponse(**result)
