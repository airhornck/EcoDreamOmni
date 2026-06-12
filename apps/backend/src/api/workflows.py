"""Workflows API — W17 Workflow可视化配置路由。

Routes:
  POST /workflows                           # Create template
  GET  /workflows                           # List templates
  GET  /workflows/{id}                      # Get template
  POST /workflows/{id}/upgrade-version      # Upgrade version
  GET  /workflows/{id}/versions             # Version history
  POST /workflows/{id}/dry-run              # Dry run
  GET  /workflows/{id}/react-flow           # React Flow format
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.api.auth import get_current_user
from src.services import workflow_engine

router = APIRouter(prefix="/workflow-visual", tags=["workflow-visual"])


# ─── Schemas ───

class WorkflowNodeSchema(BaseModel):
    node_index: int = 0
    node_type: str
    node_name: str
    agent_id: Optional[str] = None
    prompt_template_id: Optional[str] = None
    fail_strategy: str = "FAIL_FAST"
    human_config: Optional[Dict[str, Any]] = None
    timer_seconds: Optional[int] = None


class CreateTemplateRequest(BaseModel):
    name: str
    nodes: List[WorkflowNodeSchema]
    description: str = ""
    source_preset: Optional[str] = None
    owner: str = ""


class TemplateResponse(BaseModel):
    id: str
    name: str
    description: str
    source_preset: Optional[str]
    version: int
    status: str
    owner: str
    nodes: List[WorkflowNodeSchema]
    created_at: str


class VersionUpgradeResponse(BaseModel):
    id: str
    version: int
    previous_version: int


class DryRunRequest(BaseModel):
    initial_context: Optional[Dict[str, Any]] = None


class DryRunResponse(BaseModel):
    is_dry_run: bool
    template_id: str
    template_version: int
    simulated_nodes: List[Dict[str, Any]]
    overall_status: str
    validation_passed: bool
    has_human_approval: bool


class ReactFlowResponse(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]


# ─── Helpers ───

def _to_template_response(t: workflow_engine.WorkflowTemplate) -> TemplateResponse:
    return TemplateResponse(
        id=t.id,
        name=t.name,
        description=t.description,
        source_preset=t.source_preset,
        version=t.version,
        status=t.status,
        owner=t.owner,
        nodes=[
            WorkflowNodeSchema(
                node_index=n.node_index,
                node_type=n.node_type.value,
                node_name=n.node_name,
                agent_id=n.agent_id,
                prompt_template_id=n.prompt_template_id,
                fail_strategy=n.fail_strategy.value,
                human_config=n.human_config,
                timer_seconds=n.timer_seconds,
            )
            for n in t.nodes
        ],
        created_at=t.created_at,
    )


# ─── Routes ───

@router.post("", status_code=status.HTTP_201_CREATED, response_model=TemplateResponse)
def create_template(req: CreateTemplateRequest, user=Depends(get_current_user)):
    try:
        t = workflow_engine.create_template(
            name=req.name,
            nodes=[n.model_dump() for n in req.nodes],
            description=req.description,
            source_preset=req.source_preset,
            owner=req.owner,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return _to_template_response(t)


@router.get("", response_model=Dict[str, List[TemplateResponse]])
def list_templates(
    status: Optional[str] = None,
    account_id: Optional[str] = None,
    user=Depends(get_current_user),
):
    templates = workflow_engine.list_templates(status)
    return {"series": [_to_template_response(t) for t in templates]}


@router.get("/{template_id}", response_model=TemplateResponse)
def get_template(template_id: str, user=Depends(get_current_user)):
    t = workflow_engine.get_template(template_id)
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")
    return _to_template_response(t)


@router.post("/{template_id}/upgrade-version", response_model=VersionUpgradeResponse)
def upgrade_version(template_id: str, user=Depends(get_current_user)):
    t = workflow_engine.upgrade_template_version(template_id)
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")
    return VersionUpgradeResponse(id=template_id, version=t.version, previous_version=t.version - 1)


@router.get("/{template_id}/versions")
def get_versions(template_id: str, user=Depends(get_current_user)):
    t = workflow_engine.get_template(template_id)
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")
    versions = workflow_engine.get_template_versions(template_id)
    return {"versions": versions}


@router.post("/{template_id}/dry-run", response_model=DryRunResponse)
def dry_run(template_id: str, req: DryRunRequest, user=Depends(get_current_user)):
    try:
        result = workflow_engine.dry_run_execution(template_id, req.initial_context)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return DryRunResponse(**result)


@router.get("/{template_id}/react-flow", response_model=ReactFlowResponse)
def react_flow(template_id: str, user=Depends(get_current_user)):
    try:
        result = workflow_engine.to_react_flow(template_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return ReactFlowResponse(**result)
