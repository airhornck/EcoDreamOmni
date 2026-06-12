"""FastAPI routes for Agent Harness (H1–H6).

Endpoints:
  POST /harness/sessions          — create ReAct session
  GET  /harness/sessions          — list sessions
  GET  /harness/sessions/{sid}    — get session detail
  POST /harness/sessions/{sid}/step   — run one ReAct step
  POST /harness/sessions/{sid}/run    — run to completion
  POST /harness/sessions/{sid}/pause  — pause session
  POST /harness/sessions/{sid}/resume — resume session
  GET  /harness/sessions/{sid}/summary — session summary

  POST /harness/subagents         — create subagent
  GET  /harness/subagents         — list subagents
  POST /harness/subagents/{sid}/step  — run one subagent step
  POST /harness/subagents/{sid}/run   — run subagent to completion

  GET  /harness/plans             — list plans
  GET  /harness/plans/{pid}       — get plan
  POST /harness/plans/{pid}/pause   — pause plan
  POST /harness/plans/{pid}/resume  — resume plan
  POST /harness/plans/{pid}/cancel  — cancel plan

  GET  /harness/checkpoints/{sid} — list checkpoints for session
  POST /harness/checkpoints/{sid}/rollback — rollback to checkpoint

  GET  /harness/context/{sid}     — get context window messages
  POST /harness/context/{sid}/add — add message to context
  GET  /harness/context/{sid}/stats — context stats
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

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

router = APIRouter(prefix="/harness", tags=["harness"])


# ─── Schemas ───

class CreateSessionRequest(BaseModel):
    goal: str
    agent_id: Optional[str] = None


class AddMessageRequest(BaseModel):
    role: str
    content: str
    pinned: bool = False


class CreateSubagentRequest(BaseModel):
    mode: str  # initializer | coding
    task: str
    parent_agent_id: Optional[str] = None
    custom_tools: Optional[List[str]] = None


class RollbackRequest(BaseModel):
    checkpoint_id: str


# ─── ReAct Sessions ───

@router.post("/sessions", status_code=201)
def create_session(req: CreateSessionRequest) -> Dict[str, Any]:
    session = react.create_session(goal=req.goal, agent_id=req.agent_id)
    return {
        "session_id": session.session_id,
        "goal": session.goal,
        "agent_id": session.agent_id,
        "plan_id": session.plan_id,
        "status": session.status,
        "created_at": session.created_at,
    }


@router.get("/sessions")
def list_sessions() -> List[Dict[str, Any]]:
    return [
        {
            "session_id": s.session_id,
            "goal": s.goal,
            "status": s.status,
            "total_steps": len(s.steps),
            "created_at": s.created_at,
        }
        for s in react.list_sessions()
    ]


@router.get("/sessions/{session_id}")
def get_session(session_id: str) -> Dict[str, Any]:
    s = react.get_session(session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "session_id": s.session_id,
        "goal": s.goal,
        "agent_id": s.agent_id,
        "plan_id": s.plan_id,
        "status": s.status,
        "current_phase": s.current_phase.value,
        "total_steps": len(s.steps),
        "created_at": s.created_at,
        "steps": [
            {
                "step_number": step.step_number,
                "phase": step.phase.value,
                "thought": step.thought,
                "action": step.action,
                "observation": step.observation,
                "verify_result": step.verify_result,
                "timestamp": step.timestamp,
            }
            for step in s.steps
        ],
    }


@router.post("/sessions/{session_id}/step")
def run_step(session_id: str) -> Dict[str, Any]:
    s = react.get_session(session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    return react.run_step(session_id)


@router.post("/sessions/{session_id}/run")
def run_session(session_id: str, max_steps: int = 20) -> Dict[str, Any]:
    s = react.get_session(session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    return react.run_session(session_id, max_steps=max_steps)


@router.post("/sessions/{session_id}/pause")
def pause_session(session_id: str) -> Dict[str, Any]:
    ok = react.pause_session(session_id)
    if not ok:
        raise HTTPException(status_code=400, detail="Session not running or not found")
    return {"session_id": session_id, "status": "paused"}


@router.post("/sessions/{session_id}/resume")
def resume_session(session_id: str) -> Dict[str, Any]:
    ok = react.resume_session(session_id)
    if not ok:
        raise HTTPException(status_code=400, detail="Session not paused or not found")
    return {"session_id": session_id, "status": "resumed"}


@router.get("/sessions/{session_id}/summary")
def get_session_summary(session_id: str) -> Dict[str, Any]:
    summary = react.get_session_summary(session_id)
    if "error" in summary:
        raise HTTPException(status_code=404, detail=summary["error"])
    return summary


# ─── Subagents ───

@router.post("/subagents", status_code=201)
def create_subagent(req: CreateSubagentRequest) -> Dict[str, Any]:
    mode = subagent.SubagentMode(req.mode)
    sa = subagent.create_subagent(
        mode=mode,
        task=req.task,
        parent_agent_id=req.parent_agent_id,
        custom_tools=req.custom_tools,
    )
    return {
        "subagent_id": sa.subagent_id,
        "mode": sa.mode.value,
        "task": sa.task,
        "status": sa.status.value,
        "plan_id": sa.plan_id,
        "parent_agent_id": sa.parent_agent_id,
    }


@router.get("/subagents")
def list_subagents(parent_agent_id: Optional[str] = None) -> List[Dict[str, Any]]:
    return [
        {
            "subagent_id": sa.subagent_id,
            "mode": sa.mode.value,
            "task": sa.task,
            "status": sa.status.value,
            "plan_id": sa.plan_id,
            "parent_agent_id": sa.parent_agent_id,
        }
        for sa in subagent.list_subagents(parent_agent_id)
    ]


@router.post("/subagents/{subagent_id}/step")
def run_subagent_step(subagent_id: str) -> Dict[str, Any]:
    sa = subagent.get_subagent(subagent_id)
    if not sa:
        raise HTTPException(status_code=404, detail="Subagent not found")
    return subagent.run_subagent_step(subagent_id)


@router.post("/subagents/{subagent_id}/run")
def run_subagent_to_completion(subagent_id: str, max_steps: int = 20) -> Dict[str, Any]:
    sa = subagent.get_subagent(subagent_id)
    if not sa:
        raise HTTPException(status_code=404, detail="Subagent not found")
    return subagent.run_subagent_to_completion(subagent_id, max_steps=max_steps)


# ─── Plans ───

@router.get("/plans")
def list_plans() -> List[Dict[str, Any]]:
    return [
        {
            "plan_id": p.plan_id,
            "goal": p.goal,
            "status": p.status,
            "current_index": p.current_index,
            "todos": [
                {
                    "id": t.id,
                    "description": t.description,
                    "status": t.status.value,
                    "tool_id": t.tool_id,
                    "error": t.error,
                }
                for t in p.todos
            ],
        }
        for p in planning.list_plans()
    ]


@router.get("/plans/{plan_id}")
def get_plan(plan_id: str) -> Dict[str, Any]:
    p = planning.get_plan(plan_id)
    if not p:
        raise HTTPException(status_code=404, detail="Plan not found")
    return {
        "plan_id": p.plan_id,
        "goal": p.goal,
        "status": p.status,
        "current_index": p.current_index,
        "todos": [
            {
                "id": t.id,
                "description": t.description,
                "status": t.status.value,
                "tool_id": t.tool_id,
                "error": t.error,
            }
            for t in p.todos
        ],
    }


@router.post("/plans/{plan_id}/pause")
def pause_plan(plan_id: str) -> Dict[str, Any]:
    ok = planning.pause_plan(plan_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Plan not found")
    return {"plan_id": plan_id, "status": "paused"}


@router.post("/plans/{plan_id}/resume")
def resume_plan(plan_id: str) -> Dict[str, Any]:
    ok = planning.resume_plan(plan_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Plan not found")
    return {"plan_id": plan_id, "status": "resumed"}


@router.post("/plans/{plan_id}/cancel")
def cancel_plan(plan_id: str) -> Dict[str, Any]:
    ok = planning.cancel_plan(plan_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Plan not found")
    return {"plan_id": plan_id, "status": "cancelled"}


# ─── Checkpoints ───

@router.get("/checkpoints/{session_id}")
def list_checkpoints(session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    return [
        {
            "checkpoint_id": cp.checkpoint_id,
            "step_number": cp.step_number,
            "plan_id": cp.plan_id,
            "tool_outputs": cp.tool_outputs,
            "verification_result": cp.verification_result,
            "state_data": cp.state_data,
            "created_at": cp.created_at,
        }
        for cp in state.get_checkpoints(session_id, limit=limit)
    ]


@router.post("/checkpoints/{session_id}/rollback")
def rollback_checkpoint(session_id: str, req: RollbackRequest) -> Dict[str, Any]:
    cp = state.rollback_to_checkpoint(session_id, req.checkpoint_id)
    if not cp:
        raise HTTPException(status_code=404, detail="Checkpoint not found")
    return {
        "checkpoint_id": cp.checkpoint_id,
        "step_number": cp.step_number,
        "rolled_back_to": cp.created_at,
    }


# ─── Context ───

@router.get("/context/{session_id}")
def get_context(session_id: str, include_summary: bool = True) -> Dict[str, Any]:
    return {
        "session_id": session_id,
        "messages": context.get_messages(session_id, include_summary=include_summary),
        "stats": context.window_stats(session_id),
    }


@router.post("/context/{session_id}/add")
def add_context_message(session_id: str, req: AddMessageRequest) -> Dict[str, Any]:
    win = context.add_message(session_id, req.role, req.content, pinned=req.pinned)
    return {
        "session_id": session_id,
        "message_count": len(win.messages),
        "stats": context.window_stats(session_id),
    }


@router.get("/context/{session_id}/stats")
def get_context_stats(session_id: str) -> Dict[str, Any]:
    return context.window_stats(session_id)


# ─── Tools (Harness-facing) ───

@router.get("/tools")
def list_tools(layer: Optional[str] = None) -> List[Dict[str, Any]]:
    return [
        {
            "tool_id": t.tool_id,
            "name": t.name,
            "description": t.description,
            "skill_id": t.skill_id,
            "requires_tools": t.requires_tools,
        }
        for t in tool_registry.list_tools(layer=layer)
    ]


@router.get("/tools/{tool_id}")
def get_tool(tool_id: str) -> Dict[str, Any]:
    t = tool_registry.get_tool(tool_id)
    if not t:
        raise HTTPException(status_code=404, detail="Tool not found")
    return {
        "tool_id": t.tool_id,
        "name": t.name,
        "description": t.description,
        "input_schema": t.input_schema,
        "output_schema": t.output_schema,
        "requires_tools": t.requires_tools,
        "requires_toolsets": t.requires_toolsets,
    }
