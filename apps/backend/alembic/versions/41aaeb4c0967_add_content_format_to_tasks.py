"""add_content_format_to_tasks

Revision ID: 41aaeb4c0967
Revises: 19327853b7e1
Create Date: 2026-05-31 12:04:53.609536

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '41aaeb4c0967'
down_revision: Union[str, Sequence[str], None] = '19327853b7e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema — 新增 content_format 字段到 tasks 表."""
    op.add_column(
        'tasks',
        sa.Column(
            'content_format',
            sa.String(length=32),
            nullable=True,
            comment='内容格式: 图文 | 视频 | 仅文字 | 视频复刻 | 视频原创 | 长文章',
        ),
    )


def downgrade() -> None:
    """Downgrade schema — 删除 content_format 字段."""
    op.drop_column('tasks', 'content_format')
