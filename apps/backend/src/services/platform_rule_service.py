"""PlatformRule Engine — L3/L4 dynamic rules + violation attribution.

Extends ComplianceGuard with account-state rules and dynamic risk rules.
Aligned with detailed design §5.5.
"""

import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class PlatformRule:
    id: str
    layer: str  # l1, l2, l3, l4
    name: str
    condition_json: Dict  # rule condition payload
    action: str  # block | warn | suggest
    priority: int
    enabled: bool
    version: int
    effective_from: str
    created_by: str


# ── 内存存储已废弃 (W14迁移至PostgreSQL ORM) ──
# _rule_db/_rule_history 已清空; 规则CRUD已移至 platform_rule_function.py
# 保留 evaluate_l3 / get_violation_attribution 供 publisher_service 使用
_rule_db: Dict[str, PlatformRule] = {}
_rule_history: Dict[str, List[PlatformRule]] = {}
_initialized: bool = False


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _initialize_default_rules() -> None:
    global _initialized
    if _initialized:
        return
    rules = [
        # L3 Account State Rules
        PlatformRule(
            id="R_L3_001",
            layer="l3",
            name="新号日发限制",
            condition_json={
                "type": "frequency",
                "scope": "account_state",
                "condition": "account_age_days<7 AND daily_post_count>=1",
            },
            action="warn",
            priority=100,
            enabled=True,
            version=1,
            effective_from="2026-01-01",
            created_by="system",
        ),
        PlatformRule(
            id="R_L3_002",
            layer="l3",
            name="老号发布频率上限",
            condition_json={
                "type": "frequency",
                "scope": "account_state",
                "condition": "account_age_days>30 AND daily_post_count>=3",
            },
            action="warn",
            priority=100,
            enabled=True,
            version=1,
            effective_from="2026-01-01",
            created_by="system",
        ),
        PlatformRule(
            id="R_L3_003",
            layer="l3",
            name="单日登录次数限制",
            condition_json={
                "type": "frequency",
                "scope": "login",
                "condition": "login_count_today>=3 OR login_fail_count>=2",
            },
            action="block",
            priority=200,
            enabled=True,
            version=1,
            effective_from="2026-01-01",
            created_by="system",
        ),
        # L4 Dynamic Risk Rules
        PlatformRule(
            id="R_L4_001",
            layer="l4",
            name="618期间商业笔记限流",
            condition_json={
                "type": "schedule",
                "scope": "time_range",
                "condition": "month=6 AND day IN [1-18] AND content_type=commercial",
            },
            action="warn",
            priority=50,
            enabled=True,
            version=1,
            effective_from="2026-06-01",
            created_by="system",
        ),
        PlatformRule(
            id="R_L4_002",
            layer="l4",
            name="关键词临时降权",
            condition_json={
                "type": "keyword_regex",
                "scope": "title+body+tags",
                "pattern": "(驱虫药|处方)",
                "case_sensitive": False,
            },
            action="warn",
            priority=50,
            enabled=True,
            version=1,
            effective_from="2026-01-01",
            created_by="system",
        ),
    ]
    for r in rules:
        _rule_db[r.id] = r
        _rule_history[r.id] = []
    _initialized = True


def list_rules(layer: Optional[str] = None) -> List[PlatformRule]:
    _initialize_default_rules()
    rules = list(_rule_db.values())
    if layer:
        rules = [r for r in rules if r.layer == layer]
    return rules


def get_rule(rule_id: str) -> Optional[PlatformRule]:
    _initialize_default_rules()
    return _rule_db.get(rule_id)


def get_rule_history(rule_id: str) -> List[PlatformRule]:
    _initialize_default_rules()
    return list(_rule_history.get(rule_id, []))


def create_rule(data: Dict) -> PlatformRule:
    rule_id = data.get("id") or secrets.token_urlsafe(8)
    rule = PlatformRule(
        id=rule_id,
        layer=data.get("layer", "l4"),
        name=data.get("name", ""),
        condition_json=data.get("condition_json", {}),
        action=data.get("action", "warn"),
        priority=data.get("priority", 0),
        enabled=data.get("enabled", True),
        version=1,
        effective_from=data.get("effective_from", _now()),
        created_by=data.get("created_by", "user"),
    )
    _rule_db[rule_id] = rule
    _rule_history[rule_id] = []
    return rule


def update_rule(rule_id: str, data: Dict) -> Optional[PlatformRule]:
    _initialize_default_rules()
    rule = _rule_db.get(rule_id)
    if not rule:
        return None
    # Archive current version
    hist = _rule_history.get(rule_id, [])
    hist.append(rule)
    _rule_history[rule_id] = hist
    # Create new version
    new_version = rule.version + 1
    new_rule = PlatformRule(
        id=rule_id,
        layer=data.get("layer", rule.layer),
        name=data.get("name", rule.name),
        condition_json=data.get("condition_json", rule.condition_json),
        action=data.get("action", rule.action),
        priority=data.get("priority", rule.priority),
        enabled=data.get("enabled", rule.enabled),
        version=new_version,
        effective_from=data.get("effective_from", _now()),
        created_by=data.get("created_by", rule.created_by),
    )
    _rule_db[rule_id] = new_rule
    return new_rule


