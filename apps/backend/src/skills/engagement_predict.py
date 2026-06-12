"""Engagement Predict Skill — v4.0 Phase 9.

预测点赞/评论/收藏区间。
MVP: 基于内容特征和历史数据的规则引擎，无 LLM 调用。
"""

from typing import Any, Dict

SKILL_ID = "engagement_predict"
VERSION = "1.0.0"
MODALITY_SUPPORT = {"text": True}
REQUIRES_LLM = False
LLM_MODEL_PREFERENCE = ""

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "content": {"type": "string"},
        "platform_id": {"type": "string"},
        "account_followers": {"type": "integer", "default": 1000},
        "historical_avg_likes": {"type": "integer", "default": 0},
    },
    "required": ["title", "content", "platform_id"],
}

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "predicted_likes": {"type": "object"},
        "predicted_comments": {"type": "object"},
        "predicted_saves": {"type": "object"},
        "predicted_shares": {"type": "object"},
        "confidence": {"type": "string"},
        "factors": {"type": "array", "items": {"type": "string"}},
    },
}


def _score_content(content: str, title: str) -> Dict[str, float]:
    """Score content quality heuristically."""
    scores = {"hook": 0.5, "emotion": 0.5, "practical": 0.5, "visual": 0.5}

    # Hook score: numbers, questions, pain points
    if any(c in title for c in "123456789"):
        scores["hook"] += 0.2
    if "?" in title or "？" in title:
        scores["hook"] += 0.1
    if any(w in title for w in ["坑", "踩", "雷", "避", "别", "不要"]):
        scores["hook"] += 0.15

    # Emotion score: empathy, urgency
    if any(w in content for w in ["心疼", "感动", "惊喜", "焦虑", "急"]):
        scores["emotion"] += 0.2

    # Practical score: actionable, step-by-step
    if any(w in content for w in ["第一步", "步骤", "教程", "攻略", "方法"]):
        scores["practical"] += 0.2

    # Visual score: mentions images/video
    if any(w in content for w in ["图", "视频", "封面", "配图"]):
        scores["visual"] += 0.15

    return {k: min(v, 1.0) for k, v in scores.items()}


def _predict_range(base: int, quality_score: float, platform_id: str) -> Dict[str, int]:
    """Predict engagement range based on base followers and quality."""
    platform_multipliers = {
        "xhs": 1.0,
        "douyin": 1.5,
        "bilibili": 0.8,
        "wechat_official": 0.6,
    }
    mult = platform_multipliers.get(platform_id, 1.0)

    # Base rate: 2-8% of followers for likes
    low_rate = 0.02 * quality_score * mult
    high_rate = 0.08 * quality_score * mult

    low = int(base * low_rate)
    high = int(base * high_rate)
    median = (low + high) // 2

    return {"low": max(low, 1), "median": max(median, 1), "high": max(high, 1)}


def execute(context: Dict[str, Any]) -> Dict[str, Any]:
    title = context.get("title", "")
    content = context.get("content", "")
    platform_id = context.get("platform_id", "xhs")
    followers = context.get("account_followers", 1000)
    hist_avg = context.get("historical_avg_likes", 0)

    # Use historical average as base if available
    base = hist_avg if hist_avg > 0 else followers

    scores = _score_content(content, title)
    quality_score = sum(scores.values()) / len(scores)

    likes = _predict_range(base, quality_score, platform_id)
    comments = {"low": max(likes["low"] // 5, 1), "median": likes["median"] // 5, "high": likes["high"] // 3}
    saves = {"low": max(likes["low"] // 4, 1), "median": likes["median"] // 4, "high": likes["high"] // 2}
    shares = {"low": max(likes["low"] // 10, 1), "median": likes["median"] // 10, "high": likes["high"] // 5}

    confidence = "high" if quality_score > 0.75 else "medium" if quality_score > 0.5 else "low"

    factors = []
    if scores["hook"] > 0.7:
        factors.append("标题钩子强，预计点击率较高")
    if scores["practical"] > 0.7:
        factors.append("内容实用性强，预计收藏率高")
    if scores["emotion"] > 0.7:
        factors.append("情感共鸣强，预计评论活跃")
    if not factors:
        factors.append("内容中规中矩，预测基于账号基线数据")

    return {
        "predicted_likes": likes,
        "predicted_comments": comments,
        "predicted_saves": saves,
        "predicted_shares": shares,
        "confidence": confidence,
        "factors": factors,
        "quality_score": round(quality_score, 2),
        "skill_id": SKILL_ID,
        "version": VERSION,
    }
