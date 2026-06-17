"""Keyword Inject Skill — v4.0 Phase 3 P3-2/P3-3.

Inject platform-recommended keywords into content.
Reads PlatformContentTypeStyle.recommended_keywords.
MVP: Static keyword pool, no DB access.
"""

from typing import Any, Dict, List

SKILL_ID = "keyword_inject"
VERSION = "1.0.0"
MODALITY_SUPPORT = {"text": True}
REQUIRES_LLM = False
LLM_MODEL_PREFERENCE = ""

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "content": {"type": "string"},
        "topic": {"type": "string"},
        "platform_id": {"type": "string"},
        "content_type": {"type": "string"},
    },
    "required": ["content", "topic"],
}

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "prompt_fragments": {"type": "array", "items": {"type": "string"}},
        "injected_keywords": {"type": "array", "items": {"type": "string"}},
        "injected_count": {"type": "integer"},
    },
}

# MVP static keyword pools by topic
_KEYWORD_POOLS: Dict[str, List[str]] = {
    "宠物": ["养宠攻略", "科学养宠", "宠物健康", "铲屎官日常", "萌宠"],
    "美食": ["美食探店", "自制美食", "吃货日常", "美食教程", "深夜食堂"],
    "旅行": ["旅行攻略", "小众景点", "打卡圣地", "旅行日记", "说走就走"],
    "美妆": ["妆容教程", "护肤分享", "好物推荐", "变美秘籍", "素颜神器"],
}


def execute(context: Dict[str, Any]) -> Dict[str, Any]:
    context.get("content", "")
    topic = context.get("topic", "")
    platform_id = context.get("platform_id", "xhs")

    # Select keywords
    keywords = []
    for key_topic, pool in _KEYWORD_POOLS.items():
        if key_topic in topic:
            keywords = pool[:3]
            break
    if not keywords:
        keywords = ["热门推荐", "精选内容", "必看"]

    fragments = [f"推荐融入关键词：{', '.join(keywords)}"]
    if platform_id == "xhs":
        fragments.append(f"小红书热门标签建议：#{keywords[0]} #{keywords[1] if len(keywords) > 1 else '好物'}")

    return {
        "prompt_fragments": fragments,
        "injected_keywords": keywords,
        "injected_count": len(keywords),
    }
