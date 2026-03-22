"""Add Stripe fields to billing tables

Revision ID: stripe_001
Revises: sprint5_002
Create Date: 2026-03-22
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'stripe_001'
down_revision: Union[str, None] = 'sprint5_002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('plans', sa.Column('stripe_price_id', sa.String(length=100), nullable=True))
    op.add_column('user_quotas', sa.Column('stripe_customer_id', sa.String(length=100), nullable=True))
    op.add_column('user_quotas', sa.Column('stripe_subscription_id', sa.String(length=100), nullable=True))


def downgrade() -> None:
    op.drop_column('user_quotas', 'stripe_subscription_id')
    op.drop_column('user_quotas', 'stripe_customer_id')
    op.drop_column('plans', 'stripe_price_id')
