"""Add unique constraints to prevent duplicate records

Revision ID: unique_constraints_016
Revises: consolidate_015
Create Date: 2026-03-26

Adds UniqueConstraint on:
- workspace_members (workspace_id, user_id)
- marketplace_installs (user_id, listing_id)
- shared_items (workspace_id, item_type, item_id)
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'unique_constraints_016'
down_revision: Union[str, None] = 'consolidate_015'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -- workspace_members: prevent same user added twice to a workspace ----
    with op.batch_alter_table('workspace_members') as batch_op:
        batch_op.create_unique_constraint(
            'uq_workspace_members_workspace_user',
            ['workspace_id', 'user_id'],
        )

    # -- marketplace_installs: prevent duplicate installs -------------------
    with op.batch_alter_table('marketplace_installs') as batch_op:
        batch_op.create_unique_constraint(
            'uq_marketplace_installs_user_listing',
            ['user_id', 'listing_id'],
        )

    # -- shared_items: prevent same item shared twice in a workspace --------
    with op.batch_alter_table('shared_items') as batch_op:
        batch_op.create_unique_constraint(
            'uq_shared_items_workspace_type_item',
            ['workspace_id', 'item_type', 'item_id'],
        )


def downgrade() -> None:
    with op.batch_alter_table('shared_items') as batch_op:
        batch_op.drop_constraint('uq_shared_items_workspace_type_item', type_='unique')

    with op.batch_alter_table('marketplace_installs') as batch_op:
        batch_op.drop_constraint('uq_marketplace_installs_user_listing', type_='unique')

    with op.batch_alter_table('workspace_members') as batch_op:
        batch_op.drop_constraint('uq_workspace_members_workspace_user', type_='unique')
