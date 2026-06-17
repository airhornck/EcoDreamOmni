"""PlatformRule Function — ORM持久化版本 (W14).

平台规则真源基座：小红书规则迁移 + 抖音/视频号扩展预留.
Aligned with PRD V3.1 §PlatformRule / TASK_V2.7.1 FUNC-5.
"""

import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, delete

from src.models.platform_rule_orm import PlatformRuleORM, PlatformRuleHistoryORM
from src.models.platform_rule_attribution_orm import ContentRuleAttributionORM


def _now() -> datetime:
    return datetime.now(timezone.utc)


def rule_to_dict(rule: PlatformRuleORM) -> Dict[str, Any]:
    return {
        "id": str(rule.id),
        "platform": rule.platform,
        "layer": rule.layer,
        "name": rule.name,
        "description": rule.description,
        "condition_json": rule.condition_json,
        "action": rule.action,
        "priority": rule.priority,
        "enabled": rule.enabled,
        "version": rule.version,
        "effective_from": rule.effective_from.isoformat() if rule.effective_from else None,
        "effective_until": rule.effective_until.isoformat() if rule.effective_until else None,
        "applicable_lifecycle": rule.applicable_lifecycle or [],
        "created_by": rule.created_by,
        "updated_by": rule.updated_by,
        "tenant_id": rule.tenant_id,
        "created_at": rule.created_at.isoformat() if rule.created_at else None,
        "updated_at": rule.updated_at.isoformat() if rule.updated_at else None,
    }


def history_to_dict(hist: PlatformRuleHistoryORM) -> Dict[str, Any]:
    return {
        "id": str(hist.id),
        "rule_id": str(hist.rule_id),
        "platform": hist.platform,
        "layer": hist.layer,
        "name": hist.name,
        "condition_json": hist.condition_json,
        "action": hist.action,
        "priority": hist.priority,
        "enabled": hist.enabled,
        "version": hist.version,
        "effective_from": hist.effective_from.isoformat() if hist.effective_from else None,
        "change_reason": hist.change_reason,
        "changed_by": hist.changed_by,
        "created_at": hist.created_at.isoformat() if hist.created_at else None,
    }


