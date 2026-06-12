"""PersonaStory ORM model — PRD V2.7.2 §11.

素人人设剧本真源表：剧本管理、节点编排、情感曲线、内容绑定.
与 AssetPool / BrandKnowledge / TimelineLibrary 并列的第六大基础功能.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Text, Integer, DateTime, ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.core.database import Base


class PersonaStoryORM(Base):
    """素人人设剧本主表 — 情感曲线与剧本生命周期管理."""

    __tablename__ = "persona_stories"
    __table_args__ = (
        Index("ix_ps_persona_status", "persona_id", "status"),
        {"comment": "PersonaStory — PRD V2.7.2 §11"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    persona_id = Column(
        String(64),
        nullable=False,
        index=True,
        comment="关联PersonaPool人设ID",
    )
    name = Column(String(256), nullable=False, comment="剧本名称/系列主题")
    description = Column(Text, nullable=True, comment="剧本描述")

    emotion_curve_template = Column(
        String(32),
        nullable=False,
        default="gradual_growth",
        comment="情感曲线模板: gradual_growth | steady | wave | climax_first",
    )

    status = Column(
        String(16),
        nullable=False,
        default="draft",
        comment="draft | active | completed | archived",
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

    # Relationship
    nodes = relationship(
        "StoryNodeORM",
        back_populates="story",
        cascade="all, delete-orphan",
        order_by="StoryNodeORM.sequence_index",
    )


class StoryNodeORM(Base):
    """剧本节点表 — 单集/单篇内容节点，支持排序与内容绑定."""

    __tablename__ = "story_nodes"
    __table_args__ = (
        UniqueConstraint("story_id", "sequence_index", name="uq_story_node_seq"),
        Index("ix_sn_story_seq", "story_id", "sequence_index"),
        {"comment": "StoryNode — PRD V2.7.2 §11"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    story_id = Column(
        UUID(as_uuid=True),
        ForeignKey("persona_stories.id", ondelete="CASCADE"),
        nullable=False,
    )
    sequence_index = Column(
        Integer,
        nullable=False,
        comment="节点在剧本中的顺序索引",
    )

    theme = Column(String(256), nullable=False, comment="本节点主题")
    emotion_tone = Column(
        String(16),
        nullable=False,
        comment="情感基调: low | medium | high | burst",
    )
    key_event = Column(Text, nullable=False, comment="关键事件/剧情")
    prev_recap = Column(Text, nullable=True, comment="前情提要")
    next_teaser = Column(Text, nullable=True, comment="下集预告")

    content_draft_id = Column(
        String(64),
        nullable=True,
        index=True,
        comment="绑定ContentForge内容草稿ID",
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

    # Relationship
    story = relationship("PersonaStoryORM", back_populates="nodes")
