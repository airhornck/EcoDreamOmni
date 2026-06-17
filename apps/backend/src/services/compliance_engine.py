"""ComplianceGuard: L1/L2/L3 rule engine with jieba segmentation.

L1 (Hard Reject): Prescription drugs, medical treatment promises
L2 (Warning): Unlabeled commercial content
L3 (Suggestion): Missing professional consultation disclaimer

Aligned with detailed design §5.6 — compliance audit chain.
"""

import hashlib
import re
import secrets
from datetime import datetime, timezone
from typing import Dict, List, Optional

import jieba

# ─── L1 Rules: Hard Redlines ───

_L1_PRESCRIPTION_KEYWORDS = [
    "阿莫西林", "布洛芬", "对乙酰氨基酚", "头孢", "青霉素", "红霉素",
    "甲硝唑", "庆大霉素", "土霉素", "诺氟沙星", "氧氟沙星", "环丙沙星",
    "地塞米松", "泼尼松", "强的松", "胰岛素", "安定", "阿司匹林",
    "处方药", "处方药物", "人用药物", "人用药",
]

_L1_MEDICAL_PROMISE_PATTERNS = [
    re.compile(r"(?:三天|一周|马上|立即|快速|彻底).{0,5}(?:治愈|治好|根除|痊愈|康复)"),
    re.compile(r"(?:保证|确保|承诺|百分百|100%).{0,5}(?:有效|治好|痊愈|康复|根治)"),
    re.compile(r"(?:无效|不见效).{0,5}(?:退款|退钱|赔偿)"),
    re.compile(r"(?:治疗|治愈|根治).{0,5}(?:猫癣|猫瘟|传腹|肾衰|心脏病|糖尿病)"),
]

# ─── L2 Rules: Commercial Disclosure ───

_L2_COMMERCIAL_KEYWORDS = [
    "下单", "购买链接", "购物车", "优惠码", "折扣", "限时",
    "种草", "安利", "必买", "必囤", "闭眼入", "链接在",
]

_L2_DISCLOSURE_KEYWORDS = [
    "合作", "赞助", "广告", "推广", "体验", "试用",
    "#合作", "# sponsored", "#ad", "【合作】", "【广告】",
]

# ─── L3 Rules: Risk Disclaimer ───

_L3_SYMPTOM_KEYWORDS = [
    "呕吐", "腹泻", "拉稀", "便血", "抽搐", "昏迷", "呼吸困难",
    "发烧", "发热", "食欲不振", "精神萎靡", "黄疸", "腹水",
    "肠胃炎", "胰腺炎", "肾炎", "肝炎", "心脏病", "糖尿病",
]

_L3_DISCLAIMER_KEYWORDS = [
    "请咨询", "建议就医", "及时就诊", "兽医建议", "专业意见",
    "仅供参考", "不能替代", "不作为诊断",
]


# ─── Evidence Chain Storage (MVP: in-memory) ───

_compliance_evidence_db: List[Dict] = []
_compliance_audit_db: List[Dict] = []


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _segment(text: str) -> List[str]:
    """Segment Chinese text using jieba."""
    return list(jieba.cut(text))


def _snippet_hash(snippet: str) -> str:
    """Generate a short SHA-256 hash for snippet."""
    return hashlib.sha256(snippet.encode("utf-8")).hexdigest()[:16]


def _write_compliance_audit(
    content_id: str,
    layer: str,
    rule_id: str,
    snippet: str,
    payload_ref: str = "",
) -> None:
    """Write an immutable compliance audit record.

    Args:
        content_id: Associated content ID.
        layer: L1 or L2.
        rule_id: Triggered rule ID.
        snippet: Matched text snippet (or full text for pattern rules).
        payload_ref: Reference to the evidence payload (e.g. evidence_id).
    """
    record = {
        "audit_id": secrets.token_urlsafe(16),
        "content_id": content_id,
        "layer": layer,
        "rule_id": rule_id,
        "snippet_hash": _snippet_hash(snippet),
        "payload_ref": payload_ref,
        "created_at": _now(),
        "superseded_by": None,
    }
    _compliance_audit_db.append(record)


def _check_l1(text: str, segments: List[str]) -> List[Dict]:
    """Check L1 hard redlines."""
    violations = []
    text.lower()

    # Prescription drug keywords
    for kw in _L1_PRESCRIPTION_KEYWORDS:
        if kw in text:
            violations.append({
                "rule_id": "L1-PRESCRIPTION",
                "level": "L1",
                "category": "处方药违规",
                "matched": kw,
                "message": f"内容包含处方药关键词「{kw}」，宠物用药必须由兽医处方",
                "suggestion": "删除处方药相关内容，建议引导用户咨询专业兽医",
            })

    # Medical promise patterns
    for pattern in _L1_MEDICAL_PROMISE_PATTERNS:
        match = pattern.search(text)
        if match:
            violations.append({
                "rule_id": "L1-MEDICAL-PROMISE",
                "level": "L1",
                "category": "诊疗承诺违规",
                "matched": match.group(),
                "message": "内容包含诊疗效果承诺，违反《广告法》医疗广告规定",
                "suggestion": "删除治愈率、保证有效等承诺性表述",
            })

    return violations


