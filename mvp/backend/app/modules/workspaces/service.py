"""
Workspace service - Business logic for collaboration.
"""

from datetime import UTC, datetime
from typing import Optional
from uuid import UUID

import structlog
from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.workspace import (
    Comment,
    SharedItem,
    Workspace,
    WorkspaceMember,
    WorkspaceRole,
)

logger = structlog.get_logger()


class WorkspaceService:
    """Service for workspace collaboration."""

    @staticmethod
    async def create_workspace(
        owner_id: UUID,
        name: str,
        description: Optional[str],
        session: AsyncSession,
    ) -> Workspace:
        workspace = Workspace(
            name=name,
            description=description,
            owner_id=owner_id,
        )
        session.add(workspace)
        await session.flush()

        member = WorkspaceMember(
            workspace_id=workspace.id,
            user_id=owner_id,
            role=WorkspaceRole.OWNER,
        )
        session.add(member)
        await session.commit()
        await session.refresh(workspace)

        logger.info("workspace_created", workspace_id=str(workspace.id), owner=str(owner_id))
        return workspace

    @staticmethod
    async def list_workspaces(
        user_id: UUID,
        session: AsyncSession,
    ) -> list[tuple]:
        result = await session.execute(
            select(Workspace, WorkspaceMember.role)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
            .where(WorkspaceMember.user_id == user_id, Workspace.is_active == True)
            .order_by(Workspace.updated_at.desc())
        )
        return list(result.all())

    @staticmethod
    async def get_workspace(
        workspace_id: UUID,
        user_id: UUID,
        session: AsyncSession,
    ) -> Optional[Workspace]:
        result = await session.execute(
            select(Workspace)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
            .where(
                Workspace.id == workspace_id,
                WorkspaceMember.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_workspace(
        workspace_id: UUID,
        user_id: UUID,
        updates: dict,
        session: AsyncSession,
    ) -> Optional[Workspace]:
        workspace = await WorkspaceService.get_workspace(workspace_id, user_id, session)
        if not workspace or workspace.owner_id != user_id:
            return None

        if "name" in updates and updates["name"]:
            workspace.name = updates["name"]
        if "description" in updates:
            workspace.description = updates["description"]
        workspace.updated_at = datetime.now(UTC)
        session.add(workspace)
        await session.commit()
        await session.refresh(workspace)
        return workspace

    @staticmethod
    async def delete_workspace(
        workspace_id: UUID,
        user_id: UUID,
        session: AsyncSession,
    ) -> bool:
        workspace = await WorkspaceService.get_workspace(workspace_id, user_id, session)
        if not workspace or workspace.owner_id != user_id:
            return False

        for model in [Comment, SharedItem, WorkspaceMember]:
            if model == Comment:
                items = await session.execute(
                    select(SharedItem).where(SharedItem.workspace_id == workspace_id)
                )
                for item in items.scalars().all():
                    comments = await session.execute(
                        select(Comment).where(Comment.shared_item_id == item.id)
                    )
                    for c in comments.scalars().all():
                        await session.delete(c)
                items2 = await session.execute(
                    select(SharedItem).where(SharedItem.workspace_id == workspace_id)
                )
                for item in items2.scalars().all():
                    await session.delete(item)
            elif model == WorkspaceMember:
                members = await session.execute(
                    select(WorkspaceMember).where(WorkspaceMember.workspace_id == workspace_id)
                )
                for m in members.scalars().all():
                    await session.delete(m)

        await session.delete(workspace)
        await session.commit()
        logger.info("workspace_deleted", workspace_id=str(workspace_id))
        return True

    @staticmethod
    async def invite_member(
        workspace_id: UUID,
        inviter_id: UUID,
        invitee_user_id: UUID,
        role: str,
        session: AsyncSession,
    ) -> WorkspaceMember:
        existing = await session.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == invitee_user_id,
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("User is already a member")

        member = WorkspaceMember(
            workspace_id=workspace_id,
            user_id=invitee_user_id,
            role=WorkspaceRole(role) if role in [r.value for r in WorkspaceRole] else WorkspaceRole.VIEWER,
        )
        session.add(member)
        await session.commit()
        await session.refresh(member)
        logger.info("workspace_member_invited", workspace_id=str(workspace_id), user_id=str(invitee_user_id))
        return member

    @staticmethod
    async def list_members(
        workspace_id: UUID,
        session: AsyncSession,
    ) -> list[dict]:
        from app.models.user import User
        result = await session.execute(
            select(WorkspaceMember, User.email)
            .join(User, User.id == WorkspaceMember.user_id)
            .where(WorkspaceMember.workspace_id == workspace_id)
        )
        members = []
        for member, email in result.all():
            members.append({
                "id": member.id,
                "user_id": member.user_id,
                "user_email": email,
                "role": member.role.value if hasattr(member.role, 'value') else member.role,
                "joined_at": member.joined_at,
            })
        return members

    @staticmethod
    async def remove_member(
        workspace_id: UUID,
        member_user_id: UUID,
        remover_id: UUID,
        session: AsyncSession,
    ) -> bool:
        workspace = await session.get(Workspace, workspace_id)
        if not workspace or workspace.owner_id != remover_id:
            return False
        if member_user_id == remover_id:
            return False

        result = await session.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == member_user_id,
            )
        )
        member = result.scalar_one_or_none()
        if not member:
            return False

        await session.delete(member)
        await session.commit()
        return True

    @staticmethod
    async def share_item(
        workspace_id: UUID,
        user_id: UUID,
        item_type: str,
        item_id: UUID,
        session: AsyncSession,
    ) -> SharedItem:
        shared = SharedItem(
            workspace_id=workspace_id,
            item_type=item_type,
            item_id=item_id,
            shared_by=user_id,
        )
        session.add(shared)
        await session.commit()
        await session.refresh(shared)
        return shared

    @staticmethod
    async def list_shared_items(
        workspace_id: UUID,
        session: AsyncSession,
    ) -> list[SharedItem]:
        result = await session.execute(
            select(SharedItem)
            .where(SharedItem.workspace_id == workspace_id)
            .order_by(SharedItem.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def add_comment(
        shared_item_id: UUID,
        user_id: UUID,
        content: str,
        session: AsyncSession,
    ) -> Comment:
        comment = Comment(
            shared_item_id=shared_item_id,
            user_id=user_id,
            content=content,
        )
        session.add(comment)
        await session.commit()
        await session.refresh(comment)
        return comment

    @staticmethod
    async def list_comments(
        shared_item_id: UUID,
        session: AsyncSession,
    ) -> list[Comment]:
        result = await session.execute(
            select(Comment)
            .where(Comment.shared_item_id == shared_item_id)
            .order_by(Comment.created_at.asc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_member_count(workspace_id: UUID, session: AsyncSession) -> int:
        result = await session.execute(
            select(func.count()).select_from(WorkspaceMember).where(
                WorkspaceMember.workspace_id == workspace_id
            )
        )
        return result.scalar_one()

    @staticmethod
    async def is_member(workspace_id: UUID, user_id: UUID, session: AsyncSession) -> bool:
        """Check if a user is a member of a workspace."""
        result = await session.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == user_id,
            )
        )
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def get_shared_item_detail(
        item_type: str,
        item_id: UUID,
        session: AsyncSession,
    ) -> Optional[dict]:
        """Fetch the actual content of a shared item."""
        try:
            if item_type == "transcription":
                from app.models.transcription import Transcription
                item = await session.get(Transcription, item_id)
                if item:
                    return {
                        "type": "transcription",
                        "title": item.original_filename or item.video_url or "Transcription",
                        "content": item.text,
                        "status": item.status.value if hasattr(item.status, 'value') else str(item.status),
                        "created_at": str(item.created_at),
                    }

            elif item_type == "pipeline":
                from app.models.pipeline import Pipeline
                item = await session.get(Pipeline, item_id)
                if item:
                    return {
                        "type": "pipeline",
                        "title": item.name,
                        "content": item.description,
                        "status": item.status.value if hasattr(item.status, 'value') else str(item.status),
                        "created_at": str(item.created_at),
                    }

            elif item_type == "document":
                from app.models.knowledge import Document
                item = await session.get(Document, item_id)
                if item:
                    return {
                        "type": "document",
                        "title": item.filename,
                        "content": f"{item.total_chunks} chunks indexed",
                        "status": item.status,
                        "created_at": str(item.created_at),
                    }

            elif item_type == "conversation":
                from app.models.conversation import Conversation
                item = await session.get(Conversation, item_id)
                if item:
                    return {
                        "type": "conversation",
                        "title": item.title or "Conversation",
                        "content": "",
                        "created_at": str(item.created_at),
                    }

        except Exception:
            pass

        return None
