"""Persona Story Context Skill — v4.0 Phase 3 P3-3.

Inject persona story context into content generation.
MVP: Static persona templates, no DB access.
"""

from typing import Any, Dict

SKILL_ID = "persona_story_context"
VERSION = "1.0.0"
MODALITY_SUPPORT = {"text": True}
REQUIRES_LLM = False
LLM_MODEL_PREFERENCE = ""

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "persona_id": {"type": "string"},
        "content_type": {"type": "string"},
        "topic": {"type": "string"},
    },
    "required": ["persona_id", "topic"],
}

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "persona_intro": {"type": "string"},
        "story_fragments": {"type": "array", "items": {"type": "string"}},
        "tone_guidance": {"type": "string"},
    },
}

_PERSONA_TEMPLATES: Dict[str, Dict[str, str]] = {
    "pet_expert": {
        "intro": "作为一名有10年经验的宠物行为专家，我用科学方法帮你解决养宠难题。",
        "tone": "专业、亲切、有温度",
    },
    "foodie": {
        "intro": "吃货小达人，走街串巷为你寻找最地道的美味。",
        "tone": "活泼、真实、有感染力",
    },
    "traveler": {
        "intro": "背包客小A，已经走过30个国家，只分享最真实的旅行体验。",
        "tone": "自由、探索、有画面感",
    },
}


def execute(context: Dict[str, Any]) -> Dict[str, Any]:
    persona_id = context.get("persona_id", "pet_expert")
    topic = context.get("topic", "")

    persona = _PERSONA_TEMPLATES.get(persona_id, _PERSONA_TEMPLATES["pet_expert"])

    story_fragments = [
        persona["intro"],
        f"今天想和大家聊聊{topic}。",
        f"我的风格是：{persona['tone']}。",
    ]

    return {
        "persona_intro": persona["intro"],
        "story_fragments": story_fragments,
        "tone_guidance": persona["tone"],
    }
