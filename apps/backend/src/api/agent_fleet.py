"""Agent Fleet API — v4.0 Phase 8 P8-3.

Fleet 管理路由：CRUD + 实例注册/心跳/路由 + 健康查询.
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query

from src.core.schemas.base import BaseResponse
from src.services import agent_fleet as fleet_service

router = APIRouter(prefix="/agent-fleet", tags=["agent-fleet"])


# ─── Fleet CRUD ───


@router.post("/fleets", response_model=BaseResponse)
async def create_fleet(body: Dict[str, Any]) -> BaseResponse:
    agent_type = body.get("agent_type", "")
    tenant_id = body.get("tenant_id", "")
    if not agent_type or not tenant_id:
        raise HTTPException(status_code=400, detail="agent_type and tenant_id required")

    fleet = fleet_service.create_fleet(
        agent_type=agent_type,
        tenant_id=tenant_id,
        min_instances=body.get("min_instances", 1),
        max_instances=body.get("max_instances", 10),
        routing_strategy=body.get("routing_strategy", "round_robin"),
        auto_scale_enabled=body.get("auto_scale_enabled", False),
    )
    return BaseResponse(
        code="CREATED",
        message="舰队创建成功",
        data={
            "fleet_id": fleet.fleet_id,
            "agent_type": fleet.agent_type,
            "min_instances": fleet.min_instances,
            "max_instances": fleet.max_instances,
            "routing_strategy": fleet.routing_strategy.value,
        },
        trace_id="",
        timestamp="",
    )


@router.get("/fleets", response_model=BaseResponse)
async def list_fleets(tenant_id: str = Query("")) -> BaseResponse:
    fleets = fleet_service.list_fleets(tenant_id=tenant_id)
    return BaseResponse(
        code="OK",
        message="查询成功",
        data=[
            {
                "fleet_id": f.fleet_id,
                "agent_type": f.agent_type,
                "tenant_id": f.tenant_id,
                "instance_count": len(f.instances),
                "routing_strategy": f.routing_strategy.value,
                "auto_scale_enabled": f.auto_scale_enabled,
            }
            for f in fleets
        ],
        trace_id="",
        timestamp="",
    )


@router.get("/fleets/{fleet_id}", response_model=BaseResponse)
async def get_fleet(fleet_id: str) -> BaseResponse:
    fleet = fleet_service.get_fleet(fleet_id)
    if not fleet:
        raise HTTPException(status_code=404, detail="Fleet not found")
    return BaseResponse(
        code="OK",
        message="查询成功",
        data={
            "fleet_id": fleet.fleet_id,
            "agent_type": fleet.agent_type,
            "tenant_id": fleet.tenant_id,
            "min_instances": fleet.min_instances,
            "max_instances": fleet.max_instances,
            "routing_strategy": fleet.routing_strategy.value,
            "auto_scale_enabled": fleet.auto_scale_enabled,
            "instance_count": len(fleet.instances),
            "health": fleet_service.get_fleet_health(fleet_id),
        },
        trace_id="",
        timestamp="",
    )


@router.delete("/fleets/{fleet_id}", response_model=BaseResponse)
async def delete_fleet(fleet_id: str) -> BaseResponse:
    success = fleet_service.delete_fleet(fleet_id)
    if not success:
        raise HTTPException(status_code=404, detail="Fleet not found")
    return BaseResponse(
        code="OK",
        message="舰队已删除",
        data={"fleet_id": fleet_id},
        trace_id="",
        timestamp="",
    )


# ─── Instance Management ───


@router.post("/fleets/{fleet_id}/instances", response_model=BaseResponse)
async def register_instance(fleet_id: str, body: Dict[str, Any]) -> BaseResponse:
    instance = fleet_service.register_instance(
        fleet_id=fleet_id,
        agent_id=body.get("agent_id", ""),
        capabilities=body.get("capabilities"),
        max_tasks=body.get("max_tasks", 5),
        metadata=body.get("metadata"),
    )
    if not instance:
        raise HTTPException(status_code=404, detail="Fleet not found")
    return BaseResponse(
        code="CREATED",
        message="实例注册成功",
        data={
            "instance_id": instance.instance_id,
            "agent_id": instance.agent_id,
            "status": instance.status.value,
            "capabilities": instance.capabilities,
            "max_tasks": instance.max_tasks,
        },
        trace_id="",
        timestamp="",
    )


@router.delete("/fleets/{fleet_id}/instances/{instance_id}", response_model=BaseResponse)
async def unregister_instance(fleet_id: str, instance_id: str) -> BaseResponse:
    success = fleet_service.unregister_instance(fleet_id, instance_id)
    if not success:
        raise HTTPException(status_code=404, detail="Instance or fleet not found")
    return BaseResponse(
        code="OK",
        message="实例已注销",
        data={"fleet_id": fleet_id, "instance_id": instance_id},
        trace_id="",
        timestamp="",
    )


@router.get("/fleets/{fleet_id}/instances", response_model=BaseResponse)
async def list_instances(
    fleet_id: str,
    status: Optional[str] = Query(None),
) -> BaseResponse:
    instances = fleet_service.list_instances(fleet_id, status_filter=status)
    return BaseResponse(
        code="OK",
        message="查询成功",
        data=[
            {
                "instance_id": i.instance_id,
                "agent_id": i.agent_id,
                "status": i.status.value,
                "current_tasks": i.current_tasks,
                "max_tasks": i.max_tasks,
                "load_ratio": round(i.load_ratio, 2),
                "cpu_percent": i.cpu_percent,
                "memory_percent": i.memory_percent,
                "capabilities": i.capabilities,
                "last_heartbeat_at": i.last_heartbeat_at,
            }
            for i in instances
        ],
        trace_id="",
        timestamp="",
    )


# ─── Heartbeat ───


@router.post("/fleets/{fleet_id}/instances/{instance_id}/heartbeat", response_model=BaseResponse)
async def instance_heartbeat(
    fleet_id: str,
    instance_id: str,
    body: Dict[str, Any],
) -> BaseResponse:
    success = fleet_service.heartbeat(
        fleet_id=fleet_id,
        instance_id=instance_id,
        cpu_percent=body.get("cpu_percent", 0.0),
        memory_percent=body.get("memory_percent", 0.0),
        current_tasks=body.get("current_tasks", 0),
        status=body.get("status"),
    )
    if not success:
        raise HTTPException(status_code=404, detail="Instance or fleet not found")
    return BaseResponse(
        code="OK",
        message="心跳已接收",
        data={"fleet_id": fleet_id, "instance_id": instance_id},
        trace_id="",
        timestamp="",
    )


# ─── Routing ───


@router.post("/fleets/{fleet_id}/route", response_model=BaseResponse)
async def route_task(fleet_id: str, body: Dict[str, Any]) -> BaseResponse:
    instance = fleet_service.route_task(
        fleet_id=fleet_id,
        required_capabilities=body.get("required_capabilities"),
    )
    if not instance:
        return BaseResponse(
            code="SERVICE_UNAVAILABLE",
            message="无可用实例",
            data={"fleet_id": fleet_id},
            trace_id="",
            timestamp="",
        )
    return BaseResponse(
        code="OK",
        message="路由成功",
        data={
            "instance_id": instance.instance_id,
            "agent_id": instance.agent_id,
            "status": instance.status.value,
            "current_tasks": instance.current_tasks,
            "max_tasks": instance.max_tasks,
            "capabilities": instance.capabilities,
        },
        trace_id="",
        timestamp="",
    )


# ─── Health & Scaling ───


@router.get("/fleets/{fleet_id}/health", response_model=BaseResponse)
async def get_fleet_health(fleet_id: str) -> BaseResponse:
    health = fleet_service.get_fleet_health(fleet_id)
    if not health:
        raise HTTPException(status_code=404, detail="Fleet not found")
    return BaseResponse(
        code="OK",
        message="查询成功",
        data=health,
        trace_id="",
        timestamp="",
    )


@router.get("/fleets/{fleet_id}/scaling", response_model=BaseResponse)
async def evaluate_scaling(fleet_id: str) -> BaseResponse:
    result = fleet_service.evaluate_scaling(fleet_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return BaseResponse(
        code="OK",
        message="查询成功",
        data=result,
        trace_id="",
        timestamp="",
    )
