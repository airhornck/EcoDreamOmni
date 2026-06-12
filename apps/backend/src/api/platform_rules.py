"""PlatformRule Engine API — ORM持久化版本 (W14).

L3/L4 dynamic rules CRUD + violation attribution.
Switched from in-memory dict storage to PostgreSQL/SQLAlchemy ORM.
"""

from pathlib import Path
from typing import List, Optional

import yaml
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.api.auth import get_current_user
from src.services import platform_rule_function as prf
from src.services.platform_rule_douyin import evaluate_douyin_content

# YAML config directory
YAML_PLATFORMS_DIR = Path(__file__).parent.parent / "data" / "platforms"

router = APIRouter(prefix="/platform-rules", tags=["platform-rules"])


class RuleCreate(BaseModel):
    layer: str = "l4"
    name: str
    condition_json: dict = {}
    action: str = "warn"
    priority: int = 0
    enabled: bool = True
    effective_from: str = ""
    platform: str = "xiaohongshu"


class RuleOut(BaseModel):
    id: str
    layer: str
    name: str
    condition_json: dict
    action: str
    priority: int
    enabled: bool
    version: int
    effective_from: str
    created_by: str
    platform: str

    model_config = ConfigDict(from_attributes=True)


class ContentEvaluateRequest(BaseModel):
    title: str = ""
    body: str = ""
    tags: List[str] = []
    account_state: Optional[dict] = None
    content_id: Optional[str] = None


class ContentEvaluateResponse(BaseModel):
    pass_v: bool
    violations: List[dict]
    warnings: List[dict]
    suggestions: List[dict]
    violation_count: int
    warning_count: int
    suggestion_count: int


class AttributionResponse(BaseModel):
    content_id: str
    attribution: List[dict]


def _to_response(rule) -> RuleOut:
    """兼容ORM对象与内存dataclass."""
    effective_from = rule.effective_from
    if hasattr(effective_from, "isoformat"):
        effective_from = effective_from.isoformat()
    return RuleOut(
        id=str(rule.id) if hasattr(rule.id, "hex") else rule.id,
        layer=rule.layer,
        name=rule.name,
        condition_json=dict(rule.condition_json) if rule.condition_json else {},
        action=rule.action,
        priority=rule.priority,
        enabled=rule.enabled,
        version=rule.version,
        effective_from=effective_from or "",
        created_by=rule.created_by,
        platform=getattr(rule, "platform", "xiaohongshu"),
    )


async def _ensure_default_rules(db: AsyncSession):
    """If no rules exist, seed default xiaohongshu rules (functional equivalent to memory version)."""
    result = await prf.list_rules(db, platform="xiaohongshu", limit=1)
    if result["total"] == 0:
        default_rules = [
            {
                "platform": "xiaohongshu",
                "layer": "l3",
                "name": "新号日发限制",
                "condition_json": {"type": "frequency", "scope": "account_state", "condition": "account_age_days<7 AND daily_post_count>=1"},
                "action": "warn",
                "priority": 100,
                "effective_from": "2026-01-01",
                "created_by": "system",
            },
            {
                "platform": "xiaohongshu",
                "layer": "l3",
                "name": "老号发布频率上限",
                "condition_json": {"type": "frequency", "scope": "account_state", "condition": "account_age_days>30 AND daily_post_count>=3"},
                "action": "warn",
                "priority": 100,
                "effective_from": "2026-01-01",
                "created_by": "system",
            },
            {
                "platform": "xiaohongshu",
                "layer": "l3",
                "name": "单日登录次数限制",
                "condition_json": {"type": "frequency", "scope": "login", "condition": "login_count_today>=3 OR login_fail_count>=2"},
                "action": "block",
                "priority": 200,
                "effective_from": "2026-01-01",
                "created_by": "system",
            },
            {
                "platform": "xiaohongshu",
                "layer": "l4",
                "name": "618期间商业笔记限流",
                "condition_json": {"type": "schedule", "scope": "time_range", "condition": "month=6 AND day IN [1-18] AND content_type=commercial"},
                "action": "warn",
                "priority": 50,
                "effective_from": "2026-06-01",
                "created_by": "system",
            },
            {
                "platform": "xiaohongshu",
                "layer": "l4",
                "name": "关键词临时降权",
                "condition_json": {"type": "keyword_regex", "scope": "title+body+tags", "pattern": "(驱虫药|处方)", "case_sensitive": False},
                "action": "warn",
                "priority": 50,
                "effective_from": "2026-01-01",
                "created_by": "system",
            },
        ]
        for rule_data in default_rules:
            await prf.create_rule(db=db, **rule_data)
        await db.commit()


