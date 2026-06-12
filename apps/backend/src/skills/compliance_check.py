"""Compliance Check Skill — v4.0 Phase 8 P8-1.

综合合规检查：L1-L4 规则校验 + 敏感词过滤 + 兽药宣称预检。
MVP: 规则引擎基于静态规则库，无 LLM 调用。

架构红线:
- §2.1 Agent 禁 DB: 本 Skill 为无状态原子能力，输入数据由调用方通过 Function API 提供
- §2.5 LLMHub 路由: requires_llm=False，不调用 LLM
"""

from typing import Any, Dict, List

SKILL_ID = "compliance_check"
VERSION = "1.0.0"
MODALITY_SUPPORT = {"text": True}
REQUIRES_LLM = False
LLM_MODEL_PREFERENCE = ""

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "content": {"type": "string", "description": "待检查的正文内容"},
        "title": {"type": "string", "description": "待检查的标题"},
        "hashtags": {"type": "array", "items": {"type": "string"}, "description": "标签列表"},
        "platform_id": {"type": "string", "description": "平台标识: xhs / douyin / bilibili / wechat_official"},
        "content_type": {"type": "string", "description": "内容类型: note_image / note_video / video_clone / long_article"},
        "brand_id": {"type": "string", "description": "品牌ID，用于品牌一致性校验"},
    },
    "required": ["content", "platform_id"],
}

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "passed": {"type": "boolean"},
        "risk_level": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
        "violations": {"type": "array", "items": {"type": "object"}},
        "suggestions": {"type": "array", "items": {"type": "string"}},
        "check_items": {"type": "array", "items": {"type": "object"}},
    },
}

# MVP static rule bases
_SENSITIVE_WORDS: Dict[str, List[str]] = {
    "universal": ["最", "第一", "顶级", "国家级", "绝对", "万能", "特效"],
    "xhs": ["诱导点赞", "虚假种草", "医美化", "非法药品"],
    "douyin": ["诱导关注", "虚假宣传", "未成年人", "危险行为"],
    "bilibili": ["引战", "人身攻击", "色情低俗", "政治敏感"],
    "wechat_official": ["诱导分享", "虚假标题", "侵权", "谣言"],
}

_LENGTH_LIMITS: Dict[str, Dict[str, int]] = {
    "xhs": {"title_min": 1, "title_max": 20, "body_min": 10, "body_max": 1000, "hashtag_max": 10},
    "douyin": {"title_min": 1, "title_max": 55, "body_min": 0, "body_max": 500, "hashtag_max": 5},
    "bilibili": {"title_min": 1, "title_max": 80, "body_min": 0, "body_max": 2000, "hashtag_max": 10},
    "wechat_official": {"title_min": 1, "title_max": 64, "body_min": 100, "body_max": 20000, "hashtag_max": 0},
}

_VETDRUG_KEYWORDS: List[str] = ["驱虫", "疫苗", "抗生素", "消炎", "治疗", "治愈", "疗效", "处方", "兽药字"]


def _check_sensitive_words(text: str, platform_id: str) -> List[Dict[str, Any]]:
    violations = []
    words_to_check = _SENSITIVE_WORDS.get("universal", []) + _SENSITIVE_WORDS.get(platform_id, [])
    for word in words_to_check:
        if word in text:
            violations.append({
                "type": "sensitive_word",
                "level": "L2",
                "target": word,
                "message": f"内容包含敏感词「{word}」，建议修改或删除",
                "position": text.find(word),
            })
    return violations


