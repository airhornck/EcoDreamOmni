"""Platform Compliance Check Skill — v4.0 Phase 8 P8-1.

调用 PlatformRule 进行 L1-L2 平台规则校验。
MVP: 基于静态 PlatformRule 规则库，无 LLM 调用。

架构红线:
- §2.1 Agent 禁 DB: 规则数据由调用方注入或通过 Function API 提供
- §2.5 LLMHub 路由: requires_llm=False
"""

from typing import Any, Dict, List

SKILL_ID = "platform_compliance_check"
VERSION = "1.0.0"
MODALITY_SUPPORT = {"text": True}
REQUIRES_LLM = False
LLM_MODEL_PREFERENCE = ""

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "content": {"type": "string", "description": "待检查的正文内容"},
        "title": {"type": "string", "description": "待检查的标题"},
        "platform_id": {"type": "string", "description": "平台标识: xhs / douyin / bilibili / wechat_official"},
        "rules": {"type": "array", "description": "平台规则列表（由 Function API 提供）", "items": {"type": "object"}},
    },
    "required": ["content", "platform_id"],
}

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "l1_passed": {"type": "boolean"},
        "l2_passed": {"type": "boolean"},
        "l1_violations": {"type": "array", "items": {"type": "object"}},
        "l2_violations": {"type": "array", "items": {"type": "object"}},
        "platform": {"type": "string"},
        "summary": {"type": "string"},
    },
}

# MVP static L1 rules mimicking PlatformRuleORM structure
_L1_RULES: Dict[str, List[Dict[str, Any]]] = {
    "xhs": [
        {"name": "标题长度限制", "max_length": 20},
        {"name": "正文长度限制", "max_length": 1000},
        {"name": "禁止外链", "pattern": "http://|https://|www."},
        {"name": "禁止二维码", "pattern": "二维码|QR|扫码"},
    ],
    "douyin": [
        {"name": "标题长度限制", "max_length": 55},
        {"name": "正文长度限制", "max_length": 500},
        {"name": "禁止诱导关注", "pattern": "关注我|点关注|求关注"},
    ],
    "bilibili": [
        {"name": "标题长度限制", "max_length": 80},
        {"name": "正文长度限制", "max_length": 2000},
        {"name": "禁止引战", "pattern": "垃圾|废物|脑残|弱智"},
    ],
    "wechat_official": [
        {"name": "标题长度限制", "max_length": 64},
        {"name": "正文长度限制", "min_length": 100, "max_length": 20000},
        {"name": "禁止诱导分享", "pattern": "转发|分享到朋友圈|截图发朋友圈"},
    ],
}

_L2_KEYWORDS: Dict[str, List[Dict[str, Any]]] = {
    "xhs": [
        {"word": "最好", "severity": "warn", "suggestion": "建议使用「不错」替代"},
        {"word": "最便宜", "severity": "warn", "suggestion": "建议使用「性价比高」替代"},
        {"word": "永久", "severity": "block", "suggestion": "删除该词，平台禁止绝对化承诺"},
        {"word": "100%有效", "severity": "block", "suggestion": "删除该词，平台禁止功效保证"},
    ],
    "douyin": [
        {"word": "必火", "severity": "warn", "suggestion": "建议使用「有潜力」替代"},
        {"word": "保证赚钱", "severity": "block", "suggestion": "删除该词，涉嫌虚假承诺"},
    ],
    "bilibili": [
        {"word": "最强", "severity": "warn", "suggestion": "建议使用「优秀」替代"},
        {"word": "吊打", "severity": "warn", "suggestion": "建议客观对比，避免攻击性用语"},
    ],
    "wechat_official": [
        {"word": "不转不是中国人", "severity": "block", "suggestion": "删除，涉嫌道德绑架"},
        {"word": "震惊", "severity": "warn", "suggestion": "减少标题党用语"},
    ],
}


def _check_l1_rules(content: str, title: str, platform_id: str) -> List[Dict[str, Any]]:
    violations = []
    rules = _L1_RULES.get(platform_id, _L1_RULES["xhs"])
    text = title + "\n" + content

    for rule in rules:
        if "max_length" in rule and "min_length" not in rule:
            target = title if "标题" in rule["name"] else content
            if len(target) > rule["max_length"]:
                violations.append({
                    "layer": "L1",
                    "rule_name": rule["name"],
                    "message": f"{rule['name']}: {len(target)} > {rule['max_length']}",
                    "severity": "block" if len(target) > rule["max_length"] * 1.5 else "warn",
                })
        elif "min_length" in rule:
            target = content
            if len(target) < rule["min_length"]:
                violations.append({
                    "layer": "L1",
                    "rule_name": rule["name"],
                    "message": f"{rule['name']}: {len(target)} < {rule['min_length']}",
                    "severity": "warn",
                })
        elif "pattern" in rule:
            import re
            if re.search(rule["pattern"], text, re.IGNORECASE):
                violations.append({
                    "layer": "L1",
                    "rule_name": rule["name"],
                    "message": f"触发规则「{rule['name']}」",
                    "severity": "block",
                })

    return violations


def _check_l2_keywords(content: str, title: str, platform_id: str) -> List[Dict[str, Any]]:
    violations = []
    keywords = _L2_KEYWORDS.get(platform_id, _L2_KEYWORDS["xhs"])
    text = title + "\n" + content

    for kw in keywords:
        if kw["word"] in text:
            violations.append({
                "layer": "L2",
                "keyword": kw["word"],
                "severity": kw["severity"],
                "message": f"包含平台限流词「{kw['word']}」",
                "suggestion": kw["suggestion"],
            })

    return violations


def execute(context: Dict[str, Any]) -> Dict[str, Any]:
    content = context.get("content", "")
    title = context.get("title", "")
    platform_id = context.get("platform_id", "xhs")

    l1_violations = _check_l1_rules(content, title, platform_id)
    l2_violations = _check_l2_keywords(content, title, platform_id)

    l1_passed = not any(v["severity"] == "block" for v in l1_violations)
    l2_passed = not any(v["severity"] == "block" for v in l2_violations)

    total = len(l1_violations) + len(l2_violations)
    blocks = sum(1 for v in l1_violations + l2_violations if v.get("severity") == "block")
    warns = total - blocks

    if blocks > 0:
        summary = f"平台合规检查未通过：发现 {blocks} 项阻断规则、{warns} 项警告"
    elif warns > 0:
        summary = f"平台合规检查通过（含 {warns} 项警告建议优化）"
    else:
        summary = "平台合规检查全部通过"

    return {
        "l1_passed": l1_passed,
        "l2_passed": l2_passed,
        "l1_violations": l1_violations,
        "l2_violations": l2_violations,
        "platform": platform_id,
        "summary": summary,
        "skill_id": SKILL_ID,
        "version": VERSION,
    }
