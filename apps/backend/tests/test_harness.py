"""Tests for Agent Harness H1–H6.

Red-Green TDD: each test validates a harness module.
Coverage target: ≥80% of harness/ directory.
"""


# Ensure src is on path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.harness import (
    core as react,
    context,
    memory,
    planning,
    state,
    subagent,
    tool_registry,
    verification,
)
from src.harness.subagent import SubagentMode


# ─── Tool Registry ───

def test_tool_registry_list_tools():
    tools = tool_registry.list_tools()
    assert isinstance(tools, list)
    # At least the 8 built-in skills should be active
    assert len(tools) >= 8


def test_tool_registry_get_tool():
    tools = tool_registry.list_tools()
    if tools:
        t = tool_registry.get_tool(tools[0].tool_id)
        assert t is not None
        assert t.tool_id == tools[0].tool_id


def test_tool_registry_get_tool_missing():
    assert tool_registry.get_tool("nonexistent-tool-999") is None


def test_tool_registry_invoke_tool():
    tools = tool_registry.list_tools()
    if tools:
        result = tool_registry.invoke_tool(tools[0].tool_id, {"test": True})
        assert "success" in result
        assert "tool_id" in result
        assert "elapsed_ms" in result


def test_tool_registry_resolve_tools_for_agent():
    tools = tool_registry.resolve_tools_for_agent("agent-001")
    assert isinstance(tools, list)
    assert len(tools) >= 8


# ─── Planning ───

def test_planning_create_plan():
    plan = planning.create_plan("Generate a content draft about dog nutrition")
    assert plan.plan_id
    assert plan.goal == "Generate a content draft about dog nutrition"
    assert len(plan.todos) > 0
    assert plan.status == "pending"


def test_planning_create_plan_publish():
    plan = planning.create_plan("Schedule publish for account A")
    assert any("publish" in t.description.lower() or "schedule" in t.description.lower() for t in plan.todos)


def test_planning_create_plan_compliance():
    plan = planning.create_plan("Run compliance audit")
    assert any("compliance" in t.description.lower() or "rule" in t.description.lower() for t in plan.todos)


def test_planning_get_plan():
    plan = planning.create_plan("Test get plan")
    fetched = planning.get_plan(plan.plan_id)
    assert fetched is not None
    assert fetched.plan_id == plan.plan_id


def test_planning_advance_plan():
    plan = planning.create_plan("Test advance")
    todo = planning.advance_plan(plan.plan_id)
    assert todo is not None
    assert todo.status == planning.TodoStatus.IN_PROGRESS


def test_planning_update_todo():
    plan = planning.create_plan("Test update todo")
    todo = planning.advance_plan(plan.plan_id)
    ok = planning.update_todo(plan.plan_id, todo.id, planning.TodoStatus.DONE, result={"ok": True})
    assert ok is True
    updated = planning.get_plan(plan.plan_id)
    assert any(t.status == planning.TodoStatus.DONE for t in updated.todos)


def test_planning_pause_resume_cancel():
    plan = planning.create_plan("Test lifecycle")
    assert planning.pause_plan(plan.plan_id) is True
    assert planning.get_plan(plan.plan_id).status == "paused"
    assert planning.resume_plan(plan.plan_id) is True
    assert planning.get_plan(plan.plan_id).status == "running"
    assert planning.cancel_plan(plan.plan_id) is True
    assert planning.get_plan(plan.plan_id).status == "failed"


# ─── Verification ───

def test_verification_all_success_pass():
    report = verification.run_verification(
        task_id="task-1",
        tool_outputs=[{"success": True}, {"success": True}],
        state={"status": "ok"},
        assertions=[{"type": "all_success", "expected": True}],
    )
    assert report.overall_passed is True


def test_verification_all_success_fail():
    report = verification.run_verification(
        task_id="task-2",
        tool_outputs=[{"success": True}, {"success": False}],
        state={"status": "ok"},
        assertions=[{"type": "all_success", "expected": True}],
    )
    assert report.overall_passed is False


def test_verification_min_success():
    report = verification.run_verification(
        task_id="task-3",
        tool_outputs=[{"success": True}, {"success": False}],
        state={},
        assertions=[{"type": "min_success", "min_count": 1}],
    )
    assert report.overall_passed is True


def test_verification_field_eq():
    report = verification.run_verification(
        task_id="task-4",
        tool_outputs=[],
        state={"status": "approved"},
        assertions=[{"type": "field_eq", "field": "state.status", "expected": "approved"}],
    )
    assert report.overall_passed is True


def test_verification_field_eq_fail():
    report = verification.run_verification(
        task_id="task-5",
        tool_outputs=[],
        state={"status": "rejected"},
        assertions=[{"type": "field_eq", "field": "state.status", "expected": "approved"}],
    )
    assert report.overall_passed is False


# ─── Context ───

def test_context_create_window():
    win = context.create_window("sess-ctx-1")
    assert win is not None
    assert len(win.messages) == 0


def test_context_add_message():
    context.create_window("sess-ctx-2")
    win = context.add_message("sess-ctx-2", "user", "Hello")
    assert len(win.messages) == 1


def test_context_get_messages():
    context.create_window("sess-ctx-3")
    context.add_message("sess-ctx-3", "user", "Hello")
    msgs = context.get_messages("sess-ctx-3")
    assert len(msgs) == 1
    assert msgs[0]["role"] == "user"


