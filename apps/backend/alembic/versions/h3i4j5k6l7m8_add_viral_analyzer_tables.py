"""Add viral analyzer tables — structure_definitions + keyword_library.

Revision ID: h3i4j5k6l7m8
Revises: g2h3i4j5k6l7
Create Date: 2026-06-05 04:00:00.000000+00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "h3i4j5k6l7m8"
down_revision: Union[str, None] = "g2h3i4j5k6l7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create structure_definitions table
    op.create_table(
        "structure_definitions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True, comment="自增ID"),
        sa.Column("structure_type", sa.String(50), nullable=False, unique=True, comment="结构类型"),
        sa.Column("description", sa.Text, nullable=True, comment="结构描述"),
        sa.Column("scoring_weights", sa.JSON, server_default=sa.text("'{}'"), comment="评分权重"),
        sa.Column("keyword_patterns", sa.JSON, server_default=sa.text("'[]'"), comment="结构识别关键词正则列表"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), onupdate=sa.text("now()")),
        sa.Index("idx_structure_type", "structure_type"),
        comment="StructureDefinition — 爆款结构定义",
    )

    # 2. Create keyword_library table
    op.create_table(
        "keyword_library",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True, comment="自增ID"),
        sa.Column("keyword", sa.String(100), nullable=False, comment="关键词"),
        sa.Column("dimension", sa.String(50), nullable=False, comment="维度：structure|function|emotion|industry|effect"),
        sa.Column("weight", sa.Float, server_default=sa.text("1.0"), nullable=False, comment="权重"),
        sa.Column("applicable_structures", sa.ARRAY(sa.String), nullable=True, comment="适用结构类型列表"),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true"), nullable=False, comment="是否启用"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), onupdate=sa.text("now()")),
        sa.Index("idx_keyword_dimension", "dimension", "is_active"),
        sa.Index("idx_keyword_structure", "applicable_structures"),
        comment="KeywordLibrary — 爆款分析关键词库",
    )

    # 3. Extend content_templates table (source_content_id already exists)
    op.add_column(
        "content_templates",
        sa.Column("source", sa.String(50), nullable=True, server_default="manual", comment="来源：manual|viral_analyzer|ai_generated"),
    )
    op.add_column(
        "content_templates",
        sa.Column("analysis_report", sa.JSON, nullable=True, comment="关联的分析报告"),
    )

    # 4. Seed default structure definitions
    op.execute("""
        INSERT INTO structure_definitions (structure_type, description, scoring_weights, keyword_patterns)
        VALUES
        ('种草测评型', '以真实体验分享为主，推荐产品/服务', '{"completeness": 0.5, "keyword_richness": 0.5}', '["种草", "测评", "推荐", "亲测", "好用", "必入"]'),
        ('干货合集型', '汇总多个知识点或工具，信息密度高', '{"completeness": 0.5, "keyword_richness": 0.5}', '["合集", "干货", "盘点", "总结", "攻略", "大全"]'),
        ('避坑排雷型', '指出常见误区和错误做法，提供正确方案', '{"completeness": 0.5, "keyword_richness": 0.5}', '["避坑", "排雷", "误区", "千万别", "错误", "注意"]'),
        ('教程攻略型', '手把手教学，步骤清晰可操作', '{"completeness": 0.5, "keyword_richness": 0.5}', '["教程", "攻略", "步骤", "手把手", "怎么做", "方法"]'),
        ('对比测评型', '多个产品/方案对比，优劣分析', '{"completeness": 0.5, "keyword_richness": 0.5}', '["对比", "测评", "vs", "哪个好", "区别", "优劣"]'),
        ('个人故事型', '以亲身经历为线索，情感共鸣强', '{"completeness": 0.5, "keyword_richness": 0.5}', '["故事", "经历", "我", "记得", "当时", "感动"]')
    """)

    # 5. Seed minimal keyword library (MVP ~30 core keywords)
    op.execute("""
        INSERT INTO keyword_library (keyword, dimension, weight, applicable_structures)
        VALUES
        -- structure keywords
        ('避坑', 'structure', 1.2, ARRAY['避坑排雷型']),
        ('误区', 'structure', 1.1, ARRAY['避坑排雷型']),
        ('种草', 'structure', 1.2, ARRAY['种草测评型']),
        ('测评', 'structure', 1.1, ARRAY['种草测评型', '对比测评型']),
        ('教程', 'structure', 1.1, ARRAY['教程攻略型']),
        ('攻略', 'structure', 1.1, ARRAY['教程攻略型']),
        ('合集', 'structure', 1.1, ARRAY['干货合集型']),
        ('故事', 'structure', 1.0, ARRAY['个人故事型']),
        -- function keywords
        ('指南', 'function', 1.0, ARRAY['避坑排雷型', '教程攻略型']),
        ('推荐', 'function', 1.0, ARRAY['种草测评型']),
        ('分享', 'function', 0.9, NULL),
        ('必看', 'function', 1.0, NULL),
        ('干货', 'function', 1.0, ARRAY['干货合集型']),
        -- emotion keywords
        ('焦虑', 'emotion', 0.9, ARRAY['避坑排雷型']),
        ('惊喜', 'emotion', 0.9, ARRAY['种草测评型']),
        ('共鸣', 'emotion', 0.9, ARRAY['个人故事型']),
        ('信任', 'emotion', 0.8, ARRAY['教程攻略型']),
        ('愤怒', 'emotion', 0.9, ARRAY['避坑排雷型']),
        ('向往', 'emotion', 0.8, ARRAY['种草测评型']),
        -- industry keywords (pet vertical)
        ('驱虫', 'industry', 1.5, ARRAY['避坑排雷型', '种草测评型']),
        ('猫粮', 'industry', 1.3, ARRAY['种草测评型', '对比测评型']),
        ('疫苗', 'industry', 1.3, ARRAY['教程攻略型']),
        ('铲屎官', 'industry', 1.0, NULL),
        ('养猫', 'industry', 1.2, NULL),
        ('狗狗', 'industry', 1.2, NULL),
        -- effect keywords
        ('省钱', 'effect', 1.1, ARRAY['避坑排雷型', '种草测评型']),
        ('有效', 'effect', 1.0, ARRAY['种草测评型']),
        ('快速', 'effect', 0.9, ARRAY['教程攻略型']),
        ('简单', 'effect', 0.9, ARRAY['教程攻略型']),
        ('真实', 'effect', 1.0, ARRAY['个人故事型'])
    """)


def downgrade() -> None:
    op.drop_column("content_templates", "analysis_report")
    op.drop_column("content_templates", "source_content_id")
    op.drop_column("content_templates", "source")
    op.drop_table("keyword_library")
    op.drop_table("structure_definitions")