def _check_length(title: str, content: str, hashtags: List[str], platform_id: str) -> List[Dict[str, Any]]:
    violations = []
    limits = _LENGTH_LIMITS.get(platform_id, _LENGTH_LIMITS["xhs"])

    if len(title) > limits["title_max"]:
        violations.append({
            "type": "length_violation",
            "level": "L1",
            "target": "title",
            "message": f"标题长度 {len(title)} 超过平台限制 {limits['title_max']} 字",
            "actual": len(title),
            "limit": limits["title_max"],
        })

    if len(content) > limits["body_max"]:
        violations.append({
            "type": "length_violation",
            "level": "L1",
            "target": "content",
            "message": f"正文长度 {len(content)} 超过平台限制 {limits['body_max']} 字",
            "actual": len(content),
            "limit": limits["body_max"],
        })

    if hashtags and len(hashtags) > limits["hashtag_max"]:
        violations.append({
            "type": "length_violation",
            "level": "L1",
            "target": "hashtags",
            "message": f"标签数量 {len(hashtags)} 超过平台限制 {limits['hashtag_max']} 个",
            "actual": len(hashtags),
            "limit": limits["hashtag_max"],
        })

    return violations


def _check_vetdrug_claims(content: str) -> List[Dict[str, Any]]:
    violations = []
    lower_content = content.lower()
    for keyword in _VETDRUG_KEYWORDS:
        if keyword in lower_content:
            # MVP: flag for manual review; Phase 2 will cross-check VetDrugDB
            violations.append({
                "type": "vetdrug_claim",
                "level": "L3",
                "target": keyword,
                "message": f"内容包含兽药相关宣称「{keyword}」，需校验批文一致性",
                "requires_vetdrug_validation": True,
            })
    return violations


def _calculate_risk_level(violations: List[Dict[str, Any]]) -> str:
    levels = [v["level"] for v in violations]
    if "L4" in levels or "critical" in levels:
        return "critical"
    if "L3" in levels:
        return "high"
    if "L2" in levels:
        return "medium"
    if "L1" in levels:
        return "low"
    return "low"


def execute(context: Dict[str, Any]) -> Dict[str, Any]:
    content = context.get("content", "")
    title = context.get("title", "")
    hashtags = context.get("hashtags", [])
    platform_id = context.get("platform_id", "xhs")

    all_violations: List[Dict[str, Any]] = []

    # L2: 敏感词检查
    all_violations.extend(_check_sensitive_words(title + content, platform_id))

    # L1: 长度限制检查
    all_violations.extend(_check_length(title, content, hashtags, platform_id))

    # L3: 兽药宣称预检
    all_violations.extend(_check_vetdrug_claims(content))

    # Deduplicate by target
    seen = set()
    unique_violations = []
    for v in all_violations:
        key = (v["type"], v.get("target", ""))
        if key not in seen:
            seen.add(key)
            unique_violations.append(v)

    risk_level = _calculate_risk_level(unique_violations)
    passed = risk_level not in ("high", "critical")

    # Generate suggestions
    suggestions = []
    if any(v["type"] == "sensitive_word" for v in unique_violations):
        suggestions.append("建议替换绝对化用语，使用客观描述替代「最」「第一」等词汇")
    if any(v["type"] == "length_violation" for v in unique_violations):
        suggestions.append("建议调整内容长度以符合平台规范")
    if any(v["type"] == "vetdrug_claim" for v in unique_violations):
        suggestions.append("建议补充兽药批文号并确保宣称与批文一致，或提交 vetdrug_claim_validate 进一步校验")
    if not suggestions:
        suggestions.append("内容合规，建议继续下一步发布流程")

    # Check items summary
    check_items = [
        {"name": "L1 长度规范", "passed": not any(v["type"] == "length_violation" for v in unique_violations)},
        {"name": "L2 敏感词过滤", "passed": not any(v["type"] == "sensitive_word" for v in unique_violations)},
        {"name": "L3 兽药宣称预检", "passed": not any(v["type"] == "vetdrug_claim" for v in unique_violations)},
        {"name": "L4 动态风险", "passed": True, "note": "MVP 未启用动态风险模型"},
    ]

    return {
        "passed": passed,
        "risk_level": risk_level,
        "violations": unique_violations,
        "suggestions": suggestions,
        "check_items": check_items,
        "skill_id": SKILL_ID,
        "version": VERSION,
    }
