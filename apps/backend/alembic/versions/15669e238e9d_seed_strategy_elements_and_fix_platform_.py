"""seed_strategy_elements_and_fix_platform_ids

Revision ID: 15669e238e9d
Revises: 8eae2f4c39a9
Create Date: 2026-06-08 23:00:15.470173

"""
from typing import Sequence, Union
import uuid
import json
from datetime import datetime, timezone

from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session


# revision identifiers, used by Alembic.
revision: str = '15669e238e9d'
down_revision: Union[str, Sequence[str], None] = '8eae2f4c39a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _se_id() -> str:
    return f"se_{uuid.uuid4().hex[:16]}"


def upgrade() -> None:
    """1. Fix platform IDs from legacy 'xhs' to standard 'xiaohongshu'
       2. Seed strategy elements covering all major types including keyword_strategy.
    """
    bind = op.get_bind()
    session = Session(bind=bind)

    # ─── 1. Fix platform IDs ───
    session.execute(
        sa.text("UPDATE strategy_elements SET platform = 'xiaohongshu' WHERE platform = 'xhs'")
    )
    session.execute(
        sa.text("UPDATE strategy_sets SET platform = 'xiaohongshu' WHERE platform = 'xhs'")
    )

    # ─── 2. Seed new strategy elements ───
    tenant_id = "default"
    created_by = "system"
    now = _now()
    platform = "xiaohongshu"
    content_format = "图文"

    seeds = [
        # keyword_strategy
        {
            "element_id": _se_id(),
            "tenant_id": tenant_id,
            "element_type": "keyword_strategy",
            "name": "小红书热搜关键词策略",
            "description": "针对小红书平台的热搜关键词布局策略，覆盖核心词、长尾词、场景词三层结构",
            "content": {
                "core_keywords": ["护肤", "美白", "敏感肌"],
                "long_tail": ["敏感肌怎么修复屏障", "平价美白精华推荐"],
                "scene_keywords": ["换季护肤", "熬夜急救", "学生党"],
                "placement": {"title": 1, "body_first": 2, "body_middle": 1, "tags": 3},
            },
            "render_template": "【关键词策略】\n核心词：{{ core_keywords | join('、') }}\n长尾词：{{ long_tail | join('、') }}\n场景词：{{ scene_keywords | join('、') }}\n",
            "variables": json.dumps([
                {"name": "core_keywords", "label": "核心关键词", "type": "array", "default_value": ["护肤", "美白"]},
                {"name": "long_tail", "label": "长尾关键词", "type": "array", "default_value": []},
                {"name": "scene_keywords", "label": "场景关键词", "type": "array", "default_value": []},
            ]),
            "source": "system",
            "platform": platform,
            "content_format": content_format,
            "effectiveness_score": 88.5,
        },
        # structure_framework
        {
            "element_id": _se_id(),
            "tenant_id": tenant_id,
            "element_type": "structure_framework",
            "name": "小红书图文爆款结构",
            "description": "经过数据验证的小红书图文笔记高互动结构：痛点共鸣→解决方案→使用体验→CTA",
            "content": {
                "sections": [
                    {"name": "hook", "label": "痛点共鸣", "length": "30-50字"},
                    {"name": "solution", "label": "解决方案", "length": "80-120字"},
                    {"name": "experience", "label": "使用体验", "length": "100-150字"},
                    {"name": "cta", "label": "行动号召", "length": "20-30字"},
                ]
            },
            "render_template": "【结构框架】\n{% for section in sections %}→ {{ section.label }} ({{ section.length }})\n{% endfor %}",
            "variables": json.dumps([
                {"name": "sections", "label": "章节结构", "type": "array", "default_value": []},
            ]),
            "source": "system",
            "platform": platform,
            "content_format": content_format,
            "effectiveness_score": 92.0,
        },
        # hook_pattern
        {
            "element_id": _se_id(),
            "tenant_id": tenant_id,
            "element_type": "hook_pattern",
            "name": "痛点反问式开场",
            "description": "以用户痛点为切入，用反问句制造共鸣，提升前3秒留存率",
            "content": {
                "templates": [
                    "你是不是也有{{ pain_point }}的困扰？",
                    "为什么别人{{ desired_result }}，你却{{ current_state }}？",
                    "花了{{ money }}买{{ product_type }}，结果{{ bad_result }}？",
                ]
            },
            "render_template": "【Hook 模式】\n{{ templates | random }}\n",
            "variables": json.dumps([
                {"name": "pain_point", "label": "痛点描述", "type": "text", "default_value": "皮肤干燥起皮"},
                {"name": "desired_result", "label": "理想结果", "type": "text", "default_value": "皮肤细腻透亮"},
                {"name": "current_state", "label": "当前状态", "type": "text", "default_value": "毛孔粗大暗沉"},
                {"name": "money", "label": "花费金额", "type": "text", "default_value": "大几千"},
                {"name": "product_type", "label": "产品类型", "type": "text", "default_value": "护肤品"},
                {"name": "bad_result", "label": "负面结果", "type": "text", "default_value": "越用越差"},
            ]),
            "source": "system",
            "platform": platform,
            "content_format": content_format,
            "effectiveness_score": 85.5,
        },
        # emotion_curve
        {
            "element_id": _se_id(),
            "tenant_id": tenant_id,
            "element_type": "emotion_curve",
            "name": "种草文情感曲线",
            "description": "小红书种草笔记的情感波动设计：好奇→共鸣→信任→渴望→行动",
            "content": {
                "curve": [
                    {"point": "开头", "emotion": "好奇", "intensity": 0.8},
                    {"point": "痛点", "emotion": "共鸣", "intensity": 0.9},
                    {"point": "方案", "emotion": "信任", "intensity": 0.7},
                    {"point": "效果", "emotion": "渴望", "intensity": 0.95},
                    {"point": "结尾", "emotion": "行动", "intensity": 0.85},
                ]
            },
            "render_template": "【情感曲线】\n{% for p in curve %}{{ p.point }}: {{ p.emotion }} (强度{{ p.intensity }})\n{% endfor %}",
            "variables": json.dumps([]),
            "source": "system",
            "platform": platform,
            "content_format": content_format,
            "effectiveness_score": 87.0,
        },
        # engagement_formula
        {
            "element_id": _se_id(),
            "tenant_id": tenant_id,
            "element_type": "engagement_formula",
            "name": "高互动公式：提问+投票",
            "description": "在笔记中嵌入互动钩子（提问、投票、求助），显著提升评论率和收藏率",
            "content": {
                "hooks": [
                    {"type": "提问", "template": "你们{{ question }}？评论区告诉我", "placement": "结尾"},
                    {"type": "投票", "template": "A. {{ option_a }}  B. {{ option_b }}", "placement": "正文"},
                    {"type": "求助", "template": "有没有姐妹知道{{ problem }}？求安利", "placement": "正文"},
                ]
            },
            "render_template": "【互动公式】\n{% for h in hooks %}[{{ h.type }}] {{ h.template }} (位置: {{ h.placement }})\n{% endfor %}",
            "variables": json.dumps([
                {"name": "question", "label": "提问内容", "type": "text", "default_value": "用过最好的美白精华是什么"},
                {"name": "option_a", "label": "选项A", "type": "text", "default_value": "平价好用"},
                {"name": "option_b", "label": "选项B", "type": "text", "default_value": "大牌有效"},
                {"name": "problem", "label": "求助问题", "type": "text", "default_value": "怎么淡化痘印"},
            ]),
            "source": "system",
            "platform": platform,
            "content_format": content_format,
            "effectiveness_score": 83.5,
        },
        # scene_anchor
        {
            "element_id": _se_id(),
            "tenant_id": tenant_id,
            "element_type": "scene_anchor",
            "name": "换季护肤场景切入",
            "description": "以具体生活场景作为内容锚点，让笔记更具代入感和真实感",
            "content": {
                "scenes": [
                    {"name": "换季敏感", "description": "春秋交替，皮肤突然泛红发痒", "mood": "焦虑→安心"},
                    {"name": "熬夜急救", "description": "加班/追剧后脸色暗黄", "mood": "疲惫→期待"},
                    {"name": "旅行护肤", "description": "异地水土不服，皮肤状态崩了", "mood": "无助→自信"},
                ]
            },
            "render_template": "【场景切入】\n{% for s in scenes %}场景: {{ s.name }}\n描述: {{ s.description }}\n情绪: {{ s.mood }}\n\n{% endfor %}",
            "variables": json.dumps([
                {"name": "scenes", "label": "场景列表", "type": "array", "default_value": []},
            ]),
            "source": "system",
            "platform": platform,
            "content_format": content_format,
            "effectiveness_score": 80.0,
        },
        # platform_style
        {
            "element_id": _se_id(),
            "tenant_id": tenant_id,
            "element_type": "platform_style",
            "name": "小红书平台语言风格",
            "description": "小红书特有的语言风格：emoji点缀、亲切实测感、避免硬广味",
            "content": {
                "tone": "亲切、真实、种草感",
                "emoji_rules": "标题用1-2个相关emoji，正文每段开头可点缀",
                "avoid": ["绝对化用词", "硬广话术", "过度专业术语"],
                "preferred": ["实测", "自用", "回购", "安利", "姐妹们"],
            },
            "render_template": "【平台风格】\n语调: {{ tone }}\nEmoji规则: {{ emoji_rules }}\n禁用: {{ avoid | join('、') }}\n推荐用词: {{ preferred | join('、') }}\n",
            "variables": json.dumps([]),
            "source": "system",
            "platform": platform,
            "content_format": content_format,
            "effectiveness_score": 90.0,
        },
        # cta_pattern
        {
            "element_id": _se_id(),
            "tenant_id": tenant_id,
            "element_type": "cta_pattern",
            "name": "小红书温和CTA",
            "description": "避免强硬推销，用分享和互动引导用户行动",
            "content": {
                "patterns": [
                    {"type": "收藏", "text": "觉得有用可以先🌟收藏，下次找得到"},
                    {"type": "评论", "text": "有{{ topic }}问题的姐妹评论区聊聊"},
                    {"type": "关注", "text": "关注我，每天分享一个{{ niche }}小技巧"},
                    {"type": "私信", "text": "需要{{ resource }}的宝子可以私信我"},
                ]
            },
            "render_template": "【CTA 模式】\n{% for p in patterns %}[{{ p.type }}] {{ p.text }}\n{% endfor %}",
            "variables": json.dumps([
                {"name": "topic", "label": "话题", "type": "text", "default_value": "护肤"},
                {"name": "niche", "label": "领域", "type": "text", "default_value": "变美"},
                {"name": "resource", "label": "资源", "type": "text", "default_value": "产品清单"},
            ]),
            "source": "system",
            "platform": platform,
            "content_format": content_format,
            "effectiveness_score": 82.0,
        },
    ]

    for seed in seeds:
        session.execute(
            sa.text("""
                INSERT INTO strategy_elements (
                    element_id, tenant_id, element_type, name, description, content,
                    render_template, variables, source, source_content_id,
                    platform, content_format, usage_count, avg_engagement,
                    effectiveness_score, status, created_by, created_at, updated_at
                ) VALUES (
                    :eid, :tenant_id, :etype, :name, :desc, :content,
                    :render_tmpl, :vars, :source, NULL,
                    :platform, :fmt, 0, '{}',
                    :score, 'active', :created_by, :created_at, :updated_at
                )
                ON CONFLICT (element_id) DO NOTHING
            """),
            {
                "eid": seed["element_id"],
                "tenant_id": seed["tenant_id"],
                "etype": seed["element_type"],
                "name": seed["name"],
                "desc": seed["description"],
                "content": json.dumps(seed["content"]),
                "render_tmpl": seed["render_template"],
                "vars": seed["variables"],
                "source": seed["source"],
                "platform": seed["platform"],
                "fmt": seed.get("content_format"),
                "score": seed["effectiveness_score"],
                "created_by": created_by,
                "created_at": now,
                "updated_at": now,
            },
        )

    session.commit()


def downgrade() -> None:
    """Downgrade is not supported for seed migrations."""
    pass
