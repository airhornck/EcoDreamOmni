"""add_missing_copilot_context_and_cover_tables

Revision ID: b6b03e728f31
Revises: i4j5k6l7m8n9
Create Date: 2026-06-14 20:22:10.463842

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b6b03e728f31'
down_revision: Union[str, Sequence[str], None] = 'i4j5k6l7m8n9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(name: str) -> bool:
    result = op.get_bind().execute(
        sa.text("SELECT to_regclass('public." + name + "') IS NOT NULL")
    )
    return bool(result.scalar())


def upgrade() -> None:
    """Upgrade schema — create missing Copilot tables if they do not exist."""

    if not _table_exists('copilot_context_sessions'):
        op.create_table(
            'copilot_context_sessions',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
            sa.Column('user_id', sa.String(64), nullable=False, index=True, comment='用户ID'),
            sa.Column('session_id', sa.String(64), nullable=False, unique=True, comment='客户端会话ID'),
            sa.Column('page', sa.String(64), nullable=False, comment='当前页面路由'),
            sa.Column('selected_items', postgresql.JSONB(), server_default='[]', comment='选中项ID列表'),
            sa.Column('selected_content', postgresql.JSONB(), server_default='{}', comment='选中内容摘要'),
            sa.Column('workspace_state', postgresql.JSONB(), server_default='{}', comment='工作区状态'),
            sa.Column('suggested_cards', postgresql.JSONB(), server_default='[]', comment='后端预计算的卡片建议'),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
            sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW() + INTERVAL '30 minutes'"), comment='过期时间，默认 NOW() + 30min'),
            comment='Copilot 上下文会话 — TTL 30min',
        )
        op.create_index('ix_copilot_sessions_user', 'copilot_context_sessions', ['user_id', 'updated_at'])
        op.create_index('ix_copilot_sessions_expires', 'copilot_context_sessions', ['expires_at'])
        op.create_unique_constraint('uq_copilot_session_id', 'copilot_context_sessions', ['session_id'])

    if not _table_exists('ai_cover_generation_jobs'):
        op.create_table(
            'ai_cover_generation_jobs',
            sa.Column('id', sa.String(32), primary_key=True, comment='任务ID，如 cover_gen_xyz789'),
            sa.Column('task_id', sa.String(32), nullable=False, comment='关联 tasks.id'),
            sa.Column('user_id', sa.String(32), nullable=False, comment='用户ID'),
            sa.Column('prompt', sa.Text(), nullable=True, comment='用户输入的提示词'),
            sa.Column('auto_prompt', sa.Boolean(), nullable=False, server_default='false', comment='是否自动根据内容生成提示词'),
            sa.Column('style_preset', sa.String(32), nullable=True, comment='风格预设'),
            sa.Column('count', sa.Integer(), nullable=False, server_default='2', comment='生成数量'),
            sa.Column('ratio', sa.String(10), nullable=False, server_default='3:4', comment='裁剪比例'),
            sa.Column('status', sa.String(20), nullable=False, server_default='queued', comment='queued | generating | completed | failed'),
            sa.Column('results', postgresql.JSONB(), server_default='[]', comment='生成结果 [{url, thumbnail_url, ratio, seed}]'),
            sa.Column('error_message', sa.Text(), nullable=True, comment='失败原因'),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
            sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True, comment='完成时间'),
            comment='AI 封面生成异步任务',
        )
        op.create_index('idx_cover_jobs_user_created', 'ai_cover_generation_jobs', ['user_id', 'created_at'])
        op.create_index('idx_cover_jobs_task', 'ai_cover_generation_jobs', ['task_id'])


def downgrade() -> None:
    """Downgrade schema."""
    if _table_exists('ai_cover_generation_jobs'):
        op.drop_index('idx_cover_jobs_task', table_name='ai_cover_generation_jobs')
        op.drop_index('idx_cover_jobs_user_created', table_name='ai_cover_generation_jobs')
        op.drop_table('ai_cover_generation_jobs')

    if _table_exists('copilot_context_sessions'):
        op.drop_constraint('uq_copilot_session_id', table_name='copilot_context_sessions')
        op.drop_index('ix_copilot_sessions_expires', table_name='copilot_context_sessions')
        op.drop_index('ix_copilot_sessions_user', table_name='copilot_context_sessions')
        op.drop_table('copilot_context_sessions')
