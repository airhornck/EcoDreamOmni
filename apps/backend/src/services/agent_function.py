"""Agent Function layer — DB operations for AgentORM.

All direct database access for Agent entities lives here.
Agent layer (agent_hub.py) MUST NOT import AgentORM or use db sessions directly.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from src.models.agent_orm import AgentORM


# ─── Dataclasses ───

@dataclass
class AgentInfo:
    id: str
    name: str
    role: str
    description: str = ""
    avatar_url: Optional[str] = None
    skills: List[str] = field(default_factory=list)
    supported_platforms: List[str] = field(default_factory=list)
    supported_formats: List[str] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)
    success_rate: float = 0.92
    recent_tasks_1h: int = 0
    status: str = "ACTIVE"
    created_at: str = ""
    updated_at: str = ""


# ─── Helpers ───

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _db_to_agent(orm: AgentORM) -> AgentInfo:
    return AgentInfo(
        id=orm.id,
        name=orm.name,
        role=orm.role,
        description=orm.description or "",
        avatar_url=orm.avatar_url,
        skills=orm.skills or [],
        supported_platforms=orm.supported_platforms or [],
        supported_formats=orm.supported_formats or [],
        config=orm.config or {},
        success_rate=orm.success_rate or 0.0,
        recent_tasks_1h=orm.recent_tasks_1h or 0,
        status=orm.status,
        created_at=orm.created_at.isoformat() if orm.created_at else _now(),
        updated_at=orm.updated_at.isoformat() if orm.updated_at else _now(),
    )


def _agent_to_orm(agent: AgentInfo) -> AgentORM:
    return AgentORM(
        id=agent.id,
        name=agent.name,
        role=agent.role,
        description=agent.description,
        avatar_url=agent.avatar_url,
        skills=agent.skills,
        supported_platforms=agent.supported_platforms,
        supported_formats=agent.supported_formats,
        config=agent.config,
        success_rate=agent.success_rate,
        recent_tasks_1h=agent.recent_tasks_1h,
        status=agent.status,
    )


# ─── CRUD ───

async def get_agent_by_id(db: AsyncSession, agent_id: str) -> Optional[AgentInfo]:
    result = await db.execute(select(AgentORM).where(AgentORM.id == agent_id))
    orm = result.scalar_one_or_none()
    return _db_to_agent(orm) if orm else None


async def list_agents_from_db(
    db: AsyncSession,
    status: Optional[str] = None,
    platform: Optional[str] = None,
    content_format: Optional[str] = None,
) -> List[AgentInfo]:
    query = select(AgentORM)
    if status:
        query = query.where(AgentORM.status == status)
    result = await db.execute(query)
    orms = result.scalars().all()
    agents = [_db_to_agent(o) for o in orms]

    # Post-filter platform/format (JSON array containment via Python for MVP)
    if platform:
        agents = [a for a in agents if platform in (a.supported_platforms or [])]
    if content_format:
        agents = [a for a in agents if content_format in (a.supported_formats or [])]

    return agents


async def create_agent_in_db(db: AsyncSession, agent: AgentInfo) -> AgentInfo:
    orm = _agent_to_orm(agent)
    db.add(orm)
    await db.commit()
    await db.refresh(orm)
    return _db_to_agent(orm)


async def update_agent_in_db(
    db: AsyncSession, agent_id: str, **kwargs
) -> Optional[AgentInfo]:
    result = await db.execute(select(AgentORM).where(AgentORM.id == agent_id))
    orm = result.scalar_one_or_none()
    if not orm:
        return None
    for key, value in kwargs.items():
        if hasattr(orm, key):
            setattr(orm, key, value)
    orm.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(orm)
    return _db_to_agent(orm)


async def seed_default_agents(db: AsyncSession) -> int:
    """Seed default agents if table is empty."""
    result = await db.execute(select(func.count()).select_from(AgentORM))
    count = result.scalar() or 0
    if count > 0:
        return 0

    defaults = [
        AgentInfo(
            id="content_forge_xhs_image",
            name="小红书图文生成 Agent",
            role="content_generation",
            description="专为小红书图文笔记优化的内容生成 Agent，内置图文排版、封面生成、标签优化能力",
            skills=["text_generate_skill", "keyword_inject_skill", "rag_retrieval_skill", "cover_generate_skill"],
            supported_platforms=["xiaohongshu"],
            supported_formats=["图文"],
            config={
                "default_workflow_template_id": "content_creation_note_image",
                "workflow_version": 2,
                "platform_format_snapshot": {
                    "platform_id": "xiaohongshu",
                    "format_name": "图文",
                    "title_constraints": {
                        "max_length": 20,
                        "recommended": "15-20字",
                        "recommended_patterns": ["数字+痛点", "场景+解决方案", "对比+结论"],
                    },
                    "body_constraints": {
                        "max_length": 1000,
                        "recommended": "300-800字",
                        "max_paragraphs": 15,
                        "max_emojis": 20,
                        "line_break_style": "loose",
                    },
                    "tag_constraints": {
                        "max_count": 10,
                        "max_length_per_tag": 20,
                    },
                    "cover_constraints": {
                        "aspect_ratio": "3:4",
                        "min_width": 720,
                        "min_height": 960,
                        "recommended_per_post": "6-9",
                        "max_images_per_post": 18,
                    },
                },
                "safety_injection": {
                    "pre_check_agents": ["vetdrug-validate"],
                    "post_check_agents": ["compliance-guard"],
                    "rule_layers": ["l1_static", "l2_keyword"],
                    "required_disclaimers": ["本品不能替代药品"],
                },
            },
        ),
        AgentInfo(
            id="content_forge_xhs_video",
            name="小红书视频生成 Agent",
            role="content_generation",
            description="专为小红书视频内容优化的生成 Agent，支持脚本生成、分镜规划、口播稿优化",
            skills=["text_generate_skill", "video_script_skill", "shot_planning_skill", "keyword_inject_skill"],
            supported_platforms=["xiaohongshu"],
            supported_formats=["视频"],
            config={"default_workflow_template_id": "content_creation_video_original", "workflow_version": 1},
        ),
        AgentInfo(
            id="content_forge_xhs_text",
            name="小红书长文生成 Agent",
            role="content_generation",
            description="专为小红书长文/攻略类内容优化的生成 Agent，支持结构化长文、分章节输出",
            skills=["text_generate_skill", "content_structural_analysis_skill", "keyword_inject_skill", "rag_retrieval_skill"],
            supported_platforms=["xiaohongshu"],
            supported_formats=["仅文字"],
            config={"default_workflow_template_id": "content_creation_text_article", "workflow_version": 1},
        ),
        AgentInfo(
            id="content_forge_douyin_video",
            name="抖音视频生成 Agent",
            role="content_generation",
            description="专为抖音短视频优化的生成 Agent，支持爆款脚本、黄金3秒钩子、口播优化",
            skills=["text_generate_skill", "video_script_skill", "hook_optimize_skill", "voice_synthesis_skill"],
            supported_platforms=["douyin"],
            supported_formats=["视频"],
            config={"default_workflow_template_id": "content_creation_video_original", "workflow_version": 1},
        ),
        AgentInfo(
            id="content_forge_douyin_clone",
            name="抖音视频复刻 Agent",
            role="content_generation",
            description="专为抖音爆款视频复刻优化的 Agent，支持脚本克隆、风格迁移、口播克隆",
            skills=["text_generate_skill", "video_clone_skill", "style_transfer_skill", "voice_clone_skill"],
            supported_platforms=["douyin"],
            supported_formats=["视频复刻"],
            config={"default_workflow_template_id": "content_creation_video_clone", "workflow_version": 1},
        ),
        AgentInfo(
            id="content_forge_wx_text",
            name="视频号图文生成 Agent",
            role="content_generation",
            description="专为微信视频号图文内容优化的生成 Agent，支持公众号风格排版、阅读体验优化",
            skills=["text_generate_skill", "keyword_inject_skill", "rag_retrieval_skill", "readability_optimize_skill"],
            supported_platforms=["wechat_channels"],
            supported_formats=["图文"],
            config={"default_workflow_template_id": "content_creation_text_article", "workflow_version": 1},
        ),
        AgentInfo(
            id="content_forge_wx_video",
            name="视频号视频生成 Agent",
            role="content_generation",
            description="专为微信视频号视频内容优化的生成 Agent，支持竖屏视频脚本、直播切片",
            skills=["text_generate_skill", "video_script_skill", "live_clip_skill", "keyword_inject_skill"],
            supported_platforms=["wechat_channels"],
            supported_formats=["视频"],
            config={"default_workflow_template_id": "content_creation_video_original", "workflow_version": 1},
        ),
        AgentInfo(
            id="content_forge_bili_video",
            name="哔哩哔哩视频生成 Agent",
            role="content_generation",
            description="专为 B 站长视频优化的生成 Agent，支持分P规划、弹幕优化、二次元风格适配",
            skills=["text_generate_skill", "video_script_skill", "part_planning_skill", "danmaku_optimize_skill"],
            supported_platforms=["bilibili"],
            supported_formats=["视频"],
            config={"default_workflow_template_id": "content_creation_video_original", "workflow_version": 1},
        ),
        AgentInfo(
            id="content_forge_bili_clone",
            name="哔哩哔哩视频复刻 Agent",
            role="content_generation",
            description="专为 B 站爆款视频复刻优化的 Agent，支持 MMD/手书克隆、风格迁移",
            skills=["text_generate_skill", "video_clone_skill", "style_transfer_skill", "subtitle_optimize_skill"],
            supported_platforms=["bilibili"],
            supported_formats=["视频复刻"],
            config={"default_workflow_template_id": "content_creation_video_clone", "workflow_version": 1},
        ),
        AgentInfo(
            id="content_forge_generic",
            name="通用内容生成 Agent",
            role="content_generation",
            description="支持多平台多格式的通用内容生成 Agent，当没有平台-specific Agent 时作为兜底",
            skills=["text_generate_skill", "keyword_inject_skill", "rag_retrieval_skill", "content_rewrite_skill", "platform_adapt_skill"],
            supported_platforms=["xiaohongshu", "douyin", "wechat_channels", "bilibili"],
            supported_formats=["图文", "视频", "仅文字", "视频复刻"],
            config={"default_workflow_template_id": "content_creation_standard", "workflow_version": 1},
        ),
    ]

    for agent in defaults:
        orm = _agent_to_orm(agent)
        db.add(orm)
    await db.commit()
    return len(defaults)
