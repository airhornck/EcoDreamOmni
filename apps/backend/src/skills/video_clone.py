"""Video Clone Skill — v4.0 Phase 3 P3-2.

Clone video structure and style from reference.
MVP: Return script/template structure (actual video generation in production).
"""

from typing import Any, Dict

SKILL_ID = "video_clone"
VERSION = "1.0.0"
MODALITY_SUPPORT = {"text": True, "video": True}
REQUIRES_LLM = True
LLM_MODEL_PREFERENCE = "qwen-turbo"

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "reference_url": {"type": "string"},
        "topic": {"type": "string"},
        "duration_seconds": {"type": "integer"},
        "platform": {"type": "string"},
    },
    "required": ["topic"],
}

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "script_segments": {"type": "array"},
        "shot_list": {"type": "array"},
        "music_suggestion": {"type": "string"},
    },
}


def execute(context: Dict[str, Any]) -> Dict[str, Any]:
    topic = context.get("topic", "")
    duration = context.get("duration_seconds", 60)
    platform = context.get("platform", "douyin")

    # Segment duration
    seg_duration = 15 if platform == "douyin" else 30
    num_segments = max(1, duration // seg_duration)

    script_segments = []
    for i in range(num_segments):
        script_segments.append({
            "index": i + 1,
            "timestamp": f"{i * seg_duration}s",
            "hook": f"【第{i+1}段】{topic}要点{i+1}",
            "visual": "中景 + 动态文字",
            "duration": seg_duration,
        })

    shot_list = [
        {"type": "opening", "description": "3s 强钩子画面"},
        {"type": "body", "description": "主体内容展示"},
        {"type": "ending", "description": "CTA 引导关注"},
    ]

    music_map = {"douyin": "节奏感强的电子音乐", "xhs": "轻快治愈系背景音乐"}

    return {
        "script_segments": script_segments,
        "shot_list": shot_list,
        "music_suggestion": music_map.get(platform, "通用背景音乐"),
    }
