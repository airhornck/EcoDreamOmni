"""Agent Heartbeat — v4.0 Phase 2 P2-1a.

异步心跳任务，定期上报 Agent 健康状态。
可独立运行或作为 BackgroundTask 注册到 FastAPI。
"""

import asyncio
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, Optional


@dataclass
class HeartbeatConfig:
    interval_seconds: float = 30.0
    timeout_seconds: float = 5.0
    max_misses_before_degraded: int = 3
    max_misses_before_offline: int = 6


class HeartbeatTask:
    """Manage periodic heartbeat for an Agent.

    Usage:
        hb = HeartbeatTask(sdk, config)
        asyncio.create_task(hb.run())
        ...
        hb.stop()
    """

    def __init__(
        self,
        sdk: Any,  # AgentSDK
        config: Optional[HeartbeatConfig] = None,
        on_status_change: Optional[Callable[[str, str], Awaitable[None]]] = None,
    ):
        self.sdk = sdk
        self.cfg = config or HeartbeatConfig()
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._on_status_change = on_status_change
        self._miss_count = 0
        self._last_status: Optional[str] = None

    async def run(self) -> None:
        self._running = True
        while self._running:
            try:
                self.sdk.heartbeat(status="healthy")
                self._miss_count = 0
                new_status = "healthy"
            except Exception:
                self._miss_count += 1
                new_status = "unhealthy"
                if self._miss_count >= self.cfg.max_misses_before_offline:
                    new_status = "offline"
                elif self._miss_count >= self.cfg.max_misses_before_degraded:
                    new_status = "degraded"

            if new_status != self._last_status and self._on_status_change:
                await self._on_status_change(self._last_status or "unknown", new_status)
                self._last_status = new_status

            try:
                await asyncio.wait_for(
                    asyncio.sleep(self.cfg.interval_seconds),
                    timeout=self.cfg.interval_seconds + self.cfg.timeout_seconds,
                )
            except asyncio.TimeoutError:
                pass

    def stop(self) -> None:
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()

    def status(self) -> Dict[str, Any]:
        return {
            "running": self._running,
            "miss_count": self._miss_count,
            "last_status": self._last_status,
            "interval_seconds": self.cfg.interval_seconds,
        }
