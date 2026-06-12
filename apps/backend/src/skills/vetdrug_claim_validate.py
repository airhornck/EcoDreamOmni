"""VetDrug Claim Validate Skill — v4.0 Phase 8 P8-1.

校验兽药功效宣称与批文一致性。
MVP: 基于静态兽药知识库，无 LLM 调用。

架构红线:
- §2.1 Agent 禁 DB: 批文数据由调用方注入或通过 Function API 提供
- §2.5 LLMHub 路由: requires_llm=False
"""

from typing import Any, Dict, List

SKILL_ID = "vetdrug_claim_validate"
VERSION = "1.0.0"
MODALITY_SUPPORT = {"text": True}
REQUIRES_LLM = False
LLM_MODEL_PREFERENCE = ""

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "content": {"type": "string", "description": "待检查的正文内容"},
        "title": {"type": "string", "description": "待检查的标题"},
        "vetdrug_claims": {"type": "array", "items": {"type": "string"}, "description": "内容中声明的兽药功效列表"},
        "approval_numbers": {"type": "array", "items": {"type": "string"}, "description": "引用的兽药批文号列表"},
        "drug_database": {"type": "array", "items": {"type": "object"}, "description": "兽药批文数据库（由 Function API 提供）"},
    },
    "required": ["content"],
}

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "valid": {"type": "boolean"},
        "invalid_claims": {"type": "array", "items": {"type": "object"}},
        "approved_claims": {"type": "array", "items": {"type": "string"}},
        "warnings": {"type": "array", "items": {"type": "string"}},
        "summary": {"type": "string"},
    },
}

# MVP static vet drug approval database (subset)
_APPROVED_CLAIMS_DB: Dict[str, Dict[str, Any]] = {
    "兽药字220031609": {
        "product_name": "大宠爱",
        "generic_name": "塞拉菌素溶液",
        "indications": ["跳蚤", "虱子", "耳螨", "疥螨", "心丝虫预防"],
        "contraindications": ["6周龄以下", "生病期间", "怀孕哺乳期慎用"],
        "usage": "每月一次，外用滴剂",
    },
    "兽药字220031610": {
        "product_name": "海乐妙",
        "generic_name": "米尔贝肟吡喹酮片",
        "indications": ["蛔虫", "钩虫", "绦虫", "心丝虫预防"],
        "contraindications": ["6周龄以下", "体重不足0.5kg"],
        "usage": "每月一次，口服",
    },
    "兽药字220031611": {
        "product_name": "福来恩",
        "generic_name": "非泼罗尼甲氧普烯滴剂",
        "indications": ["跳蚤", "蜱虫"],
        "contraindications": ["8周龄以下"],
        "usage": "每月一次，外用滴剂",
    },
    "兽药字220031612": {
        "product_name": "拜宠清",
        "generic_name": "吡喹酮双羟萘酸噻嘧啶片",
        "indications": ["蛔虫", "钩虫", "绦虫"],
        "contraindications": ["3周龄以下"],
        "usage": "每3个月一次，口服",
    },
}

# Common over-claim patterns (not in approved indications)
_OVERCLAIM_PATTERNS: List[str] = [
    "治愈", "根治", "永不复发", "100%有效", "彻底消除",
    "无副作用", "绝对安全", "人畜共用", "替代疫苗",
    "预防所有疾病", "治疗所有寄生虫",
]


def _extract_claims_from_content(content: str) -> List[str]:
    """Extract potential vet drug claims from content."""
    claims = []
    # Simple keyword matching for MVP
    drug_keywords = ["驱虫", "除虫", "杀跳蚤", "杀蜱虫", "预防心丝虫", "体内驱虫", "体外驱虫"]
    for kw in drug_keywords:
        if kw in content:
            claims.append(kw)
    return claims


def _validate_approval_numbers(approval_numbers: List[str]) -> List[Dict[str, Any]]:
    invalid = []
    for num in approval_numbers:
        if num not in _APPROVED_CLAIMS_DB:
            invalid.append({
                "approval_number": num,
                "reason": "批文号未在数据库中找到，请核实",
            })
    return invalid


def _check_overclaims(content: str) -> List[Dict[str, Any]]:
    invalid = []
    for pattern in _OVERCLAIM_PATTERNS:
        if pattern in content:
            invalid.append({
                "claim": pattern,
                "reason": f"「{pattern}」属于夸大宣称，兽药广告禁止此类表述",
                "severity": "block",
            })
    return invalid


def _validate_claims_against_db(claims: List[str], approval_numbers: List[str]) -> tuple:
    approved: List[str] = []
    invalid: List[Dict[str, Any]] = []
    warnings: List[str] = []

    # Gather all approved indications from referenced approval numbers
    all_approved_indications = []
    for num in approval_numbers:
        if num in _APPROVED_CLAIMS_DB:
            all_approved_indications.extend(_APPROVED_CLAIMS_DB[num].get("indications", []))

    for claim in claims:
        # Check if claim is in approved indications
        matched = any(approved in claim or claim in approved for approved in all_approved_indications)
        if matched:
            approved.append(claim)
        else:
            # Check if it's a reasonable related claim
            related_terms = {
                "驱虫": ["跳蚤", "虱子", "蛔虫", "钩虫", "绦虫", "蜱虫"],
                "预防": ["心丝虫"],
                "除虫": ["跳蚤", "虱子", "蜱虫"],
            }
            is_related = any(
                claim in key and any(term in all_approved_indications for term in terms)
                for key, terms in related_terms.items()
            )
            if is_related:
                approved.append(claim)
                warnings.append(f"「{claim}」与批文适应症相关，但表述不够精确，建议使用批文原文")
            else:
                warnings.append(f"「{claim}」不在引用批文的适应症范围内，请核实")

    return approved, invalid, warnings


def execute(context: Dict[str, Any]) -> Dict[str, Any]:
    content = context.get("content", "")
    vetdrug_claims = context.get("vetdrug_claims", [])
    approval_numbers = context.get("approval_numbers", [])

    # Extract claims if not provided
    if not vetdrug_claims:
        vetdrug_claims = _extract_claims_from_content(content)

    all_invalid = []
    all_warnings = []

    # Check overclaim patterns (always block)
    overclaims = _check_overclaims(content)
    all_invalid.extend(overclaims)

    # Validate approval numbers
    if approval_numbers:
        invalid_approvals = _validate_approval_numbers(approval_numbers)
        for inv in invalid_approvals:
            all_invalid.append({
                "claim": inv["approval_number"],
                "reason": inv["reason"],
                "severity": "block",
            })

    # Validate claims against database
    approved_claims, invalid_claims, claim_warnings = _validate_claims_against_db(
        vetdrug_claims, approval_numbers
    )
    all_invalid.extend(invalid_claims)
    all_warnings.extend(claim_warnings)

    # Summary
    blocks = sum(1 for v in all_invalid if v.get("severity") == "block")
    warns = len(all_invalid) - blocks + len(all_warnings)

    if blocks > 0:
        summary = f"兽药宣称校验未通过：{blocks} 项阻断问题、{warns} 项警告"
    elif warns > 0:
        summary = f"兽药宣称校验通过（含 {warns} 项警告）"
    else:
        summary = "兽药宣称校验全部通过"

    valid = blocks == 0

    return {
        "valid": valid,
        "invalid_claims": all_invalid,
        "approved_claims": approved_claims,
        "warnings": all_warnings,
        "summary": summary,
        "skill_id": SKILL_ID,
        "version": VERSION,
    }
