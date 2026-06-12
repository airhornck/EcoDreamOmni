"""XHS Note Data Extraction Skill — v4.0 Phase 9.

采集小红书笔记数据用于趋势分析。
MVP: 解析笔记链接/ID，返回结构化数据（Mock 数据，不调用真实爬虫）。
"""

from typing import Any, Dict

SKILL_ID = "xhs_note_data_extraction"
VERSION = "1.0.0"
MODALITY_SUPPORT = {"text": True}
REQUIRES_LLM = False
LLM_MODEL_PREFERENCE = ""

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "note_url": {"type": "string"},
        "note_id": {"type": "string"},
        "extract_engagement": {"type": "boolean", "default": True},
        "extract_content": {"type": "boolean", "default": True},
    },
    "required": [],
}

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "note_id": {"type": "string"},
        "title": {"type": "string"},
        "author": {"type": "string"},
        "content": {"type": "string"},
        "images_count": {"type": "integer"},
        "hashtags": {"type": "array", "items": {"type": "string"}},
        "engagement": {"type": "object"},
        "published_at": {"type": "string"},
        "category": {"type": "string"},
    },
}


def _parse_note_id(url: str) -> str:
    """Extract note ID from XHS URL."""
    if not url:
        return ""
    # MVP: simple extraction
    if "/explore/" in url:
        return url.split("/explore/")[-1].split("?")[0].split("#")[0]
    if "/note/" in url:
        return url.split("/note/")[-1].split("?")[0].split("#")[0]
    return url.strip("/").split("/")[-1][:16]


def _mock_extract(note_id: str) -> Dict[str, Any]:
    """Return mock data for MVP."""
    return {
        "note_id": note_id or "mock_note_001",
        "title": "养猫三年总结的10个避坑指南",
        "author": "省钱狗爸",
        "content": "1. 猫粮别贪便宜... 2. 驱虫要定时...",
        "images_count": 9,
        "hashtags": ["新手养猫", "养宠攻略", "避坑指南"],
        "engagement": {
            "likes": 3456,
            "collects": 1234,
            "comments": 567,
            "shares": 89,
        },
        "published_at": "2026-05-15T08:30:00+08:00",
        "category": "宠物/养猫",
        "is_mock": True,
        "note": "MVP 返回模拟数据，生产环境需接入真实爬虫或第三方 API",
    }


def execute(context: Dict[str, Any]) -> Dict[str, Any]:
    note_url = context.get("note_url", "")
    note_id = context.get("note_id", "")
    extract_engagement = context.get("extract_engagement", True)
    extract_content = context.get("extract_content", True)

    if not note_id and note_url:
        note_id = _parse_note_id(note_url)

    result = _mock_extract(note_id)

    # Filter based on request
    if not extract_engagement:
        result.pop("engagement", None)
    if not extract_content:
        result.pop("content", None)

    return {
        **result,
        "skill_id": SKILL_ID,
        "version": VERSION,
    }
