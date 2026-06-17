"""SkillSmith — Evolved Skill auto-generation engine.

Monitors execution performance and automatically generates L4 (evolved) skills
when trigger conditions are met.
"""

import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional

from src.services import skill_hub


@dataclass
class EvolutionTrigger:
    trigger_id: str
    skill_id: str
    account_id: str
    condition_type: str  # success_rate, ces_streak, mape_threshold
    threshold: float
    current_value: float
    triggered_at: str
    status: str = "pending"  # pending, applied, dismissed


@dataclass
class PerformanceRecord:
    skill_id: str
    account_id: str
    success: bool
    ces: float
    mape: float
    executed_at: str


_trigger_db: Dict[str, EvolutionTrigger] = {}
_performance_db: Dict[str, List[PerformanceRecord]] = {}  # key: "{skill_id}:{account_id}"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _key(skill_id: str, account_id: str) -> str:
    return f"{skill_id}:{account_id}"


def record_performance(skill_id: str, account_id: str, success: bool, ces: float = 0.0, mape: float = 1.0) -> None:
    """Record a skill execution performance metric."""
    key = _key(skill_id, account_id)
    if key not in _performance_db:
        _performance_db[key] = []
    _performance_db[key].append(PerformanceRecord(
        skill_id=skill_id,
        account_id=account_id,
        success=success,
        ces=ces,
        mape=mape,
        executed_at=_now(),
    ))


def check_evolution_opportunities(skill_id: str, account_id: str) -> List[Dict]:
    """Check if any evolution conditions are met for a skill-account pair."""
    key = _key(skill_id, account_id)
    records = _performance_db.get(key, [])
    if not records:
        return []

    opportunities = []

    # Condition 1: Success rate >= 80% over last 5 executions
    recent = records[-5:]
    if len(recent) >= 5:
        success_rate = sum(1 for r in recent if r.success) / len(recent)
        if success_rate >= 0.8:
            opportunities.append({
                "condition_type": "success_rate",
                "threshold": 0.8,
                "current_value": round(success_rate, 2),
                "description": f"近5次执行成功率{success_rate:.0%}，建议进化技能",
            })

    # Condition 2: CES > 40 for 3 consecutive executions
    if len(records) >= 3:
        last3 = records[-3:]
        if all(r.ces > 40 for r in last3):
            avg_ces = sum(r.ces for r in last3) / 3
            opportunities.append({
                "condition_type": "ces_streak",
                "threshold": 40,
                "current_value": round(avg_ces, 2),
                "description": f"连续3次CES>{avg_ces:.0f}，建议进化技能",
            })

    # Condition 3: MAPE < 20%
    recent_mape = [r.mape for r in records if r.mape < 1.0]
    if recent_mape and len(recent_mape) >= 3:
        avg_mape = sum(recent_mape[-3:]) / 3
        if avg_mape < 0.2:
            opportunities.append({
                "condition_type": "mape_threshold",
                "threshold": 0.2,
                "current_value": round(avg_mape, 4),
                "description": f"近3次MAPE={avg_mape:.1%}，预测精准，建议进化技能",
            })

    return opportunities


def generate_evolved_skill(skill_id: str, account_id: str, condition_type: str) -> Optional[Dict]:
    """Generate an L4 evolved skill from a lower-level skill based on performance."""
    source_skill = skill_hub.get_skill(skill_id)
    if not source_skill:
        return None

    key = _key(skill_id, account_id)
    records = _performance_db.get(key, [])
    if not records:
        return None

    # Build evolved skill code based on success patterns
    success_records = [r for r in records if r.success]
    avg_ces = sum(r.ces for r in success_records) / len(success_records) if success_records else 0

    evolved_code = f"""# L4 Evolved Skill — Auto-generated from {source_skill.id}
# Account: {account_id}
# Condition: {condition_type}
# Avg CES: {avg_ces:.1f}

def run(ctx):
    # Evolved parameters based on historical performance
    ctx["persona"] = ctx.get("persona", {{}})
    ctx["persona"]["optimized_for"] = "{account_id}"
    
    # Delegate to original skill logic with tuned parameters
    # (Production: would inline optimized logic here)
    return {{
        "delegated_to": "{source_skill.id}",
        "evolved_params": {{
            "avg_ces": {avg_ces:.1f},
            "executions": {len(records)},
            "successes": {len(success_records)},
        }},
        "note": "L4 evolved skill — parameters tuned from real performance data",
    }}
"""

    evolved_skill = skill_hub.create_skill(
        name=f"{source_skill.name}·进化版",
        description=f"基于{source_skill.name}自动进化的L4技能（触发条件：{condition_type}）",
        level="L4",
        code=evolved_code,
        tags=["evolved", f"from:{source_skill.id}", f"account:{account_id}", condition_type],
        version="1.0.0",
    )

    trigger_id = secrets.token_urlsafe(12)
    trigger = EvolutionTrigger(
        trigger_id=trigger_id,
        skill_id=skill_id,
        account_id=account_id,
        condition_type=condition_type,
        threshold=0,
        current_value=0,
        triggered_at=_now(),
        status="applied",
    )
    _trigger_db[trigger_id] = trigger

    return {
        "evolved_skill_id": evolved_skill.id,
        "source_skill_id": skill_id,
        "account_id": account_id,
        "condition_type": condition_type,
        "trigger_id": trigger_id,
    }


def list_evolution_triggers(status: Optional[str] = None) -> List[EvolutionTrigger]:
    triggers = list(_trigger_db.values())
    if status:
        triggers = [t for t in triggers if t.status == status]
    return sorted(triggers, key=lambda t: t.triggered_at, reverse=True)


def get_evolution_trigger(trigger_id: str) -> Optional[EvolutionTrigger]:
    return _trigger_db.get(trigger_id)


def clear_skill_smith() -> None:
    _trigger_db.clear()
    _performance_db.clear()
