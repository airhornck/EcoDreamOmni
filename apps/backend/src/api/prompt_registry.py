"""Prompt Registry API — Phase 2 / PRD V2.6 §10.5.

Routes:
  POST /prompt-registry/variables           # Register variable
  GET  /prompt-registry/variables           # List variables
  DELETE /prompt-registry/variables/{name}  # Delete variable
  POST /prompt-registry/templates           # Create template
  GET  /prompt-registry/templates           # List templates
  GET  /prompt-registry/templates/{id}      # Get template (latest or specific version)
  POST /prompt-registry/templates/{id}/versions  # Create new version
  POST /prompt-registry/templates/{id}/activate  # Activate
  POST /prompt-registry/templates/{id}/archive   # Archive
  DELETE /prompt-registry/templates/{id}    # Delete template
  POST /prompt-registry/templates/{id}/render    # Render
  GET  /prompt-registry/templates/{id}/performance # Performance stats
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.services import prompt_registry

router = APIRouter(prefix="/prompt-registry", tags=["prompt-registry"])


# ─── Schemas ───

class RegisterVariableRequest(BaseModel):
    name: str
    description: str
    type: str = "STRING"
    allowed_values: Optional[List[str]] = None
    max_length: int = 100
    required: bool = True
    default_value: Optional[str] = None
    validation_regex: Optional[str] = None


class VariableResponse(BaseModel):
    name: str
    description: str
    type: str
    allowed_values: Optional[List[str]]
    max_length: int
    required: bool
    default_value: Optional[str]


class CreateTemplateRequest(BaseModel):
    name: str
    agent_id: str
    template_content: str
    variables: List[str]
    created_by: str
    env: str = "prod"


class TemplateResponse(BaseModel):
    id: str
    name: str
    agent_id: str
    version: int
    env: str
    template_content: str
    variables: List[str]
    system_fingerprint: str
    status: str
    approval_status: str
    created_by: str
    created_at: str


class CreateVersionRequest(BaseModel):
    template_content: str
    variables: List[str]
    created_by: str


class RenderRequest(BaseModel):
    variables: Dict[str, Any]
    dry_run: bool = False


class RenderResponse(BaseModel):
    ok: bool
    rendered: Optional[str] = None
    error: Optional[str] = None
    template_id: str
    version: int
    dry_run: bool


class PerformanceResponse(BaseModel):
    id: str
    template_id: str
    version: int
    date: str
    invocations: int


# ─── Helpers ───

def _to_variable_response(v: prompt_registry.PromptVariable) -> VariableResponse:
    return VariableResponse(
        name=v.name,
        description=v.description,
        type=v.type.value,
        allowed_values=v.allowed_values,
        max_length=v.max_length,
        required=v.required,
        default_value=v.default_value,
    )


def _to_template_response(t: prompt_registry.PromptTemplate) -> TemplateResponse:
    return TemplateResponse(
        id=t.id,
        name=t.name,
        agent_id=t.agent_id,
        version=t.version,
        env=t.env,
        template_content=t.template_content,
        variables=t.variables,
        system_fingerprint=t.system_fingerprint,
        status=t.status.value,
        approval_status=t.approval_status.value,
        created_by=t.created_by,
        created_at=t.created_at,
    )


# ─── Variables ───

@router.post("/variables", status_code=201, response_model=VariableResponse)
def register_variable(req: RegisterVariableRequest):
    v = prompt_registry.register_variable(
        name=req.name,
        description=req.description,
        type=req.type,
        allowed_values=req.allowed_values,
        max_length=req.max_length,
        required=req.required,
        default_value=req.default_value,
        validation_regex=req.validation_regex,
    )
    return _to_variable_response(v)


@router.get("/variables", response_model=List[VariableResponse])
def list_variables():
    return [_to_variable_response(v) for v in prompt_registry.list_variables()]


@router.delete("/variables/{name}", status_code=204)
def delete_variable(name: str):
    ok = prompt_registry.delete_variable(name)
    if not ok:
        raise HTTPException(status_code=404, detail="Variable not found")
    return None


# ─── Templates ───

@router.post("/templates", status_code=201, response_model=TemplateResponse)
def create_template(req: CreateTemplateRequest):
    try:
        t = prompt_registry.create_template(
            name=req.name,
            agent_id=req.agent_id,
            template_content=req.template_content,
            variables=req.variables,
            created_by=req.created_by,
            env=req.env,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return _to_template_response(t)


@router.get("/templates", response_model=List[TemplateResponse])
def list_templates(
    agent_id: Optional[str] = None,
    env: Optional[str] = None,
    status: Optional[str] = None,
):
    return [_to_template_response(t) for t in prompt_registry.list_templates(agent_id, env, status)]


@router.get("/templates/{template_id}", response_model=TemplateResponse)
def get_template(template_id: str, version: Optional[int] = None):
    t = prompt_registry.get_template(template_id, version)
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")
    return _to_template_response(t)


@router.post("/templates/{template_id}/versions", status_code=201, response_model=TemplateResponse)
def create_template_version(template_id: str, req: CreateVersionRequest):
    try:
        t = prompt_registry.create_template_version(
            template_id=template_id,
            template_content=req.template_content,
            variables=req.variables,
            created_by=req.created_by,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return _to_template_response(t)


@router.post("/templates/{template_id}/activate", response_model=TemplateResponse)
def activate_template(template_id: str):
    t = prompt_registry.activate_template(template_id)
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")
    return _to_template_response(t)


@router.post("/templates/{template_id}/archive", response_model=TemplateResponse)
def archive_template(template_id: str):
    t = prompt_registry.archive_template(template_id)
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")
    return _to_template_response(t)


@router.delete("/templates/{template_id}", status_code=204)
def delete_template(template_id: str):
    ok = prompt_registry.delete_template(template_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Template not found")
    return None


# ─── Rendering ───

@router.post("/templates/{template_id}/render", response_model=RenderResponse)
def render_template(template_id: str, req: RenderRequest):
    try:
        result = prompt_registry.render_template(
            template_id=template_id,
            variables=req.variables,
            dry_run=req.dry_run,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return RenderResponse(
        ok=result["ok"],
        rendered=result.get("rendered"),
        error=result.get("error"),
        template_id=result["template_id"],
        version=result["version"],
        dry_run=result["dry_run"],
    )


# ─── Performance ───

@router.get("/templates/{template_id}/performance", response_model=PerformanceResponse)
def get_performance(template_id: str, version: int):
    p = prompt_registry.get_performance(template_id, version)
    if not p:
        raise HTTPException(status_code=404, detail="Performance data not found")
    return PerformanceResponse(
        id=p.id,
        template_id=p.template_id,
        version=p.version,
        date=p.date,
        invocations=p.invocations,
    )