def test_context_compaction():
    context.create_window("sess-ctx-4", max_messages=3)
    context.add_message("sess-ctx-4", "user", "msg1")
    context.add_message("sess-ctx-4", "user", "msg2")
    context.add_message("sess-ctx-4", "user", "msg3")
    # Should trigger compaction
    context.add_message("sess-ctx-4", "user", "msg4")
    stats = context.window_stats("sess-ctx-4")
    assert stats["exists"] is True
    assert stats["message_count"] <= 3


def test_context_pin_message():
    context.create_window("sess-ctx-5")
    context.add_message("sess-ctx-5", "system", "Important", pinned=True)
    stats = context.window_stats("sess-ctx-5")
    assert stats["pinned_count"] == 1


def test_context_window_stats():
    context.create_window("sess-ctx-6")
    context.add_message("sess-ctx-6", "user", "Test message")
    stats = context.window_stats("sess-ctx-6")
    assert stats["exists"] is True
    assert stats["message_count"] == 1
    assert stats["approx_tokens"] > 0


# ─── Memory ───

def test_memory_short_term():
    memory.short_term_put("sess-mem-1", "key1", "value1")
    entries = memory.short_term_get("sess-mem-1")
    assert len(entries) == 1
    assert entries[0].key == "key1"


def test_memory_working():
    memory.working_put("pipeline-1", {"kpi": 42})
    assert memory.working_get("pipeline-1") == {"kpi": 42}


def test_memory_long_term():
    memory.long_term_append("tenant-1", {"event": "test", "tags": ["audit"]})
    records = memory.long_term_query("tenant-1", tag="audit")
    assert len(records) == 1
    assert records[0]["event"] == "test"


# ─── State ───

def test_state_save_checkpoint():
    cp = state.save_checkpoint("sess-state-1", step_number=1, state_data={"x": 1})
    assert cp.checkpoint_id
    assert cp.step_number == 1


def test_state_get_checkpoints():
    state.save_checkpoint("sess-state-2", step_number=1)
    state.save_checkpoint("sess-state-2", step_number=2)
    cps = state.get_checkpoints("sess-state-2")
    assert len(cps) == 2


def test_state_rollback():
    state.save_checkpoint("sess-state-3", step_number=1, state_data={"v": 1})
    cp2 = state.save_checkpoint("sess-state-3", step_number=2, state_data={"v": 2})
    state.save_checkpoint("sess-state-3", step_number=3, state_data={"v": 3})
    rolled = state.rollback_to_checkpoint("sess-state-3", cp2.checkpoint_id)
    assert rolled is not None
    assert rolled.step_number == 2
    assert len(state.get_checkpoints("sess-state-3")) == 2


def test_state_session_stats():
    state.save_checkpoint("sess-state-4", step_number=1)
    stats = state.session_stats("sess-state-4")
    assert stats["checkpoint_count"] == 1
    assert stats["latest_step"] == 1


# ─── Subagent ───

def test_subagent_create():
    sa = subagent.create_subagent(SubagentMode.INITIALIZER, "Research dog food trends")
    assert sa.subagent_id
    assert sa.mode == SubagentMode.INITIALIZER
    assert sa.plan_id


def test_subagent_list():
    subagent.create_subagent(SubagentMode.CODING, "Generate skill code")
    agents = subagent.list_subagents()
    assert len(agents) >= 1


def test_subagent_run_step():
    sa = subagent.create_subagent(SubagentMode.INITIALIZER, "Simple test task")
    result = subagent.run_subagent_step(sa.subagent_id)
    assert "success" in result


def test_subagent_run_to_completion():
    sa = subagent.create_subagent(SubagentMode.INITIALIZER, "Run to completion test")
    result = subagent.run_subagent_to_completion(sa.subagent_id, max_steps=10)
    assert "success" in result


def test_subagent_cancel():
    sa = subagent.create_subagent(SubagentMode.CODING, "Cancel me")
    assert subagent.cancel_subagent(sa.subagent_id) is True
    assert subagent.get_subagent(sa.subagent_id).status == subagent.SubagentStatus.FAILED


# ─── ReAct Core ───

def test_react_create_session():
    sess = react.create_session("Generate content about cats")
    assert sess.session_id
    assert sess.goal == "Generate content about cats"
    assert sess.status == "pending"
    assert sess.plan_id


def test_react_get_session():
    sess = react.create_session("Test get session")
    fetched = react.get_session(sess.session_id)
    assert fetched is not None
    assert fetched.session_id == sess.session_id


def test_react_run_step():
    sess = react.create_session("Run one step")
    result = react.run_step(sess.session_id)
    assert result["success"] is True
    assert result["session_id"] == sess.session_id
    assert result["step_number"] == 1


def test_react_run_to_completion():
    sess = react.create_session("Run to completion test")
    result = react.run_session(sess.session_id, max_steps=10)
    assert "success" in result
    assert result["session_status"] in ("done", "failed")


def test_react_pause_resume():
    sess = react.create_session("Pause resume test")
    react.run_step(sess.session_id)  # start running
    assert react.pause_session(sess.session_id) is True
    assert react.get_session(sess.session_id).status == "paused"
    assert react.resume_session(sess.session_id) is True
    assert react.get_session(sess.session_id).status in ("running", "done", "failed")


def test_react_session_summary():
    sess = react.create_session("Summary test")
    react.run_step(sess.session_id)
    summary = react.get_session_summary(sess.session_id)
    assert summary["session_id"] == sess.session_id
    assert summary["total_steps"] >= 1


# ─── Integration: full ReAct with verification ───

def test_react_with_critical_tools():
    """A compliance-heavy goal should trigger verification."""
    sess = react.create_session("Run compliance audit and publish")
    result = react.run_session(sess.session_id, max_steps=10)
    # Should complete or fail gracefully
    assert "session_status" in result
