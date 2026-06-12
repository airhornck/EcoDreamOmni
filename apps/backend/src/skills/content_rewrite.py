"""Content Rewrite Skill — v4.0 Phase 3 P3-2.

Rewrite content with style transformation.
MVP: Rule-based rewriting, no LLM call.
"""

from typing import Any, Dict

SKILL_ID = "content_rewrite"
VERSION = "1.0.0"
MODALITY_SUPPORT = {"text": True}
REQUIRES_LLM = True
LLM_MODEL_PREFERENCE = "qwen-turbo"

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "content": {"type": "string"},
        "style": {"type": "string", "enum": ["casual", "professional", "humorous", "emotional"]},
        "tone_preset": {"type": "object"},
    },
    "required": ["content", "style"],
}

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "rewritten": {"type": "string"},
        "changes": {"type": "array", "items": {"type": "string"}},
    },
}


def execute(context: Dict[str, Any]) -> Dict[str, Any]:
    content = context.get("content", "")
    style = context.get("style", "casual")

    # MVP: Simple rule-based transformations
    transformations = {
        "casual": lambda t: t.replace("您", "你").replace("非常", "超"),
        "professional": lambda t: t.replace("超", "非常").replace("棒", "优秀"),
        "humorous": lambda t: t + " 😂",
        "emotional": lambda t: t.replace("！", "！！！").replace("?", "？！"),
    }

    rewritten = transformations.get(style, lambda t: t)(content)
    changes = [f"Applied style: {style}"]

    return {"rewritten": rewritten, "changes": changes}
