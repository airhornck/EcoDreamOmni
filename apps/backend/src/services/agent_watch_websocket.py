"""AgentWatch WebSocket — v4.0 Phase 8 P8-6.

扩展 AgentWatch，支持 WebSocket 实时推送 Agent 执行进度到 AI 工作台。
MVP: 内存广播，无持久化（复用现有 AgentWatch heartbeat 数据）。
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set



class StreamEventType(str):
    THINK = "THINK"
    ACT = "ACT"
    OBSERVE = "OBSERVE"
    OUTPUT = "OUTPUT"
    ERROR = "ERROR"
    PROGRESS = "PROGRESS"
    CHECKPOINT = "CHECKPOINT"


@dataclass
class StreamEvent:
    """用于 AI 工作台实时展示 Agent 执行过程."""
    event_type: str
    timestamp: str
    content: str
    payload: Dict[str, Any] = field(default_factory=dict)
    agent_id: str = ""
    execution_id: str = ""
    tenant_id: str = ""


# ─── In-memory event bus for WebSocket broadcast ───
_websocket_subscribers: Dict[str, Set[Any]] = {}  # {tenant_id: {websocket_connections}}
_event_buffer: Dict[str, List[StreamEvent]] = {}  # {execution_id: [events]}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def subscribe(tenant_id: str, websocket: Any) -> None:
    """Subscribe a WebSocket connection to a tenant's event stream."""
    if tenant_id not in _websocket_subscribers:
        _websocket_subscribers[tenant_id] = set()
    _websocket_subscribers[tenant_id].add(websocket)


def unsubscribe(tenant_id: str, websocket: Any) -> None:
    """Unsubscribe a WebSocket connection."""
    subs = _websocket_subscribers.get(tenant_id)
    if subs:
        subs.discard(websocket)
        if not subs:
            del _websocket_subscribers[tenant_id]


async def broadcast_event(event: StreamEvent) -> None:
    """Broadcast an event to all subscribers of the tenant."""
    tenant_id = event.tenant_id or "default"

    # Buffer event
    _event_buffer.setdefault(event.execution_id, []).append(event)

    # Broadcast to WebSocket subscribers
    subs = _websocket_subscribers.get(tenant_id, set()).copy()
    payload = {
        "type": "agent_event",
        "event_type": event.event_type,
        "timestamp": event.timestamp,
        "content": event.content,
        "agent_id": event.agent_id,
        "execution_id": event.execution_id,
        "payload": event.payload,
    }
    message = json.dumps(payload, ensure_ascii=False)

    disconnected = []
    for ws in subs:
        try:
            await ws.send_text(message)
        except Exception:
            disconnected.append(ws)

    for ws in disconnected:
        unsubscribe(tenant_id, ws)


def emit_stream_event(
    execution_id: str,
    agent_id: str,
    event_type: str,
    content: str,
    payload: Optional[Dict[str, Any]] = None,
    tenant_id: str = "",
) -> StreamEvent:
    """Emit a stream event (sync helper, returns the event for testing)."""
    event = StreamEvent(
        event_type=event_type,
        timestamp=_now(),
        content=content,
        payload=payload or {},
        agent_id=agent_id,
        execution_id=execution_id,
        tenant_id=tenant_id,
    )
    # Buffer only; async broadcast is caller's responsibility
    _event_buffer.setdefault(execution_id, []).append(event)
    return event


def get_event_buffer(execution_id: str) -> List[StreamEvent]:
    """Get buffered events for an execution."""
    return list(_event_buffer.get(execution_id, []))


def clear_event_buffer(execution_id: str) -> None:
    """Clear buffered events for an execution."""
    _event_buffer.pop(execution_id, None)


def build_progress_event(
    execution_id: str,
    agent_id: str,
    current_step: int,
    total_steps: int,
    step_description: str,
    tenant_id: str = "",
) -> StreamEvent:
    """Build a PROGRESS type stream event."""
    progress_pct = int((current_step / max(total_steps, 1)) * 100)
    return emit_stream_event(
        execution_id=execution_id,
        agent_id=agent_id,
        event_type="PROGRESS",
        content=step_description,
        payload={
            "current_step": current_step,
            "total_steps": total_steps,
            "progress_percent": progress_pct,
            "estimated_remaining_sec": 0,  # MVP: no estimation
        },
        tenant_id=tenant_id,
    )


def build_agent_status_event(
    agent_id: str,
    status: str,
    tenant_id: str = "",
    extra: Optional[Dict[str, Any]] = None,
) -> StreamEvent:
    """Build an AGENT_STATUS event for AI工作台实时状态条."""
    return emit_stream_event(
        execution_id=extra.get("execution_id", "") if extra else "",
        agent_id=agent_id,
        event_type="AGENT_STATUS",
        content=f"Agent {agent_id} status: {status}",
        payload={"status": status, **(extra or {})},
        tenant_id=tenant_id,
    )
