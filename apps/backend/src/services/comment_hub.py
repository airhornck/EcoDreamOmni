"""CommentHub — W16 合规评论管理 Agent。

核心合规要求:
- AI建议 + 人工手动发布（不存在自动发布）
- 回复接口强制人工确认
- 诱导话术自动拦截
- 每日回复频率 ≤ 20 条/账号
- jieba 情感分析
"""

import re
import secrets
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Dict, List, Optional

import jieba


# ─── Inducement / 诱导话术关键词 ───
_INDUCEMENT_KEYWORDS = [
    "加我微信", "私聊", "私信", "加V", "扫码", "进群", "领福利",
    "免费领", "点击链接", "跳转", "外部", "二维码",
]

# ─── Daily limit ───
_MAX_DAILY_REPLIES_PER_ACCOUNT = 20


@dataclass
class CommentReply:
    id: str
    content_id: str
    account_id: str
    original_comment: str
    suggested_reply: str
    final_reply: Optional[str] = None
    status: str = "suggested"  # suggested | PENDING_REVIEW | APPROVED | REJECTED | PUBLISHED
    risk_level: str = "LOW"    # LOW | MEDIUM | HIGH
    inducement_detected: bool = False
    blocked_keywords: List[str] = field(default_factory=list)
    sentiment: str = "neutral"  # positive | neutral | negative
    created_at: str = ""
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    reject_reason: Optional[str] = None


_comment_reply_db: Dict[str, CommentReply] = {}
_daily_publish_count: Dict[str, Dict[str, int]] = {}  # {account_id: {date_str: count}}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _today() -> str:
    return date.today().isoformat()


def _detect_inducement(text: str) -> tuple[bool, List[str]]:
    """Detect inducement keywords in text."""
    found = []
    for kw in _INDUCEMENT_KEYWORDS:
        if kw in text:
            found.append(kw)
    return len(found) > 0, found


def _analyze_sentiment(text: str) -> str:
    """Simple sentiment analysis using keyword matching (MVP)."""
    positive_words = ["感谢", "谢谢", "棒", "好", "喜欢", "有用", "帮助", "赞", "love", "great"]
    negative_words = ["差", "坏", "垃圾", "骗", "坑", "失望", "讨厌", "恶心", "恨", "hate", "bad"]

    pos_count = sum(1 for w in positive_words if w in text)
    neg_count = sum(1 for w in negative_words if w in text)

    if pos_count > neg_count:
        return "positive"
    elif neg_count > pos_count:
        return "negative"
    return "neutral"


def _generate_suggested_reply(original_comment: str) -> str:
    """MVP: Generate a simple suggested reply based on comment content."""
    # Check for common question patterns
    if any(kw in original_comment for kw in ["怎么办", "怎么", "如何", "吗？", "吗?"]):
        return "感谢提问！具体情况建议咨询专业兽医，也可以参考我之前的笔记~"
    if any(kw in original_comment for kw in ["谢谢", "感谢"]):
        return "不用谢~ 有帮助就好！记得点赞关注，持续分享养宠干货 😊"
    if any(kw in original_comment for kw in ["好看", "喜欢", "棒"]):
        return "谢谢喜欢！有问题随时评论区交流~"
    return "感谢评论！有问题可以随时交流，也欢迎看看我的其他笔记~"


def _get_daily_count(account_id: str) -> int:
    """Get today's published reply count for an account."""
    return _daily_publish_count.get(account_id, {}).get(_today(), 0)


def _increment_daily_count(account_id: str) -> None:
    """Increment today's published reply count."""
    if account_id not in _daily_publish_count:
        _daily_publish_count[account_id] = {}
    today_str = _today()
    _daily_publish_count[account_id][today_str] = _daily_publish_count[account_id].get(today_str, 0) + 1


