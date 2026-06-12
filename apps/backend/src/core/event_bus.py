"""Event Bus — v4.0 Phase 5 P5-2.

Redis Streams 统一通信层，支持发布/消费/ACK。
 fallback 内存模式（Redis 不可用时）。

架构红线:
- §2.2 Event Bus 优先于直接调用：Agent 间通信必须通过 Event Bus
- §2.3 MCP 协议预留：事件格式兼容 MCP Tool Call 结构
"""

import json
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

# ─── Redis 可选导入（未安装/未连接时回退内存实现） ───
try:
    import redis.asyncio as aioredis

    _HAS_REDIS = True
except ImportError:
    aioredis = None  # type: ignore
    _HAS_REDIS = False

# ─── 预定义事件频道 ───

AGENT_EVENTS = "agent.events"
PIPELINE_EVENTS = "pipeline.events"
SYSTEM_EVENTS = "system.events"
WORKBENCH_EVENTS = "workbench.events"

ALL_STREAMS: Set[str] = {
    AGENT_EVENTS,
    PIPELINE_EVENTS,
    SYSTEM_EVENTS,
    WORKBENCH_EVENTS,
}

# ─── Message format ───


def build_message(
    event_type: str,
    source: str,
    payload: Dict[str, Any],
    trace_id: Optional[str] = None,
) -> Dict[str, Any]:
    """构建标准事件消息."""
    return {
        "event_type": event_type,
        "source": source,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "payload": payload,
        "trace_id": trace_id or secrets.token_hex(8),
    }


# ─── EventBus ───


@dataclass
class EventBus:
    """Redis Streams Event Bus + 内存 fallback."""

    redis_client: Optional[Any] = None
    _memory_streams: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    _memory_pending: Dict[str, Dict[str, Dict[str, Any]]] = field(default_factory=dict)
    _memory_groups: Dict[str, Set[str]] = field(default_factory=dict)
    _seq: int = 0

    def __post_init__(self):
        # 初始化内存组状态
        for stream in ALL_STREAMS:
            if stream not in self._memory_streams:
                self._memory_streams[stream] = []
            if stream not in self._memory_pending:
                self._memory_pending[stream] = {}
            if stream not in self._memory_groups:
                self._memory_groups[stream] = set()

    # ═══════════════════════════════════════════════════════
    # Publish
    # ═══════════════════════════════════════════════════════

    async def publish(self, stream: str, message: Dict[str, Any]) -> str:
        """发布事件到指定 Stream，返回 message_id."""
        if self.redis_client is not None:
            try:
                msg_id = await self.redis_client.xadd(
                    stream,
                    {"data": json.dumps(message, default=str)},
                    maxlen=10000,
                    approximate=True,
                )
                return str(msg_id)
            except Exception:
                # Redis 失败时回退内存
                pass

        # 内存 fallback
        self._seq += 1
        msg_id = f"mem-{self._seq}"
        entry = {
            "id": msg_id,
            "data": message,
            "acknowledged": False,
        }
        self._memory_streams.setdefault(stream, []).append(entry)
        return msg_id

    # ═══════════════════════════════════════════════════════
    # Consumer Group
    # ═══════════════════════════════════════════════════════

    async def create_consumer_group(self, stream: str, group: str) -> bool:
        """创建消费者组，若已存在则返回 True."""
        if self.redis_client is not None:
            try:
                await self.redis_client.xgroup_create(
                    stream, group, id="0", mkstream=True
                )
                return True
            except Exception as exc:
                # 组已存在时 Redis 返回错误，视为成功
                if "already exists" in str(exc).lower():
                    return True
                return False

        # 内存 fallback
        self._memory_groups.setdefault(stream, set()).add(group)
        return True

    # ═══════════════════════════════════════════════════════
    # Consume
    # ═══════════════════════════════════════════════════════

    async def consume(
        self,
        stream: str,
        group: str,
        consumer: str,
        count: int = 10,
        block_ms: int = 5000,
    ) -> List[Dict[str, Any]]:
        """消费者组消费消息，返回消息列表（含 id / data）."""
        if self.redis_client is not None:
            try:
                result = await self.redis_client.xreadgroup(
                    groupname=group,
                    consumername=consumer,
                    streams={stream: ">"},
                    count=count,
                    block=block_ms,
                )
                messages: List[Dict[str, Any]] = []
                for _, entries in result:
                    for msg_id, fields in entries:
                        raw = fields.get("data", "{}")
                        data = json.loads(raw) if isinstance(raw, str) else raw
                        messages.append({
                            "id": str(msg_id),
                            "data": data,
                        })
                return messages
            except Exception:
                pass

        # 内存 fallback
        await self.create_consumer_group(stream, group)
        group_key = f"{stream}:{group}"
        pending = self._memory_pending.setdefault(group_key, {})
        messages = []

        for entry in self._memory_streams.get(stream, []):
            if entry["acknowledged"]:
                continue
            msg_id = entry["id"]
            # 同组内避免重复分配给同一消费者
            if msg_id in pending and pending[msg_id].get("consumer") != consumer:
                continue
            pending[msg_id] = {
                "group": group,
                "consumer": consumer,
                "data": entry["data"],
            }
            messages.append({
                "id": msg_id,
                "data": entry["data"],
            })
            if len(messages) >= count:
                break

        return messages

    # ═══════════════════════════════════════════════════════
    # ACK
    # ═══════════════════════════════════════════════════════

    async def ack(self, stream: str, group: str, message_id: str) -> bool:
        """确认消息已处理."""
        if self.redis_client is not None:
            try:
                await self.redis_client.xack(stream, group, message_id)
                return True
            except Exception:
                return False

        # 内存 fallback
        group_key = f"{stream}:{group}"
        pending = self._memory_pending.get(group_key, {})
        if message_id in pending:
            del pending[message_id]

        for entry in self._memory_streams.get(stream, []):
            if entry["id"] == message_id:
                entry["acknowledged"] = True
                return True
        return False

    # ═══════════════════════════════════════════════════════
    # Info / Metrics
    # ═══════════════════════════════════════════════════════

    def get_stream_length(self, stream: str) -> int:
        """获取 Stream 消息总数（含已 ACK）."""
        return len(self._memory_streams.get(stream, []))

    def get_pending_count(self, stream: str, group: Optional[str] = None) -> int:
        """获取未 ACK 消息数."""
        if group:
            return len(self._memory_pending.get(f"{stream}:{group}", {}))
        # 所有组的总 pending 数
        total = 0
        for key, items in self._memory_pending.items():
            if key.startswith(f"{stream}:"):
                total += len(items)
        return total

    def get_memory_events(self, stream: str) -> List[Dict[str, Any]]:
        """获取内存中某 Stream 的全部事件（调试用）."""
        return [e["data"] for e in self._memory_streams.get(stream, [])]