def _parse_dt(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


async def create_rule(
    db: AsyncSession,
    platform: str,
    layer: str,
    name: str,
    condition_json: Dict[str, Any],
    action: str = "warn",
    priority: int = 0,
    enabled: bool = True,
    effective_from: Optional[str] = None,
    effective_until: Optional[str] = None,
    applicable_lifecycle: Optional[List[str]] = None,
    description: Optional[str] = None,
    created_by: str = "system",
    tenant_id: Optional[str] = None,
) -> PlatformRuleORM:
    rule = PlatformRuleORM(
        platform=platform,
        layer=layer,
        name=name,
        description=description,
        condition_json=condition_json,
        action=action,
        priority=priority,
        enabled=enabled,
        effective_from=_parse_dt(effective_from) or _now(),
        effective_until=_parse_dt(effective_until),
        applicable_lifecycle=applicable_lifecycle or [],
        created_by=created_by,
        tenant_id=tenant_id,
    )
    db.add(rule)
    await db.flush()
    await db.commit()
    await db.refresh(rule)
    return rule


async def get_rule(
    db: AsyncSession, rule_id: str
) -> Optional[PlatformRuleORM]:
    result = await db.execute(
        select(PlatformRuleORM).where(PlatformRuleORM.id == rule_id)
    )
    return result.scalar_one_or_none()


async def list_rules(
    db: AsyncSession,
    platform: Optional[str] = None,
    layer: Optional[str] = None,
    enabled: Optional[bool] = None,
    tenant_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, Any]:
    query = select(PlatformRuleORM)
    if platform:
        query = query.where(PlatformRuleORM.platform == platform)
    if layer:
        query = query.where(PlatformRuleORM.layer == layer)
    if enabled is not None:
        query = query.where(PlatformRuleORM.enabled == enabled)
    if tenant_id:
        query = query.where(PlatformRuleORM.tenant_id == tenant_id)

    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar() or 0

    query = (
        query.order_by(desc(PlatformRuleORM.priority), PlatformRuleORM.name)
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(query)
    items = result.scalars().all()

    return {"items": list(items), "total": total, "limit": limit, "offset": offset}


async def update_rule(
    db: AsyncSession,
    rule_id: str,
    updated_by: str,
    change_reason: Optional[str] = None,
    **kwargs,
) -> Optional[PlatformRuleORM]:
    """更新规则 — 自动创建历史快照并递增版本."""
    old_rule = await get_rule(db, rule_id)
    if not old_rule:
        return None

    # 保存历史快照
    hist = PlatformRuleHistoryORM(
        rule_id=old_rule.id,
        platform=old_rule.platform,
        layer=old_rule.layer,
        name=old_rule.name,
        condition_json=dict(old_rule.condition_json or {}),
        action=old_rule.action,
        priority=old_rule.priority,
        enabled=old_rule.enabled,
        version=old_rule.version,
        effective_from=old_rule.effective_from,
        change_reason=change_reason or "规则更新",
        changed_by=updated_by,
    )
    db.add(hist)

    # 更新当前规则
    for key, value in kwargs.items():
        if key in {"effective_from", "effective_until"} and isinstance(value, str):
            value = _parse_dt(value)
        if key not in {"id", "created_at"} and hasattr(old_rule, key):
            setattr(old_rule, key, value)

    old_rule.version += 1
    old_rule.updated_by = updated_by
    old_rule.updated_at = _now()
    await db.flush()
    await db.commit()
    await db.refresh(old_rule)
    return old_rule


async def delete_rule(db: AsyncSession, rule_id: str) -> bool:
    rule = await get_rule(db, rule_id)
    if not rule:
        return False
    await db.delete(rule)
    await db.flush()
    await db.commit()
    return True


async def get_rule_history(
    db: AsyncSession, rule_id: str
) -> List[PlatformRuleHistoryORM]:
    result = await db.execute(
        select(PlatformRuleHistoryORM)
        .where(PlatformRuleHistoryORM.rule_id == rule_id)
        .order_by(desc(PlatformRuleHistoryORM.version))
    )
    return list(result.scalars().all())


async def evaluate_content(
    db: AsyncSession,
    content: Dict[str, Any],
    platform: str = "xiaohongshu",
    account_state: Optional[Dict[str, Any]] = None,
    tenant_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Evaluate content against active rules for a platform."""
    query = (
        select(PlatformRuleORM)
        .where(PlatformRuleORM.platform == platform)
        .where(PlatformRuleORM.enabled)
    )
    if tenant_id:
        query = query.where(PlatformRuleORM.tenant_id == tenant_id)

    now = _now()
    # Note: effective date filtering done in Python to avoid timezone SQL complexity
    result = await db.execute(query)
    rules = result.scalars().all()

    text = f"{content.get('title', '')} {content.get('body', '')} {' '.join(content.get('tags', []))}"

    violations = []
    warnings = []
    suggestions = []

    for rule in rules:
        if rule.effective_until and rule.effective_until < now:
            continue
        if rule.effective_from and rule.effective_from > now:
            continue

        triggered = False
        condition = rule.condition_json or {}

        if condition.get("type") == "keyword_regex":
            pattern = condition.get("pattern", "")
            if pattern and re.search(
                pattern,
                text,
                re.IGNORECASE if not condition.get("case_sensitive") else 0,
            ):
                triggered = True

        elif condition.get("type") == "keyword":
            keywords = condition.get("keywords", [])
            case_sensitive = condition.get("case_sensitive", False)
            check_text = text if case_sensitive else text.lower()
            for kw in keywords:
                kw_check = kw if case_sensitive else kw.lower()
                if kw_check in check_text:
                    triggered = True
                    break

        elif condition.get("type") == "keyword_pair":
            # Trigger if ANY trigger keyword is present AND NO required keyword is present
            trigger_keywords = condition.get("trigger_keywords", [])
            required_keywords = condition.get("required_keywords", [])
            case_sensitive = condition.get("case_sensitive", False)
            check_text = text if case_sensitive else text.lower()
            has_trigger = False
            for kw in trigger_keywords:
                kw_check = kw if case_sensitive else kw.lower()
                if kw_check in check_text:
                    has_trigger = True
                    break
            has_required = False
            for kw in required_keywords:
                kw_check = kw if case_sensitive else kw.lower()
                if kw_check in check_text:
                    has_required = True
                    break
            if has_trigger and not has_required:
                triggered = True

        elif condition.get("type") == "frequency":
            if account_state:
                cond = condition.get("condition", "")
                daily_count = account_state.get("daily_post_count", 0)
                if "daily_post_count" in cond:
                    if daily_count >= 1 and "new" in cond.lower():
                        triggered = True
                    if daily_count >= 3 and "old" in cond.lower():
                        triggered = True

        matched_detail = ""
        if triggered:
            # Capture matched detail for audit
            cond = rule.condition_json or {}
            if cond.get("type") == "keyword":
                for kw in cond.get("keywords", []):
                    if kw.lower() in text.lower():
                        matched_detail = kw
                        break
            elif cond.get("type") == "keyword_pair":
                for kw in cond.get("trigger_keywords", []):
                    if kw.lower() in text.lower():
                        matched_detail = kw
                        break
            elif cond.get("type") == "keyword_regex":
                pattern = cond.get("pattern", "")
                m = re.search(pattern, text, re.IGNORECASE)
                if m:
                    matched_detail = m.group()

            result_item = {
                "rule_id": str(rule.id),
                "layer": rule.layer,
                "name": rule.name,
                "action": rule.action,
                "matched": matched_detail,
            }
            if rule.action == "block":
                violations.append(result_item)
            elif rule.action == "warn":
                warnings.append(result_item)
            else:
                suggestions.append(result_item)

            # Persist attribution for audit trail
            if content.get("content_id"):
                attr = ContentRuleAttributionORM(
                    content_id=content["content_id"],
                    rule_id=str(rule.id),
                    rule_name=rule.name,
                    layer=rule.layer,
                    action=rule.action,
                    matched_text=matched_detail,
                    platform=platform,
                    tenant_id=tenant_id,
                )
                db.add(attr)

    await db.commit()

    return {
        "pass": len(violations) == 0,
        "violations": violations,
        "warnings": warnings,
        "suggestions": suggestions,
        "violation_count": len(violations),
        "warning_count": len(warnings),
        "suggestion_count": len(suggestions),
    }


# ─── Default compliance rules seed (migrates hardcoded rules from compliance_engine.py) ───

_DEFAULT_COMPLIANCE_RULES = [
    {
        "platform": "universal",
        "layer": "l1_static",
        "name": "L1-PRESCRIPTION",
        "description": "禁止提及或推荐人用处方药给宠物使用",
        "condition_json": {
            "type": "keyword",
            "keywords": [
                "阿莫西林", "布洛芬", "对乙酰氨基酚", "头孢", "青霉素", "红霉素",
                "甲硝唑", "庆大霉素", "土霉素", "诺氟沙星", "氧氟沙星", "环丙沙星",
                "地塞米松", "泼尼松", "强的松", "胰岛素", "安定", "阿司匹林",
                "处方药", "处方药物", "人用药物", "人用药",
            ],
        },
        "action": "block",
        "priority": 100,
    },
    {
        "platform": "universal",
        "layer": "l1_static",
        "name": "L1-MEDICAL-PROMISE",
        "description": "禁止承诺治愈率、保证疗效等诊疗效果",
        "condition_json": {
            "type": "keyword_regex",
            "pattern": r"(?:(?:三天|一周|马上|立即|快速|彻底).{0,5}(?:治愈|治好|根除|痊愈|康复))|(?:(?:保证|确保|承诺|百分百|100%).{0,5}(?:有效|治好|痊愈|康复|根治))|(?:(?:无效|不见效).{0,5}(?:退款|退钱|赔偿))|(?:(?:治疗|治愈|根治).{0,5}(?:猫癣|猫瘟|传腹|肾衰|心脏病|糖尿病))",
        },
        "action": "block",
        "priority": 99,
    },
    {
        "platform": "universal",
        "layer": "l2_keyword",
        "name": "L2-COMMERCIAL-DISCLOSURE",
        "description": "商业推广内容必须标注「合作/广告/体验」",
        "condition_json": {
            "type": "keyword_pair",
            "trigger_keywords": [
                "下单", "购买链接", "购物车", "优惠码", "折扣", "限时",
                "种草", "安利", "必买", "必囤", "闭眼入", "链接在",
            ],
            "required_keywords": [
                "合作", "赞助", "广告", "推广", "体验", "试用",
                "#合作", "# sponsored", "#ad", "【合作】", "【广告】",
            ],
        },
        "action": "warn",
        "priority": 80,
    },
    {
        "platform": "universal",
        "layer": "l3_dynamic_risk",
        "name": "L3-RISK-DISCLAIMER",
        "description": "涉及症状描述时应建议咨询专业兽医",
        "condition_json": {
            "type": "keyword_pair",
            "trigger_keywords": [
                "呕吐", "腹泻", "拉稀", "便血", "抽搐", "昏迷", "呼吸困难",
                "发烧", "发热", "食欲不振", "精神萎靡", "黄疸", "腹水",
                "肠胃炎", "胰腺炎", "肾炎", "肝炎", "心脏病", "糖尿病",
            ],
            "required_keywords": [
                "请咨询", "建议就医", "及时就诊", "兽医建议", "专业意见",
                "仅供参考", "不能替代", "不作为诊断",
            ],
        },
        "action": "warn",
        "priority": 60,
    },
]


async def seed_default_compliance_rules(
    db: AsyncSession,
    created_by: str = "system",
    tenant_id: Optional[str] = None,
) -> Dict[str, int]:
    """Seed hardcoded compliance rules into PlatformRuleORM.

    Idempotent: skips rules that already exist by name+platform+tenant.
    """
    created = 0
    skipped = 0
    for rule_data in _DEFAULT_COMPLIANCE_RULES:
        # Check if already exists
        result = await db.execute(
            select(PlatformRuleORM)
            .where(PlatformRuleORM.name == rule_data["name"])
            .where(PlatformRuleORM.platform == rule_data["platform"])
            .where(PlatformRuleORM.tenant_id == tenant_id)
        )
        existing = result.scalar_one_or_none()
        if existing:
            skipped += 1
            continue

        rule = PlatformRuleORM(
            platform=rule_data["platform"],
            layer=rule_data["layer"],
            name=rule_data["name"],
            description=rule_data["description"],
            condition_json=rule_data["condition_json"],
            action=rule_data["action"],
            priority=rule_data["priority"],
            enabled=True,
            effective_from=_now(),
            created_by=created_by,
            tenant_id=tenant_id,
        )
        db.add(rule)
        created += 1

    await db.commit()
    return {"created": created, "skipped": skipped}


async def clear_platform_rules(db: AsyncSession) -> None:
    await db.execute(delete(PlatformRuleHistoryORM))
    await db.execute(delete(PlatformRuleORM))
    await db.commit()


async def get_attributions_for_content(
    db: AsyncSession, content_id: str
) -> List[Dict]:
    """Query persisted rule attributions for a content."""
    from sqlalchemy import select
    result = await db.execute(
        select(ContentRuleAttributionORM).where(
            ContentRuleAttributionORM.content_id == content_id
        ).order_by(ContentRuleAttributionORM.evaluated_at.desc())
    )
    rows = result.scalars().all()
    return [
        {
            "rule_id": str(r.rule_id),
            "rule_name": r.rule_name,
            "layer": r.layer,
            "action": r.action,
            "matched": r.matched_text,
            "platform": r.platform,
            "evaluated_at": r.evaluated_at.isoformat() if r.evaluated_at else None,
        }
        for r in rows
    ]
