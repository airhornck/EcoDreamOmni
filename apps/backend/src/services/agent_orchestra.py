"""Agent Orchestra — multi-agent orchestration engine.

Concepts:
  Agent:    A worker with role, skills, and config
  Workflow: Ordered steps defining which agent does what
  Pipeline: A running instance of a workflow
"""

import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from src.services import skill_hub


@dataclass
class Agent:
    id: str
    name: str
    role: str
    description: str
    skills: List[str] = field(default_factory=list)
    config: Dict = field(default_factory=dict)
    status: str = "active"
    created_at: str = ""
    updated_at: str = ""


@dataclass
class WorkflowStep:
    agent_id: str
    name: str
    input_from: str = "trigger"
    output_to: str = "result"


@dataclass
class Workflow:
    id: str
    name: str
    description: str
    steps: List[WorkflowStep] = field(default_factory=list)
    status: str = "active"
    created_at: str = ""


@dataclass
class Pipeline:
    id: str
    workflow_id: str
    status: str = "pending"  # pending, running, completed, failed
    current_step: int = 0
    context: Dict = field(default_factory=dict)
    results: List[Dict] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""


# In-memory stores
_agent_db: Dict[str, Agent] = {}
_workflow_db: Dict[str, Workflow] = {}
_pipeline_db: Dict[str, Pipeline] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─── Agent CRUD ───

def create_agent(
    name: str,
    role: str,
    description: str = "",
    skills: Optional[List[str]] = None,
    config: Optional[Dict] = None,
) -> Agent:
    agent_id = secrets.token_urlsafe(16)
    now = _now()
    agent = Agent(
        id=agent_id,
        name=name,
        role=role,
        description=description,
        skills=skills or [],
        config=config or {},
        status="active",
        created_at=now,
        updated_at=now,
    )
    _agent_db[agent_id] = agent
    return agent


def get_agent(agent_id: str) -> Optional[Agent]:
    return _agent_db.get(agent_id)


def update_agent(agent_id: str, **fields) -> Optional[Agent]:
    agent = _agent_db.get(agent_id)
    if agent is None:
        return None
    for key, value in fields.items():
        if hasattr(agent, key) and value is not None:
            setattr(agent, key, value)
    agent.updated_at = _now()
    return agent


def list_agents() -> List[Agent]:
    return list(_agent_db.values())


def bind_skill_to_agent(agent_id: str, skill_id: str) -> Optional[Agent]:
    agent = _agent_db.get(agent_id)
    if agent is None:
        return None
    if skill_id not in agent.skills:
        agent.skills.append(skill_id)
    agent.updated_at = _now()
    return agent


def delete_agent(agent_id: str) -> bool:
    if agent_id in _agent_db:
        del _agent_db[agent_id]
        return True
    return False


# ─── Workflow CRUD ───

def create_workflow(
    name: str,
    description: str = "",
    steps: Optional[List[Dict]] = None,
) -> Workflow:
    wf_id = secrets.token_urlsafe(16)
    step_objs = []
    for s in (steps or []):
        step_objs.append(WorkflowStep(
            agent_id=s.get("agent_id", ""),
            name=s.get("name", ""),
            input_from=s.get("input_from", "trigger"),
            output_to=s.get("output_to", "result"),
        ))
    wf = Workflow(
        id=wf_id,
        name=name,
        description=description,
        steps=step_objs,
        status="active",
        created_at=_now(),
    )
    _workflow_db[wf_id] = wf
    return wf


def get_workflow(workflow_id: str) -> Optional[Workflow]:
    return _workflow_db.get(workflow_id)


def list_workflows() -> List[Workflow]:
    return list(_workflow_db.values())


# ─── Pipeline ───

def create_pipeline(workflow_id: str, context: Optional[Dict] = None) -> Optional[Pipeline]:
    if workflow_id not in _workflow_db:
        return None
    pipe_id = secrets.token_urlsafe(16)
    now = _now()
    pipe = Pipeline(
        id=pipe_id,
        workflow_id=workflow_id,
        status="pending",
        current_step=0,
        context=context or {},
        results=[],
        created_at=now,
        updated_at=now,
    )
    _pipeline_db[pipe_id] = pipe
    return pipe


def get_pipeline(pipeline_id: str) -> Optional[Pipeline]:
    return _pipeline_db.get(pipeline_id)


def list_pipelines() -> List[Pipeline]:
    return list(_pipeline_db.values())


# ─── Execution Engine ───

def execute_pipeline(pipeline_id: str) -> Pipeline:
    """Execute a pipeline synchronously (MVP).

    For each step:
      1. Resolve the agent
      2. Execute the agent's first active skill with current context
      3. Merge skill result back into context under output_to key
      4. Advance current_step
    """
    pipe = _pipeline_db.get(pipeline_id)
    if pipe is None:
        raise ValueError("Pipeline not found")

    wf = _workflow_db.get(pipe.workflow_id)
    if wf is None:
        raise ValueError("Workflow not found")

    pipe.status = "running"
    pipe.updated_at = _now()

    try:
        for idx, step in enumerate(wf.steps):
            pipe.current_step = idx
            agent = _agent_db.get(step.agent_id)
            if agent is None:
                raise ValueError(f"Agent {step.agent_id} not found")

            # Prepare step context: inject step_name for tracing
            step_ctx = dict(pipe.context)
            step_ctx["step_name"] = step.name
            step_ctx["step_index"] = idx

            # Execute agent's skills (first available skill for MVP)
            step_result = None
            for skill_id in agent.skills:
                skill = skill_hub.get_skill(skill_id)
                if skill and skill.status == "active":
                    exec_res = skill_hub.execute_skill(skill_id, step_ctx)
                    if exec_res["success"]:
                        step_result = exec_res.get("result")
                        break

            # If no skill executed, keep context as-is
            if step_result is not None:
                pipe.context[step.output_to] = step_result
                pipe.results.append({
                    "step_index": idx,
                    "step_name": step.name,
                    "agent_id": agent.id,
                    "output": step_result,
                })
            else:
                pipe.results.append({
                    "step_index": idx,
                    "step_name": step.name,
                    "agent_id": agent.id,
                    "output": None,
                    "notice": "No active skill executed",
                })

            pipe.updated_at = _now()

        pipe.status = "completed"
    except Exception as e:
        pipe.status = "failed"
        pipe.results.append({"error": str(e), "step_index": pipe.current_step})

    pipe.updated_at = _now()
    return pipe


def clear_all() -> None:
    _agent_db.clear()
    _workflow_db.clear()
    _pipeline_db.clear()
