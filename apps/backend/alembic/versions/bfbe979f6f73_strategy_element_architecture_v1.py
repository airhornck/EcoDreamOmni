"""strategy_element_architecture_v1

Revision ID: bfbe979f6f73
Revises: e73c72089a1a
Create Date: 2026-06-05 23:08:12.176581

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'bfbe979f6f73'
down_revision: Union[str, Sequence[str], None] = 'e73c72089a1a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema — Strategy Element Architecture v1.
    
    新增两张核心表：
      1. strategy_elements — 策略元素真源表（原子化内容策略组件）
      2. strategy_sets — 策略组合快照表（可复用的元素组合）
    
    扩展 tasks 表：
      - content_strategy: JSON 存储完整内容策略配置
      - methodology_stage_id: 关联方法论阶段
      - timeline_event_id: 关联时间线事件
    """
    # ═══════════════════════════════════════════════════════════════════
    # 1. strategy_elements 表
    # ═══════════════════════════════════════════════════════════════════
    op.create_table(
        'strategy_elements',
        sa.Column('element_id', sa.String(64), primary_key=True, comment='策略元素唯一标识 elem_xxx'),
        sa.Column('tenant_id', sa.String(64), nullable=False, index=True, comment='所属租户'),
        sa.Column('element_type', sa.String(50), nullable=False, index=True, comment='元素类型'),
        sa.Column('element_subtype', sa.String(50), nullable=True, index=True, comment='元素子类型'),
        sa.Column('name', sa.String(128), nullable=False, comment='元素名称'),
        sa.Column('description', sa.Text, nullable=True, comment='元素描述'),
        sa.Column('content', sa.JSON, nullable=False, comment='元素内容（Schema 由 element_type 定义）'),
        sa.Column('render_template', sa.Text, nullable=False, comment='Jinja2 渲染模板'),
        sa.Column('variables', sa.JSON, server_default=sa.text("'[]'"), comment='变量定义 [{name, label, type, default_value}]'),
        sa.Column('source', sa.String(50), server_default='manual', comment='来源：manual|viral_analyzer|ai_generated|system'),
        sa.Column('source_content_id', sa.String(64), nullable=True, comment='关联的爆款笔记/源内容 ID'),
        sa.Column('source_element_ids', sa.JSON, server_default=sa.text("'[]'"), comment='若由多个元素合并，记录来源元素 ID 列表'),
        sa.Column('platform', sa.String(32), nullable=True, index=True, comment='适用平台'),
        sa.Column('content_format', sa.String(32), nullable=True, comment='适用内容格式'),
        sa.Column('methodology_stage_id', sa.String(64), nullable=True, index=True, comment='关联方法论阶段'),
        sa.Column('category', sa.String(64), nullable=True, index=True, comment='内容分类'),
        sa.Column('usage_count', sa.Integer, server_default='0', nullable=False, comment='使用次数'),
        sa.Column('avg_engagement', sa.JSON, server_default=sa.text("'{}'"), comment='平均互动数据'),
        sa.Column('effectiveness_score', sa.Float, server_default='0.0', nullable=False, comment='效果评分 0-100'),
        sa.Column('status', sa.String(32), server_default='active', nullable=False, index=True, comment='active|deprecated|draft'),
        sa.Column('created_by', sa.String(64), nullable=False, comment='创建者'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        comment='StrategyElement — 策略元素真源表',
    )

    op.create_index('ix_se_tenant_type', 'strategy_elements', ['tenant_id', 'element_type', 'status'])
    op.create_index('ix_se_tenant_platform', 'strategy_elements', ['tenant_id', 'platform', 'status'])
    op.create_index('ix_se_recommend', 'strategy_elements', ['tenant_id', 'element_type', 'platform', 'methodology_stage_id', 'status'])

    # ═══════════════════════════════════════════════════════════════════
    # 2. strategy_sets 表（ContentTemplate 的演进）
    # ═══════════════════════════════════════════════════════════════════
    op.create_table(
        'strategy_sets',
        sa.Column('set_id', sa.String(64), primary_key=True, comment='策略组合唯一标识 set_xxx'),
        sa.Column('tenant_id', sa.String(64), nullable=False, index=True, comment='所属租户'),
        sa.Column('name', sa.String(128), nullable=False, comment='策略组合名称'),
        sa.Column('description', sa.Text, nullable=True, comment='策略组合描述'),
        sa.Column('element_refs', sa.JSON, nullable=False, comment='策略元素引用列表 [{element_id, priority, override_variables}]'),
        sa.Column('default_variables', sa.JSON, server_default=sa.text("'{}'"), comment='默认变量值'),
        sa.Column('source', sa.String(50), server_default='manual', comment='来源：manual|viral_analyzer|ai_generated'),
        sa.Column('source_content_id', sa.String(64), nullable=True, comment='关联的爆款笔记/源内容 ID'),
        sa.Column('platform', sa.String(32), nullable=True, index=True, comment='适用平台'),
        sa.Column('content_format', sa.String(32), nullable=True, comment='适用内容格式'),
        sa.Column('methodology_stage_id', sa.String(64), nullable=True, comment='关联方法论阶段'),
        sa.Column('category', sa.String(64), nullable=True, comment='内容分类'),
        sa.Column('usage_count', sa.Integer, server_default='0', nullable=False, comment='使用次数'),
        sa.Column('avg_engagement', sa.JSON, server_default=sa.text("'{}'"), comment='平均互动数据'),
        sa.Column('status', sa.String(32), server_default='active', nullable=False, index=True, comment='active|deprecated|draft'),
        sa.Column('created_by', sa.String(64), nullable=False, comment='创建者'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        comment='StrategySet — 策略组合快照（ContentTemplate 的演进）',
    )

    op.create_index('ix_ss_tenant_status', 'strategy_sets', ['tenant_id', 'status'])
    op.create_index('ix_ss_tenant_platform', 'strategy_sets', ['tenant_id', 'platform', 'status'])

    # ═══════════════════════════════════════════════════════════════════
    # 3. tasks 表扩展
    # ═══════════════════════════════════════════════════════════════════
    op.add_column(
        'tasks',
        sa.Column('content_strategy', sa.JSON, nullable=True, comment='完整内容策略配置（ContentStrategy JSON）'),
    )
    op.add_column(
        'tasks',
        sa.Column('methodology_stage_id', sa.String(64), nullable=True, comment='关联方法论阶段ID'),
    )
    op.add_column(
        'tasks',
        sa.Column(
            'timeline_event_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('timeline_events.id', ondelete='SET NULL'),
            nullable=True,
            comment='关联时间线事件ID',
        ),
    )

    # Note: 不在 JSON 字段上创建 btree 索引（PG 不支持）。
    # 如需按 content_strategy 查询，后续可添加 GIN 索引。
    op.create_index('ix_tasks_methodology_stage', 'tasks', ['methodology_stage_id'])
    op.create_index('ix_tasks_timeline_event', 'tasks', ['timeline_event_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_tasks_timeline_event', table_name='tasks')
    op.drop_index('ix_tasks_methodology_stage', table_name='tasks')
    op.drop_column('tasks', 'timeline_event_id')
    op.drop_column('tasks', 'methodology_stage_id')
    op.drop_column('tasks', 'content_strategy')

    op.drop_index('ix_ss_tenant_platform', table_name='strategy_sets')
    op.drop_index('ix_ss_tenant_status', table_name='strategy_sets')
    op.drop_table('strategy_sets')

    op.drop_index('ix_se_recommend', table_name='strategy_elements')
    op.drop_index('ix_se_tenant_platform', table_name='strategy_elements')
    op.drop_index('ix_se_tenant_type', table_name='strategy_elements')
    op.drop_table('strategy_elements')
