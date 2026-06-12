"""Planning Engine — task decomposition with todo list execution.

Aligned with dev-plan H4: "Planning Engine: write_todos + incremental execution".

MVP:
  - Accept a goal string
  - Decompose into ordered todo list
  - Track execution state per todo
  - Allow pause/resume/cancel
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid


class TodoStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Todo:
    id: str
    description: str
    status: TodoStatus = TodoStatus.PENDING
    tool_id: Optional[str] = None
    tool_input: Dict[str, Any] = field(default_factory=dict)
    result: Any = None
    error: Optional[str] = None
    depends_on: List[str] = field(default_factory=list)


@dataclass
class Plan:
    plan_id: str
    goal: str
    todos: List[Todo] = field(default_factory=list)
    status: str = "pending"  # pending | running | paused | done | failed
    current_index: int = 0


_plans: Dict[str, Plan] = {}


# ─── Task decomposition (rule-based MVP) ───

_DECOMPOSITION_RULES: List[Dict[str, Any]] = [
    {
        "keywords": ["content", "generate", "create", "draft"],
        "todos": [
            {"description": "Analyze topic and select template", "tool_id": "content-generate", "tool_input": {"step": "analyze"}},
            {"description": "Generate content draft", "tool_id": "content-generate", "tool_input": {"step": "draft"}},
            {"description": "Run compliance scan", "tool_id": "compliance-check", "tool_input": {}},
            {"description": "Predict engagement", "tool_id": "engagement-predict", "tool_input": {}},
        ],
    },
    {
        "keywords": ["publish", "schedule", "post"],
        "todos": [
            {"description": "Validate account health", "tool_id": "health-score", "tool_input": {}},
            {"description": "Run compliance scan", "tool_id": "compliance-check", "tool_input": {}},
            {"description": "Schedule publication", "tool_id": "publish-schedule", "tool_input": {}},
        ],
    },
    {
        "keywords": ["compliance", "audit", "scan", "review"],
        "todos": [
            {"description": "Extract claims and entities", "tool_id": "compliance-check", "tool_input": {"step": "extract"}},
            {"description": "Run rule engine (L1-L4)", "tool_id": "compliance-check", "tool_input": {"step": "evaluate"}},
            {"description": "Generate audit report", "tool_id": "compliance-check", "tool_input": {"step": "report"}},
        ],
    },
    {
        "keywords": ["trend", "topic", "hot", "scout"],
        "todos": [
            {"description": "Fetch trend data", "tool_id": "content-generate", "tool_input": {"step": "trend_fetch"}},
            {"description": "Analyze topic relevance", "tool_id": "content-generate", "tool_input": {"step": "topic_analyze"}},
            {"description": "Draft content outline", "tool_id": "content-generate", "tool_input": {"step": "outline"}},
        ],
    },
    {
        "keywords": ["analyze", "data", "metric", "report", "dashboard"],
        "todos": [
            {"description": "Load data source", "tool_id": "engagement-predict", "tool_input": {"step": "load"}},
            {"description": "Compute KPIs", "tool_id": "engagement-predict", "tool_input": {"step": "compute"}},
            {"description": "Generate summary", "tool_id": "engagement-predict", "tool_input": {"step": "summarize"}},
        ],
    },
]


def _decompose_goal(goal: str) -> List[Dict[str, Any]]:
    goal_lower = goal.lower()
    for rule in _DECOMPOSITION_RULES:
        if any(kw in goal_lower for kw in rule["keywords"]):
            return rule["todos"]
    # Fallback: generic single-step plan
    return [{"description": goal, "tool_id": None, "tool_input": {}}]


def create_plan(goal: str) -> Plan:
    plan_id = str(uuid.uuid4())[:8]
    todo_specs = _decompose_goal(goal)
    todos = []
    for i, spec in enumerate(todo_specs):
        todos.append(Todo(
            id=f"{plan_id}-{i}",
            description=spec["description"],
            tool_id=spec.get("tool_id"),
            tool_input=spec.get("tool_input", {}),
            depends_on=spec.get("depends_on", []),
        ))
    plan = Plan(plan_id=plan_id, goal=goal, todos=todos)
    _plans[plan_id] = plan
    return plan


def get_plan(plan_id: str) -> Optional[Plan]:
    return _plans.get(plan_id)


def list_plans() -> List[Plan]:
    return list(_plans.values())


def update_todo(plan_id: str, todo_id: str, status: TodoStatus, result: Any = None, error: Optional[str] = None) -> bool:
    plan = _plans.get(plan_id)
    if not plan:
        return False
    for todo in plan.todos:
        if todo.id == todo_id:
            todo.status = status
            if result is not None:
                todo.result = result
            if error is not None:
                todo.error = error
            return True
    return False


def advance_plan(plan_id: str) -> Optional[Todo]:
    """Return the next pending todo that has all dependencies satisfied."""
    plan = _plans.get(plan_id)
    if not plan or plan.status in ("done", "failed", "paused"):
        return None

    done_ids = {t.id for t in plan.todos if t.status == TodoStatus.DONE}
    for todo in plan.todos:
        if todo.status != TodoStatus.PENDING:
            continue
        if all(dep in done_ids for dep in todo.depends_on):
            todo.status = TodoStatus.IN_PROGRESS
            plan.current_index = plan.todos.index(todo)
            plan.status = "running"
            return todo

    # All done?
    if all(t.status in (TodoStatus.DONE, TodoStatus.SKIPPED) for t in plan.todos):
        plan.status = "done"
    return None


def pause_plan(plan_id: str) -> bool:
    plan = _plans.get(plan_id)
    if plan:
        plan.status = "paused"
        return True
    return False


def resume_plan(plan_id: str) -> bool:
    plan = _plans.get(plan_id)
    if plan:
        plan.status = "running"
        return True
    return False


def cancel_plan(plan_id: str) -> bool:
    plan = _plans.get(plan_id)
    if plan:
        plan.status = "failed"
        for t in plan.todos:
            if t.status in (TodoStatus.PENDING, TodoStatus.IN_PROGRESS):
                t.status = TodoStatus.SKIPPED
        return True
    return False
