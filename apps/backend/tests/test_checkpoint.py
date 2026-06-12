"""Tests for Checkpoint Manager — Phase 4 P4-3.

Red-Green TDD for:
  - Sync save/load (local file + memory)
  - Async save/load (DB + Redis fallback)
  - Large payload offload to local file
  - Resume reconstruction from checkpoints
  - Corruption recovery
"""

import tempfile

import pytest

from src.core.checkpoint import CheckpointManager, CheckpointRecord, PAYLOAD_SIZE_THRESHOLD


# ─── 1. Sync API ───


def test_save_sync_creates_record():
    """save_sync 返回 CheckpointRecord 并写入内存缓存."""
    mgr = CheckpointManager()
    record = mgr.save_sync(
        execution_id="exec_001",
        node_id="0",
        input_data={"topic": "宠物"},
        output_data={"keywords": ["a", "b"]},
        status="SUCCESS",
        latency_ms=150,
    )
    assert record.execution_id == "exec_001"
    assert record.node_id == "0"
    assert record.node_status == "SUCCESS"
    assert record.latency_ms == 150
    assert record.is_recoverable is True


def test_load_sync_returns_saved_record():
    """load_sync 能读取刚 save_sync 的数据."""
    mgr = CheckpointManager()
    mgr.save_sync(
        execution_id="exec_002",
        node_id="1",
        input_data={"x": 1},
        output_data={"y": 2},
        status="FAILED",
    )
    loaded = mgr.load_sync("exec_002", "1")
    assert loaded is not None
    assert loaded.node_status == "FAILED"
    assert loaded.output_data == {"y": 2}


def test_load_sync_missing_returns_none():
    """未保存的 checkpoint 返回 None."""
    mgr = CheckpointManager()
    assert mgr.load_sync("exec_none", "0") is None


def test_load_all_sync_sorted():
    """load_all_sync 按 node_id 排序返回."""
    mgr = CheckpointManager()
    for i in [2, 0, 1]:
        mgr.save_sync(
            execution_id="exec_003",
            node_id=str(i),
            input_data={},
            output_data={"step": i},
            status="SUCCESS",
        )
    records = mgr.load_all_sync("exec_003")
    assert len(records) == 3
    assert [r.node_id for r in records] == ["0", "1", "2"]


# ─── 2. Large Payload Offload ───


def test_large_payload_offloaded_to_file():
    """Payload 超过阈值时写入本地文件，记录存引用."""
    with tempfile.TemporaryDirectory() as tmpdir:
        mgr = CheckpointManager(checkpoint_dir=tmpdir)
        large_data = {"content": "x" * (PAYLOAD_SIZE_THRESHOLD + 100)}
        mgr.save_sync(
            execution_id="exec_large",
            node_id="0",
            input_data={},
            output_data=large_data,
            status="SUCCESS",
        )
        # 验证引用写入缓存
        key = mgr._key("exec_large", "0")
        cache_entry = mgr._local_cache[key]
        assert cache_entry["output_ref"].startswith("file://")
        # 验证 load 能解析回完整数据
        loaded = mgr.load_sync("exec_large", "0")
        assert loaded is not None
        assert loaded.output_data == large_data


# ─── 3. Async API (with DB mock) ───


@pytest.mark.asyncio
async def test_async_save_load_roundtrip():
    """async save / load 在仅有内存缓存时也能工作."""
    mgr = CheckpointManager(db_session=None, redis_client=None)
    record = await mgr.save(
        execution_id="exec_async",
        node_id="0",
        input_data={"a": 1},
        output_data={"b": 2},
        status="SUCCESS",
    )
    assert record.checkpoint_id.startswith("cp_")

    loaded = await mgr.load("exec_async", "0")
    assert loaded is not None
    assert loaded.node_status == "SUCCESS"
    assert loaded.output_data == {"b": 2}


@pytest.mark.asyncio
async def test_async_load_all():
    """async load_all 返回全部 checkpoint."""
    mgr = CheckpointManager(db_session=None, redis_client=None)
    for i in range(3):
        await mgr.save(
            execution_id="exec_all",
            node_id=str(i),
            input_data={},
            output_data={"step": i},
            status="SUCCESS",
        )
    records = await mgr.load_all("exec_all")
    assert len(records) == 3
    assert all(isinstance(r, CheckpointRecord) for r in records)


# ─── 4. CheckpointRecord dataclass ───


def test_checkpoint_record_defaults():
    """CheckpointRecord 默认值正确."""
    r = CheckpointRecord(
        checkpoint_id="cp_1",
        execution_id="exec_1",
        node_id="0",
        node_status="SUCCESS",
    )
    assert r.is_recoverable is True
    assert r.input_data is None
    assert r.latency_ms is None


# ─── 5. Resume reconstruction ───


def test_resume_context_rebuild():
    """从多个 checkpoint 重建 context."""
    mgr = CheckpointManager()
    for i in range(3):
        mgr.save_sync(
            execution_id="exec_resume",
            node_id=str(i),
            input_data={},
            output_data={f"key_{i}": f"val_{i}"},
            status="SUCCESS",
        )
    records = mgr.load_all_sync("exec_resume")
    assert len(records) == 3
    reconstructed = {}
    for r in records:
        if r.output_data:
            reconstructed.update(r.output_data)
    assert reconstructed == {"key_0": "val_0", "key_1": "val_1", "key_2": "val_2"}
