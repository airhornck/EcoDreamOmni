"""ViralAnalyzer ORM models — 实验室 · 爆款笔记分析引擎.

Aligned with docs/后端需求/后端需求补充_实验室爆款笔记分析_2026-06-05.md
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    JSON,
    DateTime,
    Boolean,
    Index,
    ARRAY,
)

from src.core.database import Base


class StructureDefinitionORM(Base):
    """结构定义表 — 6种爆款结构 + 评分权重."""

    __tablename__ = "structure_definitions"
    __table_args__ = (
        Index("idx_structure_type", "structure_type"),
        {"comment": "StructureDefinition — 爆款结构定义"},
    )

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="自增ID",
    )
    structure_type = Column(
        String(50),
        nullable=False,
        unique=True,
        comment="结构类型：种草测评型|干货合集型|避坑排雷型|教程攻略型|对比测评型|个人故事型",
    )
    description = Column(
        Text,
        nullable=True,
        comment="结构描述",
    )
    scoring_weights = Column(
        JSON,
        nullable=False,
        default=lambda: {"completeness": 0.5, "keyword_richness": 0.5},
        comment="评分权重：{completeness, keyword_richness, emotion_curve, interaction_weight, emoji_strategy}",
    )
    keyword_patterns = Column(
        JSON,
        nullable=True,
        default=list,
        comment="结构识别关键词正则列表",
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class KeywordLibraryORM(Base):
    """最小关键词库表 — MVP 50-100 核心词，作为 LLM 校准集."""

    __tablename__ = "keyword_library"
    __table_args__ = (
        Index("idx_keyword_dimension", "dimension", "is_active"),
        Index("idx_keyword_structure", "applicable_structures"),
        {"comment": "KeywordLibrary — 爆款分析关键词库"},
    )

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="自增ID",
    )
    keyword = Column(
        String(100),
        nullable=False,
        comment="关键词",
    )
    dimension = Column(
        String(50),
        nullable=False,
        comment="维度：structure|function|emotion|industry|effect",
    )
    weight = Column(
        Float,
        default=1.0,
        nullable=False,
        comment="权重",
    )
    applicable_structures = Column(
        ARRAY(String),
        nullable=True,
        comment="适用结构类型列表",
    )
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否启用",
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
