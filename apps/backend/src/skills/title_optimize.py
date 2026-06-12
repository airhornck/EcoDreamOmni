"""Title Optimize Skill — v4.0 Phase 3 P3-2.

Optimize titles for engagement.
MVP: Rule-based title enhancement, no LLM call.
"""

import secrets
from typing import Any, Dict, List

SKILL_ID = "title_optimize"
VERSION = "1.0.0"
MODALITY_SUPPORT = {"text": True}
REQUIRES_LLM = True
LLM_MODEL_PREFERENCE = "qwen-turbo"

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "keywords": {"type": "array", "items": {"type": "string"}},
        "platform": {"type": "string"},
    },
    "required": ["title"],
}

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "variants": {"type": "array", "items": {"type": "string"}},
        "best_index": {"type": "integer"},
        "reason": {"type": "string"},
    },
}


def execute(context: Dict[str, Any]) -> Dict[str, Any]:
    title = context.get("title", "")
    keywords = context.get("keywords", [])
    platform = context.get("platform", "xhs")

    variants = [title]

    # Add keyword if present
    if keywords:
        variants.append(f"{' '.join(keywords[:2])} | {title}")

    # Platform-specific patterns
    if platform == "xhs":
        variants.append(f"🔥 {title}")
        variants.append(f"建议收藏！{title}")
    elif platform == "douyin":
        variants.append(f"#{keywords[0] if keywords else '热门'} {title}")

    # Deduplicate
    variants = list(dict.fromkeys(variants))

    return {
        "variants": variants,
        "best_index": 0,
        "reason": "First variant preserves original intent",
    }
