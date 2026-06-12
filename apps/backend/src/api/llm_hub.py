"""LLM Hub API — PRD V2.7.2 §8 精简版.

Routes:
  POST /llm-hub/models                    → register_model
  GET  /llm-hub/models                    → list_models
  GET  /llm-hub/models/{id}               → get_model
  PUT  /llm-hub/models/{id}               → update_model
  DELETE /llm-hub/models/{id}             → delete_model
  POST /llm-hub/models/{id}/test          → test_connectivity

  POST /llm-hub/scope-configs             → set_scope_config
  GET  /llm-hub/scope-configs             → list_scope_configs
  DELETE /llm-hub/scope-configs/{id}      → remove_scope_config
  GET  /llm-hub/scope-configs/nodes       → get_node_scope_overview

  POST /llm-hub/usage-logs                → log_usage
  GET  /llm-hub/usage-logs                → get_usage_logs
  GET  /llm-hub/cost-summary              → get_cost_summary
"""

from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.dependencies import get_current_user
from src.models.user import User
from src.services import llm_hub as lhs

router = APIRouter(prefix="/llm-hub", tags=["llm-hub"])


# ─── Schemas ───
class RegisterModelRequest(BaseModel):
    provider: str
    model_name: str
    api_key: str
    endpoint_url: Optional[str] = None
    status: str = "active"
    modality_support: Optional[Dict[str, bool]] = None


class ModelUpdateRequest(BaseModel):
    provider: Optional[str] = None
    model_name: Optional[str] = None
    api_key: Optional[str] = None
    endpoint_url: Optional[str] = None
    status: Optional[str] = None
    data_training_opt_out: Optional[bool] = None
    modality_support: Optional[Dict[str, bool]] = None


class ModelResponse(BaseModel):
    id: str
    provider: str
    model_name: str
    api_key_encrypted: str
    endpoint_base_url: Optional[str]
    status: str
    data_training_opt_out: bool
    modality_support: Optional[Dict[str, bool]] = None
    created_at: str
    updated_at: str
    # 前端兼容字段
    name: str = ""


class ScopeConfigRequest(BaseModel):
    scope_type: str
    model_id: str
    node_id: Optional[str] = None
    temperature: Optional[float] = None
    timeout: Optional[int] = None


class ScopeConfigResponse(BaseModel):
    id: str
    scope_type: str
    node_id: Optional[str]
    model_id: str
    temperature: float
    timeout_seconds: int
    created_at: str
    updated_at: str


class ScopeOverviewItem(BaseModel):
    node_id: str
    node_type: str
    current_model: Optional[str]
    source: str
    model_id: Optional[str]


class UsageLogRequest(BaseModel):
    model_id: str
    node_id: str
    provider_region: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0
    status: str
    error_message: Optional[str] = None


class UsageLogResponse(BaseModel):
    id: str
    model_id: Optional[str]
    node_id: str
    provider_region: str
    input_tokens: int
    output_tokens: int
    latency_ms: int
    status: str
    error_message: Optional[str]
    created_at: str


class CostSummaryResponse(BaseModel):
    period_days: int
    total_calls: int
    total_input_tokens: int
    total_output_tokens: int
    estimated_cost_cny: float
    by_model: List[dict]
    by_node: List[dict]
    trend: List[dict]


# ─── Model Registry ───
@router.post("/models", status_code=201, response_model=ModelResponse)
async def register_model(
    req: RegisterModelRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    data = await lhs.register_model(
        db=db,
        provider=req.provider,
        model_name=req.model_name,
        api_key=req.api_key,
        endpoint_url=req.endpoint_url,
        status=req.status,
        modality_support=req.modality_support,
    )
    return data


@router.get("/models", response_model=dict)
async def list_models(
    provider: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    models = await lhs.list_models(db=db, provider=provider, status=status)
    # 填充前端兼容字段
    enriched = []
    for m in models:
        d = m.model_dump() if hasattr(m, "model_dump") else dict(m)
        d["name"] = d.get("model_name", "")
        enriched.append(d)
    return {"items": enriched, "total": len(enriched)}


@router.get("/models/{model_id}", response_model=ModelResponse)
async def get_model(
    model_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    data = await lhs.get_model(db=db, model_id=model_id)
    if not data:
        raise HTTPException(status_code=404, detail="Model not found")
    return data


@router.put("/models/{model_id}", response_model=ModelResponse)
async def update_model(
    model_id: str,
    req: ModelUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    update_data = req.model_dump(exclude_unset=True)
    data = await lhs.update_model(db=db, model_id=model_id, **update_data)
    if not data:
        raise HTTPException(status_code=404, detail="Model not found")
    return data


@router.delete("/models/{model_id}", status_code=204)
async def delete_model(
    model_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ok = await lhs.delete_model(db=db, model_id=model_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Model not found")
    return None


@router.post("/models/{model_id}/test")
async def test_connectivity(
    model_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await lhs.test_connectivity(db=db, model_id=model_id)


# ─── Routing ───
class RouteRequest(BaseModel):
    modality: str
    preferred_provider: Optional[str] = None


class RouteResponse(BaseModel):
    model_id: str
    provider: str
    model_name: str
    region: str
    cross_border_risk: bool
    reason: str


@router.post("/route", response_model=RouteResponse)
async def route_model(
    req: RouteRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        decision = await lhs.route_model_by_modality(
            db=db,
            modality=req.modality,
            preferred_provider=req.preferred_provider,
            node_id=f"user:{user.id}",
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return RouteResponse(
        model_id=decision["model_id"],
        provider=decision["provider"],
        model_name=decision["model_name"],
        region=decision["region"],
        cross_border_risk=decision["cross_border_risk"],
        reason=decision["reason"],
    )


# ─── Scope Config ───
@router.post("/scope-configs", status_code=201, response_model=ScopeConfigResponse)
async def set_scope_config(
    req: ScopeConfigRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        data = await lhs.set_scope_config(
            db=db,
            scope_type=req.scope_type,
            model_id=req.model_id,
            node_id=req.node_id,
            temperature=req.temperature,
            timeout=req.timeout,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return data


@router.get("/scope-configs", response_model=List[ScopeOverviewItem])
async def list_scope_configs(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await lhs.list_scope_configs(db=db)


@router.delete("/scope-configs/{config_id}", status_code=204)
async def remove_scope_config(
    config_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ok = await lhs.remove_scope_config(db=db, config_id=config_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Config not found")
    return None


@router.get("/scope-configs/nodes", response_model=List[ScopeOverviewItem])
async def get_node_scope_overview(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Simplified: return current scope configs (global + overrides)
    # Full implementation may pull all registered agents/skills from agent_hub.
    configs = await lhs.list_scope_configs(db=db)
    return configs


# ─── Usage & Cost ───
@router.post("/usage-logs", status_code=201, response_model=UsageLogResponse)
async def log_usage(
    req: UsageLogRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    data = await lhs.log_usage(
        db=db,
        model_id=req.model_id,
        node_id=req.node_id,
        provider_region=req.provider_region,
        input_tokens=req.input_tokens,
        output_tokens=req.output_tokens,
        latency_ms=req.latency_ms,
        status=req.status,
        error=req.error_message,
    )
    return data


@router.get("/usage-logs", response_model=List[UsageLogResponse])
async def get_usage_logs(
    model_id: Optional[str] = Query(None),
    node_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await lhs.get_usage_logs(
        db=db,
        model_id=model_id,
        node_id=node_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )


@router.get("/cost-summary", response_model=CostSummaryResponse)
async def get_cost_summary(
    period_days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await lhs.get_cost_summary(db=db, period_days=period_days)
