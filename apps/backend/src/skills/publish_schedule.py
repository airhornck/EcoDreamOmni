"""Publish Schedule Skill — v4.0 Phase 9.

基于最佳时段算法计算发布时机。
MVP: 规则引擎 + 平台时段库，无 LLM 调用。
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

SKILL_ID = "publish_schedule"
VERSION = "1.0.0"
MODALITY_SUPPORT = {"text": True}
REQUIRES_LLM = False
LLM_MODEL_PREFERENCE = ""

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "platform_id": {"type": "string"},
        "content_type": {"type": "string"},
        "target_audience": {"type": "string"},
        "prefer_immediate": {"type": "boolean", "default": False},
        "earliest_time": {"type": "string", "description": "ISO datetime"},
    },
    "required": ["platform_id"],
}

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "recommended_time": {"type": "string"},
        "recommended_hour": {"type": "integer"},
        "reason": {"type": "string"},
        "alternative_slots": {"type": "array", "items": {"type": "object"}},
        "timezone": {"type": "string"},
    },
}

# Platform optimal posting windows (hour ranges, local time)
_PLATFORM_SLOTS: Dict[str, List[Dict[str, Any]]] = {
    "xhs": [
        {"hours": [7, 8, 9], "label": "早高峰", "score": 85, "reason": "通勤刷笔记高峰"},
        {"hours": [12, 13], "label": "午间", "score": 80, "reason": "午休浏览时段"},
        {"hours": [18, 19, 20, 21], "label": "晚间黄金", "score": 95, "reason": "晚饭后黄金浏览时段"},
        {"hours": [22, 23], "label": "深夜", "score": 70, "reason": "睡前浏览"},
    ],
    "douyin": [
        {"hours": [7, 8], "label": "早间", "score": 70, "reason": "起床刷视频"},
        {"hours": [12, 13], "label": "午间", "score": 80, "reason": "午休刷视频"},
        {"hours": [18, 19, 20, 21, 22], "label": "晚间黄金", "score": 95, "reason": "晚饭后至睡前高峰"},
    ],
    "bilibili": [
        {"hours": [12, 13], "label": "午间", "score": 75, "reason": "午休刷B站"},
        {"hours": [18, 19, 20, 21, 22, 23], "label": "晚间", "score": 90, "reason": "晚间长视频消费高峰"},
        {"hours": [0, 1], "label": "深夜", "score": 65, "reason": "深夜党活跃"},
    ],
    "wechat_official": [
        {"hours": [7, 8, 9], "label": "早间", "score": 90, "reason": "上班路上读公众号"},
        {"hours": [12, 13], "label": "午间", "score": 85, "reason": "午休阅读"},
        {"hours": [18, 19, 20, 21], "label": "晚间", "score": 80, "reason": "下班后阅读"},
    ],
}


def _next_slot(hours: List[int], earliest: datetime) -> datetime:
    """Find the next occurrence of one of the given hours."""
    candidate = earliest.replace(minute=0, second=0, microsecond=0)
    for _ in range(48):  # search up to 48 hours
        if candidate.hour in hours and candidate >= earliest:
            return candidate
        candidate += timedelta(hours=1)
    return earliest


def execute(context: Dict[str, Any]) -> Dict[str, Any]:
    platform_id = context.get("platform_id", "xhs")
    prefer_immediate = context.get("prefer_immediate", False)
    earliest_str = context.get("earliest_time", "")

    if earliest_str:
        try:
            earliest = datetime.fromisoformat(earliest_str.replace("Z", "+00:00"))
        except ValueError:
            earliest = datetime.now(timezone.utc)
    else:
        earliest = datetime.now(timezone.utc)

    slots = _PLATFORM_SLOTS.get(platform_id, _PLATFORM_SLOTS["xhs"])

    if prefer_immediate:
        # Return next available slot
        best = min(slots, key=lambda s: _next_slot(s["hours"], earliest))
    else:
        # Return highest score slot
        best = max(slots, key=lambda s: s["score"])

    recommended = _next_slot(best["hours"], earliest)

    alternatives = []
    for slot in sorted(slots, key=lambda s: s["score"], reverse=True)[:3]:
        if slot["label"] != best["label"]:
            alt_time = _next_slot(slot["hours"], earliest)
            alternatives.append({
                "time": alt_time.isoformat(),
                "hour": alt_time.hour,
                "label": slot["label"],
                "score": slot["score"],
                "reason": slot["reason"],
            })

    return {
        "recommended_time": recommended.isoformat(),
        "recommended_hour": recommended.hour,
        "reason": f"{best['label']} — {best['reason']}（平台: {platform_id}）",
        "alternative_slots": alternatives,
        "timezone": "UTC",
        "skill_id": SKILL_ID,
        "version": VERSION,
    }
