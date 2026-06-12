"""add_platform_content_type_styles_and_content_templates

Revision ID: e1f2a3b4c5d6
Revises: d9e3f4a5b6c7
Create Date: 2026-06-03 08:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e1f2a3b4c5d6'
down_revision: Union[str, Sequence[str], None] = 'd9e3f4a5b6c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema — v4.0 Phase 1: PlatformContentTypeStyle + ContentTemplate + LLM modality_support."""

    # ── 1. platform_content_type_styles ──
    op.create_table(
        'platform_content_type_styles',
        sa.Column('style_id', sa.String(64), primary_key=True, comment="风格唯一标识（style_xxx）"),
        sa.Column('tenant_id', sa.String(64), nullable=False, index=True, comment="所属租户"),
        sa.Column('platform_id', sa.String(32), nullable=False, index=True, comment="平台标识: xhs | douyin | wechat_official | bilibili"),
        sa.Column('content_type', sa.String(32), nullable=False, index=True, comment="内容类型: note_image | note_video | video_clone | long_article"),
        sa.Column('content_dna', postgresql.JSONB(), nullable=True, server_default='{}', comment="内容 DNA：{hook_types, structure_patterns, tone_presets}"),
        sa.Column('default_prompt_fragments', postgresql.JSONB(), nullable=True, server_default='[]', comment='默认 Prompt 片段列表'),
        sa.Column('recommended_keywords', postgresql.JSONB(), nullable=True, server_default='{}', comment="推荐关键词：{high_performing, trending, seasonal}"),
        sa.Column('tone_preset', postgresql.JSONB(), nullable=True, server_default='{}', comment="语气参数：{formality, enthusiasm, urgency, empathy}"),
        sa.Column('structure_template', postgresql.JSONB(), nullable=True, server_default='{}', comment="结构模板：{paragraphs, paragraph_1...}"),
        sa.Column('avg_engagement_rate', sa.Float(), nullable=False, server_default='0.0', comment="平均互动率"),
        sa.Column('sample_count', sa.Integer(), nullable=False, server_default='0', comment="分析样本数"),
        sa.Column('is_ai_generated', sa.Boolean(), nullable=False, server_default='true', comment="是否由 AI 分析自动沉淀"),
        sa.Column('source_template_ids', postgresql.JSONB(), nullable=True, server_default='[]', comment="来源 ContentTemplate ID 列表"),
        sa.Column('status', sa.String(32), nullable=False, server_default='active', index=True, comment="active | deprecated | draft"),
        sa.Column('created_by', sa.String(64), nullable=False, comment="创建者"),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Index('idx_pcstyles_tenant_platform_type', 'tenant_id', 'platform_id', 'content_type'),
        sa.Index('idx_pcstyles_status', 'status'),
        comment="PlatformContentTypeStyle — 平台内容类型风格真源",
    )

    # ── 2. content_templates ──
    op.create_table(
        'content_templates',
        sa.Column('template_id', sa.String(64), primary_key=True, comment="模板唯一标识（tmpl_xxx）"),
        sa.Column('tenant_id', sa.String(64), nullable=False, index=True, comment="所属租户"),
        sa.Column('source_platform_id', sa.String(32), nullable=False, comment="来源平台"),
        sa.Column('source_content_url', sa.String(512), nullable=True, comment="源爆款链接"),
        sa.Column('source_content_id', sa.String(64), nullable=True, comment="源内容 ID"),
        sa.Column('extracted_structure', postgresql.JSONB(), nullable=False, server_default='{}', comment="解析结构：{hook_pattern, body_structure, cta_pattern}"),
        sa.Column('prompt_template', sa.Text(), nullable=False, comment="Prompt 模板（含变量占位符）"),
        sa.Column('variables', postgresql.JSONB(), nullable=False, server_default='[]', comment="变量定义：[{name, label, type, default_value}]"),
        sa.Column('engagement_benchmark', postgresql.JSONB(), nullable=True, server_default='{}', comment="源爆款互动数据：{likes, comments, saves, shares}"),
        sa.Column('platform_content_type_style_id', sa.String(64), sa.ForeignKey('platform_content_type_styles.style_id', ondelete='SET NULL'), nullable=True, comment="关联 PlatformContentTypeStyle"),
        sa.Column('created_by', sa.String(64), nullable=False, comment="创建者：user / ai"),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0', comment="使用次数"),
        sa.Column('avg_generated_engagement', postgresql.JSONB(), nullable=True, comment="生成内容的平均互动数据"),
        sa.Column('status', sa.String(32), nullable=False, server_default='active', index=True, comment="active | deprecated | draft"),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Index('idx_ctemplates_tenant_status', 'tenant_id', 'status'),
        sa.Index('idx_ctemplates_style', 'platform_content_type_style_id'),
        comment="ContentTemplate — 内容模板真源",
    )

    # ── 3. LLMModelORM modality_support ──
    op.add_column(
        'llm_models',
        sa.Column('modality_support', postgresql.JSONB(), nullable=True, server_default='{}', comment="模态支持：{text: bool, image: bool, video: bool, audio: bool, embedding: bool}"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('llm_models', 'modality_support')
    op.drop_table('content_templates')
    op.drop_table('platform_content_type_styles')
