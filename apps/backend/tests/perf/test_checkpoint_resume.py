"""P7-4: 性能测试 — Pipeline Checkpoint 恢复

目标:
- Checkpoint 保存延迟 < 100ms
- 断点续跑恢复时间 < 500ms
"""

import time
import pytest

from src.core.checkpoint import CheckpointManager
from src.services.workflow_engine import (
    resume_execution,
    WorkflowStatus,
    WorkflowExecution,
    _execution_db,
    set_checkpoint_manager,
)


@pytest.mark.perf
class TestCheckpointPerf:
    """Checkpoint 性能测试。"""

    def test_checkpoint_save_latency(self):
        """Checkpoint 保存延迟 < 100ms。"""
        manager = CheckpointManager(checkpoint_dir="test_checkpoints_perf")

        start = time.perf_counter()
        cp = manager.save_sync(
            execution_id="exec_perf_001",
            node_id="node_0",
            input_data={"prompt": "测试内容"},
            output_data={"content": "生成结果"},
            status="SUCCESS",
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert cp is not None
        assert elapsed_ms < 100, f"Checkpoint 保存延迟 {elapsed_ms:.2f}ms 超过 100ms 阈值"

    def test_checkpoint_resume_latency(self):
        """断点续跑恢复时间 < 500ms。"""
        manager = CheckpointManager(checkpoint_dir="test_checkpoints_perf")

        # 预先生成一些 checkpoint
        for i in range(5):
            manager.save_sync(
                execution_id="exec_resume_001",
                node_id=f"node_{i}",
                input_data={"step": i},
                output_data={"result": i},
                status="SUCCESS",
            )

        # 创建执行并暂停
        execution = WorkflowExecution(
            id="exec_resume_001",
            task_id="task_test",
            template_id="tmpl_test",
            template_version=1,
            status=WorkflowStatus.PAUSED,
            current_node_index=0,
            context={},
        )
        _execution_db["exec_resume_001"] = execution

        start = time.perf_counter()
        set_checkpoint_manager(manager)
        resumed = resume_execution("exec_resume_001")
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert resumed is not None
        assert resumed.status == WorkflowStatus.RUNNING
        assert elapsed_ms < 500, f"断点续跑恢复时间 {elapsed_ms:.2f}ms 超过 500ms 阈值"
