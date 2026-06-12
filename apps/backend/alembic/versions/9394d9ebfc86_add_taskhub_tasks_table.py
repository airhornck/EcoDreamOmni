"""add_taskhub_tasks_table

Revision ID: 9394d9ebfc86
Revises: b0f15b5bd21a
Create Date: 2026-05-25 10:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '9394d9ebfc86'
down_revision: Union[str, Sequence[str], None] = 'b0f15b5bd21a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema — TaskHub 任务真源表."""

    op.create_table(
        'tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False, comment='任务名称'),
        sa.Column('workflow_template_id', sa.String(64), nullable=False, comment='关联工作流模板ID'),
        sa.Column('workflow_version', sa.Integer(), nullable=False, server_default='1', comment='工作流版本号'),
        sa.Column('account_id', sa.String(64), nullable=False, index=True, comment='关联账号池ID'),
        sa.Column('persona_id', sa.String(64), nullable=False, index=True, comment='关联PersonaID'),
        sa.Column('persona_story_id', sa.String(64), nullable=True, index=True, comment='关联PersonaStory剧本ID'),
        sa.Column('node_id', sa.String(64), nullable=True, comment='关联剧本节点ID'),
        sa.Column('content_series_id', sa.String(64), nullable=True, comment='关联内容系列ID'),
        sa.Column('platform', sa.String(16), nullable=False, server_default='xhs', comment='发布平台: xhs | douyin | wechat_channels'),
        sa.Column('status', sa.String(32), nullable=False, server_default='draft', comment='draft | configuring | queued | running | paused | human_wait | approved_waiting_publish | completed | failed | cancelled'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='50', comment='优先级 0-100'),
        sa.Column('current_node_index', sa.Integer(), nullable=False, server_default='0', comment='当前执行节点索引'),
        sa.Column('prompt_variables', postgresql.JSONB(), server_default='{}', comment='工作流提示变量字典'),
        sa.Column('parent_task_id', sa.String(64), nullable=True, comment='父任务ID（批量任务）'),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True, comment='定时执行时间'),
        sa.Column('created_by', sa.String(64), nullable=False, server_default='', comment='创建者'),
        sa.Column('review_decision', sa.String(16), nullable=True, comment='APPROVE | REJECT | REVISE'),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True, comment='审核时间'),
        sa.Column('reviewer', sa.String(64), nullable=True, comment='审核人'),
        sa.Column('review_reason', sa.String(512), nullable=True, comment='审核原因/反馈'),
        sa.Column('publish_confirmed_at', sa.DateTime(timezone=True), nullable=True, comment='发布确认时间'),
        sa.Column('publish_confirmer', sa.String(64), nullable=True, comment='发布确认人'),
        sa.Column('cron_job_id', sa.String(64), nullable=True, comment='关联CronHub定时任务ID'),
        sa.Column('trace_id', sa.String(32), nullable=True, comment='OpenTelemetry Trace ID'),
        sa.Column('execution_id', sa.String(64), nullable=True, comment='关联WorkflowEngine执行实例ID'),
        sa.Column('tenant_id', sa.String(64), nullable=True, index=True, comment='租户ID'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True, comment='完成/失败/取消时间'),
        comment='TaskHub — PRD V2.7.1 §10.3',
    )
    op.create_index('ix_tasks_status', 'tasks', ['status'])
    op.create_index('ix_tasks_template', 'tasks', ['workflow_template_id'])
    op.create_index('ix_tasks_parent', 'tasks', ['parent_task_id'])
    op.create_index('ix_tasks_tenant_status', 'tasks', ['tenant_id', 'status'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_tasks_tenant_status', table_name='tasks')
    op.drop_index('ix_tasks_parent', table_name='tasks')
    op.drop_index('ix_tasks_template', table_name='tasks')
    op.drop_index('ix_tasks_status', table_name='tasks')
    op.drop_table('tasks')
