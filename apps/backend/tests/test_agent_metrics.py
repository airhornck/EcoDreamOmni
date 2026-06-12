"""Tests for AgentMetrics (W16).

Red-Green TDD for:
  - Task recording & listing
  - Agent metrics aggregation (completion rate, latency percentiles, cost)
  - Overall metrics
  - Quality scoring
  - Cost attribution by agent / by content
"""

import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.services import agent_metrics as am
from src.services.agent_metrics import TaskOutcome


@pytest.fixture(autouse=True)
def clear_db():
    am._task_db.clear()
    am._metric_cache.clear()
    yield


# ─── Task Recording ───

def test_record_task():
    now = am._now()
    task = am.record_task(
        agent_id="agt-1", agent_role="CONTENT_FORGE", content_id="c-1",
        outcome="success", start_time=now, end_time=now,
        duration_ms=5000, token_count=200, cost_usd=0.004,
        model_version="gpt-4o", pipeline_type="CONTENT_CREATION",
    )
    assert task.agent_id == "agt-1"
    assert task.outcome == TaskOutcome.SUCCESS
    assert task.duration_ms == 5000


def test_list_tasks_filter():
    now = am._now()
    am.record_task("agt-1", "CF", "c-1", "success", now)
    am.record_task("agt-2", "CG", "c-2", "failure", now)
    tasks = am.list_tasks(agent_id="agt-1")
    assert len(tasks) == 1
    assert tasks[0]["agent_id"] == "agt-1"


def test_list_tasks_by_outcome():
    now = am._now()
    am.record_task("agt-1", "CF", "c-1", "success", now)
    am.record_task("agt-1", "CF", "c-2", "failure", now)
    failed = am.list_tasks(outcome="failure")
    assert len(failed) == 1
    assert failed[0]["outcome"] == "failure"


# ─── Metrics Aggregation ───

def test_compute_agent_metrics():
    now = am._now()
    am.record_task("agt-1", "CF", "c-1", "success", now, duration_ms=1000, token_count=100, cost_usd=0.002)
    am.record_task("agt-1", "CF", "c-2", "success", now, duration_ms=2000, token_count=150, cost_usd=0.003)
    am.record_task("agt-1", "CF", "c-3", "failure", now, duration_ms=3000, token_count=50, cost_usd=0.001)

    metric = am.compute_agent_metrics("agt-1", window_minutes=60)
    assert metric is not None
    assert metric.total_tasks == 3
    assert metric.success_count == 2
    assert metric.failure_count == 1
    assert metric.avg_duration_ms == 2000.0
    assert metric.total_tokens == 300
    assert metric.total_cost_usd == pytest.approx(0.006)


def test_get_agent_metrics():
    now = am._now()
    am.record_task("agt-1", "CF", "c-1", "success", now, duration_ms=1000, token_count=100, cost_usd=0.002)
    metrics = am.get_agent_metrics("agt-1")
    assert metrics is not None
    assert metrics["completion_rate"] == 1.0
    assert metrics["total_tokens"] == 100


def test_get_agent_metrics_no_data():
    assert am.get_agent_metrics("nonexistent") is None


def test_latency_percentiles():
    now = am._now()
    for i in range(1, 11):
        am.record_task("agt-1", "CF", f"c-{i}", "success", now, duration_ms=i * 100)

    metric = am.compute_agent_metrics("agt-1", window_minutes=60)
    assert metric is not None
    assert metric.p50_duration_ms == 550.0  # median of 100..1000
    assert metric.p95_duration_ms == 955.0
    assert metric.p99_duration_ms == 991.0


# ─── Overall Metrics ───

def test_overall_metrics():
    now = am._now()
    am.record_task("agt-1", "CF", "c-1", "success", now, duration_ms=1000, token_count=100, cost_usd=0.002)
    am.record_task("agt-2", "CG", "c-2", "failure", now, duration_ms=500, token_count=50, cost_usd=0.001)

    overall = am.get_overall_metrics(window_minutes=60)
    assert overall["total_tasks"] == 2
    assert overall["total_agents"] == 2
    assert overall["overall_completion_rate"] == 0.5
    assert overall["total_tokens"] == 150


# ─── Quality Scoring ───

def test_submit_quality_score():
    now = am._now()
    task = am.record_task("agt-1", "CF", "c-1", "success", now)
    updated = am.submit_quality_score(task.task_id, 85.5)
    assert updated is not None
    assert updated.quality_score == 85.5


def test_submit_quality_score_clamped():
    now = am._now()
    task = am.record_task("agt-1", "CF", "c-1", "success", now)
    am.submit_quality_score(task.task_id, 150)
    assert task.quality_score == 100.0
    am.submit_quality_score(task.task_id, -10)
    assert task.quality_score == 0.0


def test_avg_quality_score():
    now = am._now()
    t1 = am.record_task("agt-1", "CF", "c-1", "success", now)
    t2 = am.record_task("agt-1", "CF", "c-2", "success", now)
    am.submit_quality_score(t1.task_id, 80)
    am.submit_quality_score(t2.task_id, 90)
    metric = am.compute_agent_metrics("agt-1", window_minutes=60)
    assert metric is not None
    assert metric.avg_quality_score == 85.0


# ─── Cost Attribution ───

def test_cost_by_agent():
    now = am._now()
    am.record_task("agt-1", "CF", "c-1", "success", now, token_count=100, cost_usd=0.002)
    am.record_task("agt-2", "CG", "c-2", "success", now, token_count=200, cost_usd=0.005)
    breakdown = am.get_cost_by_agent(window_minutes=60)
    assert len(breakdown) == 2
    # Sorted by cost descending
    assert breakdown[0]["agent_id"] == "agt-2"
    assert breakdown[0]["total_cost_usd"] == pytest.approx(0.005)


def test_cost_by_content():
    now = am._now()
    am.record_task("agt-1", "CF", "c-x", "success", now, token_count=100, cost_usd=0.002)
    am.record_task("agt-2", "CG", "c-x", "success", now, token_count=200, cost_usd=0.005)
    breakdown = am.get_cost_by_content("c-x")
    assert len(breakdown) == 2
    ids = {b["agent_id"] for b in breakdown}
    assert ids == {"agt-1", "agt-2"}
