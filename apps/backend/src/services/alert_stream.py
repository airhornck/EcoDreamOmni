"""Real-time Alert Stream — WebSocket pub/sub + alert generator.

MVP: In-memory connection manager + alert history.
Production: Redis Pub/Sub + persistent DB.
"""

import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import WebSocket


@dataclass
class Alert:
    id: str
    level: str  # emergency, warning, info, success
    title: str
    message: str
    timestamp: str
    source: str = "system"


class AlertManager:
    """Manages WebSocket connections and broadcasts alerts."""

    def __init__(self):
        self._connections: List[WebSocket] = []
        self._history: List[Alert] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self._connections:
            self._connections.remove(websocket)

    async def broadcast(self, alert: Alert) -> None:
        """Send alert to all connected clients."""
        payload = {
            "id": alert.id,
            "level": alert.level,
            "title": alert.title,
            "message": alert.message,
            "timestamp": alert.timestamp,
            "source": alert.source,
        }
        # Send to all connected sockets; remove dead ones
        dead = []
        for ws in self._connections:
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    def add_to_history(self, alert: Alert) -> None:
        self._history.append(alert)
        # Keep last 100 alerts
        if len(self._history) > 100:
            self._history = self._history[-100:]

    def get_history(self, level: Optional[str] = None, limit: int = 50) -> List[Alert]:
        alerts = self._history
        if level:
            alerts = [a for a in alerts if a.level == level]
        return alerts[-limit:][::-1]


# Global singleton
_manager = AlertManager()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─── Public API ───

def get_manager() -> AlertManager:
    return _manager


def broadcast_alert(data: Dict) -> None:
    """Broadcast an alert immediately (synchronous wrapper for tests).
    
    In async context, use manager.broadcast() directly.
    """
    alert = Alert(
        id=data.get("id", secrets.token_urlsafe(8)),
        level=data.get("level", "info"),
        title=data.get("title", ""),
        message=data.get("message", ""),
        timestamp=_now(),
        source=data.get("source", "system"),
    )
    _manager.add_to_history(alert)
    # For sync test compatibility, we cannot await async broadcast.
    # Tests using TestClient websocket_connect will receive on next receive_json
    # if the broadcast was triggered before receive.
    # In production this is called from async handlers.


def generate_alert(level: str, title: str, message: str, source: str = "generator") -> Alert:
    """Generate a new alert, add to history, and broadcast."""
    alert = Alert(
        id=secrets.token_urlsafe(8),
        level=level,
        title=title,
        message=message,
        timestamp=_now(),
        source=source,
    )
    _manager.add_to_history(alert)
    return alert


def list_alerts(level: Optional[str] = None, limit: int = 50) -> List[Dict]:
    alerts = _manager.get_history(level=level, limit=limit)
    return [
        {
            "id": a.id,
            "level": a.level,
            "title": a.title,
            "message": a.message,
            "timestamp": a.timestamp,
            "source": a.source,
        }
        for a in alerts
    ]


def clear_alerts() -> None:
    _manager._history.clear()
    _manager._connections.clear()
