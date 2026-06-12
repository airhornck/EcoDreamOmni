# 后端需求补充文档 — 全局 Copilot-Driven 改造

> **关联前端任务**: Phase 2-P3 审核发布 + 全局 10 页面 Copilot-Driven 改造  
> **关联设计文档**: `Copilot-Workspace-交互模式规范_v2.0.md`  
> **提出日期**: 2026-06-04  
> **优先级**: 🔴 P0（阻塞前端 Step 3 全面开发）  
> **影响范围**: AI 服务层、全部业务服务、Copilot 网关、WebSocket 推送、数据库  

---

## 一、需求背景

前端正在进行 v4.0 全面重构，核心交互范式从「工作区按钮操作」彻底升级为 **「Copilot-Driven（副驾驶驱动）」**。此变更要求后端提供全局统一的 API 能力和数据支持，覆盖全部 10 个页面。

**核心变更**:
1. 所有业务操作（保存、提交、审核、生成、发布等）从工作区按钮迁移至 Copilot Action Cards
2. 后端需要支持 Copilot 上下文感知、Action Card 动态组装、AI 建议生成
3. 所有 API 响应需要可选携带 `copilot_followup` 字段，驱动下一步 Copilot 交互
4. 需要统一的 Copilot 网关和 WebSocket 通道

---

## 二、通用基础设施（所有页面共享）

### 2.1 Copilot 上下文网关

```
POST /api/ai/copilot/context
```

**请求体**:
```json
{
  "session_id": "sess_usr123_abc",
  "page": "/review",
  "page_title": "审核发布",
  "selected_items": ["task_001"],
  "selected_content": {
    "type": "review_task",
    "id": "task_001",
    "title": "猫咪驱虫避坑指南...",
    "status": "human_wait"
  },
  "workspace_state": {
    "active_tab": "pending",
    "filter_platform": "xhs",
    "editor_dirty": true
  },
  "timestamp": "2026-06-04T15:30:00Z"
}
```

**响应**:
```json
{
  "code": "OK",
  "message": "上下文已更新",
  "data": {
    "context_id": "ctx_abc456",
    "suggested_cards": [
      {
        "card_type": "decision",
        "priority": 1,
        "target_page": "/review",
        "reasoning": "human_wait 状态，合规分 96 > 85"
      }
    ],
    "ai_insights": [
      "3 条待审中，1 条合规分低于 80 分建议优先处理"
    ]
  }
}
```

### 2.2 Action Cards 模板引擎

```
GET /api/ai/copilot/action-cards?page={page}&context_id={ctx_id}
```

**响应**:
```json
{
  "code": "OK",
  "message": "查询成功",
  "data": {
    "cards": [
      {
        "id": "review-decision-task_001",
        "type": "decision",
        "title": "审核决策",
        "description": "合规分 96 分，质量分 88 分，L1-L4 全部通过。建议直接通过。",
        "priority": 1,
        "inputs": [],
        "actions": [
          {
            "id": "approve",
            "label": "✅ 审核通过",
            "variant": "primary",
            "api": {
              "method": "POST",
              "endpoint": "/api/human-in-the-loop/tasks/task_001/approve",
              "payload": {}
            }
          }
        ]
      }
    ]
  }
}
```

### 2.3 通用 Action 执行网关

```
POST /api/ai/copilot/execute
```

**请求体**:
```json
{
  "context_id": "ctx_abc456",
  "card_id": "review-decision-task_001",
  "action_id": "approve",
  "inputs": {},
  "payload": {
    "copilot_suggested": true,
    "reason": ""
  }
}
```

**响应**:
```json
{
  "code": "OK",
  "message": "审核已通过",
  "data": {
    "status": "approved_waiting_publish",
    "task_id": "task_001"
  },
  "copilot_followup": {
    "message": "审核已通过！要现在发布还是定时发布？",
    "suggested_cards": [
      {
        "type": "decision",
        "title": "发布确认",
        "actions": [
          { "id": "publish_now", "label": "立即发布", "api": { "method": "POST", "endpoint": "/api/review-publish-center/conclusions/task_001/confirm-publish", "payload": { "publish_mode": "immediate" } } },
          { "id": "schedule", "label": "定时发布", "api": { "method": "POST", "endpoint": "/api/review-publish-center/conclusions/task_001/confirm-publish", "payload": { "publish_mode": "scheduled" } } }
        ]
      }
    ]
  }
}
```

### 2.4 WebSocket 统一通道

```
WS /ws/copilot?session_id={sess_id}
```

**消息格式**:
```typescript
interface WSMessage {
  direction: 'client_to_server' | 'server_to_client'
  event: string
  payload: Record<string, unknown>
  timestamp: string
  trace_id: string
}
```

**核心事件**:

