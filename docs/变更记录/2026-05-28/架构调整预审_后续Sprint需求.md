# 架构调整预审 — 后续 Sprint 需求

> **日期**: 2026-05-28  
> **预审范围**: W15 工作流注入平台规则 + W16 ImageForge/代码分割 + W19-W20 AccountPool 状态机  
> **执行人**: 专家团队  
> **状态**: ⚠️ 发现多项架构调整红线触发，需用户严格审核

---

## 一、需求概述

用户要求继续推进以下三个批次的需求：

| 批次 | 需求 | 原计划排期 |
|------|------|-----------|
| W15 | 工作流注入平台规则 | Phase 1.5 |
| W16 | ImageForge 封面裁剪 + 代码分割优化 | Phase 2 |
| W19-W20 | AccountPool 状态机 + 自动熔断 + 每日配额 | Phase 2 |

---

## 二、六章强制检查 — 技术架构对齐

### 2.1 架构调整红线检查

根据 `docs/需求对齐约束_通用提示词.md` §2.2 架构调整红线：

| 需求 | 是否触发红线 | 触发项 | 影响评估 |
|------|-------------|--------|----------|
| **W15 工作流注入平台规则** | ✅ **是** | **修改全局状态设计** + **修改 Function 层职责边界** | WorkflowEngine 的 `start_execution` 需注入平台规则到 execution context；content-forge 的 `_build_system_prompt` 需读取 context 中的规则。这涉及 WorkflowNode 的 input_context / output_context 数据结构变更 |
| **W16 ImageForge 封面裁剪** | ✅ **是** | **新增 Service 文件** + **引入新的外部依赖** | 需新增 `image_forge_service.py` 或扩展现有 `image_forge.py`；图片裁剪可能引入 `Pillow` 或 `sharp` 等图像处理库 |
| **W16 代码分割优化** | ⚠️ **需评估** | **修改前端路由结构** | 需修改 `App.tsx` 路由配置，将大页面改为 `React.lazy()` 动态导入；涉及路由级别的拆分策略 |
| **W19-W20 AccountPool 状态机** | ✅ **是** | **新增 Service 文件** + **新增 ORM 模型/字段** + **修改 Celery 任务签名** | 需新增 `account_state_machine.py` Service；`AccountPoolEntry` 需扩展状态字段（warming/restricted）；Celery Beat 需新增 `account-health-daily` 任务 |
| **W19-W20 自动熔断** | ✅ **是** | **修改 Celery 任务签名** + **新增 Service 文件** | 需新增 `circuit_breaker.py` 或扩展 `account_health.py`；Celery 定时任务触发状态转换 |
| **W19-W20 每日配额** | ✅ **是** | **修改全局状态设计** + **修改 Function 层职责边界** | Publisher 层需在 `create_publish_task` 前拦截配额超限的账号；涉及 Publisher 与 AccountPool 的跨层调用 |

### 2.2 按红线暂停声明

> **⚠️ 发现 6 项架构调整红线触发：**
>
> 1. **W15 工作流注入平台规则**：触发"修改全局状态设计"红线
> 2. **W16 ImageForge 封面裁剪**：触发"新增 Service 文件" + "引入新的外部依赖"红线
> 3. **W16 代码分割优化**：可能触发"修改前端路由结构"红线
> 4. **W19-W20 AccountPool 状态机**：触发"新增 Service 文件" + "新增 ORM 模型/字段" + "修改 Celery 任务签名"红线
> 5. **W19-W20 自动熔断**：触发"修改 Celery 任务签名" + "新增 Service 文件"红线
> 6. **W19-W20 每日配额**：触发"修改全局状态设计" + "修改 Function 层职责边界"红线
>
> **暂停实施，等待用户严格审核。**

---

## 三、详细影响分析

### W15：工作流注入平台规则

**当前状态**：
- `workflow_engine.py` 的 `start_execution()` 创建 `WorkflowExecution` 时，`context={}` 为空字典
- `content_generator.py` 的 `_build_system_prompt()` 使用硬编码 `platform_rules` 字典
- `platform_rule_function.py` 已建立 ORM 持久化规则基座，但工作流未接入

**需要修改的文件**：
- `apps/backend/src/services/workflow_engine.py` — `start_execution()` 注入平台规则
- `apps/backend/src/services/content_generator.py` — 从 execution context 读取规则
- `apps/backend/src/services/content_forge_service.py` — 透传规则到 LLM prompt
- `apps/backend/src/api/workflow_engine.py` — 可能需新增执行参数

**风险**：
- WorkflowExecution.context 结构变更影响所有现有执行记录
- 规则缺失时（ORM 未初始化）需有降级策略
- content-forge 的 prompt 模板需支持动态规则插槽

### W16：ImageForge 封面裁剪 + 代码分割

**ImageForge 封面裁剪**：
- 当前 `CoverPickerModal` 仅支持选择图片，不处理裁剪
- 需新增：接收 `url + ratio`，生成裁剪后的图片
- 可能引入依赖：`Pillow` (Python) 或 `sharp` (Node.js)

**代码分割优化**：
- 当前主 JS 包 1,183KB（含 TipTap）
- 需将 `AgentOrchestraPage`、`DataAnalystPage`、`ReviewPublishDetailPage` 等大页面改为 `React.lazy()`
- 需修改 `App.tsx` 路由配置

### W19-W20：AccountPool 状态机 + 自动熔断 + 每日配额

**状态机**：
- 当前 `status` 仅 `active/paused/suspended`
- 需扩展为：`warming → active → restricted → blocked → expired`
- 需新增状态转换逻辑（如 warming 7 天后自动转 active）

**自动熔断**：
- 健康评分 < 阈值（如 60 分）→ 自动 `status = 'paused'`
- 需 Celery 每日定时检查任务

**每日配额**：
- `posts_today` 达到上限时拒绝发布
- Publisher 层需在 `create_publish_task` 前拦截

---

## 四、待用户决策事项

### 决策 1：是否授权 W15 工作流注入平台规则实施？

- [ ] **授权实施**：接受 WorkflowExecution.context 结构变更风险
- [ ] **推迟到 W15  Sprint 规划会**：需先补充详细设计文档

### 决策 2：是否授权 W16 ImageForge 封面裁剪？

- [ ] **授权实施**：接受引入 Pillow/sharp 新依赖
- [ ] **简化方案**：仅前端 CSS 裁剪预览，后端不实际处理图片（当前已实现）

### 决策 3：是否授权 W16 代码分割优化？

- [ ] **授权实施**：接受修改 App.tsx 路由结构
- [ ] **暂缓**：当前 1.1MB JS 包在可接受范围，优先功能开发

### 决策 4：是否授权 W19-W20 AccountPool 增强？

- [ ] **授权实施**：接受新增状态机 Service + Celery 任务 + ORM 字段变更
- [ ] **分拆实施**：先只做"每日配额"（影响最小），状态机和熔断延后

### 决策 5：实施顺序优先级

用户原排期：W15 → W16 → W19-W20

是否调整？
- [ ] 保持原顺序
- [ ] 调整为：W16 代码分割（低风险）→ W15 → W19-W20

---

> **预审结论**：
> 
> 根据 `需求对齐约束_通用提示词.md` §2.2 架构调整红线，上述 3 个批次共 **6 项红线触发**。按照规范，**必须暂停实施，等待用户明确批准后再继续**。
>
> 建议用户先决策上述 5 项问题，确认授权范围和优先级后，专家团队再按 Red-Green-Blue 纪律分批次实施。
