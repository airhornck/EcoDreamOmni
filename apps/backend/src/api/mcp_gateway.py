"""MCP Gateway — v4.0 Phase 5 P5-3.

MCP (Model Context Protocol) Tool 注册/发现/调用预留接口。
当前为骨架实现，所有接口返回 501 Not Implemented（Phase 2 实现）。

架构红线:
- §2.3 MCP 协议预留：所有对外暴露的 Agent/Skill 接口必须兼容 MCP 协议结构
- §2.5 模态路由必须使用 LLM Hub
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/mcp-gateway", tags=["mcp-gateway"])


# ─── Schemas ───

class MCPToolSchema(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any] = Field(default_factory=dict)


class MCPRegisterServerRequest(BaseModel):
    name: str
    url: str
    tools: List[MCPToolSchema] = Field(default_factory=list)


class MCPToolCallRequest(BaseModel):
    server_id: str
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)


class MCPResponse(BaseModel):
    status: str = "not_implemented"
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# ─── Endpoints ───

@router.post(
    "/servers",
    status_code=501,
    response_model=MCPResponse,
    summary="Register an MCP Server (Phase 2)",
)
def register_server(req: MCPRegisterServerRequest):
    """Register an MCP-compatible tool server.

    **Not implemented** — scheduled for Phase 2.
    """
    raise HTTPException(
        status_code=501,
        detail="MCP Server registration is not implemented yet (Phase 2).",
    )


@router.get(
    "/servers/{server_id}/tools",
    status_code=501,
    response_model=MCPResponse,
    summary="Discover tools on an MCP Server (Phase 2)",
)
def discover_tools(server_id: str):
    """Discover available tools on a registered MCP server.

    **Not implemented** — scheduled for Phase 2.
    """
    raise HTTPException(
        status_code=501,
        detail="MCP Tool discovery is not implemented yet (Phase 2).",
    )


@router.post(
    "/tools/call",
    status_code=501,
    response_model=MCPResponse,
    summary="Call an MCP Tool (Phase 2)",
)
def call_tool(req: MCPToolCallRequest):
    """Invoke a tool via the MCP Gateway.

    **Not implemented** — scheduled for Phase 2.
    """
    raise HTTPException(
        status_code=501,
        detail="MCP Tool call is not implemented yet (Phase 2).",
    )