def _check_l2(text: str, segments: List[str]) -> List[Dict]:
    """Check L2 commercial disclosure."""
    violations = []

    # Check for commercial indicators
    has_commercial = any(kw in text for kw in _L2_COMMERCIAL_KEYWORDS)
    has_disclosure = any(kw in text for kw in _L2_DISCLOSURE_KEYWORDS)

    if has_commercial and not has_disclosure:
        violations.append({
            "rule_id": "L2-COMMERCIAL-DISCLOSURE",
            "level": "L2",
            "category": "商业内容未标注",
            "matched": "",
            "message": "内容疑似商业推广但未标注「合作/广告/体验」",
            "suggestion": '请在内容开头或结尾添加「合作」「体验」等标注，如「本内容为合作推广」',
        })

    return violations


def _check_l3(text: str, segments: List[str]) -> List[Dict]:
    """Check L3 risk disclaimer suggestions."""
    violations = []

    has_symptom = any(kw in text for kw in _L3_SYMPTOM_KEYWORDS)
    has_disclaimer = any(kw in text for kw in _L3_DISCLAIMER_KEYWORDS)

    if has_symptom and not has_disclaimer:
        violations.append({
            "rule_id": "L3-RISK-DISCLAIMER",
            "level": "L3",
            "category": "缺少专业咨询提示",
            "matched": "",
            "message": "内容涉及宠物症状描述，但未提示咨询专业兽医",
            "suggestion": "请添加免责声明，如「如宠物出现不适，请及时咨询专业兽医」",
        })

    return violations


def check_compliance(text: str, content_id: str = "") -> Dict:
    """Run L1/L2/L3 compliance checks and record evidence + audit.

    Returns:
        {
            "evidence_id": str,
            "content_id": str,
            "level": "pass" | "warning" | "reject",
            "violations": [...],
            "suggestions": [...],
            "checked_at": str,
        }
    """
    segments = _segment(text)

    l1_violations = _check_l1(text, segments)
    l2_violations = _check_l2(text, segments)
    l3_violations = _check_l3(text, segments)

    all_violations = l1_violations + l2_violations + l3_violations

    # Determine overall level
    if l1_violations:
        level = "reject"
    elif l2_violations:
        level = "warning"
    elif l3_violations:
        level = "warning"
    else:
        level = "pass"

    suggestions = [v["suggestion"] for v in all_violations]

    evidence_id = secrets.token_urlsafe(16)
    checked_at = _now()

    result = {
        "evidence_id": evidence_id,
        "content_id": content_id,
        "level": level,
        "violations": all_violations,
        "suggestions": suggestions,
        "checked_at": checked_at,
    }

    # Record evidence
    _compliance_evidence_db.append(result)

    # Write compliance audit for L1 intercepts and L2 warnings
    for v in l1_violations:
        snippet = v.get("matched") or text[:200]
        _write_compliance_audit(
            content_id=content_id or "",
            layer="L1",
            rule_id=v["rule_id"],
            snippet=snippet,
            payload_ref=evidence_id,
        )
    for v in l2_violations:
        snippet = v.get("matched") or text[:200]
        _write_compliance_audit(
            content_id=content_id or "",
            layer="L2",
            rule_id=v["rule_id"],
            snippet=snippet,
            payload_ref=evidence_id,
        )

    return result


def list_rules() -> List[Dict]:
    """List all active compliance rules."""
    return [
        {
            "rule_id": "L1-PRESCRIPTION",
            "level": "L1",
            "category": "处方药违规",
            "description": "禁止提及或推荐人用处方药给宠物使用",
            "action": "reject",
        },
        {
            "rule_id": "L1-MEDICAL-PROMISE",
            "level": "L1",
            "category": "诊疗承诺违规",
            "description": "禁止承诺治愈率、保证疗效等诊疗效果",
            "action": "reject",
        },
        {
            "rule_id": "L2-COMMERCIAL-DISCLOSURE",
            "level": "L2",
            "category": "商业内容未标注",
            "description": "商业推广内容必须标注「合作/广告/体验」",
            "action": "warn",
        },
        {
            "rule_id": "L3-RISK-DISCLAIMER",
            "level": "L3",
            "category": "缺少专业咨询提示",
            "description": "涉及症状描述时应建议咨询专业兽医",
            "action": "suggest",
        },
    ]


def list_compliance_audit(content_id: str = "") -> List[Dict]:
    """List compliance audit records."""
    if content_id:
        return [r for r in _compliance_audit_db if r["content_id"] == content_id]
    return list(_compliance_audit_db)


def supersede_audit(audit_id: str) -> Optional[Dict]:
    """Correct an audit record by appending a new row with superseded_by linkage.

    Returns the new record, or None if audit_id not found.
    """
    for record in _compliance_audit_db:
        if record["audit_id"] == audit_id:
            new_record = {
                **record,
                "audit_id": secrets.token_urlsafe(16),
                "created_at": _now(),
                "superseded_by": None,
            }
            record["superseded_by"] = new_record["audit_id"]
            _compliance_audit_db.append(new_record)
            return new_record
    return None


def clear_evidence() -> None:
    _compliance_evidence_db.clear()
    _compliance_audit_db.clear()
