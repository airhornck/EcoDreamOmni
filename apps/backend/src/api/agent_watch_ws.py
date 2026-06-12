"""AgentWatch WebSocket API — v4.0 Phase 8 P8-6.

WebSocket endpoint for real-time Agent execution streaming.
"""

from typing import Any, Dict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.services.agent_watch_websocket import (
    subscribe,
    unsubscribe,
)

router = APIRouter(prefix="/agent-watch-ws", tags=["agent-watch-ws"])


@router.websocket("/stream/{tenant_id}")
async def agent_stream_websocket(websocket: WebSocket, tenant_id: str) -> None:
    """
    WebSocket endpoint for AI Workbench to receive real-time Agent events.

    Connection lifecycle:
    1. Client connects with tenant_id
    2. Server subscribes the WebSocket to tenant's event stream
    3. Server sends buffered events (if any) for recent executions
    4. Server forwards all new StreamEvents to the client
    5. Client disconnects → unsubscribe
    """
    await websocket.accept()
    subscribe(tenant_id, websocket)

    try:
        while True:
            # Keep connection alive, optionally process client messages
            data = await websocket.receive_text()
            # MVP: client can send ping or subscription filter commands
            try:
                msg: Dict[str, Any] = __import__("json").loads(data)
                action = msg.get("action", "")
                if action == "ping":
                    await websocket.send_json({"type": "pong", "timestamp": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()})
                elif action == "subscribe_execution":
                    execution_id = msg.get("execution_id", "")
                    await websocket.send_json({"type": "subscribed", "execution_id": execution_id})
            except Exception:
                pass
    except WebSocketDisconnect:
        unsubscribe(tenant_id, websocket)
    finally:
        unsubscribe(tenant_id, websocket)
