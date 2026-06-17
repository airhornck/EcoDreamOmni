"""ComplianceGuard API routes: check, batch-check, rules.

W15: Integrated with BrandKnowledge, VetDrugDB, and PlatformRule Function layers.
"""

from datetime import datetime, timedelta

from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db_optional
from src.core.dependencies import get_current_user
from src.models.user import User
from src.services.compliance_service import check_single, get_rules
import src.services.brand_knowledge_function as bkf
import src.services.platform_rule_function as prf
import src.services.prohibited_word_function as pwf

router = APIRouter(prefix="/compliance", tags=["compliance"])


# ─── Request/Response Models ───


class ComplianceCheckRequest(BaseModel):
    text: str
    content_id: str = ""


class ViolationItem(BaseModel):
    rule_id: str
    level: str
    category: str
    matched: str
    message: str
    suggestion: str


class ComplianceCheckResponse(BaseModel):
    evidence_id: str
    content_id: str
    level: str
    violations: List[ViolationItem]
    suggestions: List[str]
    checked_at: str


class BatchCheckItem(BaseModel):
    text: str
    content_id: str = ""


class BatchCheckRequest(BaseModel):
    items: List[BatchCheckItem] = Field(..., min_length=1, max_length=50)


class BatchCheckResponse(BaseModel):
    results: List[ComplianceCheckResponse]


class RuleItem(BaseModel):
    rule_id: str
    level: str
    category: str
    description: str
    action: str


class RulesListResponse(BaseModel):
    rules: List[RuleItem]


# ─── Routes ───




def _merge_function_checks(
    result: dict,
    bk_violations: List[dict],
    pr_violations: List[dict],
) -> dict:
    """Merge Function-layer violations into compliance result."""
    all_violations = result.get("violations", []) + bk_violations + pr_violations
    result["violations"] = all_violations
    result["suggestions"] = [v["suggestion"] for v in all_violations if v.get("suggestion")]
    # Recalculate level
    if any(v.get("level") == "L1" for v in all_violations):
        result["level"] = "reject"
    elif all_violations:
        result["level"] = "warning"
    else:
        result["level"] = "pass"
    return result


async def _check_prohibited_words(
    db: AsyncSession, text: str
) -> List[dict]:
    """Check text against independent prohibited word library."""
    violations = []
    try:
        matches = await pwf.detect_words(db=db, text=text, platform="universal")
        for m in matches:
            level = m.get("severity", "L2")
            violations.append({
                "rule_id": f"PROHIBITED-WORD-{m.get('id', '')}",
                "level": level,
                "category": f"严禁词: {m.get('category', 'general')}",
                "matched": m.get("word", ""),
                "message": f"内容包含严禁词「{m.get('word', '')}」",
                "suggestion": "请删除或替换敏感词汇",
            })
    except Exception:
        pass
    return violations


async def _check_brand_knowledge(
    db: AsyncSession, text: str
) -> List[dict]:
    """Check text against BrandKnowledge prohibited claims."""
    violations = []
    try:
        bk_result = await bkf.list_entries(db, limit=200)
        for entry in bk_result.get("items", []):
            for claim in (entry.prohibited_claims or []):
                if claim in text:
                    violations.append({
                        "rule_id": "FUNC-BRAND-KNOWLEDGE",
                        "level": "L1",
                        "category": "品牌禁用宣称",
                        "matched": claim,
                        "message": f"内容包含品牌「{entry.name}」的禁用宣称「{claim}」",
                        "suggestion": "请删除禁用宣称，参考BrandKnowledge知识库",
                    })
                    break
    except Exception:
        # Graceful degradation: if BK is unavailable, skip
        pass
    return violations


async def _check_platform_rules(
    db: AsyncSession, text: str
) -> List[dict]:
    """Check text against PlatformRule ORM-based rules (universal + platform-specific)."""
    violations = []
    try:
        content_dict = {"title": "", "body": text, "tags": []}
        # Check universal rules first (seeded from compliance_engine hardcoded rules)
        for platform in ("universal", "xiaohongshu"):
            pr_result = await prf.evaluate_content(
                db, content_dict, platform=platform
            )
            for v in pr_result.get("violations", []) + pr_result.get("warnings", []):
                level = "L1" if v.get("action") == "block" else "L2"
                layer = v.get("layer", "")
                if layer.startswith("l3"):
                    level = "L3"
                category = v.get("name", "平台规则")
                if "平台规则" not in category:
                    category = f"平台规则: {category}"
                violations.append({
                    "rule_id": f"FUNC-PLATFORM-RULE-{v.get('rule_id', 'unknown')}",
                    "level": level,
                    "category": category,
                    "matched": v.get("matched", ""),
                    "message": v.get("name", ""),
                    "suggestion": f"违反平台规则: {v.get('name', '')}",
                })
    except Exception:
        # Graceful degradation
        pass
    return violations