def delete_rule(rule_id: str) -> bool:
    if rule_id in _rule_db:
        del _rule_db[rule_id]
        _rule_history.pop(rule_id, None)
        return True
    return False


def evaluate_content_v2(content: Dict, account_state: Optional[Dict] = None) -> Dict:
    """Evaluate content against all active rules."""
    _initialize_default_rules()
    violations = []
    warnings = []
    suggestions = []

    text = f"{content.get('title', '')} {content.get('body', '')} {' '.join(content.get('tags', []))}"

    for rule in _rule_db.values():
        if not rule.enabled:
            continue

        triggered = False
        condition = rule.condition_json

        if condition.get("type") == "keyword":
            keywords = condition.get("keywords", [])
            case_sensitive = condition.get("case_sensitive", False)
            check_text = text if case_sensitive else text.lower()
            for kw in keywords:
                kw_check = kw if case_sensitive else kw.lower()
                if kw_check in check_text:
                    triggered = True
                    break

        elif condition.get("type") == "keyword_pair":
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

        elif condition.get("type") == "keyword_regex":
            import re

            pattern = condition.get("pattern", "")
            if pattern and re.search(
                pattern,
                text,
                re.IGNORECASE if not condition.get("case_sensitive") else 0,
            ):
                triggered = True

        elif condition.get("type") == "frequency":
            # MVP: simplified frequency check
            if account_state:
                cond = condition.get("condition", "")
                if "daily_post_count" in cond:
                    daily_count = account_state.get("daily_post_count", 0)
                    if daily_count >= 1 and "new" in cond:
                        triggered = True
                    if daily_count >= 3 and "old" in cond:
                        triggered = True

        if triggered:
            result = {
                "rule_id": rule.id,
                "layer": rule.layer,
                "name": rule.name,
                "action": rule.action,
            }
            if rule.action == "block":
                violations.append(result)
            elif rule.action == "warn":
                warnings.append(result)
            else:
                suggestions.append(result)

    return {
        "pass": len(violations) == 0,
        "violations": violations,
        "warnings": warnings,
        "suggestions": suggestions,
        "violation_count": len(violations),
        "warning_count": len(warnings),
        "suggestion_count": len(suggestions),
    }


async def evaluate_l3(account_id: str, proposed_publish_at: Optional[str] = None, db=None) -> Dict:
    """Evaluate L3 rules before publisher scheduling.

    Returns:
        {"allowed": bool, "adjusted_at": str|None, "reason": str}
    """
    # 1. Check account daily quota (from 4B enhancement)
    from src.models.account_pool import get_pool_entry, list_pool_entries

    account = get_pool_entry(account_id)
    if account is None:
        for entry in list_pool_entries():
            if entry.account_id == account_id:
                account = entry
                break

    if account and account.quota_exceeded:
        return {
            "allowed": False,
            "adjusted_at": None,
            "reason": f"账号今日配额已用尽 ({account.posts_today}/{account.daily_quota})",
        }

    # 2. Check ORM PlatformRule L3/L4 rules (if db available)
    if db is not None:
        try:
            from src.services import platform_rule_function as prf

            account_state = {"daily_post_count": account.posts_today if account else 0}
            orm_result = await prf.evaluate_content(
                db=db,
                content={},
                platform=account.platform if account else "xiaohongshu",
                account_state=account_state,
            )
            if orm_result.get("violations"):
                return {
                    "allowed": False,
                    "adjusted_at": None,
                    "reason": f"平台规则拦截: {orm_result['violations'][0].get('name', 'L3规则')}",
                }
        except Exception:
            pass  # fallback to legacy

    # 3. Legacy memory-based rules as safety net
    _initialize_default_rules()

    from src.models.publish_task import list_tasks

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    daily_count = 0
    for task in list_tasks():
        if task.account_id == account_id and task.scheduled_at and task.scheduled_at.startswith(today):
            daily_count += 1

    lifecycle = account.lifecycle_phase if account else "mature"
    limits = {"cold_start": 1, "growth": 3, "mature": 5}
    limit = limits.get(lifecycle, 5)

    if daily_count >= limit:
        return {
            "allowed": False,
            "adjusted_at": None,
            "reason": f"Daily publish limit reached ({limit}) for lifecycle {lifecycle}",
        }

    return {"allowed": True, "adjusted_at": None, "reason": ""}


def get_violation_attribution(content_id: str, violations: List[Dict]) -> Dict:
    """Generate violation attribution report."""
    return {
        "content_id": content_id,
        "attribution": [
            {
                "rule_id": v.get("rule_id", ""),
                "rule_name": v.get("name", ""),
                "layer": v.get("layer", ""),
                "action": v.get("action", ""),
                "triggered_reason": v.get("action", ""),
                "recommended_action": v.get("action", ""),
            }
            for v in violations
        ],
    }


def clear_platform_rules() -> None:
    _rule_db.clear()
    _rule_history.clear()
    global _initialized
    _initialized = False
