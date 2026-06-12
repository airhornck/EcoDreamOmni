"""add_note_engagement_orm

Revision ID: a6135eeaae42
Revises: 7467cf46d41c
Create Date: 2026-05-30 11:45:58.679096

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a6135eeaae42'
down_revision: Union[str, Sequence[str], None] = '7467cf46d41c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'note_engagements',
        sa.Column('id', sa.String(length=64), nullable=False, comment='互动记录ID'),
        sa.Column('publish_task_id', sa.String(length=64), nullable=False, comment='关联PublishTaskID'),
        sa.Column('account_id', sa.String(length=64), nullable=False, comment='关联账号池ID'),
        sa.Column('platform_post_id', sa.String(length=128), nullable=False, comment='平台帖子ID (note_id)'),
        sa.Column('likes', sa.Integer(), nullable=True, comment='点赞数'),
        sa.Column('comments', sa.Integer(), nullable=True, comment='评论数'),
        sa.Column('saves', sa.Integer(), nullable=True, comment='收藏数'),
        sa.Column('shares', sa.Integer(), nullable=True, comment='分享数'),
        sa.Column('views', sa.Integer(), nullable=True, comment='阅读量（可能不可用）'),
        sa.Column('fetch_status', sa.String(length=16), nullable=False, comment='pending | success | failed | manual'),
        sa.Column('fetch_error', sa.String(length=512), nullable=True, comment='获取失败原因'),
        sa.Column('fetched_at', sa.DateTime(timezone=True), nullable=True, comment='数据获取时间'),
        sa.Column('raw_response', sa.JSON(), nullable=True, comment='平台原始响应JSON'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['publish_task_id'], ['publish_tasks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='NoteEngagement — PRD V2.3 §2.6'
    )
    op.create_index('ix_ne_account', 'note_engagements', ['account_id'], unique=False)
    op.create_index('ix_ne_fetch_status', 'note_engagements', ['fetch_status'], unique=False)
    op.create_index('ix_ne_post', 'note_engagements', ['platform_post_id'], unique=False)
    op.create_index(op.f('ix_note_engagements_account_id'), 'note_engagements', ['account_id'], unique=False)
    op.create_index(op.f('ix_note_engagements_platform_post_id'), 'note_engagements', ['platform_post_id'], unique=False)
    op.create_index(op.f('ix_note_engagements_publish_task_id'), 'note_engagements', ['publish_task_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_note_engagements_publish_task_id'), table_name='note_engagements')
    op.drop_index(op.f('ix_note_engagements_platform_post_id'), table_name='note_engagements')
    op.drop_index(op.f('ix_note_engagements_account_id'), table_name='note_engagements')
    op.drop_index('ix_ne_post', table_name='note_engagements')
    op.drop_index('ix_ne_fetch_status', table_name='note_engagements')
    op.drop_index('ix_ne_account', table_name='note_engagements')
    op.drop_table('note_engagements')