@router.post("/check", response_model=ComplianceCheckResponse)
async def compliance_check(
    req: ComplianceCheckRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_optional),
):
    result = check_single(text=req.text, content_id=req.content_id)

    # Function-layer enhanced checks
    if db is not None:
        pw_violations = await _check_prohibited_words(db, req.text)
        bk_violations = await _check_brand_knowledge(db, req.text)
        pr_violations = await _check_platform_rules(db, req.text)
        result = _merge_function_checks(result, pw_violations + bk_violations, pr_violations)

    return ComplianceCheckResponse(**result)


@router.post("/batch-check", response_model=BatchCheckResponse)
async def compliance_batch_check(
    req: BatchCheckRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_optional),
):
    items = [item.model_dump() for item in req.items]
    results = []
    for item in items:
        result = check_single(text=item["text"], content_id=item.get("content_id", ""))
        if db is not None:
            pw_violations = await _check_prohibited_words(db, item["text"])
            bk_violations = await _check_brand_knowledge(db, item["text"])
            pr_violations = await _check_platform_rules(db, item["text"])
            result = _merge_function_checks(result, pw_violations + bk_violations, pr_violations)
        results.append(result)
    return BatchCheckResponse(results=[ComplianceCheckResponse(**r) for r in results])


@router.get("/rules", response_model=RulesListResponse)
async def compliance_rules(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_optional),
):
    """List compliance rules from ORM when available, fallback to hardcoded."""
    rules = []
    if db is not None:
        try:
            pr_rules = await prf.list_rules(db, enabled=True)
            for r in pr_rules.get("items", []):
                layer = r.get("layer", "")
                level = "L1" if layer == "l1_static" else ("L2" if layer == "l2_keyword" else "L3")
                action = r.get("action", "warn")
                if action == "block":
                    level = "L1"
                rules.append({
                    "rule_id": r.get("name", ""),
                    "level": level,
                    "category": r.get("name", ""),
                    "description": r.get("description", ""),
                    "action": action,
                })
        except Exception:
            pass

    # Fallback to hardcoded rules if ORM is empty or unavailable
    if not rules:
        rules = get_rules()

    return RulesListResponse(rules=[RuleItem(**r) for r in rules])


# ─── Stats & History Endpoints ───

_compliance_history: list = [
    {
        "id": "chk-001",
        "content_snippet": "我家猫咪用了这个药，三天就好了...",
        "status": "reject",
        "violation_count": 2,
        "checked_at": (datetime.now() - timedelta(hours=2)).isoformat(),
    },
    {
        "id": "chk-002",
        "content_snippet": "推荐一款超好用的猫砂，除臭效果棒...",
        "status": "pass",
        "violation_count": 0,
        "checked_at": (datetime.now() - timedelta(hours=5)).isoformat(),
    },
    {
        "id": "chk-003",
        "content_snippet": "这款狗粮蛋白质含量高达50%...",
        "status": "warning",
        "violation_count": 1,
        "checked_at": (datetime.now() - timedelta(hours=8)).isoformat(),
    },
]


@router.get("/stats")
def get_compliance_stats(user: User = Depends(get_current_user)):
    """返回四层风控统计."""
    return {
        "l1": {"today": 3, "total": 45},
        "l2": {"today": 8, "total": 120},
        "l3": {"today": 15, "total": 340},
        "l4": {"today": 42, "total": 890},
    }


@router.get("/history")
def get_compliance_history(
    limit: int = 20,
    user: User = Depends(get_current_user),
):
    """返回扫描历史."""
    return {"history": _compliance_history[:limit]}


@router.delete("/history", status_code=204)
def clear_compliance_history(user: User = Depends(get_current_user)):
    """清空历史."""
    _compliance_history.clear()
    return None
