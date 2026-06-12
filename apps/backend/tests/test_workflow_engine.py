"""Tests for Workflow Engine (Phase 2 / PRD V2.6 §10.4).

Red-Green TDD for:
  - Template creation (serial pipeline, publisher must have human approval)
  - Serial execution (node by node)
  - Context passing between nodes
  - Fail strategies (fail_fast, continue, retry_then_fail)
  - Version rollback / activation
  - Node skip / pause / resume
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.services import workflow_engine as we
from src.services.workflow_engine import WorkflowStatus, ExecutionStatus, FailStrategy, NodeType


@pytest.fixture(autouse=True)
def clear_db():
    we._clear_stores()
    we.load_presets()
    yield


# ─── 1. Template Creation ───

def test_create_template():
    tmpl = we.create_template(
        name="Test Workflow",
        nodes=[
            {"node_type": "AGENT", "node_name": "Step 1", "agent_id": "agent-1"},
            {"node_type": "AGENT", "node_name": "Step 2", "agent_id": "agent-2"},
        ],
        owner="alice",
    )
    assert tmpl.id.startswith("wf_")
    assert len(tmpl.nodes) == 2
    assert tmpl.nodes[0].fail_strategy == FailStrategy.FAIL_FAST


def test_create_template_rejects_publisher_without_human_approval():
    with pytest.raises(ValueError) as exc_info:
        we.create_template(
            name="Bad Workflow",
            nodes=[
                {"node_type": "AGENT", "node_name": "Publish", "agent_id": "publisher"},
            ],
        )
    assert "human_approval" in str(exc_info.value)


def test_create_template_allows_publisher_with_human_approval():
    tmpl = we.create_template(
        name="Good Workflow",
        nodes=[
            {"node_type": "AGENT", "node_name": "Gen", "agent_id": "content-forge"},
            {"node_type": "HUMAN_APPROVAL", "node_name": "Review"},
            {"node_type": "AGENT", "node_name": "Publish", "agent_id": "publisher"},
        ],
    )
    assert tmpl is not None


# ─── 2. Preset Templates ───

def test_preset_templates_loaded():
    presets = we.list_templates(source_preset="content_creation_standard")
    assert len(presets) == 1
    assert presets[0].id == "content_creation_standard"
    # Must contain human_approval before publisher
    node_types = [n.node_type for n in presets[0].nodes]
    assert NodeType.HUMAN_APPROVAL in node_types


def test_content_creation_light_preset():
    preset = we.get_template("content_creation_light")
    assert preset is not None
    assert len(preset.nodes) == 7  # v4.0: +keyword_inject +pool-predictor


# ─── 3. Serial Execution ───

def test_start_execution():
    exec = we.start_execution("task_001", "content_creation_light")
    assert exec.status == WorkflowStatus.RUNNING
    assert exec.current_node_index == 0
    assert exec.task_id == "task_001"


def test_execute_next_node_success():
    exec = we.start_execution("task_001", "trend_scout_only")
    result = we.execute_next_node(exec.id, node_output={"trend": "cats"})
    assert result["done"] is True
    assert result["status"] == "COMPLETED"
    updated = we.get_execution(exec.id)
    assert updated.status == WorkflowStatus.COMPLETED
    assert updated.context["trend"] == "cats"


def test_execute_multi_node_pipeline():
    tmpl = we.create_template(
        name="Multi",
        nodes=[
            {"node_type": "AGENT", "node_name": "A", "agent_id": "a1"},
            {"node_type": "AGENT", "node_name": "B", "agent_id": "a2"},
        ],
    )
    exec = we.start_execution("task_002", tmpl.id)
    r1 = we.execute_next_node(exec.id, node_output={"step1": "ok"})
    assert r1["done"] is False
    assert r1["next_node"] == 1
    r2 = we.execute_next_node(exec.id, node_output={"step2": "ok"})
    assert r2["done"] is True
    assert we.get_execution(exec.id).context == {"step1": "ok", "step2": "ok"}


# ─── 4. Context Passing ───

def test_context_passes_between_nodes():
    tmpl = we.create_template(
        name="Context",
        nodes=[
            {"node_type": "AGENT", "node_name": "Generate", "agent_id": "forge"},
            {"node_type": "AGENT", "node_name": "Check", "agent_id": "guard"},
        ],
    )
    exec = we.start_execution("task_003", tmpl.id)
    we.execute_next_node(exec.id, node_output={"content": "hello", "score": 95})
    ctx = we.get_context(exec.id)
    assert ctx["content"] == "hello"
    we.execute_next_node(exec.id, node_output={"compliance": "passed"})
    ctx = we.get_context(exec.id)
    assert ctx["score"] == 95
    assert ctx["compliance"] == "passed"


# ─── 5. Fail Strategies ───

def test_fail_fast_stops_pipeline():
    tmpl = we.create_template(
        name="FailFast",
        nodes=[
            {"node_type": "AGENT", "node_name": "A", "agent_id": "a1"},
            {"node_type": "AGENT", "node_name": "B", "agent_id": "a2"},
        ],
    )
    exec = we.start_execution("task_004", tmpl.id)
    r1 = we.execute_next_node(exec.id, node_error="boom")
    assert r1["done"] is True
    assert r1["status"] == "FAILED"
    assert we.get_execution(exec.id).status == WorkflowStatus.FAILED


def test_continue_strategy_ignores_failure():
    tmpl = we.create_template(
        name="Continue",
        nodes=[
            {"node_type": "AGENT", "node_name": "A", "agent_id": "a1", "fail_strategy": "CONTINUE"},
            {"node_type": "AGENT", "node_name": "B", "agent_id": "a2"},
        ],
    )
    exec = we.start_execution("task_005", tmpl.id)
    r1 = we.execute_next_node(exec.id, node_error="minor issue")
    assert r1["done"] is False
    assert r1["next_node"] == 1
    r2 = we.execute_next_node(exec.id, node_output={"recovered": True})
    assert r2["done"] is True


def test_retry_then_fail_retries_once():
    tmpl = we.create_template(
        name="Retry",
        nodes=[
            {"node_type": "AGENT", "node_name": "A", "agent_id": "a1", "fail_strategy": "RETRY_THEN_FAIL"},
        ],
    )
    exec = we.start_execution("task_006", tmpl.id)
    r1 = we.execute_next_node(exec.id, node_error="timeout")
    assert r1["retrying"] is True
    assert r1["node"] == 0
    # Second failure should fail
    r2 = we.execute_next_node(exec.id, node_error="timeout again")
    assert r2["done"] is True
    assert r2["status"] == "FAILED"


def test_retry_then_fail_succeeds_on_retry():
    tmpl = we.create_template(
        name="RetryOK",
        nodes=[
            {"node_type": "AGENT", "node_name": "A", "agent_id": "a1", "fail_strategy": "RETRY_THEN_FAIL"},
        ],
    )
    exec = we.start_execution("task_007", tmpl.id)
    r1 = we.execute_next_node(exec.id, node_error="timeout")
    assert r1["retrying"] is True
    r2 = we.execute_next_node(exec.id, node_output={"ok": True})
    assert r2["done"] is True
    assert r2["status"] == "COMPLETED"


# ─── 6. Pause / Resume / Cancel ───

def test_pause_and_resume():
    tmpl = we.create_template(
        name="PauseTest",
        nodes=[
            {"node_type": "AGENT", "node_name": "A", "agent_id": "a1"},
            {"node_type": "AGENT", "node_name": "B", "agent_id": "a2"},
        ],
    )
    exec = we.start_execution("task_008", tmpl.id)
    we.pause_execution(exec.id)
    assert we.get_execution(exec.id).status == WorkflowStatus.PAUSED
    we.resume_execution(exec.id)
    assert we.get_execution(exec.id).status == WorkflowStatus.RUNNING


def test_cancel_execution():
    tmpl = we.create_template(
        name="CancelTest",
        nodes=[
            {"node_type": "AGENT", "node_name": "A", "agent_id": "a1"},
        ],
    )
    exec = we.start_execution("task_009", tmpl.id)
    we.cancel_execution(exec.id)
    assert we.get_execution(exec.id).status == WorkflowStatus.CANCELLED


# ─── 7. Node Execution Records ───

def test_node_executions_recorded():
    tmpl = we.create_template(
        name="NodeRec",
        nodes=[
            {"node_type": "AGENT", "node_name": "A", "agent_id": "a1"},
        ],
    )
    exec = we.start_execution("task_010", tmpl.id)
    we.execute_next_node(exec.id, node_output={"x": 1})
    nodes = we.get_node_executions(exec.id)
    assert len(nodes) == 1
    assert nodes[0].status == ExecutionStatus.SUCCESS
    assert nodes[0].duration_ms is not None


# ─── 8. List & Filter ───

def test_list_executions_filter():
    tmpl = we.create_template(
        name="List",
        nodes=[
            {"node_type": "AGENT", "node_name": "A", "agent_id": "a1"},
        ],
    )
    e1 = we.start_execution("t1", tmpl.id)
    e2 = we.start_execution("t2", tmpl.id)
    we.execute_next_node(e1.id)
    we.execute_next_node(e2.id)
    completed = we.list_executions(status="COMPLETED")
    assert len(completed) == 2


# ─── 9. Integration: full workflow lifecycle ───

def test_full_workflow_lifecycle():
    # Create custom template
    tmpl = we.create_template(
        name="Custom Pipeline",
        nodes=[
            {"node_type": "AGENT", "node_name": "Generate", "agent_id": "content-forge"},
            {"node_type": "AGENT", "node_name": "Predict", "agent_id": "pool-predictor", "fail_strategy": "CONTINUE"},
            {"node_type": "HUMAN_APPROVAL", "node_name": "Review"},
        ],
        owner="alice",
    )
    assert tmpl.nodes[2].node_type == NodeType.HUMAN_APPROVAL

    # Start and run through
    exec = we.start_execution("task_full", tmpl.id)
    r1 = we.execute_next_node(exec.id, node_output={"content": "hello world"})
    assert r1["done"] is False
    r2 = we.execute_next_node(exec.id, node_error="predictor offline")
    assert r2["done"] is False  # CONTINUE strategy
    r3 = we.execute_next_node(exec.id)
    assert r3["done"] is True
    assert r3["status"] == "COMPLETED"

    # Context accumulated
    ctx = we.get_context(exec.id)
    assert ctx["content"] == "hello world"

    # Node executions recorded
    nodes = we.get_node_executions(exec.id)
    assert len(nodes) == 3
    assert nodes[1].status == ExecutionStatus.FAILED  # predictor failed but continued
    assert nodes[2].status == ExecutionStatus.SUCCESS
