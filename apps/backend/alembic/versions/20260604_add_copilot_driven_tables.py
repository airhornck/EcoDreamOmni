"""add_copilot_driven_tables

Revision ID: 20260604addc
Revises: g2h3i4j5k6l7
Create Date: 2026-06-04 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20260604addc'
down_revision: Union[str, Sequence[str], None] = 'g2h3i4j5k6l7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema — Copilot-driven tables v4.0 Step 2."""

    # 1. copilot_context_sessions
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

    # 2. ai_cover_generation_jobs
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

    # 3. copilot_action_logs
    op.create_table(
        'copilot_action_logs',
        sa.Column('id', sa.String(32), primary_key=True, comment='日志ID'),
        sa.Column('user_id', sa.String(32), nullable=False, comment='用户ID'),
        sa.Column('session_id', sa.String(64), nullable=False, comment='会话ID'),
        sa.Column('context_id', sa.String(32), nullable=True, comment='上下文ID'),
        sa.Column('card_id', sa.String(64), nullable=True, comment='Action Card ID'),
        sa.Column('action_id', sa.String(64), nullable=True, comment='执行的 Action ID'),
        sa.Column('page', sa.String(64), nullable=True, comment='所在页面'),
        sa.Column('status', sa.String(20), nullable=True, comment='success | failed | cancelled'),
        sa.Column('request_payload', postgresql.JSONB(), server_default='{}', comment='请求体'),
        sa.Column('response_payload', postgresql.JSONB(), server_default='{}', comment='响应体'),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True, comment='执行耗时(ms)'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        comment='Copilot 操作审计日志 — 保留 90 天',
    )
    op.create_index('idx_copilot_logs_user', 'copilot_action_logs', ['user_id', 'created_at'])
    op.create_index('idx_copilot_logs_session', 'copilot_action_logs', ['session_id'])

    # 4. Extend review_conclusions with copilot fields
    op.add_column(
        'review_conclusions',
        sa.Column('copilot_recommended_action', sa.String(20), nullable=True, comment='Copilot 推荐操作'),
    )
    op.add_column(
        'review_conclusions',
        sa.Column('copilot_confidence', sa.DECIMAL(3, 2), nullable=True, comment='Copilot 置信度 0.00-1.00'),
    )
    op.add_column(
        'review_conclusions',
        sa.Column('copilot_reasoning', sa.Text(), nullable=True, comment='Copilot 推理过程'),
    )
    op.add_column(
        'review_conclusions',
        sa.Column('copilot_suggested_improvements', postgresql.JSONB(), nullable=True, comment='Copilot 建议改进项'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    # 4. Remove copilot columns from review_conclusions
    op.drop_column('review_conclusions', 'copilot_suggested_improvements')
    op.drop_column('review_conclusions', 'copilot_reasoning')
    op.drop_column('review_conclusions', 'copilot_confidence')
    op.drop_column('review_conclusions', 'copilot_recommended_action')

    # 3. Drop copilot_action_logs
    op.drop_index('idx_copilot_logs_session', table_name='copilot_action_logs')
    op.drop_index('idx_copilot_logs_user', table_name='copilot_action_logs')
    op.drop_table('copilot_action_logs')

    # 2. Drop ai_cover_generation_jobs
    op.drop_index('idx_cover_jobs_task', table_name='ai_cover_generation_jobs')
    op.drop_index('idx_cover_jobs_user_created', table_name='ai_cover_generation_jobs')
    op.drop_table('ai_cover_generation_jobs')

    # 1. Drop copilot_context_sessions
    op.drop_constraint('uq_copilot_session_id', table_name='copilot_context_sessions')
    op.drop_index('ix_copilot_sessions_expires', table_name='copilot_context_sessions')
    op.drop_index('ix_copilot_sessions_user', table_name='copilot_context_sessions')
    op.drop_table('copilot_context_sessions')
