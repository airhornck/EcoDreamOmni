"""add_platform_schema_orm

Revision ID: 19327853b7e1
Revises: a6135eeaae42
Create Date: 2026-05-31 10:44:16.734208

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '19327853b7e1'
down_revision: Union[str, Sequence[str], None] = 'a6135eeaae42'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema — 新增平台格式规范表."""
    op.create_table('platform_schemas',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('platform_id', sa.String(length=32), nullable=False, comment='平台标识: xiaohongshu | douyin | wechat_official | bilibili'),
    sa.Column('display_name', sa.String(length=100), nullable=False),
    sa.Column('version', sa.String(length=20), nullable=False),
    sa.Column('content_dna', sa.JSON(), nullable=True, comment='[{element, value, validation_skill}]'),
    sa.Column('audit_rules', sa.JSON(), nullable=True, comment='[{category, forbidden_terms, audit_skill, examples, notes}]'),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    comment='PlatformSchema — 平台 API 发布格式规范真源'
    )
    op.create_index(op.f('ix_platform_schemas_platform_id'), 'platform_schemas', ['platform_id'], unique=True)
    op.create_index('ix_ps_platform_id', 'platform_schemas', ['platform_id'], unique=False)
    op.create_table('platform_content_formats',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('schema_id', sa.UUID(), nullable=False),
    sa.Column('format_name', sa.String(length=50), nullable=False),
    sa.Column('fields', sa.JSON(), nullable=False, comment='[{name, label, type, required, min, max, default, description, ...}]'),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['schema_id'], ['platform_schemas.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    comment='PlatformContentFormat — 平台内容格式字段约束'
    )
    op.create_index('ix_pcf_schema_format', 'platform_content_formats', ['schema_id', 'format_name'], unique=False)
    op.create_index(op.f('ix_platform_content_formats_schema_id'), 'platform_content_formats', ['schema_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema — 删除平台格式规范表."""
    op.drop_index(op.f('ix_platform_content_formats_schema_id'), table_name='platform_content_formats')
    op.drop_index('ix_pcf_schema_format', table_name='platform_content_formats')
    op.drop_table('platform_content_formats')
    op.drop_index('ix_ps_platform_id', table_name='platform_schemas')
    op.drop_index(op.f('ix_platform_schemas_platform_id'), table_name='platform_schemas')
    op.drop_table('platform_schemas')