| 事件名 | 方向 | 说明 |
|--------|------|------|
| `context.update` | C→S | 客户端上报上下文变更 |
| `card.push` | S→C | 服务端主动推送 Action Card |
| `card.execute` | C→S | 客户端请求执行 Card Action |
| `card.result` | S→C | 服务端返回执行结果 |
| `card.progress` | S→C | 长时间任务的进度推送 |
| `insight.push` | S→C | AI 洞察主动推送 |
| `workspace.sync` | S→C | 工作区数据同步（多端） |

---

## 三、各页面后端需求详单

### 3.1 审核发布 /review

**已有文档**: `后端需求补充_审核发布_Copilot-Driven_2026-06-04.md`（v1.0）

**本次扩展**:
- 审核列表接口新增 `copilot_summary` 字段
- 审核详情接口新增 `copilot_context` 字段
- 封面生成接口 `POST /api/ai/generate-cover`
- 审核决策接口新增 `copilot_suggested`/`copilot_card_id` 字段

**实施状态**: 🔴 已就绪，等待排期

---

### 3.2 工作台 /

**API 扩展**:

```
GET /api/dashboard/overview
```

**响应新增**:
```json
{
  "copilot_summary": {
    "total_pending_tasks": 5,
    "recommended_priority": ["task_003", "task_001"],
    "ai_insight": "今日最佳发布时间是 18:00，建议提前准备 2 条内容",
    "suggested_actions": [
      { "type": "create_task", "label": "新建任务", "reason": "账号矩阵今日发布进度仅 60%" },
      { "type": "batch_review", "label": "批量审核", "reason": "有 3 条内容待审" }
    ]
  }
}
```

```
GET /api/contents?limit=10
```

**响应新增**:
```json
{
  "items": [
    {
      "id": "content_001",
      "title": "...",
      "copilot_recommended_action": "publish",
      "copilot_reasoning": "合规分 96 分，已过审 2 小时，建议立即发布"
    }
  ]
}
```

**新增 API**:
```
POST /api/ai/copilot/create-task
```
- 通过 Copilot 快速创建任务（输入自然语言，AI 解析为任务配置）

---

### 3.3 内容生产 /generate

**API 扩展**:

```
GET /api/task-hub/tasks
```

**响应新增**:
```json
{
  "copilot_summary": {
    "kanban_stats": { "draft": 5, "reviewing": 3, "approved": 12 },
    "recommended_focus": "draft",
    "ai_insight": "草稿区堆积 5 个任务，建议优先处理过期任务"
  }
}
```

```
GET /api/task-hub/tasks/:id
```

**响应新增**:
```json
{
  "copilot_context": {
    "editor_suggestions": [
      { "type": "title_optimization", "confidence": 0.89, "reason": "加入数字可提升 CTR 15%" },
      { "type": "tag_expansion", "confidence": 0.76, "reason": "可补充 2 个高热度标签" }
    ],
    "save_status": "unsaved_changes",
    "recommended_next": "save_draft"
  }
}
```

**新增 API**:
```
POST /api/ai/copilot/regenerate-content
```
- Copilot 驱动重新生成（支持风格/长度/语气选择）

```
POST /api/ai/copilot/save-and-submit
```
- 保存草稿 + 提交审核（原子操作，避免两步走）

---

### 3.4 数据报表 /analytics

**API 扩展**:

```
GET /api/analytics/metrics
```

**响应新增**:
```json
{
  "copilot_insights": {
    "anomalies": [
      { "metric": "engagement", "change": -0.15, "severity": "warning", "reason": "近 3 天发布频率下降" }
    ],
    "recommendations": [
      { "action": "increase_publish_frequency", "label": "增加发布频率", "expected_impact": "+12% 互动量" }
    ]
  }
}
```

**新增 API**:
```
POST /api/ai/copilot/generate-report
```
- AI 战报生成（自然语言总结 + 可视化图表配置）

```
POST /api/ai/copilot/analyze-anomaly
```
- 异常诊断（传入指标 ID，返回根因分析）

---

### 3.5 账号矩阵 /accounts

**API 扩展**:

```
GET /api/accounts
```

**响应新增**:
```json
{
  "copilot_summary": {
    "low_health_accounts": ["acc_001", "acc_003"],
    "recommended_actions": [
      { "account_id": "acc_001", "action": "publish_now", "reason": "3 天未发布，健康度下降至 65" }
    ]
  }
}
```

**新增 API**:
```
POST /api/ai/copilot/generate-publish-schedule
```
- 生成最优发布时间表（基于账号历史数据 + 平台流量高峰）

```
POST /api/ai/copilot/adjust-persona
```
- 人设调整建议（基于账号表现数据）

---

### 3.6 Agent 舰队 /agents

**API 扩展**:

