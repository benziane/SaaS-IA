"""Add tenants table and tenant_id to users for multi-tenant RLS

Revision ID: 013bbb123ccc
Revises: 012aaa789bbb
Create Date: 2026-03-25

This migration:
1. Creates the 'tenants' table for multi-tenant organization management
2. Adds 'tenant_id' column (nullable FK) to 'users' table
3. Creates indexes for tenant lookups
4. Documents RLS policies as SQL comments (require superuser to apply)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '013bbb123ccc'
down_revision: Union[str, None] = '012aaa789bbb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---------------------------------------------------------------
    # 1. Create tenants table
    # ---------------------------------------------------------------
    op.create_table(
        'tenants',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('plan', sa.String(length=50), nullable=False, server_default='free'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('config_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('branding_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('max_users', sa.Integer(), nullable=False, server_default=sa.text('5')),
        sa.Column('max_storage_mb', sa.Integer(), nullable=False, server_default=sa.text('1000')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )

    # Unique index on slug for fast tenant lookup by subdomain/slug
    op.create_index('ix_tenants_slug', 'tenants', ['slug'], unique=True)

    # Index on plan for filtering tenants by plan
    op.create_index('ix_tenants_plan', 'tenants', ['plan'])

    # Index on is_active for filtering active tenants
    op.create_index('ix_tenants_is_active', 'tenants', ['is_active'])

    # ---------------------------------------------------------------
    # 2. Add tenant_id to users table (nullable for migration safety)
    # ---------------------------------------------------------------
    op.add_column(
        'users',
        sa.Column('tenant_id', sa.Uuid(), nullable=True),
    )

    # Foreign key from users.tenant_id -> tenants.id
    op.create_foreign_key(
        'fk_users_tenant_id',
        'users',
        'tenants',
        ['tenant_id'],
        ['id'],
        ondelete='SET NULL',
    )

    # Index on users.tenant_id for fast tenant-scoped queries
    op.create_index('ix_users_tenant_id', 'users', ['tenant_id'])

    # ---------------------------------------------------------------
    # 3. RLS Policies (to be applied by DBA with superuser privileges)
    # ---------------------------------------------------------------
    # These are documented as comments because:
    # - RLS requires superuser or table owner privileges
    # - The Alembic migration user may not have these privileges
    # - DBA should review and apply these policies manually
    #
    # -- Enable RLS on users table:
    # ALTER TABLE users ENABLE ROW LEVEL SECURITY;
    #
    # -- Policy: users can only see rows matching their tenant
    # CREATE POLICY tenant_isolation_users ON users
    #   USING (tenant_id = current_setting('app.tenant_id')::uuid);
    #
    # -- Policy: users can only insert rows for their tenant
    # CREATE POLICY tenant_insert_users ON users
    #   FOR INSERT
    #   WITH CHECK (tenant_id = current_setting('app.tenant_id')::uuid);
    #
    # -- Policy: users can only update rows for their tenant
    # CREATE POLICY tenant_update_users ON users
    #   FOR UPDATE
    #   USING (tenant_id = current_setting('app.tenant_id')::uuid)
    #   WITH CHECK (tenant_id = current_setting('app.tenant_id')::uuid);
    #
    # -- Policy: users can only delete rows for their tenant
    # CREATE POLICY tenant_delete_users ON users
    #   FOR DELETE
    #   USING (tenant_id = current_setting('app.tenant_id')::uuid);
    #
    # -- Bypass RLS for admin/service role:
    # ALTER TABLE users FORCE ROW LEVEL SECURITY;
    # -- (The application service user should use SET LOCAL app.tenant_id
    # --  in each transaction. Admin queries can use SET ROLE to bypass.)
    #
    # -- Pattern for other tables (transcriptions, conversations, etc.):
    # -- 1. Add tenant_id UUID column with FK to tenants(id)
    # -- 2. ALTER TABLE <table> ENABLE ROW LEVEL SECURITY;
    # -- 3. CREATE POLICY tenant_isolation_<table> ON <table>
    # --      USING (tenant_id = current_setting('app.tenant_id')::uuid);
    #
    # -- PostgreSQL session variable setup (done by TenantMiddleware):
    # -- SET LOCAL app.tenant_id = '<uuid>';
    # -- This is set per-transaction and automatically cleared on commit/rollback.
    #
    # -- To verify RLS is working:
    # -- SET app.tenant_id = '<tenant-uuid>';
    # -- SELECT * FROM users;  -- Should only show rows for that tenant
    # -- RESET app.tenant_id;


def downgrade() -> None:
    # Drop FK and index on users.tenant_id
    op.drop_constraint('fk_users_tenant_id', 'users', type_='foreignkey')
    op.drop_index('ix_users_tenant_id', table_name='users')
    op.drop_column('users', 'tenant_id')

    # Drop tenants table and its indexes
    op.drop_index('ix_tenants_is_active', table_name='tenants')
    op.drop_index('ix_tenants_plan', table_name='tenants')
    op.drop_index('ix_tenants_slug', table_name='tenants')
    op.drop_table('tenants')
