"""Add P1 modules: multi_agent_crew, voice_clone, realtime_ai, security_guardian

Revision ID: p1_modules_001
Revises: cs_wf_001
Create Date: 2026-03-23

Adds:
- crews, crew_runs: Multi-agent collaborative teams
- voice_profiles, speech_syntheses: Voice cloning and TTS
- realtime_sessions: Live AI voice/vision sessions
- security_scans, audit_logs, guardrail_rules: Security and governance
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'p1_modules_001'
down_revision: Union[str, None] = 'cs_wf_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---- Multi-Agent Crews ----
    op.create_table(
        'crews',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.String(1000), nullable=True),
        sa.Column('goal', sa.String(2000), nullable=True),
        sa.Column('agents_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('process_type', sa.String(20), nullable=False, server_default='sequential'),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('is_template', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('template_category', sa.String(100), nullable=True),
        sa.Column('run_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_crews_user_id', 'crews', ['user_id'])

    op.create_table(
        'crew_runs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('crew_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('instruction', sa.String(5000), nullable=False, server_default=''),
        sa.Column('current_agent', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_agents', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('messages_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('final_output', sa.Text(), nullable=True),
        sa.Column('error', sa.String(2000), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('tokens_used', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['crew_id'], ['crews.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_crew_runs_crew_id', 'crew_runs', ['crew_id'])
    op.create_index('ix_crew_runs_user_id', 'crew_runs', ['user_id'])

    # ---- Voice Clone ----
    op.create_table(
        'voice_profiles',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('provider', sa.String(50), nullable=False, server_default='elevenlabs'),
        sa.Column('external_voice_id', sa.String(200), nullable=True),
        sa.Column('language', sa.String(10), nullable=False, server_default='auto'),
        sa.Column('sample_duration_s', sa.Float(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='processing'),
        sa.Column('settings_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_voice_profiles_user_id', 'voice_profiles', ['user_id'])

    op.create_table(
        'speech_syntheses',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('voice_id', sa.Uuid(), nullable=True),
        sa.Column('text', sa.Text(), nullable=False, server_default=''),
        sa.Column('source_type', sa.String(50), nullable=False, server_default='text'),
        sa.Column('source_id', sa.String(200), nullable=True),
        sa.Column('provider', sa.String(50), nullable=False, server_default='elevenlabs'),
        sa.Column('output_format', sa.String(10), nullable=False, server_default='mp3'),
        sa.Column('audio_url', sa.String(1000), nullable=True),
        sa.Column('duration_s', sa.Float(), nullable=True),
        sa.Column('language', sa.String(10), nullable=False, server_default='auto'),
        sa.Column('target_language', sa.String(10), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('error', sa.String(1000), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['voice_id'], ['voice_profiles.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_speech_syntheses_user_id', 'speech_syntheses', ['user_id'])

    # ---- Realtime AI ----
    op.create_table(
        'realtime_sessions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('title', sa.String(300), nullable=True),
        sa.Column('mode', sa.String(20), nullable=False, server_default='voice'),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('provider', sa.String(50), nullable=False, server_default='gemini'),
        sa.Column('model', sa.String(100), nullable=True),
        sa.Column('system_prompt', sa.String(5000), nullable=True),
        sa.Column('knowledge_base_id', sa.String(200), nullable=True),
        sa.Column('config_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('messages_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('transcript', sa.Text(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('total_turns', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('audio_duration_s', sa.Float(), nullable=False, server_default='0'),
        sa.Column('tokens_used', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('started_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_realtime_sessions_user_id', 'realtime_sessions', ['user_id'])

    # ---- Security Guardian ----
    op.create_table(
        'security_scans',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('scan_type', sa.String(50), nullable=False),
        sa.Column('target_type', sa.String(50), nullable=False),
        sa.Column('target_id', sa.String(200), nullable=True),
        sa.Column('content_preview', sa.String(500), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('findings_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('findings_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('severity', sa.String(20), nullable=True),
        sa.Column('auto_redacted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('redacted_text', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_security_scans_user_id', 'security_scans', ['user_id'])

    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('module', sa.String(50), nullable=False),
        sa.Column('provider', sa.String(50), nullable=True),
        sa.Column('model', sa.String(100), nullable=True),
        sa.Column('input_preview', sa.String(500), nullable=True),
        sa.Column('output_preview', sa.String(500), nullable=True),
        sa.Column('tokens_used', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('cost_usd', sa.Float(), nullable=False, server_default='0'),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('user_agent', sa.String(300), nullable=True),
        sa.Column('metadata_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('risk_level', sa.String(20), nullable=True),
        sa.Column('flagged', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('ix_audit_logs_module', 'audit_logs', ['module'])

    op.create_table(
        'guardrail_rules',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.String(1000), nullable=True),
        sa.Column('rule_type', sa.String(50), nullable=False),
        sa.Column('config_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('action', sa.String(20), nullable=False, server_default='warn'),
        sa.Column('severity', sa.String(20), nullable=False, server_default='medium'),
        sa.Column('triggers_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_guardrail_rules_user_id', 'guardrail_rules', ['user_id'])


def downgrade() -> None:
    op.drop_table('guardrail_rules')
    op.drop_table('audit_logs')
    op.drop_table('security_scans')
    op.drop_table('realtime_sessions')
    op.drop_table('speech_syntheses')
    op.drop_table('voice_profiles')
    op.drop_table('crew_runs')
    op.drop_table('crews')
