"""add_checkpoint_table_p4

Revision ID: 120d8c25393c
Revises: e1f2a3b4c5d6
Create Date: 2026-06-03 10:33:40.004156

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '120d8c25393c'
down_revision: Union[str, Sequence[str], None] = 'e1f2a3b4c5d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema — v4.0 Phase 4: Checkpoint table."""
    op.create_table(
        'checkpoints',
        sa.Column('checkpoint_id', sa.String(length=64), nullable=False, comment='快照唯一标识（cp_xxx）'),
        sa.Column('execution_id', sa.String(length=64), nullable=False, comment='关联 Pipeline 执行 ID'),
        sa.Column('node_id', sa.String(length=64), nullable=False, comment='节点 ID（node_index 字符串化）'),
        sa.Column('node_status', sa.String(length=32), nullable=False, comment='SUCCESS | FAILED | SKIPPED'),
        sa.Column('input_ref', sa.String(length=256), nullable=True, comment='输入数据 S3/本地文件引用'),
        sa.Column('output_ref', sa.String(length=256), nullable=True, comment='输出数据 S3/本地文件引用'),
        sa.Column('output_summary', sa.String(length=512), nullable=True, comment='输出摘要（AI Copilot 展示用）'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True, comment='开始时间'),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True, comment='完成时间'),
        sa.Column('latency_ms', sa.Integer(), nullable=True, comment='执行延迟（毫秒）'),
        sa.Column('token_usage', sa.JSON(), nullable=True, comment='Token 消耗：{prompt_tokens, completion_tokens}'),
        sa.Column('is_recoverable', sa.Boolean(), nullable=False, default=True, comment='是否可恢复'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('checkpoint_id'),
        comment='Checkpoint — PRD v4.0 P4-3',
    )
    op.create_index('ix_ck_execution', 'checkpoints', ['execution_id'], unique=False)
    op.create_index('ix_ck_execution_node', 'checkpoints', ['execution_id', 'node_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_ck_execution_node', table_name='checkpoints')
    op.drop_index('ix_ck_execution', table_name='checkpoints')
    op.drop_table('checkpoints')
