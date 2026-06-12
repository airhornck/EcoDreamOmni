"""Checkpoint Manager — v4.0 Phase 4 P4-3.

分层存储：PostgreSQL（持久化）+ Redis（热缓存，TTL 7 天）+ 本地文件（大 Payload）。

架构红线:
- §2.1 Pipeline 层只执行不决策：Checkpoint 仅记录状态，不解释业务含义
- §2.4 状态快照可恢复：Agent 执行必须支持 Checkpoints，故障可恢复
"""

import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# ─── Redis 可选导入（未安装/未连接时回退内存实现） ───
try:
    import redis.asyncio as aioredis

    _HAS_REDIS = True
except ImportError:
    aioredis = None  # type: ignore
    _HAS_REDIS = False

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

CHECKPOINT_TTL_SECONDS = 7 * 24 * 60 * 60  # 7 days
PAYLOAD_SIZE_THRESHOLD = 1024 * 1024  # 1MB


@dataclass
class CheckpointRecord:
    checkpoint_id: str
    execution_id: str
    node_id: str
    node_status: str
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    output_summary: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    latency_ms: Optional[int] = None
    token_usage: Optional[Dict[str, Any]] = None
    is_recoverable: bool = True
    created_at: Optional[str] = None


class CheckpointManager:
    """节点级状态快照管理器.

    同步接口（save_sync / load_sync / load_all_sync）：
        供同步代码（如 workflow_engine.execute_next_node）使用。
        仅写本地文件 + 内存，不阻塞。

    异步接口（save / load / load_all）：
        供 async 上下文使用。
        先调用同步接口，再写 PostgreSQL + Redis。
    """

    def __init__(
        self,
        db_session: Optional[AsyncSession] = None,
        redis_client: Optional[Any] = None,
        checkpoint_dir: Optional[str] = None,
    ):
        self._db = db_session
        self._redis = redis_client
        self._local_cache: Dict[str, Dict[str, Any]] = {}
        self._checkpoint_dir = Path(checkpoint_dir or "checkpoints")
        self._checkpoint_dir.mkdir(parents=True, exist_ok=True)

    # ═══════════════════════════════════════════════════════
    # Key helpers
    # ═══════════════════════════════════════════════════════

    def _key(self, execution_id: str, node_id: str) -> str:
        return f"checkpoint:{execution_id}:{node_id}"

    def _file_path(self, execution_id: str, node_id: str, suffix: str = "") -> Path:
        dir_path = self._checkpoint_dir / execution_id
        dir_path.mkdir(parents=True, exist_ok=True)
        name = f"{node_id}{suffix}.json"
        return dir_path / name

    # ═══════════════════════════════════════════════════════
    # Serialization helpers
    # ═══════════════════════════════════════════════════════

    @staticmethod
    def _payload_size(data: Dict[str, Any]) -> int:
        return len(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def _maybe_offload(
        self,
        execution_id: str,
        node_id: str,
        data: Dict[str, Any],
        suffix: str,
    ) -> tuple[Dict[str, Any], Optional[str]]:
        """若 Payload 超过阈值，写入本地文件并返回引用."""
        if self._payload_size(data) <= PAYLOAD_SIZE_THRESHOLD:
            return data, None
        path = self._file_path(execution_id, node_id, suffix)
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return {}, f"file://{path}"

    def _resolve_ref(self, ref: Optional[str]) -> Dict[str, Any]:
        """从引用加载实际数据."""
        if not ref or not ref.startswith("file://"):
            return {}
        path = Path(ref[7:])
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        return {}

    def _build_record(
        self,
        checkpoint_id: str,
        execution_id: str,
        node_id: str,
        node_status: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        input_ref: Optional[str],
        output_ref: Optional[str],
        started_at: Optional[str],
        completed_at: Optional[str],
        latency_ms: Optional[int],
        token_usage: Optional[Dict[str, Any]],
    ) -> CheckpointRecord:
        now = datetime.now(timezone.utc).isoformat()
        return CheckpointRecord(
            checkpoint_id=checkpoint_id,
            execution_id=execution_id,
            node_id=node_id,
            node_status=node_status,
            input_data=input_data,
            output_data=output_data,
            output_summary=str(output_data)[:512] if output_data else None,
            started_at=started_at,
            completed_at=completed_at or now,
            latency_ms=latency_ms,
            token_usage=token_usage,
            is_recoverable=True,
            created_at=now,
        )

    # ═══════════════════════════════════════════════════════
    # Sync API（供 workflow_engine 同步上下文使用）
    # ═══════════════════════════════════════════════════════

    def save_sync(
        self,
        execution_id: str,
        node_id: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        status: str,
        *,
        started_at: Optional[str] = None,
        completed_at: Optional[str] = None,
        latency_ms: Optional[int] = None,
        token_usage: Optional[Dict[str, Any]] = None,
    ) -> CheckpointRecord:
        """同步保存 Checkpoint（本地文件 + 内存缓存）."""
        checkpoint_id = f"cp_{secrets.token_urlsafe(8)}"

        input_data_stored, input_ref = self._maybe_offload(
            execution_id, node_id, input_data, "_input"
        )
        output_data_stored, output_ref = self._maybe_offload(
            execution_id, node_id, output_data, "_output"
        )

        record = self._build_record(
            checkpoint_id=checkpoint_id,
            execution_id=execution_id,
            node_id=node_id,
            node_status=status,
            input_data=input_data_stored,
            output_data=output_data_stored,
            input_ref=input_ref,
            output_ref=output_ref,
            started_at=started_at,
            completed_at=completed_at,
            latency_ms=latency_ms,
            token_usage=token_usage,
        )

        # 内存缓存（同步接口也写缓存，保证 load_sync 可见）
        self._local_cache[self._key(execution_id, node_id)] = {
            "checkpoint_id": record.checkpoint_id,
            "execution_id": record.execution_id,
            "node_id": record.node_id,
            "node_status": record.node_status,
            "input_data": record.input_data,
            "output_data": record.output_data,
            "input_ref": input_ref,
            "output_ref": output_ref,
            "output_summary": record.output_summary,
            "started_at": record.started_at,
            "completed_at": record.completed_at,
            "latency_ms": record.latency_ms,
            "token_usage": record.token_usage,
            "is_recoverable": record.is_recoverable,
            "created_at": record.created_at,
        }

        return record

    def load_sync(self, execution_id: str, node_id: str) -> Optional[CheckpointRecord]:
        """同步加载 Checkpoint（优先内存缓存）."""
        key = self._key(execution_id, node_id)
        data = self._local_cache.get(key)
        if data:
            return self._from_dict(data)
        return None

    def load_all_sync(self, execution_id: str) -> List[CheckpointRecord]:
        """同步加载某 execution 的全部 Checkpoint."""
        prefix = f"checkpoint:{execution_id}:"
        records: List[CheckpointRecord] = []
        for key, data in self._local_cache.items():
            if key.startswith(prefix):
                records.append(self._from_dict(data))
        records.sort(key=lambda r: r.node_id)
        return records

    # ═══════════════════════════════════════════════════════
    # Async API（完整持久化：DB + Redis）
    # ═══════════════════════════════════════════════════════

    async def save(
        self,
        execution_id: str,
        node_id: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        status: str,
        *,
        started_at: Optional[str] = None,
        completed_at: Optional[str] = None,
        latency_ms: Optional[int] = None,
        token_usage: Optional[Dict[str, Any]] = None,
    ) -> CheckpointRecord:
        """异步保存 Checkpoint（本地文件 + 内存 + PostgreSQL + Redis）."""
        # 1. 同步底层保存
        record = self.save_sync(
            execution_id=execution_id,
            node_id=node_id,
            input_data=input_data,
            output_data=output_data,
            status=status,
            started_at=started_at,
            completed_at=completed_at,
            latency_ms=latency_ms,
            token_usage=token_usage,
        )

        cache_entry = self._local_cache[self._key(execution_id, node_id)]
        input_ref = cache_entry.get("input_ref")
        output_ref = cache_entry.get("output_ref")

        # 2. 写入 PostgreSQL
        if self._db is not None:
            try:
                from src.models.checkpoint_orm import CheckpointORM

                orm = CheckpointORM(
                    checkpoint_id=record.checkpoint_id,
                    execution_id=record.execution_id,
                    node_id=record.node_id,
                    node_status=record.node_status,
                    input_ref=input_ref,
                    output_ref=output_ref,
                    output_summary=record.output_summary,
                    started_at=datetime.fromisoformat(record.started_at) if record.started_at else None,
                    completed_at=datetime.fromisoformat(record.completed_at) if record.completed_at else None,
                    latency_ms=record.latency_ms,
                    token_usage=record.token_usage,
                    is_recoverable=record.is_recoverable,
                    created_at=datetime.fromisoformat(record.created_at) if record.created_at else None,
                )
                self._db.add(orm)
                await self._db.commit()
            except Exception:
                await self._db.rollback()
                # Checkpoint 为 best-effort，不抛异常

        # 3. 写入 Redis（TTL 7 天）
        if self._redis is not None:
            try:
                key = self._key(execution_id, node_id)
                await self._redis.setex(
                    key,
                    CHECKPOINT_TTL_SECONDS,
                    json.dumps(cache_entry, default=str),
                )
            except Exception:
                pass  # Redis 失败不阻塞

        return record

    async def load(self, execution_id: str, node_id: str) -> Optional[CheckpointRecord]:
        """异步加载 Checkpoint（Redis → 内存 → PostgreSQL）."""
        key = self._key(execution_id, node_id)

        # 1. Redis
        if self._redis is not None:
            try:
                data = await self._redis.get(key)
                if data:
                    return self._from_dict(json.loads(data))
            except Exception:
                pass

        # 2. 内存缓存
        if key in self._local_cache:
            return self._from_dict(self._local_cache[key])

        # 3. PostgreSQL
        if self._db is not None:
            try:
                from src.models.checkpoint_orm import CheckpointORM

                result = await self._db.execute(
                    select(CheckpointORM).where(
                        CheckpointORM.execution_id == execution_id,
                        CheckpointORM.node_id == node_id,
                    )
                )
                orm = result.scalar_one_or_none()
                if orm:
                    return self._from_orm(orm)
            except Exception:
                pass

        return None

    async def load_all(self, execution_id: str) -> List[CheckpointRecord]:
        """异步加载某 execution 的全部 Checkpoint（优先 DB）."""
        if self._db is not None:
            try:
                from src.models.checkpoint_orm import CheckpointORM

                result = await self._db.execute(
                    select(CheckpointORM)
                    .where(CheckpointORM.execution_id == execution_id)
                    .order_by(CheckpointORM.node_id)
                )
                return [self._from_orm(row) for row in result.scalars().all()]
            except Exception:
                pass

        return self.load_all_sync(execution_id)

    # ═══════════════════════════════════════════════════════
    # Internal deserialization
    # ═══════════════════════════════════════════════════════

    def _from_dict(self, data: Dict[str, Any]) -> CheckpointRecord:
        input_data = data.get("input_data", {})
        output_data = data.get("output_data", {})
        # 若内联数据为空但有引用，尝试加载
        if not input_data:
            input_data = self._resolve_ref(data.get("input_ref"))
        if not output_data:
            output_data = self._resolve_ref(data.get("output_ref"))

        return CheckpointRecord(
            checkpoint_id=data["checkpoint_id"],
            execution_id=data["execution_id"],
            node_id=data["node_id"],
            node_status=data["node_status"],
            input_data=input_data,
            output_data=output_data,
            output_summary=data.get("output_summary"),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            latency_ms=data.get("latency_ms"),
            token_usage=data.get("token_usage"),
            is_recoverable=data.get("is_recoverable", True),
            created_at=data.get("created_at"),
        )

    def _from_orm(self, orm) -> CheckpointRecord:
        input_data = self._resolve_ref(orm.input_ref)
        output_data = self._resolve_ref(orm.output_ref)

        return CheckpointRecord(
            checkpoint_id=orm.checkpoint_id,
            execution_id=orm.execution_id,
            node_id=orm.node_id,
            node_status=orm.node_status,
            input_data=input_data,
            output_data=output_data,
            output_summary=orm.output_summary,
            started_at=orm.started_at.isoformat() if orm.started_at else None,
            completed_at=orm.completed_at.isoformat() if orm.completed_at else None,
            latency_ms=orm.latency_ms,
            token_usage=orm.token_usage,
            is_recoverable=orm.is_recoverable,
            created_at=orm.created_at.isoformat() if orm.created_at else None,
        )
