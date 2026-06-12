"""AgentHub API — W15.

Routes:
  POST /agent-hub/agents              # Register
  GET  /agent-hub/agents              # List
  GET  /agent-hub/agents/{id}         # Detail
  PATCH /agent-hub/agents/{id}        # Update metadata
  DELETE /agent-hub/agents/{id}       # Deregister (soft)
  POST /agent-hub/agents/{id}/configs              # Create config version
  GET  /agent-hub/agents/{id}/configs              # List versions
  GET  /agent-hub/agents/{id}/configs/{ver}        # Get version
  POST /agent-hub/agents/{id}/configs/{ver}/activate  # Activate
  POST /agent-hub/agents/{id}/configs/{ver}/rollback  # Rollback
  GET  /agent-hub/agents/{id}/dependencies         # List deps
  POST /agent-hub/agents/{id}/health-check        # Check deps
  GET  /agent-hub/agents/{id}/permissions          # List perms
  POST /agent-hub/agents/{id}/permissions          # Grant perm
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.services import agent_hub

router = APIRouter(prefix="/agent-hub", tags=["agent-hub"])


# ─── Schemas ───

class RegisterAgentRequest(BaseModel):
    name: str
    role: str
    description: str = ""
    owner: str = ""


class UpdateAgentRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    owner: Optional[str] = None
    status: Optional[str] = None


class CreateConfigRequest(BaseModel):
    env: str = Field(default="dev", description="dev / staging / prod")
    config_payload: Dict[str, Any] = {}
    ui_config: Dict[str, Any] = {}
    quick_actions: List[Dict[str, Any]] = []
    adaptive_config: Dict[str, Any] = {}
    created_by: str = ""


class DeclareDepRequest(BaseModel):
    dep_type: str = Field(..., description="llm / tool / data_source")
    dep_name: str
    failover_config: Optional[Dict[str, Any]] = None


class GrantPermRequest(BaseModel):
    principal: str
    principal_type: str = "USER"
    actions: List[str] = ["READ"]
    granted_by: str = ""
    expires_at: Optional[str] = None


class AgentResponse(BaseModel):
    id: str
    name: str
    role: str
    description: str
    owner: str
    status: str
    created_at: str
    updated_at: str


class ConfigResponse(BaseModel):
    id: str
    agent_id: str
    version: int
    env: str
    checksum: str
    created_by: str
    created_at: str
    status: str
    approval_status: str


# ─── Helpers ───

def _to_agent_response(a: agent_hub.AgentRegistration) -> AgentResponse:
    return AgentResponse(
        id=a.id, name=a.name, role=a.role, description=a.description,
        owner=a.owner, status=a.status.value, created_at=a.created_at, updated_at=a.updated_at,
    )


def _to_config_response(c: agent_hub.AgentConfigSnapshot) -> ConfigResponse:
    return ConfigResponse(
        id=c.id, agent_id=c.agent_id, version=c.version, env=c.env,
        checksum=c.checksum, created_by=c.created_by, created_at=c.created_at,
        status=c.status.value, approval_status=c.approval_status.value,
    )


# ─── Agent CRUD ───

@router.post("/agents", status_code=201, response_model=AgentResponse)
def register_agent(req: RegisterAgentRequest):
    a = agent_hub.register_agent(
        name=req.name, role=req.role,
        description=req.description, owner=req.owner,
    )
    return _to_agent_response(a)


@router.get("/agents", response_model=List[AgentResponse])
def list_agents(
    status: Optional[str] = None,
    role: Optional[str] = None,
):
    return [_to_agent_response(a) for a in agent_hub.list_agents(status=status, role=role)]


@router.get("/agents/{agent_id}", response_model=AgentResponse)
def get_agent(agent_id: str):
    a = agent_hub.get_agent(agent_id)
    if not a:
        raise HTTPException(status_code=404, detail="Agent not found")
    active = agent_hub.get_active_config(agent_id)
    resp = _to_agent_response(a)
    return {
        **resp.model_dump(),
        "active_config_version": active.version if active else None,
        "active_config_env": active.env if active else None,
    }


@router.patch("/agents/{agent_id}", response_model=AgentResponse)
def update_agent(agent_id: str, req: UpdateAgentRequest):
    a = agent_hub.get_agent(agent_id)
    if not a:
        raise HTTPException(status_code=404, detail="Agent not found")
    data = req.model_dump(exclude_unset=True)
    updated = agent_hub.update_agent(agent_id, **data)
    return _to_agent_response(updated)


@router.delete("/agents/{agent_id}", status_code=204)
def deregister_agent(agent_id: str):
    ok = agent_hub.deregister_agent(agent_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Agent not found")
    return None


# ─── Config Versioning ───

@router.post("/agents/{agent_id}/configs", status_code=201, response_model=ConfigResponse)
def create_config(agent_id: str, req: CreateConfigRequest):
    a = agent_hub.get_agent(agent_id)
    if not a:
        raise HTTPException(status_code=404, detail="Agent not found")
    snap = agent_hub.create_config(
        agent_id=agent_id,
        env=req.env,
        config_payload=req.config_payload,
        created_by=req.created_by,
        ui_config=req.ui_config,
        quick_actions=req.quick_actions,
        adaptive_config=req.adaptive_config,
    )
    return _to_config_response(snap)


@router.get("/agents/{agent_id}/configs")
def list_configs(agent_id: str):
    a = agent_hub.get_agent(agent_id)
    if not a:
        raise HTTPException(status_code=404, detail="Agent not found")
    return [_to_config_response(c) for c in agent_hub.list_configs(agent_id)]


@router.get("/agents/{agent_id}/configs/{version}")
def get_config(agent_id: str, version: int):
    c = agent_hub.get_config(agent_id, version)
    if not c:
        raise HTTPException(status_code=404, detail="Config version not found")
    return _to_config_response(c)


@router.post("/agents/{agent_id}/configs/{version}/activate")
def activate_config(agent_id: str, version: int):
    a = agent_hub.get_agent(agent_id)
    if not a:
        raise HTTPException(status_code=404, detail="Agent not found")
    result = agent_hub.activate_config(agent_id, version)
    if not result:
        raise HTTPException(status_code=404, detail="Config version not found")
    return {"activated_version": result.version, "status": result.status.value}


@router.post("/agents/{agent_id}/configs/{version}/rollback")
def rollback_config(agent_id: str, version: int):
    a = agent_hub.get_agent(agent_id)
    if not a:
        raise HTTPException(status_code=404, detail="Agent not found")
    result = agent_hub.rollback_config(agent_id, version)
    if not result:
        raise HTTPException(status_code=404, detail="Config version not found")
    return {"rolled_back_to": result.version, "status": result.status.value}


# ─── Dependencies ───

@router.get("/agents/{agent_id}/dependencies")
def list_dependencies(agent_id: str):
    a = agent_hub.get_agent(agent_id)
    if not a:
        raise HTTPException(status_code=404, detail="Agent not found")
    deps = agent_hub.list_dependencies(agent_id)
    return {
        "agent_id": agent_id,
        "dependencies": [
            {
                "id": d.id,
                "dep_type": d.dep_type.value,
                "dep_name": d.dep_name,
                "dep_status": d.dep_status.value,
                "last_check": d.last_check,
            }
            for d in deps
        ],
    }


@router.post("/agents/{agent_id}/dependencies")
def declare_dependency(agent_id: str, req: DeclareDepRequest):
    a = agent_hub.get_agent(agent_id)
    if not a:
        raise HTTPException(status_code=404, detail="Agent not found")
    dep = agent_hub.declare_dependency(
        agent_id=agent_id,
        dep_type=req.dep_type,
        dep_name=req.dep_name,
        failover_config=req.failover_config,
    )
    return {
        "id": dep.id,
        "dep_type": dep.dep_type.value,
        "dep_name": dep.dep_name,
        "dep_status": dep.dep_status.value,
    }


@router.post("/agents/{agent_id}/health-check")
def health_check(agent_id: str):
    a = agent_hub.get_agent(agent_id)
    if not a:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent_hub.check_all_dependencies(agent_id)


# ─── Permissions ───

@router.get("/agents/{agent_id}/permissions")
def list_permissions(agent_id: str):
    a = agent_hub.get_agent(agent_id)
    if not a:
        raise HTTPException(status_code=404, detail="Agent not found")
    perms = agent_hub.list_permissions(agent_id)
    return {
        "agent_id": agent_id,
        "permissions": [
            {
                "id": p.id,
                "principal": p.principal,
                "principal_type": p.principal_type,
                "actions": p.actions,
                "granted_by": p.granted_by,
                "granted_at": p.granted_at,
                "expires_at": p.expires_at,
            }
            for p in perms
        ],
    }


@router.post("/agents/{agent_id}/permissions")
def grant_permission(agent_id: str, req: GrantPermRequest):
    a = agent_hub.get_agent(agent_id)
    if not a:
        raise HTTPException(status_code=404, detail="Agent not found")
    perm = agent_hub.grant_permission(
        agent_id=agent_id,
        principal=req.principal,
        principal_type=req.principal_type,
        actions=req.actions,
        granted_by=req.granted_by,
        expires_at=req.expires_at,
    )
    return {
        "id": perm.id,
        "principal": perm.principal,
        "actions": perm.actions,
        "granted_at": perm.granted_at,
    }


# ─── AI Workbench Config (v4.0 P2-4) ───

@router.get("/agents/{agent_id}/workbench-config")
def get_workbench_config(agent_id: str):
    """Get workbench-ready config for AI Workbench display."""
    a = agent_hub.get_agent(agent_id)
    if not a:
        raise HTTPException(status_code=404, detail="Agent not found")
    config = agent_hub.get_workbench_config(agent_id)
    if not config:
        raise HTTPException(status_code=404, detail="No active config found")
    return {"code": "OK", "data": config}
