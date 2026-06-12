"""PlatformRule Douyin Adapter — W16 抖音平台规则适配。

核心能力:
- 调用 PlatformRule Function 基座扩展
- 兽药广告审查号强制校验
- 引流话术 L1 拦截
- 平台差异规则矩阵
"""

import re
from typing import Dict, List, Any


# ─── Douyin-specific redlines ───

# 兽药广告审查批准文号格式
_AD_APPROVAL_PATTERN = re.compile(
    r"兽药广审[（(][视视听文][）)]\s*第\s*\d{4,}\s*号"
)

# 引流话术关键词
_DIVERSION_KEYWORDS = [
    "微信", "私聊", "私信", "加V", "扫码", "进群", "二维码",
    "外部链接", "点击链接", "跳转", "联系方式",
]

# 处方药/诊疗承诺（抖音额外严格）
_EXTRA_STRICT_PATTERNS = [
    re.compile(r"(?:三天|一周|马上|立即|快速|彻底).{0,5}(?:治愈|治好|根除|痊愈|康复)"),
    re.compile(r"(?:保证|确保|承诺|百分百|100%).{0,5}(?:有效|治好|痊愈|康复|根治)"),
]


def _check_ad_approval_number(text: str) -> Dict[str, Any]:
    """Check if text contains veterinary drug advertisement approval number."""
    has_approval = bool(_AD_APPROVAL_PATTERN.search(text))
    return {
        "has_approval_number": has_approval,
        "matched": _AD_APPROVAL_PATTERN.search(text).group() if has_approval else None,
    }


def _check_diversion_phrases(text: str) -> List[Dict]:
    """Check for diversion/off-platform引流 phrases."""
    violations = []
    for kw in _DIVERSION_KEYWORDS:
        if kw in text:
            violations.append({
                "rule_id": "DOUYIN-DIVERSION",
                "level": "L1",
                "category": "引流违规",
                "matched": kw,
                "message": f"内容包含引流话术「{kw}」，抖音平台禁止引导用户至站外",
                "suggestion": "删除微信/私聊/二维码等站外引流信息",
            })
    return violations


def _check_medical_promises(text: str) -> List[Dict]:
    """Extra-strict medical promise detection for Douyin."""
    violations = []
    for pattern in _EXTRA_STRICT_PATTERNS:
        match = pattern.search(text)
        if match:
            violations.append({
                "rule_id": "DOUYIN-MEDICAL-PROMISE",
                "level": "L1",
                "category": "诊疗承诺违规",
                "matched": match.group(),
                "message": "抖音平台严禁承诺治愈率、保证疗效等诊疗效果",
                "suggestion": "删除治愈率、保证有效等承诺性表述",
            })
    return violations


def evaluate_douyin_content(content: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate content against Douyin-specific platform rules.

    Args:
        content: {"title": str, "body": str, "tags": List[str], ...}

    Returns:
        {"pass": bool, "violations": [...], "warnings": [...], "suggestions": [...]}
    """
    text = f"{content.get('title', '')} {content.get('body', '')}"
    tags = content.get("tags", [])

    violations = []
    warnings = []
    suggestions = []

    # 1. 兽药广告审查号校验（内容涉及兽药时必须包含）
    if any(tag in str(tags) for tag in ["兽药", "驱虫", "疫苗", "药品"]):
        ad_check = _check_ad_approval_number(text)
        if not ad_check["has_approval_number"]:
            violations.append({
                "rule_id": "DOUYIN-AD-APPROVAL",
                "level": "L1",
                "category": "广告审查号缺失",
                "matched": "",
                "message": "抖音平台要求兽药广告须显著展示广告审查批准文号（如：兽药广审（视）第XXXX号）",
                "suggestion": "在内容中显著位置添加兽药广告审查批准文号",
            })

    # 2. 引流话术拦截
    diversion_violations = _check_diversion_phrases(text)
    violations.extend(diversion_violations)

    # 3. 诊疗承诺（抖音额外严格）
    medical_violations = _check_medical_promises(text)
    violations.extend(medical_violations)

    # 4. 处方药关键词（通用）
    prescription_keywords = ["处方药", "处方药物", "阿莫西林", "头孢"]
    for kw in prescription_keywords:
        if kw in text:
            violations.append({
                "rule_id": "DOUYIN-PRESCRIPTION",
                "level": "L1",
                "category": "处方药违规",
                "matched": kw,
                "message": f"内容包含处方药关键词「{kw}」，抖音平台禁止推荐人用/兽用处方药",
                "suggestion": "删除处方药相关内容，建议引导用户咨询专业兽医",
            })

    return {
        "pass": len(violations) == 0,
        "violations": violations,
        "warnings": warnings,
        "suggestions": suggestions,
        "violation_count": len(violations),
        "warning_count": len(warnings),
        "suggestion_count": len(suggestions),
        "platform": "douyin",
    }
