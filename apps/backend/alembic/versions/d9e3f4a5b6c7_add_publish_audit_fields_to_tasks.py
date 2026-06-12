"""add_publish_audit_fields_to_tasks

Revision ID: d9e3f4a5b6c7
Revises: c8d2e3f4a5b6
Create Date: 2026-05-31 23:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'd9e3f4a5b6c7'
down_revision: Union[str, Sequence[str], None] = 'c8d2e3f4a5b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema — Add publish audit fields to tasks table."""

    op.add_column('tasks', sa.Column('published_url', sa.String(512), nullable=True, comment='发布后平台URL'))
    op.add_column('tasks', sa.Column('platform_post_id', sa.String(128), nullable=True, comment='平台帖子ID（如小红书note_id）'))
    op.add_column('tasks', sa.Column('published_at', sa.DateTime(timezone=True), nullable=True, comment='实际发布时间'))
    op.add_column('tasks', sa.Column('publish_error', sa.Text(), nullable=True, comment='发布失败错误信息'))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('tasks', 'publish_error')
    op.drop_column('tasks', 'published_at')
    op.drop_column('tasks', 'platform_post_id')
    op.drop_column('tasks', 'published_url')
