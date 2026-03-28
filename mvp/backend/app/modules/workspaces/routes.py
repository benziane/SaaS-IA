"""
Workspace API routes - Collaboration with shared items and comments.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth import get_current_user
from app.modules.auth_guards.middleware import require_verified_email
from app.database import get_session
from app.models.user import User
from app.modules.workspaces.schemas import (
    CommentCreate,
    CommentRead,
    InviteRequest,
    MemberRead,
    ShareItemRequest,
    SharedItemRead,
    WorkspaceCreate,
    WorkspaceRead,
    WorkspaceUpdate,
)
from app.modules.workspaces.service import WorkspaceService
from app.rate_limit import limiter

router = APIRouter()


@router.post("/", response_model=WorkspaceRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_workspace(
    request: Request,
    body: WorkspaceCreate,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """Create a new workspace. The creator becomes the owner."""
    workspace = await WorkspaceService.create_workspace(
        owner_id=current_user.id,
        name=body.name,
        description=body.description,
        session=session,
    )
    count = await WorkspaceService.get_member_count(workspace.id, session)
    return WorkspaceRead(
        id=workspace.id,
        name=workspace.name,
        description=workspace.description,
        owner_id=workspace.owner_id,
        is_active=workspace.is_active,
        member_count=count,
        created_at=workspace.created_at,
        updated_at=workspace.updated_at,
    )


@router.get("/", response_model=list[WorkspaceRead])
@limiter.limit("20/minute")
async def list_workspaces(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List all workspaces the user is a member of."""
    results = await WorkspaceService.list_workspaces(current_user.id, session)
    items = []
    for workspace, role in results:
        count = await WorkspaceService.get_member_count(workspace.id, session)
        items.append(WorkspaceRead(
            id=workspace.id,
            name=workspace.name,
            description=workspace.description,
            owner_id=workspace.owner_id,
            is_active=workspace.is_active,
            member_count=count,
            created_at=workspace.created_at,
            updated_at=workspace.updated_at,
        ))
    return items


