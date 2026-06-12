"""Subagent Orchestrator — dual-mode subagent management.

Aligned with dev-plan H5: "Subagent Orchestrator: Initializer + Coding dual mode".

Modes:
  - "initializer" → Context building, research, data gathering
  - "coding"      → Code generation, skill evolution, sandboxed execution

Each subagent is a lightweight task runner with its own plan + tool subset.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

from src.harness import planning, tool_registry


class SubagentMode(str, Enum):
    INITIALIZER = "initializer"
    CODING = "coding"


class SubagentStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


@dataclass
class Subagent:
    subagent_id: str
    mode: SubagentMode
    task: str
    status: SubagentStatus = SubagentStatus.PENDING
    plan_id: Optional[str] = None
    tool_ids: List[str] = field(default_factory=list)
    result: Any = None
    error: Optional[str] = None
    parent_agent_id: Optional[str] = None


_subagents: Dict[str, Subagent] = {}


# Tool subsets per mode (whitelist)
_INITIALIZER_TOOLS = [
    "content-generate",
    "compliance-check",
    "fingerprint-gen",
    "health-score",
    "engagement-predict",
]

_CODING_TOOLS = [
    "content-generate",
    "compliance-check",
    "fingerprint-gen",
    "health-score",
    "engagement-predict",
    "publish-schedule",
    "qr-login",
    "session-check",
]


def create_subagent(
    mode: SubagentMode,
    task: str,
    parent_agent_id: Optional[str] = None,
    custom_tools: Optional[List[str]] = None,
) -> Subagent:
    subagent_id = str(uuid.uuid4())[:8]
    tool_ids = custom_tools or (_INITIALIZER_TOOLS if mode == SubagentMode.INITIALIZER else _CODING_TOOLS)

    # Create plan via planning engine
    plan = planning.create_plan(task)
    # Filter todos to allowed tools
    plan.todos = [t for t in plan.todos if t.tool_id is None or t.tool_id in tool_ids]

    subagent = Subagent(
        subagent_id=subagent_id,
        mode=mode,
        task=task,
        plan_id=plan.plan_id,
        tool_ids=tool_ids,
        parent_agent_id=parent_agent_id,
    )
    _subagents[subagent_id] = subagent
    return subagent


def get_subagent(subagent_id: str) -> Optional[Subagent]:
    return _subagents.get(subagent_id)


def list_subagents(parent_agent_id: Optional[str] = None) -> List[Subagent]:
    agents = list(_subagents.values())
    if parent_agent_id:
        agents = [a for a in agents if a.parent_agent_id == parent_agent_id]
    return agents


def run_subagent_step(subagent_id: str) -> Dict[str, Any]:
    """Execute one step of a subagent's plan.

    Returns the result of the step execution.
    """
    subagent = _subagents.get(subagent_id)
    if not subagent:
        return {"success": False, "error": "Subagent not found"}
    if subagent.status == SubagentStatus.FAILED:
        return {"success": False, "error": "Subagent already failed"}

    plan = planning.get_plan(subagent.plan_id) if subagent.plan_id else None
    if not plan:
        return {"success": False, "error": "Plan not found"}

    subagent.status = SubagentStatus.RUNNING
    todo = planning.advance_plan(plan.plan_id)
    if todo is None:
        subagent.status = SubagentStatus.DONE
        return {"success": True, "status": "done", "message": "All todos completed"}

    # Execute the todo's tool if specified
    if todo.tool_id:
        result = tool_registry.invoke_tool(todo.tool_id, todo.tool_input)
        if result["success"]:
            planning.update_todo(plan.plan_id, todo.id, planning.TodoStatus.DONE, result=result)
        else:
            planning.update_todo(plan.plan_id, todo.id, planning.TodoStatus.FAILED, error=result.get("error"))
            subagent.status = SubagentStatus.FAILED
            subagent.error = result.get("error")
            return {"success": False, "error": result.get("error"), "todo_id": todo.id}
    else:
        # No tool — mark as done (e.g. manual step)
        planning.update_todo(plan.plan_id, todo.id, planning.TodoStatus.DONE)

    # Check if plan is now done
    updated_plan = planning.get_plan(plan.plan_id)
    if updated_plan and updated_plan.status == "done":
        subagent.status = SubagentStatus.DONE

    return {
        "success": True,
        "status": subagent.status.value,
        "todo_id": todo.id,
        "todo_description": todo.description,
        "result": todo.result if hasattr(todo, "result") else None,
    }


def run_subagent_to_completion(subagent_id: str, max_steps: int = 20) -> Dict[str, Any]:
    """Run a subagent until completion or failure."""
    steps = 0
    while steps < max_steps:
        result = run_subagent_step(subagent_id)
        steps += 1
        if not result["success"]:
            return {"success": False, "error": result.get("error"), "steps_executed": steps}
        if result.get("status") == "done":
            return {"success": True, "steps_executed": steps, "subagent_id": subagent_id}
    return {"success": False, "error": "Max steps exceeded", "steps_executed": steps}


def cancel_subagent(subagent_id: str) -> bool:
    subagent = _subagents.get(subagent_id)
    if not subagent:
        return False
    subagent.status = SubagentStatus.FAILED
    if subagent.plan_id:
        planning.cancel_plan(subagent.plan_id)
    return True
