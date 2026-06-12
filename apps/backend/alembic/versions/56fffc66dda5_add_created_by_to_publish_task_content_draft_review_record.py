"""Add created_by to publish_tasks, content_drafts; add task_created_by to review_records

Revision ID: 56fffc66dda5
Revises: 41aaeb4c0967
Create Date: 2026-05-31 19:42:00

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "56fffc66dda5"
down_revision: Union[str, None] = "41aaeb4c0967"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- publish_tasks ---
    op.add_column(
        "publish_tasks",
        sa.Column("created_by", sa.String(length=64), nullable=True, comment="创建者用户ID"),
    )
    op.create_index("ix_pt_created_by", "publish_tasks", ["created_by"])

    # --- content_drafts ---
    op.add_column(
        "content_drafts",
        sa.Column("created_by", sa.String(length=64), nullable=True, comment="创建者用户ID"),
    )
    op.create_index("ix_cd_created_by", "content_drafts", ["created_by"])

    # --- review_records ---
    op.add_column(
        "review_records",
        sa.Column(
            "task_created_by",
            sa.String(length=64),
            nullable=True,
            comment="被审核任务的创建者用户ID",
        ),
    )
    op.create_index("ix_rr_task_created_by", "review_records", ["task_created_by"])


def downgrade() -> None:
    # --- review_records ---
    op.drop_index("ix_rr_task_created_by", table_name="review_records")
    op.drop_column("review_records", "task_created_by")

    # --- content_drafts ---
    op.drop_index("ix_cd_created_by", table_name="content_drafts")
    op.drop_column("content_drafts", "created_by")

    # --- publish_tasks ---
    op.drop_index("ix_pt_created_by", table_name="publish_tasks")
    op.drop_column("publish_tasks", "created_by")