@router.get("")
async def list_rules(
    layer: Optional[str] = None,
    platform: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    await _ensure_default_rules(db)
    result = await prf.list_rules(db, layer=layer, platform=platform)
    return {"rules": [_to_response(r) for r in result["items"]]}


@router.post("", status_code=201, response_model=RuleOut)
async def create_rule(
    data: RuleCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    effective_from = data.effective_from or ""
    rule = await prf.create_rule(
        db=db,
        platform=data.platform,
        layer=data.layer,
        name=data.name,
        condition_json=data.condition_json,
        action=data.action,
        priority=data.priority,
        enabled=data.enabled,
        effective_from=effective_from if effective_from else None,
        created_by=user.email if hasattr(user, "email") else "user",
    )
    await db.commit()
    return _to_response(rule)


@router.get("/{rule_id}", response_model=RuleOut)
async def get_rule(
    rule_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    rule = await prf.get_rule(db, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return _to_response(rule)


@router.patch("/{rule_id}", response_model=RuleOut)
async def update_rule(
    rule_id: str,
    data: dict,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    rule = await prf.update_rule(
        db=db,
        rule_id=rule_id,
        updated_by=user.email if hasattr(user, "email") else "user",
        **data,
    )
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    await db.commit()
    return _to_response(rule)


@router.delete("/{rule_id}", status_code=204)
async def delete_rule(
    rule_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    if not await prf.delete_rule(db, rule_id):
        raise HTTPException(status_code=404, detail="Rule not found")
    await db.commit()
    return None


@router.post("/evaluate", response_model=ContentEvaluateResponse)
async def evaluate_content(
    data: ContentEvaluateRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    result = await prf.evaluate_content(
        db=db,
        content={"title": data.title, "body": data.body, "tags": data.tags,
                 "content_id": data.content_id},
        account_state=data.account_state,
    )
    return ContentEvaluateResponse(
        pass_v=result["pass"],
        violations=result["violations"],
        warnings=result["warnings"],
        suggestions=result["suggestions"],
        violation_count=result["violation_count"],
        warning_count=result["warning_count"],
        suggestion_count=result["suggestion_count"],
    )


@router.get("/yaml-platforms")
async def list_yaml_platforms(user=Depends(get_current_user)):
    """List available YAML platform rule configurations."""
    if not YAML_PLATFORMS_DIR.exists():
        return {"platforms": []}
    platforms = []
    for f in YAML_PLATFORMS_DIR.glob("*.yaml"):
        try:
            data = yaml.safe_load(f.read_text(encoding="utf-8"))
            platforms.append({
                "file": f.name,
                "platform": data.get("platform"),
                "name": data.get("name"),
                "rule_count": len(data.get("rules", [])),
            })
        except Exception:
            continue
    return {"platforms": platforms}


@router.post("/load-yaml")
async def load_yaml_rules(
    platform: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Load platform rules from YAML file into database."""
    yaml_file = YAML_PLATFORMS_DIR / f"{platform}.yaml"
    if not yaml_file.exists():
        raise HTTPException(status_code=404, detail=f"YAML config for platform '{platform}' not found")

    try:
        data = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse YAML: {e}")

    rules = data.get("rules", [])
    created = 0
    for rule in rules:
        try:
            await prf.create_rule(
                db=db,
                layer=rule.get("layer", "l4"),
                name=rule["name"],
                condition_json=rule.get("condition_json", {}),
                action=rule.get("action", "warn"),
                priority=rule.get("priority", 0),
                enabled=rule.get("enabled", True),
                effective_from=rule.get("effective_from", ""),
                platform=data.get("platform", platform),
                created_by=user.email if hasattr(user, "email") else "system",
            )
            created += 1
        except Exception:
            continue

    await db.commit()
    return {"platform": platform, "loaded": created, "total_in_file": len(rules)}


@router.post("/seed-compliance-defaults")
async def seed_compliance_defaults(
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Seed default compliance rules (L1/L2/L3) migrated from compliance_engine.py hardcoded rules."""
    from src.services.platform_rule_function import seed_default_compliance_rules
    result = await seed_default_compliance_rules(db, created_by=user.email if hasattr(user, "email") else "system")
    return {"seeded": result["created"], "skipped": result["skipped"]}


@router.get("/{rule_id}/history")
async def get_rule_history(
    rule_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Get version history for a rule."""
    history = await prf.get_rule_history(db, rule_id)
    return {
        "rule_id": rule_id,
        "history": [prf.history_to_dict(h) for h in history],
    }


@router.get("/attribution/{content_id}", response_model=AttributionResponse)
async def get_attribution(
    content_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    attrs = await prf.get_attributions_for_content(db, content_id)
    return AttributionResponse(
        content_id=content_id,
        attribution=attrs,
    )


# ─── W16: Douyin platform-specific evaluation ───


@router.post("/douyin/evaluate", response_model=ContentEvaluateResponse)
async def evaluate_douyin(
    data: ContentEvaluateRequest,
    user=Depends(get_current_user),
):
    """Evaluate content against Douyin-specific platform rules."""
    result = evaluate_douyin_content(
        {"title": data.title, "body": data.body, "tags": data.tags}
    )
    return ContentEvaluateResponse(
        pass_v=result["pass"],
        violations=result["violations"],
        warnings=result["warnings"],
        suggestions=result["suggestions"],
        violation_count=result["violation_count"],
        warning_count=result["warning_count"],
        suggestion_count=result["suggestion_count"],
    )


@router.post("/xiaohongshu/evaluate", response_model=ContentEvaluateResponse)
async def evaluate_xiaohongshu(
    data: ContentEvaluateRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Evaluate content against Xiaohongshu platform rules (explicit endpoint)."""
    result = await prf.evaluate_content(
        db=db,
        content={"title": data.title, "body": data.body, "tags": data.tags,
                 "content_id": data.content_id},
        platform="xiaohongshu",
        account_state=data.account_state,
    )
    return ContentEvaluateResponse(
        pass_v=result["pass"],
        violations=result["violations"],
        warnings=result["warnings"],
        suggestions=result["suggestions"],
        violation_count=result["violation_count"],
        warning_count=result["warning_count"],
        suggestion_count=result["suggestion_count"],
    )
