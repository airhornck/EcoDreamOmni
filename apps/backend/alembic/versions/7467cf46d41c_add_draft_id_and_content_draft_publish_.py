"""add_draft_id_and_content_draft_publish_task_review_record_tables

Revision ID: 7467cf46d41c
Revises: 9394d9ebfc86
Create Date: 2026-05-25 18:08:16.930251

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '7467cf46d41c'
down_revision: Union[str, Sequence[str], None] = '9394d9ebfc86'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add draft_id to tasks
    op.add_column('tasks', sa.Column('draft_id', sa.String(length=64), nullable=True, comment='关联ContentDraftID'))
    op.create_index(op.f('ix_tasks_draft_id'), 'tasks', ['draft_id'], unique=False)

    # Create content_drafts table
    op.create_table(
        'content_drafts',
        sa.Column('id', sa.String(64), primary_key=True, comment='草稿ID'),
        sa.Column('title', sa.String(255), nullable=False, comment='标题'),
        sa.Column('content_type', sa.String(16), nullable=False, comment='类型: note | video | carousel'),
        sa.Column('platform', sa.String(16), nullable=False, default='xhs', comment='平台'),
        sa.Column('account_id', sa.String(64), nullable=False, index=True, comment='关联账号池ID'),
        sa.Column('body', sa.Text(), nullable=False, default='', comment='正文'),
        sa.Column('tags', sa.JSON(), nullable=False, default=list, comment='标签列表'),
        sa.Column('status', sa.String(16), nullable=False, default='draft', comment='draft | reviewing | approved | published | rejected'),
        sa.Column('cover_image_url', sa.String(512), nullable=True, comment='封面图URL'),
        sa.Column('engagement_estimate', sa.Float(), nullable=True, comment=' Engagement预估'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        comment='ContentDraft — 内容草稿表',
    )

    # Create publish_tasks table
    op.create_table(
        'publish_tasks',
        sa.Column('id', sa.String(64), primary_key=True, comment='发布任务ID'),
        sa.Column('draft_id', sa.String(64), nullable=False, index=True, comment='关联ContentDraftID'),
        sa.Column('account_id', sa.String(64), nullable=False, index=True, comment='关联账号池ID'),
        sa.Column('platform', sa.String(16), nullable=False, comment='平台'),
        sa.Column('status', sa.String(16), nullable=False, default='pending', comment='pending | scheduled | publishing | published | failed | cancelled | skipped'),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True, comment='定时发布时间'),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True, comment='实际发布时间'),
        sa.Column('published_url', sa.String(512), nullable=True, comment='发布链接'),
        sa.Column('platform_post_id', sa.String(128), nullable=True, comment='平台帖子ID'),
        sa.Column('error_reason', sa.String(512), nullable=True, comment='错误原因'),
        sa.Column('publish_skipped_reason', sa.String(512), nullable=True, comment='跳过原因'),
        sa.Column('retry_count', sa.Integer(), nullable=False, default=0),
        sa.Column('task_hub_task_id', sa.String(64), nullable=True, index=True, comment='关联TaskHub任务ID'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        comment='PublishTask — 发布任务表',
    )

    # Create review_records table
    op.create_table(
        'review_records',
        sa.Column('id', sa.String(64), primary_key=True, comment='审核记录ID'),
        sa.Column('task_id', sa.String(64), nullable=False, index=True, comment='关联TaskHub任务ID'),
        sa.Column('reviewer', sa.String(64), nullable=False, comment='审核人'),
        sa.Column('decision', sa.String(16), nullable=False, comment='APPROVE | REJECT | REVISE'),
        sa.Column('reason', sa.String(512), nullable=True, comment='审核原因'),
        sa.Column('target_node_index', sa.Integer(), nullable=True, comment='目标节点索引'),
        sa.Column('revised_variables', sa.JSON(), nullable=True, comment='修订变量'),
        sa.Column('publish_mode', sa.String(16), nullable=True, comment='immediate | scheduled'),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True, comment='定时发布时间'),
        sa.Column('is_dual_approval', sa.Boolean(), nullable=False, default=False),
        sa.Column('dual_approver', sa.String(64), nullable=True, comment='二次审核人'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        comment='ReviewRecord — 人工审核记录表',
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('review_records')
    op.drop_table('publish_tasks')
    op.drop_table('content_drafts')
    op.drop_index(op.f('ix_tasks_draft_id'), table_name='tasks')
    op.drop_column('tasks', 'draft_id')
