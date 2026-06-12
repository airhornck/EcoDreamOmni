"""Health Score Skill — v4.0 Phase 9.

基于多维度计算账号健康分。
MVP: 加权评分规则引擎，无 LLM 调用。
"""

from typing import Any, Dict

SKILL_ID = "health_score"
VERSION = "1.0.0"
MODALITY_SUPPORT = {"text": True}
REQUIRES_LLM = False
LLM_MODEL_PREFERENCE = ""

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "account_id": {"type": "string"},
        "platform_id": {"type": "string"},
        "recent_posts_count": {"type": "integer", "default": 0},
        "recent_violations": {"type": "integer", "default": 0},
        "avg_engagement_rate": {"type": "number", "default": 0.0},
        "login_success_rate": {"type": "number", "default": 1.0},
        "days_since_last_post": {"type": "integer", "default": 0},
        "follower_growth_rate": {"type": "number", "default": 0.0},
    },
    "required": ["account_id", "platform_id"],
}

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "health_score": {"type": "integer"},
        "status": {"type": "string"},
        "dimensions": {"type": "array", "items": {"type": "object"}},
        "suggestions": {"type": "array", "items": {"type": "string"}},
    },
}


def _score_activity(posts: int, days_since: int) -> int:
    if posts >= 7 and days_since <= 3:
        return 100
    if posts >= 4 and days_since <= 7:
        return 80
    if posts >= 1 and days_since <= 14:
        return 60
    if days_since <= 30:
        return 40
    return 20


def _score_compliance(violations: int) -> int:
    if violations == 0:
        return 100
    if violations <= 1:
        return 80
    if violations <= 3:
        return 60
    if violations <= 5:
        return 40
    return 20


def _score_engagement(rate: float) -> int:
    if rate >= 0.08:
        return 100
    if rate >= 0.05:
        return 80
    if rate >= 0.03:
        return 60
    if rate >= 0.01:
        return 40
    return 20


def _score_stability(login_rate: float) -> int:
    return int(login_rate * 100)


def _score_growth(growth: float) -> int:
    if growth >= 0.1:
        return 100
    if growth >= 0.05:
        return 80
    if growth >= 0.0:
        return 60
    if growth >= -0.05:
        return 40
    return 20


def execute(context: Dict[str, Any]) -> Dict[str, Any]:
    account_id = context.get("account_id", "")
    platform_id = context.get("platform_id", "")
    posts = context.get("recent_posts_count", 0)
    violations = context.get("recent_violations", 0)
    engagement = context.get("avg_engagement_rate", 0.0)
    login_rate = context.get("login_success_rate", 1.0)
    days_since = context.get("days_since_last_post", 0)
    growth = context.get("follower_growth_rate", 0.0)

    dimensions: list[dict[str, Any]] = [
        {"name": "活跃度", "score": _score_activity(posts, days_since), "weight": 0.25},
        {"name": "合规度", "score": _score_compliance(violations), "weight": 0.25},
        {"name": "互动率", "score": _score_engagement(engagement), "weight": 0.2},
        {"name": "稳定性", "score": _score_stability(login_rate), "weight": 0.15},
        {"name": "成长性", "score": _score_growth(growth), "weight": 0.15},
    ]

    total = sum(float(d["score"]) * float(d["weight"]) for d in dimensions)
    health_score = int(total)

    if health_score >= 80:
        status = "healthy"
    elif health_score >= 60:
        status = "normal"
    elif health_score >= 40:
        status = "warning"
    else:
        status = "critical"

    suggestions = []
    if dimensions[0]["score"] < 60:
        suggestions.append("建议提高发布频率，保持账号活跃")
    if dimensions[1]["score"] < 80:
        suggestions.append("近期有违规记录，建议加强内容合规审核")
    if dimensions[2]["score"] < 60:
        suggestions.append("互动率偏低，建议优化标题和封面提升 CTR")
    if dimensions[3]["score"] < 80:
        suggestions.append("登录稳定性下降，建议检查 Cookie/Token 有效期")
    if dimensions[4]["score"] < 40:
        suggestions.append("粉丝增长放缓，建议分析竞品选题策略")
    if not suggestions:
        suggestions.append("账号健康状况良好，继续保持")

    return {
        "health_score": health_score,
        "status": status,
        "dimensions": dimensions,
        "suggestions": suggestions,
        "account_id": account_id,
        "platform_id": platform_id,
        "skill_id": SKILL_ID,
        "version": VERSION,
    }