```
GET /api/agents/status
```

**响应新增**:
```json
{
  "copilot_insights": {
    "degraded_agents": ["TrendScout"],
    "recommendations": [
      { "agent": "TrendScout", "action": "restart", "reason": "失败率上升至 8%，建议重启" },
      { "agent": "ContentForge", "action": "scale_up", "reason": "队列堆积 12 个任务，建议扩容" }
    ]
  }
}
```

**新增 API**:
```
POST /api/ai/copilot/diagnose-agent
```
- Agent 故障诊断（传入 Agent ID，返回根因 + 修复建议）

---

### 3.7 模型中心 /models

**API 扩展**:

```
GET /api/models
```

**响应新增**:
```json
{
  "copilot_insights": {
    "cost_alert": { "current": 4200, "budget": 5000, "percentage": 0.84 },
    "recommendations": [
      { "action": "switch_to_cheaper_model", "label": "切换至低成本模型", "saving": "¥800/月" }
    ]
  }
}
```

---

### 3.8 素材库 /assets

**API 扩展**:

```
GET /api/assets
```

**响应新增**:
```json
{
  "copilot_summary": {
    "untagged_count": 45,
    "recommended_action": "batch_tag",
    "ai_suggestion": "45 张图片未打标签，建议批量 AI 打标签以提升搜索效率"
  }
}
```

**新增 API**:
```
POST /api/ai/copilot/batch-tag
```
- 批量 AI 打标签（传入 asset_ids，返回标签建议）

---

### 3.9 实验室 /lab

**API 扩展**:

```
POST /api/lab/parse
```

**响应新增**:
```json
{
  "copilot_followup": {
    "message": "已解析出 5 个关键结构点，生成 ContentTemplate？",
    "suggested_cards": [
      { "type": "generation", "title": "生成模板", "api": { "method": "POST", "endpoint": "/api/lab/templates" } }
    ]
  }
}
```

---

### 3.10 设置 /settings

**API 扩展**:

```
GET /api/settings
```

**响应新增**:
```json
{
  "copilot_insights": {
    "unsaved_changes": ["notification_email", "permission_role"],
    "recommended_action": "save_now"
  }
}
```

---

## 四、数据模型变更（全局）

### 4.1 新增表：`copilot_context_sessions`

```sql
CREATE TABLE copilot_context_sessions (
  id VARCHAR(32) PRIMARY KEY,
  user_id VARCHAR(32) NOT NULL,
  session_id VARCHAR(64) NOT NULL UNIQUE,
  page VARCHAR(64) NOT NULL,
  selected_items JSONB DEFAULT '[]',
  selected_content JSONB,
  workspace_state JSONB,
  suggested_cards JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  expires_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() + INTERVAL '30 minutes'
);

CREATE INDEX idx_copilot_sessions_user ON copilot_context_sessions(user_id, updated_at);
CREATE INDEX idx_copilot_sessions_expires ON copilot_context_sessions(expires_at);
```

### 4.2 新增表：`ai_cover_generation_jobs`

（详见 v1.0 文档，此处省略）

### 4.3 新增表：`copilot_action_logs`

```sql
CREATE TABLE copilot_action_logs (
  id VARCHAR(32) PRIMARY KEY,
  user_id VARCHAR(32) NOT NULL,
  session_id VARCHAR(64) NOT NULL,
  context_id VARCHAR(32),
  card_id VARCHAR(64),
  action_id VARCHAR(64),
  page VARCHAR(64),
  status VARCHAR(20),  -- success / failed / cancelled
  request_payload JSONB,
  response_payload JSONB,
  execution_time_ms INTEGER,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_copilot_logs_user ON copilot_action_logs(user_id, created_at);
CREATE INDEX idx_copilot_logs_session ON copilot_action_logs(session_id);
```

### 4.4 各业务表扩展字段

| 表名 | 新增字段 | 说明 |
|------|---------|------|
| `review_conclusions` | `copilot_recommended_action`, `copilot_confidence`, `copilot_reasoning` | AI 审核建议 |
| `tasks` | `copilot_suggested_agent`, `copilot_priority_score` | AI 任务建议 |
| `accounts` | `copilot_health_prediction`, `copilot_publish_recommendation` | AI 账号建议 |
| `agents` | `copilot_diagnosis_result`, `copilot_scale_recommendation` | AI Agent 建议 |
| `contents` | `copilot_engagement_prediction`, `copilot_viral_probability` | AI 内容预测 |

---

## 五、错误码扩展（全局）

