"""Brand Consistency Check Skill — v4.0 Phase 9.

校验内容与品牌知识库的一致性。
MVP: 关键词匹配 + 品牌调性规则引擎，无 LLM 调用。
"""

from typing import Any, Dict, List

SKILL_ID = "brand_consistency_check"
VERSION = "1.0.0"
MODALITY_SUPPORT = {"text": True}
REQUIRES_LLM = False
LLM_MODEL_PREFERENCE = ""

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "content": {"type": "string"},
        "title": {"type": "string"},
        "brand_name": {"type": "string"},
        "brand_keywords": {"type": "array", "items": {"type": "string"}},
        "brand_tone": {"type": "string"},
        "prohibited_phrases": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["content", "brand_name"],
}

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "consistent": {"type": "boolean"},
        "score": {"type": "number"},
        "issues": {"type": "array", "items": {"type": "object"}},
        "suggestions": {"type": "array", "items": {"type": "string"}},
    },
}


def _check_brand_keywords(text: str, brand_keywords: List[str]) -> List[Dict[str, Any]]:
    issues = []
    for kw in brand_keywords:
        if kw not in text:
            issues.append({
                "type": "missing_keyword",
                "target": kw,
                "message": f"建议融入品牌关键词「{kw}」",
                "severity": "suggest",
            })
    return issues


def _check_prohibited_phrases(text: str, prohibited: List[str]) -> List[Dict[str, Any]]:
    issues = []
    for phrase in prohibited:
        if phrase in text:
            issues.append({
                "type": "prohibited_phrase",
                "target": phrase,
                "message": f"包含品牌禁用表述「{phrase}」",
                "severity": "warn",
            })
    return issues


def _check_tone_match(text: str, expected_tone: str) -> List[Dict[str, Any]]:
    issues = []
    # MVP: simple heuristic rules
    tone_rules = {
        "professional": ["太随意", "口语化", "emoji 过多"],
        "casual": ["过于正式", "生硬", "套话"],
        "luxury": ["廉价感", "打折", "便宜"],
        "young": ["老套", "过时", "严肃"],
    }
    for bad_signal in tone_rules.get(expected_tone, []):
        if bad_signal in text:
            issues.append({
                "type": "tone_mismatch",
                "target": bad_signal,
                "message": f"语气可能与「{expected_tone}」品牌调性不符：包含「{bad_signal}」",
                "severity": "suggest",
            })
    return issues


def _calculate_score(issues: List[Dict[str, Any]]) -> float:
    base = 100.0
    for issue in issues:
        if issue["severity"] == "warn":
            base -= 10.0
        elif issue["severity"] == "suggest":
            base -= 3.0
    return max(0.0, base)


def execute(context: Dict[str, Any]) -> Dict[str, Any]:
    content = context.get("content", "")
    title = context.get("title", "")
    brand_name = context.get("brand_name", "")
    brand_keywords = context.get("brand_keywords", [])
    brand_tone = context.get("brand_tone", "")
    prohibited_phrases = context.get("prohibited_phrases", [])

    text = title + "\n" + content
    all_issues: List[Dict[str, Any]] = []

    all_issues.extend(_check_brand_keywords(text, brand_keywords))
    all_issues.extend(_check_prohibited_phrases(text, prohibited_phrases))
    if brand_tone:
        all_issues.extend(_check_tone_match(text, brand_tone))

    score = _calculate_score(all_issues)
    consistent = score >= 80.0

    suggestions = []
    if any(i["type"] == "missing_keyword" for i in all_issues):
        suggestions.append(f"建议在内容中自然融入品牌关键词，强化「{brand_name}」品牌认知")
    if any(i["type"] == "prohibited_phrase" for i in all_issues):
        suggestions.append("删除或替换品牌禁用表述")
    if any(i["type"] == "tone_mismatch" for i in all_issues):
        suggestions.append(f"调整语气以贴合「{brand_tone}」品牌调性")
    if not suggestions:
        suggestions.append("品牌一致性良好")

    return {
        "consistent": consistent,
        "score": round(score, 1),
        "issues": all_issues,
        "suggestions": suggestions,
        "brand_name": brand_name,
        "skill_id": SKILL_ID,
        "version": VERSION,
    }
