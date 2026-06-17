"""Content Structural Analysis Skill — v4.0 Phase 3 P3-2.

Parse content structure into hook / body / CTA segments.
MVP: Rule-based segmentation, no LLM call.
"""

from typing import Any, Dict

SKILL_ID = "content_structural_analysis"
VERSION = "1.0.0"
MODALITY_SUPPORT = {"text": True}
REQUIRES_LLM = False
LLM_MODEL_PREFERENCE = ""

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "content": {"type": "string", "description": "Raw content text"},
        "platform": {"type": "string", "description": "Target platform (xhs/douyin/etc)"},
    },
    "required": ["content"],
}

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "hook": {"type": "string"},
        "body": {"type": "string"},
        "cta": {"type": "string"},
        "structure_type": {"type": "string"},
    },
}


def execute(context: Dict[str, Any]) -> Dict[str, Any]:
    content = context.get("content", "")
    platform = context.get("platform", "xhs")

    lines = [line.strip() for line in content.split("\n") if line.strip()]
    if not lines:
        return {"hook": "", "body": "", "cta": "", "structure_type": "empty"}

    # Heuristic segmentation
    hook = lines[0]
    cta = ""
    body_lines = lines[1:]

    # Detect CTA patterns
    cta_patterns = ["关注", "点赞", "收藏", "评论", "私信", "加群", "扫码", "点击", "了解更多"]
    if body_lines and any(p in body_lines[-1] for p in cta_patterns):
        cta = body_lines[-1]
        body_lines = body_lines[:-1]

    body = "\n".join(body_lines)

    # Determine structure type
    structure_type = "standard"
    if platform == "xhs":
        if len(lines) <= 3:
            structure_type = "short_note"
        elif "|" in content or "·" in content:
            structure_type = "listicle"

    return {
        "hook": hook,
        "body": body,
        "cta": cta,
        "structure_type": structure_type,
    }
