"""ReAct Orchestration Loop — H1 core for Agent Harness.

Think → Act → Observe → (Verify) → Loop

Each ReAct step:
  1. THINK   — reasoning about the current state and next action
  2. ACT     — invoke tool(s) via Tool Registry
  3. OBSERVE — capture tool outputs
  4. VERIFY  — (optional) run verification loop
  5. MEMORY  — persist short-term + checkpoint

Sessions are identified by `session_id`. Each session has:
  - A ContextWindow (context.py)
  - A Plan (planning.py)
  - Checkpoints (state.py)
  - Short-term Memory (memory.py)

Aligned with dev-plan H1: "ReAct loop + Tool Registry".
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

from src.harness import context, memory, planning, state, tool_registry, verification


class ReActPhase(str, Enum):
    THINK = "think"
    ACT = "act"
    OBSERVE = "observe"
    VERIFY = "verify"
    DONE = "done"
    FAILED = "failed"


@dataclass
class ReActStep:
    step_number: int
    phase: ReActPhase
    thought: str = ""
    action: Optional[Dict[str, Any]] = None
    observation: Optional[Dict[str, Any]] = None
    verify_result: Optional[Dict[str, Any]] = None
    timestamp: str = ""


@dataclass
class ReActSession:
    session_id: str
    agent_id: Optional[str]
    goal: str
    plan_id: str
    steps: List[ReActStep] = field(default_factory=list)
    status: str = "pending"  # pending | running | paused | done | failed
    current_phase: ReActPhase = ReActPhase.THINK
    created_at: str = ""


_sessions: Dict[str, ReActSession] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─── Session Lifecycle ───

def create_session(goal: str, agent_id: Optional[str] = None) -> ReActSession:
    session_id = str(uuid.uuid4())[:12]
    plan = planning.create_plan(goal)
    session = ReActSession(
        session_id=session_id,
        agent_id=agent_id,
        goal=goal,
        plan_id=plan.plan_id,
        created_at=_now(),
    )
    _sessions[session_id] = session
    # Init context window
    context.create_window(session_id)
    context.add_message(session_id, "system", f"Goal: {goal}", pinned=True)
    # Init short-term memory
    memory.short_term_put(session_id, "goal", goal, role="system")
    return session


def get_session(session_id: str) -> Optional[ReActSession]:
    return _sessions.get(session_id)


def list_sessions() -> List[ReActSession]:
    return list(_sessions.values())


def pause_session(session_id: str) -> bool:
    s = _sessions.get(session_id)
    if s and s.status == "running":
        s.status = "paused"
        planning.pause_plan(s.plan_id)
        return True
    return False


def resume_session(session_id: str) -> bool:
    s = _sessions.get(session_id)
    if s and s.status == "paused":
        s.status = "running"
        planning.resume_plan(s.plan_id)
        return True
    return False


# ─── ReAct Step Execution ───

def _think(session: ReActSession) -> str:
    """THINK phase: determine next action based on plan state."""
    plan = planning.get_plan(session.plan_id)
    if not plan:
        return "No plan found — terminating."

    pending = [t for t in plan.todos if t.status == planning.TodoStatus.PENDING]
    in_progress = [t for t in plan.todos if t.status == planning.TodoStatus.IN_PROGRESS]

    if not pending and not in_progress:
        return "All tasks completed. Goal achieved."

    if in_progress:
        todo = in_progress[0]
        return f"Continuing task: {todo.description}"

    next_todo = pending[0]
    return f"Next task: {next_todo.description} (tool={next_todo.tool_id})"


def _act(session: ReActSession, thought: str) -> Dict[str, Any]:
    """ACT phase: advance plan and invoke tool if needed."""
    plan = planning.get_plan(session.plan_id)
    if not plan:
        return {"success": False, "error": "Plan not found"}

    todo = planning.advance_plan(plan.plan_id)
    if todo is None:
        return {"success": True, "status": "done", "message": "No more tasks"}

    if todo.tool_id:
        result = tool_registry.invoke_tool(todo.tool_id, todo.tool_input)
        if result["success"]:
            planning.update_todo(plan.plan_id, todo.id, planning.TodoStatus.DONE, result=result)
        else:
            planning.update_todo(plan.plan_id, todo.id, planning.TodoStatus.FAILED, error=result.get("error"))
        return {
            "success": result["success"],
            "tool_id": todo.tool_id,
            "todo_id": todo.id,
            "result": result,
        }
    else:
        planning.update_todo(plan.plan_id, todo.id, planning.TodoStatus.DONE)
        return {"success": True, "status": "manual", "todo_id": todo.id}


def _observe(session: ReActSession, action_result: Dict[str, Any]) -> Dict[str, Any]:
    """OBSERVE phase: capture and log tool output."""
    observation = {
        "step_number": len(session.steps) + 1,
        "action_result": action_result,
        "plan_status": planning.get_plan(session.plan_id).status if planning.get_plan(session.plan_id) else "unknown",
    }
    # Short-term memory
    memory.short_term_put(
        session.session_id,
        f"step_{observation['step_number']}",
        str(action_result.get("result", "")),
        role="tool" if action_result.get("tool_id") else "system",
    )
    # Context window
    context.add_message(
        session.session_id,
        "assistant" if action_result.get("success") else "system",
        f"Step {observation['step_number']}: {action_result.get('result', action_result.get('error', 'N/A'))}",
    )
    return observation


def _verify(session: ReActSession, tool_outputs: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """VERIFY phase: optional verification for critical paths."""
    plan = planning.get_plan(session.plan_id)
    if not plan:
        return None

    # Only verify if any todo involves compliance or publishing
    critical_tools = {"compliance-check", "publish-schedule", "health-score"}
    has_critical = any(t.tool_id in critical_tools for t in plan.todos)
    if not has_critical:
        return None

    report = verification.run_verification(
        task_id=session.session_id,
        tool_outputs=tool_outputs,
        state={"plan_status": plan.status, "agent_id": session.agent_id},
        assertions=[
            {"type": "min_success", "min_count": 1},
        ],
    )
    return {
        "passed": report.overall_passed,
        "summary": report.summary,
        "steps": [
            {
                "step_name": s.step_name,
                "passed": s.verify_passed,
                "notes": s.verify_notes,
            }
            for s in report.steps
        ],
    }


def run_step(session_id: str) -> Dict[str, Any]:
    """Execute one full ReAct step (Think → Act → Observe → Verify)."""
    session = _sessions.get(session_id)
    if not session:
        return {"success": False, "error": "Session not found"}
    if session.status in ("done", "failed"):
        return {"success": False, "error": f"Session already {session.status}"}

    session.status = "running"
    step_number = len(session.steps) + 1

    # THINK
    session.current_phase = ReActPhase.THINK
    thought = _think(session)
    context.add_message(session_id, "assistant", f"Thought: {thought}")

    # ACT
    session.current_phase = ReActPhase.ACT
    action_result = _act(session, thought)

    # OBSERVE
    session.current_phase = ReActPhase.OBSERVE
    observation = _observe(session, action_result)

    # VERIFY (optional)
    session.current_phase = ReActPhase.VERIFY
    verify_result = _verify(session, [action_result])

    # Build step record
    step = ReActStep(
        step_number=step_number,
        phase=ReActPhase.DONE if action_result.get("status") == "done" else ReActPhase.OBSERVE,
        thought=thought,
        action=action_result,
        observation=observation,
        verify_result=verify_result,
        timestamp=_now(),
    )
    session.steps.append(step)

    # Check session completion
    plan = planning.get_plan(session.plan_id)
    if plan and plan.status == "done":
        session.status = "done"
        session.current_phase = ReActPhase.DONE
        # Save final checkpoint
        state.save_checkpoint(
            session_id=session_id,
            agent_id=session.agent_id,
            step_number=step_number,
            plan_id=session.plan_id,
            tool_outputs=[action_result],
            verification_result=verify_result,
            state_data={"status": "done", "goal": session.goal},
        )
    elif not action_result.get("success"):
        session.status = "failed"
        session.current_phase = ReActPhase.FAILED

    return {
        "success": action_result.get("success", False),
        "session_id": session_id,
        "step_number": step_number,
        "phase": session.current_phase.value,
        "thought": thought,
        "action": action_result,
        "observation": observation,
        "verify": verify_result,
        "session_status": session.status,
    }


def run_session(session_id: str, max_steps: int = 20) -> Dict[str, Any]:
    """Run a session to completion (or failure)."""
    steps = 0
    while steps < max_steps:
        result = run_step(session_id)
        steps += 1
        session_status = result.get("session_status", "failed")
        if not result["success"]:
            return {"success": False, "error": result.get("action", {}).get("error"), "steps": steps, "session_status": session_status}
        if session_status in ("done", "failed"):
            return {"success": session_status == "done", "steps": steps, "session_status": session_status}
    return {"success": False, "error": "Max steps exceeded", "steps": steps, "session_status": "failed"}


def get_session_summary(session_id: str) -> Dict[str, Any]:
    """Get a human-readable summary of a session."""
    session = _sessions.get(session_id)
    if not session:
        return {"error": "Session not found"}

    plan = planning.get_plan(session.plan_id)
    return {
        "session_id": session_id,
        "goal": session.goal,
        "status": session.status,
        "total_steps": len(session.steps),
        "plan_status": plan.status if plan else "unknown",
        "todos_completed": sum(1 for t in (plan.todos if plan else []) if t.status == planning.TodoStatus.DONE),
        "todos_total": len(plan.todos) if plan else 0,
        "created_at": session.created_at,
        "latest_thought": session.steps[-1].thought if session.steps else None,
    }
