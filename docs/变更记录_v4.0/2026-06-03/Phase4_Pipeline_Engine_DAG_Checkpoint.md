# Phase 4 变更记录 — Pipeline Engine DAG 增强 + Checkpoint + keyword_inject

**日期**: 2026-06-03
**Phase**: Phase 4（Pipeline 层改造）
**任务**: P4-1 ~ P4-4
**状态**: 已完成

---

## 变更摘要

### P4-1: Pipeline Engine DAG 增强
- `src/services/workflow_engine.py`:
  - 新增 `NodeType.SKILL`
  - `WorkflowNode` 新增 `skill_id` / `depends_on` 字段
  - `WorkflowExecution` 新增 `completed_nodes` / `failed_nodes` / `resumed_count`
  - 新增 `CompiledDAG` dataclass + `compile_dag()`（Kahn 拓扑排序 + 环检测）
  - 新增 `_find_next_executable_node()` DAG 调度函数
  - `execute_next_node()` 内部改用 DAG 拓扑序计算下一个节点，100% 向后兼容
  - `to_react_flow()` 改为 DAG-aware（按层级分配 x 坐标）
  - `create_template()` 支持自定义 `node_index` / `skill_id` / `depends_on`

### P4-2: keyword_inject 节点集成
- `src/services/workflow_engine.py`:
  - 新增 `_run_skill_node()` 路由函数，支持 `keyword_inject` / `brand_knowledge_inject`
  - `execute_next_node()` 自动执行 `SKILL` 类型节点（无需外部传入输出）
- 8 个预设模板全部更新为 v2（插入 keyword_inject / brand_knowledge_inject / vetdrug_validate / image-forge）

### P4-3: Checkpoint 机制
- **新建** `src/core/checkpoint.py`:
  - `CheckpointRecord` dataclass
  - `CheckpointManager`：同步/异步双接口
  - 分层存储：本地文件（大 Payload >1MB）+ 内存缓存 + PostgreSQL + Redis（TTL 7 天）
  - Redis 不可用时自动 fallback 内存，不抛异常
- **新建** `src/models/checkpoint_orm.py`：`CheckpointORM` SQLAlchemy 模型
- **新建** Alembic 迁移 `120d8c25393c_add_checkpoint_table_p4.py`
- `resume_execution()` 从 Checkpoint 重建 `completed_nodes` / `context` / `current_node_index`
- `pause_execution()` / `resume_execution()` / `cancel_execution()` 记录审计日志到 `_audit_log`

### P4-4: Pipeline 模板更新
- 8 个预设模板全部更新：
  - `content_creation_standard` (8→12 节点)
  - `content_creation_light` (5→7 节点)
  - `content_creation_note_image` (8→12 节点)
  - `content_creation_video_clone` (8→11 节点)
  - `content_creation_video_original` (8→11 节点)
  - `content_creation_text_article` (8→11 节点)
  - `trend_scout_only` / `data_analysis_only` 保持不变

### API 层更新
- `src/api/workflow_engine.py`:
  - `WorkflowNodeSchema` 新增 `skill_id` / `depends_on`
  - `_to_template_response()` 序列化新字段

---

## 测试覆盖

| 测试文件 | 测试数 | 状态 |
|----------|--------|------|
| `tests/test_workflow_engine.py` | 18 | ✅ 全部通过 |
| `tests/test_workflow_dag.py` | 12 | ✅ 全部通过（新增） |
| `tests/test_checkpoint.py` | 10 | ✅ 全部通过（新增） |
| `tests/test_workflow_real_nodes.py` | 4 | ✅ 全部通过 |

**总计**: 新增测试 22 个，现有测试 18 个回归通过。

---

## 质量门禁

| 门禁项 | 结果 |
|--------|------|
| pytest 新代码测试通过 | ✅ 22/22 |
| pytest 现有代码回归 | ✅ 18/18 workflow 测试通过 |
| ruff 0 errors（新代码） | ✅ 通过 |
| mypy 0 errors（新代码） | ✅ 通过（现有技术债务 5 处无关） |
| Alembic upgrade | ✅ `120d8c25393c` 成功 |
| Alembic downgrade | ✅ 成功回退到 `e1f2a3b4c5d6` |

---

## 关联文档更新

- `docs/v4.0_开发Checklist.md` — Phase 4 逐项打勾
- `docs/契约与数据/01-API接口契约.md` — 新增 §3.5a 节点类型枚举（SKILL）
- `docs/契约与数据/02-数据库ER图.md` — `checkpoints.started_at` 修正为 nullable
- 本文档 — 新增

---

## 已知限制

- `test_workflow_visual.py` 中 3 个测试因 `get_auth_token` 调用 `we._clear_stores()` 导致预设模板被清除而返回 404 — 现有测试环境问题，与 Phase 4 无关
- `test_skill_hub.py` / `test_agent_orchestra.py` 中 `SkillCreate` 缺少 `modality_support` 字段 — Phase 1/3 遗留问题
- S3/MinIO 大 Payload 存储当前使用本地文件 fallback，正式环境需替换为对象存储
