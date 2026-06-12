"""WebSocket API — real-time alert stream + Copilot channel."""

import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from jose import jwt, JWTError

from src.services.alert_stream import get_manager, generate_alert
from src.core.security import SECRET_KEY, ALGORITHM

router = APIRouter()

# ─── Copilot WebSocket Connections ───
COPILOT_WS_CONNECTIONS: dict[str, WebSocket] = {}


async def _get_user_from_token(token: str) -> dict:
    """Validate JWT token and return payload."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return {}


@router.websocket("/ws/alerts")
async def alert_websocket(websocket: WebSocket, token: str = Query("")):
    """WebSocket endpoint for real-time alerts.
    
    Connect with: ws://host/ws/alerts?token=<jwt>
    """
    user = await _get_user_from_token(token)
    if not user.get("sub"):
        await websocket.close(code=4001, reason="Unauthorized")
        return

    manager = get_manager()
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive; client can send ping or subscribe filters
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ─── REST API for alert history ───

from fastapi import Depends
from pydantic import BaseModel
from src.api.auth import get_current_user


class AlertOut(BaseModel):
    id: str
    level: str
    title: str
    message: str
    timestamp: str
    source: str


@router.get("/api/alerts")
def list_alerts_api(level: str = None, limit: int = 50, user=Depends(get_current_user)):
    from src.services.alert_stream import list_alerts
    alerts = list_alerts(level=level, limit=limit)
    return {"alerts": alerts}


@router.post("/api/alerts", status_code=201)
def create_alert_api(
    level: str,
    title: str,
    message: str,
    source: str = "api",
    user=Depends(get_current_user),
):
    alert = generate_alert(level=level, title=title, message=message, source=source)
    return {
        "id": alert.id,
        "level": alert.level,
        "title": alert.title,
        "message": alert.message,
        "timestamp": alert.timestamp,
        "source": alert.source,
    }


# ───────────────────────────────────────────────
# WebSocket /ws/copilot — v4.0 Copilot-Driven
# ───────────────────────────────────────────────

@router.websocket("/ws/copilot")
async def copilot_websocket(websocket: WebSocket, token: str = Query("")):
    """WebSocket endpoint for Copilot real-time events.

    Connect with: ws://host/ws/copilot?token=<jwt>

    Events:
      C→S: {"event": "context.update", "payload": {...}}
      S→C: {"event": "copilot.card.push", "payload": {...}}
      S→C: {"event": "cover.generation.progress", "payload": {...}}
      S→C: {"event": "cover.generation.completed", "payload": {...}}
      S→C: {"event": "review.decision.completed", "payload": {...}}
    """
    user = await _get_user_from_token(token)
    user_id = user.get("sub")
    if not user_id:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    await websocket.accept()
    COPILOT_WS_CONNECTIONS[user_id] = websocket

    try:
        await asyncio.gather(
            _handle_client_messages(websocket, user_id),
            _redis_listener(websocket, user_id),
            return_exceptions=True,
        )
    except WebSocketDisconnect:
        pass
    finally:
        if user_id in COPILOT_WS_CONNECTIONS:
            del COPILOT_WS_CONNECTIONS[user_id]


async def _handle_client_messages(websocket: WebSocket, user_id: str):
    """Handle incoming messages from the WebSocket client."""
    while True:
        data = await websocket.receive_json()
        event = data.get("event")
        payload = data.get("payload", {})

        if event == "context.update":
            await websocket.send_json({
                "event": "context.ack",
                "payload": {"received": True},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
        elif event == "ping":
            await websocket.send_json({"event": "pong", "timestamp": datetime.now(timezone.utc).isoformat()})


async def _redis_listener(websocket: WebSocket, user_id: str):
    """Subscribe to Redis pub/sub and forward events to WebSocket client."""
    import json
    try:
        import redis.asyncio as aioredis
        redis_client = aioredis.from_url("redis://localhost:6379/0")
        pubsub = redis_client.pubsub()
        channel = f"copilot:events:{user_id}"
        await pubsub.subscribe(channel)

        async for message in pubsub.listen():
            if message["type"] == "message":
                data = json.loads(message["data"])
                await websocket.send_json(data)
    except Exception:
        pass
    finally:
        try:
            await pubsub.unsubscribe(channel)
            await pubsub.aclose()
            await redis_client.aclose()
        except Exception:
            pass


# Re-import datetime for websocket module
from datetime import datetime, timezone