@router.get("/{workspace_id}", response_model=WorkspaceRead)
@limiter.limit("30/minute")
async def get_workspace(
    request: Request,
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get workspace details."""
    workspace = await WorkspaceService.get_workspace(workspace_id, current_user.id, session)
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    count = await WorkspaceService.get_member_count(workspace.id, session)
    return WorkspaceRead(
        id=workspace.id, name=workspace.name, description=workspace.description,
        owner_id=workspace.owner_id, is_active=workspace.is_active, member_count=count,
        created_at=workspace.created_at, updated_at=workspace.updated_at,
    )


@router.put("/{workspace_id}", response_model=WorkspaceRead)
@limiter.limit("10/minute")
async def update_workspace(
    request: Request,
    workspace_id: UUID,
    body: WorkspaceUpdate,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """Update workspace (owner only)."""
    workspace = await WorkspaceService.update_workspace(
        workspace_id, current_user.id, body.model_dump(exclude_unset=True), session
    )
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found or access denied")
    count = await WorkspaceService.get_member_count(workspace.id, session)
    return WorkspaceRead(
        id=workspace.id, name=workspace.name, description=workspace.description,
        owner_id=workspace.owner_id, is_active=workspace.is_active, member_count=count,
        created_at=workspace.created_at, updated_at=workspace.updated_at,
    )


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("5/minute")
async def delete_workspace(
    request: Request,
    workspace_id: UUID,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """Delete workspace (owner only)."""
    deleted = await WorkspaceService.delete_workspace(workspace_id, current_user.id, session)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found or access denied")
    return None


@router.post("/{workspace_id}/invite", response_model=MemberRead)
@limiter.limit("10/minute")
async def invite_member(
    request: Request,
    workspace_id: UUID,
    body: InviteRequest,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """Invite a user to the workspace by email (owner only)."""
    workspace = await WorkspaceService.get_workspace(workspace_id, current_user.id, session)
    if not workspace or workspace.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner can invite members")

    from app.auth import get_user_by_email
    invitee = await get_user_by_email(session, body.email)
    if not invitee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    try:
        member = await WorkspaceService.invite_member(
            workspace_id, current_user.id, invitee.id, body.role, session
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return MemberRead(
        id=member.id, user_id=member.user_id, user_email=body.email,
        role=member.role.value if hasattr(member.role, 'value') else member.role,
        joined_at=member.joined_at,
    )


@router.get("/{workspace_id}/members", response_model=list[MemberRead])
@limiter.limit("20/minute")
async def list_members(
    request: Request,
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List workspace members."""
    workspace = await WorkspaceService.get_workspace(workspace_id, current_user.id, session)
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    members = await WorkspaceService.list_members(workspace_id, session)
    return [MemberRead(**m) for m in members]


@router.delete("/{workspace_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def remove_member(
    request: Request,
    workspace_id: UUID,
    user_id: UUID,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """Remove a member from workspace (owner only)."""
    removed = await WorkspaceService.remove_member(workspace_id, user_id, current_user.id, session)
    if not removed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove member")
    return None


@router.post("/{workspace_id}/share", response_model=SharedItemRead)
@limiter.limit("10/minute")
async def share_item(
    request: Request,
    workspace_id: UUID,
    body: ShareItemRequest,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """Share a transcription, pipeline, or document with the workspace."""
    workspace = await WorkspaceService.get_workspace(workspace_id, current_user.id, session)
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    shared = await WorkspaceService.share_item(
        workspace_id, current_user.id, body.item_type, body.item_id, session
    )
    return shared


@router.get("/{workspace_id}/items", response_model=list[SharedItemRead])
@limiter.limit("20/minute")
async def list_shared_items(
    request: Request,
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List shared items in a workspace."""
    workspace = await WorkspaceService.get_workspace(workspace_id, current_user.id, session)
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    return await WorkspaceService.list_shared_items(workspace_id, session)


@router.post("/items/{item_id}/comments", response_model=CommentRead)
@limiter.limit("20/minute")
async def add_comment(
    request: Request,
    item_id: UUID,
    body: CommentCreate,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """Add a comment to a shared item."""
    from app.models.workspace import SharedItem

    shared_item = await session.get(SharedItem, item_id)
    if not shared_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shared item not found")

    is_member = await WorkspaceService.is_member(
        shared_item.workspace_id, current_user.id, session
    )
    if not is_member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    comment = await WorkspaceService.add_comment(
        item_id, current_user.id, body.content, session
    )
    return comment


@router.get("/items/{shared_item_id}/detail")
@limiter.limit("20/minute")
async def get_shared_item_detail(
    request: Request,
    shared_item_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get the actual content of a shared item."""
    from app.models.workspace import SharedItem

    shared_item = await session.get(SharedItem, shared_item_id)
    if not shared_item:
        raise HTTPException(status_code=404, detail="Shared item not found")

    # Verify user is member of the workspace
    is_member = await WorkspaceService.is_member(
        shared_item.workspace_id, current_user.id, session
    )
    if not is_member:
        raise HTTPException(status_code=403, detail="Access denied")

    detail = await WorkspaceService.get_shared_item_detail(
        item_type=shared_item.item_type,
        item_id=shared_item.item_id,
        session=session,
    )

    if not detail:
        raise HTTPException(status_code=404, detail="Item content not found")

    return detail


@router.get("/items/{item_id}/comments", response_model=list[CommentRead])
@limiter.limit("30/minute")
async def list_comments(
    request: Request,
    item_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List comments on a shared item."""
    from app.models.workspace import SharedItem

    shared_item = await session.get(SharedItem, item_id)
    if not shared_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shared item not found")

    is_member = await WorkspaceService.is_member(
        shared_item.workspace_id, current_user.id, session
    )
    if not is_member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return await WorkspaceService.list_comments(item_id, session)
