"""ContentSeries — W16 内容系列化引擎。

核心能力:
- 系列上下文注入（{{series.prev_content}}）
- 单账号内前后文呼应
- 矩阵互评互赞代码层拦截
"""

import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class ContentSeries:
    id: str
    name: str
    account_id: str
    stage_sequence: List[str]
    contents: List[Dict] = field(default_factory=list)  # [{content_draft_id, stage, added_at}]
    status: str = "active"  # active | archived
    created_at: str = ""


_series_db: Dict[str, ContentSeries] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _seed_series():
    """Seed default content series for MVP."""
    if _series_db:
        return
    defaults = [
        {
            "name": "新手养宠入门系列",
            "account_id": "",
            "stage_sequence": ["认知", "兴趣", "信任", "行动"],
        },
        {
            "name": "宠物健康知识科普",
            "account_id": "",
            "stage_sequence": ["问题引入", "知识讲解", "实操建议", "总结提醒"],
        },
        {
            "name": "素人养宠日常记录",
            "account_id": "",
            "stage_sequence": ["早晨", "白天", "傍晚", "夜晚"],
        },
    ]
    for data in defaults:
        series = ContentSeries(
            id=secrets.token_urlsafe(12),
            name=data["name"],
            account_id=data["account_id"],
            stage_sequence=data["stage_sequence"],
            created_at=_now(),
        )
        _series_db[series.id] = series


_seed_series()


def create_series(name: str, account_id: str, stage_sequence: List[str]) -> ContentSeries:
    series = ContentSeries(
        id=secrets.token_urlsafe(12),
        name=name,
        account_id=account_id,
        stage_sequence=stage_sequence,
        created_at=_now(),
    )
    _series_db[series.id] = series
    return series


def get_series(series_id: str) -> Optional[ContentSeries]:
    return _series_db.get(series_id)


def list_series(account_id: Optional[str] = None) -> List[ContentSeries]:
    all_series = list(_series_db.values())
    if account_id:
        return [s for s in all_series if s.account_id == account_id]
    return all_series


def add_content_to_series(series_id: str, content_draft_id: str, stage: str) -> Optional[ContentSeries]:
    series = _series_db.get(series_id)
    if not series:
        return None
    series.contents.append({
        "content_draft_id": content_draft_id,
        "stage": stage,
        "added_at": _now(),
    })
    return series


def get_series_context(series_id: str, content_draft_id: str) -> Optional[Dict]:
    """Get series context for a content draft, including previous content."""
    series = _series_db.get(series_id)
    if not series:
        return None

    # Find current index
    current_index = -1
    for i, c in enumerate(series.contents):
        if c["content_draft_id"] == content_draft_id:
            current_index = i
            break

    if current_index == -1:
        return None

    prev_content = None
    if current_index > 0:
        prev = series.contents[current_index - 1]
        prev_content = {
            "content_draft_id": prev["content_draft_id"],
            "stage": prev["stage"],
            "summary": f"上一篇内容（{prev['stage']}阶段）",
        }

    next_content = None
    if current_index < len(series.contents) - 1:
        nxt = series.contents[current_index + 1]
        next_content = {
            "content_draft_id": nxt["content_draft_id"],
            "stage": nxt["stage"],
            "summary": f"下一篇内容（{nxt['stage']}阶段）",
        }

    return {
        "series_id": series.id,
        "series_name": series.name,
        "account_id": series.account_id,
        "current_stage": series.contents[current_index]["stage"],
        "current_index": current_index,
        "total_contents": len(series.contents),
        "prev_content": prev_content,
        "next_content": next_content,
        "prev_summary": prev_content["summary"] if prev_content else "（系列第一篇）",
        "stage_sequence": series.stage_sequence,
    }


def check_engagement_allowed(account_ids: List[str], action: str) -> Dict:
    """Check if engagement action is allowed between accounts.

    Returns:
        {"allowed": bool, "reason": str}
    """
    # Block mutual engagement between different accounts in matrix
    if action in ("mutual_like_comment", "cross_like", "cross_comment"):
        if len(account_ids) >= 2:
            return {
                "allowed": False,
                "reason": "matrix_mutual_engagement: 禁止矩阵账号互评互赞",
            }

    # Self-reply is allowed within single account
    if action == "self_reply" and len(account_ids) == 1:
        return {"allowed": True, "reason": "单账号内互动允许"}

    # Default: allow
    return {"allowed": True, "reason": "操作允许"}


def clear_content_series() -> None:
    _series_db.clear()
