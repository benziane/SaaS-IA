"""Add fine_tuning tables

Revision ID: p3_fine_tuning_001
Revises: p2_modules_001
Create Date: 2026-03-23
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'p3_fine_tuning_001'
down_revision: Union[str, None] = 'p2_modules_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('training_datasets',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.String(1000), nullable=True),
        sa.Column('dataset_type', sa.String(50), nullable=False, server_default='instruction'),
        sa.Column('source_type', sa.String(50), nullable=False, server_default='manual'),
        sa.Column('samples_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('sample_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('validation_split', sa.Float(), nullable=False, server_default='0.1'),
        sa.Column('quality_score', sa.Float(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_training_datasets_user_id', 'training_datasets', ['user_id'])

    op.create_table('fine_tune_jobs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('dataset_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('base_model', sa.String(100), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False, server_default='together'),
        sa.Column('external_job_id', sa.String(200), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('hyperparams_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('metrics_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('result_model_id', sa.String(300), nullable=True),
        sa.Column('error', sa.String(2000), nullable=True),
        sa.Column('epochs_completed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_epochs', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('estimated_cost_usd', sa.Float(), nullable=False, server_default='0'),
        sa.Column('actual_cost_usd', sa.Float(), nullable=False, server_default='0'),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['dataset_id'], ['training_datasets.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_fine_tune_jobs_user_id', 'fine_tune_jobs', ['user_id'])
    op.create_index('ix_fine_tune_jobs_dataset_id', 'fine_tune_jobs', ['dataset_id'])

    op.create_table('model_evaluations',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('job_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('eval_type', sa.String(50), nullable=False),
        sa.Column('test_prompts_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('metrics_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('base_model_score', sa.Float(), nullable=True),
        sa.Column('tuned_model_score', sa.Float(), nullable=True),
        sa.Column('improvement_pct', sa.Float(), nullable=True),
        sa.Column('summary', sa.String(2000), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['job_id'], ['fine_tune_jobs.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_model_evaluations_job_id', 'model_evaluations', ['job_id'])


def downgrade() -> None:
    op.drop_table('model_evaluations')
    op.drop_table('fine_tune_jobs')
    op.drop_table('training_datasets')