| 错误码 | HTTP 状态 | 中文说明 | 触发场景 | 前端处理 |
|--------|----------|---------|---------|---------|
| `COPILOT_CONTEXT_EXPIRED` | 400 | Copilot 上下文过期 | 超过 30 分钟未更新 | 自动刷新后重试 |
| `INVALID_COPILOT_CARD_ACTION` | 400 | 无效的 Copilot 卡片操作 | 卡片已过期或已处理 | 刷新页面 |
| `COPILOT_ACTION_FAILED` | 500 | Copilot 操作执行失败 | 执行网关异常 | 展示错误 + [重试] |
| `COVER_GENERATION_LIMIT_EXCEEDED` | 429 | 封面生成次数超限 | 单用户 3 次/分钟 | 展示冷却时间 |
| `AI_INSIGHT_UNAVAILABLE` | 503 | AI 洞察暂不可用 | LLM 服务降级 | 降级为静态提示 |
| `REVIEW_DECISION_ALREADY_MADE` | 409 | 审核决策已存在 | 并发操作 | 刷新获取最新状态 |
| `TASK_ALREADY_SUBMITTED` | 409 | 任务已提交 | 重复提交 | 刷新状态 |

---

## 六、性能与容量要求

| 指标 | 要求 | 说明 |
|------|------|------|
| Copilot 上下文接口 | ≤ 100ms | 轻量级，高频调用 |
| Action Cards 获取 | ≤ 150ms | 含业务逻辑判断 |
| 通用 Action 执行网关 | ≤ 200ms | 透传到底层 API |
| WebSocket 推送延迟 | ≤ 100ms | 服务端→客户端 |
| AI 封面生成完成 | ≤ 15s（P95） | 异步任务 |
| AI 战报生成 | ≤ 5s（P95） | 流式输出 |
| 上下文会话存储 | 30min TTL | 过期自动清理 |
| Action Log 保留 | 90 天 | 审计需求 |

---

## 七、安全与权限

1. **Copilot 上下文隔离**: 用户只能访问自己的 `session_id` 对应的数据
2. **Action 执行校验**: 执行网关必须校验用户是否有权限调用底层 API
3. **Card 防篡改**: Action Card 中的 `api.endpoint` 必须在服务端白名单中
4. **AI 生成内容过滤**: 封面生成、内容生成的 Prompt 需经过内容安全过滤
5. **审计日志**: 所有 Copilot 驱动的操作必须记录 `copilot_action_logs`

---

## 八、实施计划

### Sprint 1: 基础设施（Week 5，与审核发布并行）
- `copilot_context_sessions` 表 + 上下文接口
- `copilot_action_logs` 表
- WebSocket 统一通道 `/ws/copilot`
- 通用 Action 执行网关 `/api/ai/copilot/execute`

### Sprint 2: 审核发布专属（Week 5-6）
- 封面生成 API + 图片生成 Agent
- 审核决策接口增强
- 审核详情/列表接口增强

### Sprint 3: 全局扩展（Week 6-7）
- 工作台、内容生产接口增强
- 数据报表、账号矩阵、Agent、模型、素材库接口增强
- 各页面 `copilot_summary`/`copilot_insights` 字段

### Sprint 4: 实验室 + 设置 + 优化（Week 7-8）
- 实验室 Copilot 驱动
- 设置页面 Copilot 驱动
- 性能优化、限流、监控

---

## 九、前后端约定

### 9.1 开发顺序

```
1. 后端先完成 Sprint 1 基础设施（通用网关 + WebSocket）
2. 前端基于 mock 继续各页面开发（不阻塞）
3. 后端完成审核发布专属 API 后，前端联调审核发布
4. 后端逐页面交付 API，前端逐页面联调
5. 全局 E2E 测试
```

### 9.2 Mock 策略

在接口就绪前，前端使用统一 Mock 服务：

```typescript
// lib/mockCopilot.ts
export const mockCopilotAPI = {
  async executeAction(actionId: string, payload: unknown) {
    await delay(800)
    return {
      success: true,
      data: generateMockResult(actionId, payload),
      copilot_followup: generateMockFollowup(actionId)
    }
  }
}
```

---

## 十、附录

### 10.1 参考文档

- `docs/前端设计/Copilot-Workspace-交互模式规范_v2.0.md`
- `docs/后端需求/后端需求补充_审核发布_Copilot-Driven_2026-06-04.md`（v1.0，已合并至本文档）
- `docs/契约与数据/01-API接口契约.md`
- `EcoDream_Omni_PRD_v2_对齐核心方案.md`

### 10.2 变更日志

| 版本 | 日期 | 变更内容 |
|------|------|---------|
| v1.0 | 2026-06-04 | 仅覆盖审核发布页面 |
| v2.0 | 2026-06-04 | 扩展至全局 10 页面，新增通用 Copilot 网关 |

---

*文档版本: v2.0*  
*制定日期: 2026-06-04*  
*状态: 待后端负责人评审并排期*  
*评审通过后，按 Sprint 计划分阶段实施*