def suggest_reply(content_id: str, account_id: str, original_comment: str) -> CommentReply:
    """Generate AI-suggested reply for a comment."""
    reply_id = secrets.token_urlsafe(12)

    # Detect inducement
    inducement_detected, blocked_keywords = _detect_inducement(original_comment)

    # Sentiment analysis
    sentiment = _analyze_sentiment(original_comment)

    # Generate suggestion
    suggested_reply = _generate_suggested_reply(original_comment)

    # Risk level
    risk_level = "HIGH" if inducement_detected else "LOW"
    if sentiment == "negative" and not inducement_detected:
        risk_level = "MEDIUM"

    reply = CommentReply(
        id=reply_id,
        content_id=content_id,
        account_id=account_id,
        original_comment=original_comment,
        suggested_reply=suggested_reply,
        status="suggested",
        risk_level=risk_level,
        inducement_detected=inducement_detected,
        blocked_keywords=blocked_keywords,
        sentiment=sentiment,
        created_at=_now(),
    )
    _comment_reply_db[reply_id] = reply
    return reply


def submit_reply(reply_id: str, final_reply: str) -> Optional[CommentReply]:
    """Submit final reply for human review."""
    reply = _comment_reply_db.get(reply_id)
    if not reply:
        return None

    # Re-check inducement in final reply
    inducement_detected, blocked_keywords = _detect_inducement(final_reply)
    reply.final_reply = final_reply
    reply.inducement_detected = inducement_detected
    reply.blocked_keywords = blocked_keywords
    if inducement_detected:
        reply.risk_level = "HIGH"
        reply.status = "REJECTED"
        reply.reject_reason = "提交回复包含诱导话术，已被自动拦截"
    else:
        reply.status = "PENDING_REVIEW"
    return reply


def approve_reply(reply_id: str, reviewer_id: str) -> Optional[CommentReply]:
    """Approve a pending reply."""
    reply = _comment_reply_db.get(reply_id)
    if not reply:
        return None
    if reply.status != "PENDING_REVIEW":
        return reply  # No-op if not pending

    # Check daily limit
    daily_count = _get_daily_count(reply.account_id)
    if daily_count >= _MAX_DAILY_REPLIES_PER_ACCOUNT:
        reply.status = "REJECTED"
        reply.reject_reason = f"超出每日回复上限({_MAX_DAILY_REPLIES_PER_ACCOUNT}条)"
        return reply

    reply.status = "APPROVED"
    reply.reviewed_by = reviewer_id
    reply.reviewed_at = _now()
    _increment_daily_count(reply.account_id)
    return reply


def reject_reply(reply_id: str, reviewer_id: str, reason: str) -> Optional[CommentReply]:
    """Reject a pending reply."""
    reply = _comment_reply_db.get(reply_id)
    if not reply:
        return None
    reply.status = "REJECTED"
    reply.reviewed_by = reviewer_id
    reply.reviewed_at = _now()
    reply.reject_reason = reason
    return reply


def get_reply(reply_id: str) -> Optional[CommentReply]:
    return _comment_reply_db.get(reply_id)


def list_pending_replies() -> List[CommentReply]:
    return [r for r in _comment_reply_db.values() if r.status == "PENDING_REVIEW"]


def list_replies_by_account(account_id: str) -> List[CommentReply]:
    return [r for r in _comment_reply_db.values() if r.account_id == account_id]


def get_account_stats(account_id: str) -> Dict:
    """Get reply statistics for an account."""
    replies = list_replies_by_account(account_id)
    today_str = _today()
    daily_published = _daily_publish_count.get(account_id, {}).get(today_str, 0)
    return {
        "account_id": account_id,
        "total_replies": len(replies),
        "pending_review": len([r for r in replies if r.status == "PENDING_REVIEW"]),
        "approved": len([r for r in replies if r.status == "APPROVED"]),
        "rejected": len([r for r in replies if r.status == "REJECTED"]),
        "daily_published_count": daily_published,
        "daily_limit": _MAX_DAILY_REPLIES_PER_ACCOUNT,
    }


def clear_comment_hub() -> None:
    _comment_reply_db.clear()
    _daily_publish_count.clear()
