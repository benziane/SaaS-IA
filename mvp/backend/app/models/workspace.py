"""
Workspace and collaboration models.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class WorkspaceRole(str, Enum):
    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"


class Workspace(SQLModel, table=True):
    """A shared workspace for collaboration."""
    __tablename__ = "workspaces"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    owner_id: UUID = Field(foreign_key="users.id", index=True)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class WorkspaceMember(SQLModel, table=True):
    """Membership in a workspace."""
    __tablename__ = "workspace_members"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    workspace_id: UUID = Field(foreign_key="workspaces.id", index=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    role: WorkspaceRole = Field(default=WorkspaceRole.VIEWER)
    joined_at: datetime = Field(default_factory=datetime.utcnow)


class SharedItem(SQLModel, table=True):
    """An item shared within a workspace (transcription, pipeline, etc.)."""
    __tablename__ = "shared_items"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    workspace_id: UUID = Field(foreign_key="workspaces.id", index=True)
    item_type: str = Field(max_length=50)
    item_id: UUID
    shared_by: UUID = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Comment(SQLModel, table=True):
    """A comment on a shared item."""
    __tablename__ = "comments"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    shared_item_id: UUID = Field(foreign_key="shared_items.id", index=True)
    user_id: UUID = Field(foreign_key="users.id")
    content: str = Field(max_length=5000)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
