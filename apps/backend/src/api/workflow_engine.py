"""Workflow Engine API — Phase 2 / PRD V2.6 §10.4.

Routes:
  POST /workflow-engine/templates           # Create template
  GET  /workflow-engine/templates           # List templates
  GET  /workflow-engine/templates/{id}      # Get template
  PATCH /workflow-engine/templates/{id}     # Update template
  DELETE /workflow-engine/templates/{id}    # Delete template
  POST /workflow-engine/templates/{id}/executions  # Start execution
  GET  /workflow-engine/executions          # List executions
  GET  /workflow-engine/executions/{id}     # Get execution
  POST /workflow-engine/executions/{id}/next       # Execute next node
  POST /workflow-engine/executions/{id}/pause      # Pause
  POST /workflow-engine/executions/{id}/resume     # Resume
  POST /workflow-engine/executions/{id}/cancel     # Cancel
  GET  /workflow-engine/executions/{id}/nodes      # Node executions
  GET  /workflow-engine/executions/{id}/context    # Context
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.services import workflow_engine

router = APIRouter(prefix="/workflow-engine", tags=["workflow-engine"])


# ─── Schemas ───

class WorkflowNodeSchema(BaseModel):
    node_index: int
    node_type: str
    node_name: str
    agent_id: Optional[str] = None
    prompt_template_id: Optional[str] = None
    fail_strategy: str = "FAIL_FAST"
    human_config: Optional[Dict[str, Any]] = None
    timer_seconds: Optional[int] = None
    skill_id: Optional[str] = None
    depends_on: Optional[List[int]] = None


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


class UpdateTemplateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class StartExecutionRequest(BaseModel):
    task_id: str


class ExecutionResponse(BaseModel):
    id: str
    task_id: str
    template_id: str
    template_version: int
    status: str
    current_node_index: int
    context: Dict[str, Any]
    started_at: Optional[str]
    ended_at: Optional[str]


class ExecuteNextRequest(BaseModel):
    node_output: Optional[Dict[str, Any]] = None
    node_error: Optional[str] = None


class RecommendTemplateRequest(BaseModel):
    platform_id: str = Field(..., description="平台ID，如 xiaohongshu | douyin")
    content_format: str = Field(..., description="内容格式，如 图文 | 视频 | 仅文字")


class RecommendTemplateResponse(BaseModel):
    platform_id: str
    content_format: str
    recommended_template_id: Optional[str]
    recommended_template_name: Optional[str]
    is_fallback: bool = False


class ExecuteNextResponse(BaseModel):
    status: str
    done: bool
    next_node: Optional[int] = None
    retrying: Optional[bool] = None
    node_failed: Optional[int] = None


class NodeExecutionResponse(BaseModel):
    id: str
    execution_id: str
    node_index: int
    node_type: str
    status: str
    input_context: Dict[str, Any]
    output_context: Dict[str, Any]
    duration_ms: Optional[int]
    error_message: Optional[str]


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
                skill_id=n.skill_id,
                depends_on=n.depends_on,
            )
            for n in t.nodes
        ],
        created_at=t.created_at,
    )


def _to_execution_response(e: workflow_engine.WorkflowExecution) -> ExecutionResponse:
    return ExecutionResponse(
        id=e.id,
        task_id=e.task_id,
        template_id=e.template_id,
        template_version=e.template_version,
        status=e.status.value,
        current_node_index=e.current_node_index,
        context=e.context,
        started_at=e.started_at,
        ended_at=e.ended_at,
    )


def _to_node_execution_response(n: workflow_engine.NodeExecution) -> NodeExecutionResponse:
    return NodeExecutionResponse(
        id=n.id,
        execution_id=n.execution_id,
        node_index=n.node_index,
        node_type=n.node_type,
        status=n.status.value,
        input_context=n.input_context,
        output_context=n.output_context,
        duration_ms=n.duration_ms,
        error_message=n.error_message,
    )


# ─── Templates ───

@router.post("/templates/recommend", response_model=RecommendTemplateResponse)
def recommend_template(req: RecommendTemplateRequest):
    """根据平台ID和内容格式推荐工作流模板."""
    tmpl = workflow_engine.recommend_template(req.platform_id, req.content_format)
    return RecommendTemplateResponse(
        platform_id=req.platform_id,
        content_format=req.content_format,
        recommended_template_id=tmpl.id if tmpl else None,
        recommended_template_name=tmpl.name if tmpl else None,
        is_fallback=tmpl is not None and tmpl.id == "content_creation_standard" if tmpl else True,
    )


@router.post("/templates", status_code=201, response_model=TemplateResponse)
def create_template(req: CreateTemplateRequest):
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


@router.get("/templates", response_model=List[TemplateResponse])
def list_templates(
    status: Optional[str] = None,
    source_preset: Optional[str] = None,
):
    return [_to_template_response(t) for t in workflow_engine.list_templates(status, source_preset)]


@router.get("/templates/{template_id}", response_model=TemplateResponse)
def get_template(template_id: str):
    t = workflow_engine.get_template(template_id)
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")
    return _to_template_response(t)


@router.patch("/templates/{template_id}", response_model=TemplateResponse)
def update_template(template_id: str, req: UpdateTemplateRequest):
    t = workflow_engine.get_template(template_id)
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")
    data = req.model_dump(exclude_unset=True)
    updated = workflow_engine.update_template(template_id, **data)
    return _to_template_response(updated)


@router.delete("/templates/{template_id}", status_code=204)
def delete_template(template_id: str):
    ok = workflow_engine.delete_template(template_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Template not found")
    return None


# ─── Executions ───

@router.post("/templates/{template_id}/executions", status_code=201, response_model=ExecutionResponse)
def start_execution(template_id: str, req: StartExecutionRequest):
    try:
        e = workflow_engine.start_execution(req.task_id, template_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _to_execution_response(e)


@router.get("/executions", response_model=List[ExecutionResponse])
def list_executions(
    template_id: Optional[str] = None,
    status: Optional[str] = None,
):
    return [_to_execution_response(e) for e in workflow_engine.list_executions(template_id, status)]


@router.get("/executions/{execution_id}", response_model=ExecutionResponse)
def get_execution(execution_id: str):
    e = workflow_engine.get_execution(execution_id)
    if not e:
        raise HTTPException(status_code=404, detail="Execution not found")
    return _to_execution_response(e)


@router.post("/executions/{execution_id}/next", response_model=ExecuteNextResponse)
def execute_next_node(execution_id: str, req: ExecuteNextRequest):
    try:
        result = workflow_engine.execute_next_node(
            execution_id,
            node_output=req.node_output,
            node_error=req.node_error,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return ExecuteNextResponse(
        status=result["status"],
        done=result["done"],
        next_node=result.get("next_node"),
        retrying=result.get("retrying"),
        node_failed=result.get("node_failed"),
    )


@router.post("/executions/{execution_id}/pause", response_model=ExecutionResponse)
def pause_execution(execution_id: str):
    e = workflow_engine.pause_execution(execution_id)
    if not e:
        raise HTTPException(status_code=404, detail="Execution not found")
    return _to_execution_response(e)


@router.post("/executions/{execution_id}/resume", response_model=ExecutionResponse)
def resume_execution(execution_id: str):
    e = workflow_engine.resume_execution(execution_id)
    if not e:
        raise HTTPException(status_code=404, detail="Execution not found")
    return _to_execution_response(e)


@router.post("/executions/{execution_id}/cancel", response_model=ExecutionResponse)
def cancel_execution(execution_id: str):
    e = workflow_engine.cancel_execution(execution_id)
    if not e:
        raise HTTPException(status_code=404, detail="Execution not found")
    return _to_execution_response(e)


@router.get("/executions/{execution_id}/nodes", response_model=List[NodeExecutionResponse])
def get_node_executions(execution_id: str):
    return [_to_node_execution_response(n) for n in workflow_engine.get_node_executions(execution_id)]


@router.get("/executions/{execution_id}/context")
def get_context(execution_id: str):
    e = workflow_engine.get_execution(execution_id)
    if not e:
        raise HTTPException(status_code=404, detail="Execution not found")
    return {"execution_id": execution_id, "context": e.context}
