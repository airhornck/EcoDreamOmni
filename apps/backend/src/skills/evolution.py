"""Skill Evolution — v4.0 Phase 3 P3-4.

MVP: Quality scoring + positive sample沉淀 + failure analysis.
Production: Curator Agent evaluation (Phase 2 Meta-Orchestrator).
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class SkillExecutionRecord:
    record_id: str
    skill_id: str
    agent_id: str
    tenant_id: str
    inputs: Dict
    outputs: Dict
    success: bool
    error: str = ""
    latency_ms: int = 0
    created_at: str = ""


@dataclass
class SkillQualityScore:
    skill_id: str
    total_executions: int = 0
    success_count: int = 0
    failure_count: int = 0
    avg_latency_ms: float = 0.0
    score: float = 0.0  # 0.0 - 1.0
    positive_samples: List[Dict] = field(default_factory=list)
    failure_patterns: Dict[str, int] = field(default_factory=dict)


_execution_db: List[SkillExecutionRecord] = []
_quality_scores: Dict[str, SkillQualityScore] = {}


def record_execution(
    skill_id: str,
    agent_id: str,
    tenant_id: str,
    inputs: Dict,
    outputs: Dict,
    success: bool,
    error: str = "",
    latency_ms: int = 0,
) -> SkillExecutionRecord:
    """Record a skill execution for evolution analysis."""
    record = SkillExecutionRecord(
        record_id=f"rec_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{len(_execution_db)}",
        skill_id=skill_id,
        agent_id=agent_id,
        tenant_id=tenant_id,
        inputs=inputs,
        outputs=outputs,
        success=success,
        error=error,
        latency_ms=latency_ms,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    _execution_db.append(record)
    _update_quality_score(record)
    return record


def _update_quality_score(record: SkillExecutionRecord) -> None:
    """Update quality score for a skill based on execution record."""
    qs = _quality_scores.setdefault(record.skill_id, SkillQualityScore(skill_id=record.skill_id))
    qs.total_executions += 1
    if record.success:
        qs.success_count += 1
        qs.positive_samples.append({
            "inputs": record.inputs,
            "outputs": record.outputs,
            "latency_ms": record.latency_ms,
        })
        # Keep only last 100 positive samples
        qs.positive_samples = qs.positive_samples[-100:]
    else:
        qs.failure_count += 1
        error_key = record.error[:50] if record.error else "unknown"
        qs.failure_patterns[error_key] = qs.failure_patterns.get(error_key, 0) + 1

    # Recalculate score
    success_rate = qs.success_count / qs.total_executions if qs.total_executions > 0 else 0.0
    qs.avg_latency_ms = (
        sum(r.latency_ms for r in _execution_db if r.skill_id == record.skill_id) /
        qs.total_executions
    )
    # Score = success_rate * 0.7 + latency_penalty * 0.3
    latency_penalty = max(0, 1.0 - qs.avg_latency_ms / 5000)
    qs.score = round(success_rate * 0.7 + latency_penalty * 0.3, 3)


def get_quality_score(skill_id: str) -> Optional[SkillQualityScore]:
    return _quality_scores.get(skill_id)


def get_evolution_report(skill_id: str) -> Dict[str, Any]:
    """Generate evolution report for a skill."""
    qs = _quality_scores.get(skill_id)
    if not qs:
        return {"skill_id": skill_id, "status": "no_data"}

    # Determine evolution recommendation
    recommendation = "stable"
    if qs.score < 0.5:
        recommendation = "needs_improvement"
    elif qs.score > 0.9 and qs.total_executions > 50:
        recommendation = "candidate_for_promotion"

    top_failures = sorted(qs.failure_patterns.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        "skill_id": skill_id,
        "score": qs.score,
        "total_executions": qs.total_executions,
        "success_rate": round(qs.success_count / qs.total_executions, 3) if qs.total_executions else 0,
        "avg_latency_ms": round(qs.avg_latency_ms, 1),
        "positive_sample_count": len(qs.positive_samples),
        "top_failure_patterns": [{"error": e, "count": c} for e, c in top_failures],
        "recommendation": recommendation,
    }


def get_all_scores() -> List[SkillQualityScore]:
    return list(_quality_scores.values())
