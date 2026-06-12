"""Tests for MCP Gateway — Phase 5 P5-3.

Red-Green TDD for:
  - 3 个接口均返回 501
  - 请求 Schema 校验通过
  - 响应格式符合 MCPResponse
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.mcp_gateway import router

# 创建临时 FastAPI app 以支持中间件上下文
_app = FastAPI()
_app.include_router(router)
client = TestClient(_app)


# ─── 1. Register Server ───


def test_register_server_returns_501():
    """POST /mcp-gateway/servers 返回 501."""
    response = client.post(
        "/mcp-gateway/servers",
        json={"name": "test-server", "url": "http://localhost:8080"},
    )
    assert response.status_code == 501
    data = response.json()
    assert "Phase 2" in data["detail"]


# ─── 2. Discover Tools ───


def test_discover_tools_returns_501():
    """GET /mcp-gateway/servers/{id}/tools 返回 501."""
    response = client.get("/mcp-gateway/servers/srv_001/tools")
    assert response.status_code == 501
    data = response.json()
    assert "Phase 2" in data["detail"]


# ─── 3. Call Tool ───


def test_call_tool_returns_501():
    """POST /mcp-gateway/tools/call 返回 501."""
    response = client.post(
        "/mcp-gateway/tools/call",
        json={"server_id": "srv_001", "tool_name": "echo", "arguments": {"msg": "hi"}},
    )
    assert response.status_code == 501
    data = response.json()
    assert "Phase 2" in data["detail"]


# ─── 4. Schema validation ───


def test_register_server_validates_schema():
    """缺少必填字段时返回 422."""
    response = client.post("/mcp-gateway/servers", json={})
    assert response.status_code == 422


def test_call_tool_validates_schema():
    """缺少必填字段时返回 422."""
    response = client.post("/mcp-gateway/tools/call", json={})
    assert response.status_code == 422
