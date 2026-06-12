# 后端需求补充文档 — 内容生产 `/generate`（Mode C: Hybrid）

> **关联前端任务**: Phase 2-P2 内容生产回炉改造  
> **关联设计文档**: `Copilot-Workspace-交互模式规范_v2.0.md` §3.3  
> **关联契约文档**: `01-API接口契约.md` §九（Agent-任务接口契约）  
> **提出日期**: 2026-06-05  
> **优先级**: 🔴 P0（阻塞前端内容生产 Step 3 全面开发）  
> **页面 Mode**: C（Hybrid — 工作区保留编辑控件，所有提交类操作走 Copilot Action Cards）

---

## 一、页面范围与职责边界

### 1.1 涉及子页面

| 子页面 | 路由 | 工作区职责 | Copilot 职责 |
|--------|------|-----------|-------------|
| **看板** | `/generate` | 任务卡片浏览、筛选、拖拽（编辑辅助） | 新建内容、Agent 推荐、批量操作 |
| **创建向导** | `/generate/create` | 4 步配置展示（纯预览，无提交） | 确认创建、Agent 推荐、配置校验 |
| **编辑器** | `/generate/editor/:taskId` | 标题/正文编辑、图片上传、平台预览 | 保存草稿、提交审核、重新生成、标题优化 |

### 1.2 Mode C 红线（工作区禁止元素）

- ❌ 看板页：无「+ 新建内容」按钮
- ❌ 看板卡片：无「发布」「编辑」「删除」操作按钮（点击仅选中态）
- ❌ 创建向导：无「下一步」「确认创建」按钮（Stepper 纯导航展示）
- ❌ 编辑器：无「保存」「发布」「重新生成」按钮（保留格式化工具栏）
- ✅ 允许：编辑器格式化工具栏、Tab 切换、卡片点击选中、拖拽调整

---

## 二、API 清单

### 2.1 已有 API（无需新增，需扩展字段）

| # | 方法 | 路径 | 已有状态 | 本次扩展 |
|---|------|------|---------|---------|
| 1 | `GET` | `/api/task-hub/tasks` | ✅ 已有 | 响应新增 `copilot_summary` |
| 2 | `GET` | `/api/task-hub/tasks/{id}` | ✅ 已有 | 响应新增 `copilot_context` |
| 3 | `POST` | `/api/task-hub/tasks` | ✅ 已有（Agent-First） | 响应新增 `copilot_followup` |
| 4 | `GET` | `/api/agents` | ✅ 已有 | 无需扩展 |
| 5 | `GET` | `/api/agents/recommend` | ✅ 已有 | 无需扩展 |
| 6 | `GET` | `/api/account-pool` | ✅ 已有 | 无需扩展 |
| 7 | `GET` | `/api/personas` | ✅ 已有 | 无需扩展 |
| 8 | `GET` | `/api/platform-schemas` | ✅ 已有 | 无需扩展 |

### 2.2 新增 API（内容生产专属）

| # | 方法 | 路径 | 说明 | 优先级 |
|---|------|------|------|--------|
| 9 | `POST` | `/api/ai/copilot/regenerate-content` | Copilot 驱动重新生成（支持风格/长度/语气选择） | 🔴 P0 |
| 10 | `POST` | `/api/ai/copilot/save-and-submit` | 保存草稿 + 提交审核（原子操作） | 🔴 P0 |

### 2.3 通用 Copilot 网关（所有页面共享，Sprint 1 实现）

| # | 方法 | 路径 | 说明 | 优先级 |
|---|------|------|------|--------|
| 11 | `POST` | `/api/ai/copilot/context` | 上下文上报 | 🔴 P0 |
| 12 | `GET` | `/api/ai/copilot/action-cards` | 获取推荐 Action Cards | 🔴 P0 |
| 13 | `POST` | `/api/ai/copilot/execute` | 通用 Action 执行网关 | 🔴 P0 |
| 14 | `WS` | `/ws/copilot` | Copilot 实时通道 | 🟡 P1 |

---

## 三、API Schema 详单

### 3.1 GET /api/task-hub/tasks — 扩展响应

**新增响应字段**:

```json
{
  "code": "OK",
  "message": "查询成功",
  "data": {
    "items": [
      {
        "task_id": "task_001",
        "name": "猫咪驱虫避坑指南",
        "status": "draft",
        "platform": "xhs",
        "content_format": "note_image",
        "agent_id": "content_forge_xhs_image",
        "agent_name": "小红书图文生成 Agent",
        "account_name": "小艾养猫记",
        "persona_name": "省钱狗爸",
        "compliance_score": 96,
        "created_at": "2026-06-05T10:00:00Z",
        "updated_at": "2026-06-05T14:00:00Z"
      }
    ],
    "copilot_summary": {
      "kanban_stats": {
        "draft": 5,
        "reviewing": 3,
        "approved": 12,
        "published": 47
      },
      "recommended_focus": "draft",
      "ai_insight": "草稿区堆积 5 个任务，建议优先处理过期任务",
      "suggested_actions": [
        {
          "type": "create_task",
          "label": "新建内容",
          "reason": "今日发布进度仅 60%，建议补充 2 条内容"
        },
        {
          "type": "batch_generate",
          "label": "批量生成",
          "reason": "有 3 个草稿任务已配置但未生成内容"
        }
      ]
    }
  },
  "trace_id": "req_abc123",
  "timestamp": "2026-06-05T14:30:00Z"
}
```

### 3.2 GET /api/task-hub/tasks/{id} — 扩展响应

**新增响应字段**:

```json
{
  "code": "OK",
  "message": "查询成功",
  "data": {
    "task_id": "task_001",
    "name": "猫咪驱虫避坑指南",
    "status": "draft",
    "platform": "xhs",
    "content_format": "note_image",
    "title": "猫咪驱虫避坑指南",
    "body": "作为一个省钱狗爸...",
    "hashtags": ["驱虫", "新手养猫"],
    "media_urls": ["https://cdn.example.com/img1.jpg"],
    "agent_id": "content_forge_xhs_image",
    "agent_name": "小红书图文生成 Agent",
    "compliance_score": 96,
    "quality_score": 88,
    "agent_trace": [
      {"agent_name": "TrendScout", "status": "success", "duration": 0.8, "timestamp": "2026-06-05T10:01:00Z"},
      {"agent_name": "ContentForge", "status": "success", "duration": 8.5, "timestamp": "2026-06-05T10:02:00Z"},
      {"agent_name": "Compliance", "status": "success", "duration": 2.1, "timestamp": "2026-06-05T10:03:00Z"}
    ],
    "predictions": {
      "likes_range": [25, 60],
      "comments_range": [5, 15]
    },
    "copilot_context": {
      "editor_suggestions": [
        {
          "type": "title_optimization",
          "confidence": 0.89,
          "reason": "加入数字可提升 CTR 15%",
          "suggested_title": "猫咪驱虫避坑指南，这3个误区90%的人都不知道"
        },
        {
          "type": "tag_expansion",
          "confidence": 0.76,
          "reason": "可补充 2 个高热度标签",
          "suggested_tags": ["养宠攻略", "科学养宠"]
        }
      ],
      "save_status": "unsaved_changes",
      "recommended_next": "save_draft",
      "generation_progress": null
    }
  },
  "trace_id": "req_abc123",
  "timestamp": "2026-06-05T14:30:00Z"
}
```

### 3.3 POST /api/task-hub/tasks — 创建任务（响应扩展）

**新增 `copilot_followup` 字段**:

```json
{
  "code": "CREATED",
  "message": "任务创建成功",
  "data": {
    "task_id": "task_002",
    "status": "draft",
    "agent_id": "content_forge_xhs_image",
    "agent_name": "小红书图文生成 Agent",
    "estimated_completion_at": "2026-06-05T14:45:00Z"
  },
  "copilot_followup": {
    "message": "任务已创建！推荐 Agent「小红书图文生成」成功率 94%。要现在生成内容吗？",
    "suggested_cards": [
      {
        "type": "action",
        "title": "立即生成内容",
        "description": "使用小红书图文生成 Agent 生成内容",
        "actions": [
          {
            "id": "generate_now",
            "label": "🚀 立即生成",
            "variant": "primary",
            "api": {
              "method": "POST",
              "endpoint": "/api/task-hub/tasks/task_002/generate",
              "payload": {}
            }
          },
          {
            "id": "configure_first",
            "label": "⚙️ 先配置",
            "variant": "secondary",
            "api": {
              "method": "GET",
              "endpoint": "/api/task-hub/tasks/task_002",
              "payload": {}
            }
          }
        ]
      }
    ]
  },
  "trace_id": "req_abc123",
  "timestamp": "2026-06-05T14:30:00Z"
}
```

### 3.4 POST /api/ai/copilot/regenerate-content — 重新生成（新增）

**请求体**:

```json
{
  "task_id": "task_001",
  "style_option": "casual",
  "length_option": "medium",
  "tone_option": "friendly",
  "prompt_variables": {
    "hook_angle": "省钱",
    "product_name": "大宠爱"
  },
  "copilot_suggested": true,
  "card_id": "regenerate-task_001"
}
```

**响应**:

```json
{
  "code": "ACCEPTED",
  "message": "重新生成任务已提交",
  "data": {
    "job_id": "job_reg_001",
    "task_id": "task_001",
    "status": "queued",
    "estimated_seconds": 15
  },
  "copilot_followup": {
    "message": "重新生成已提交，预计 15 秒完成。正在调用 ContentForge Agent...",
    "suggested_cards": [
      {
        "type": "info",
        "title": "生成进度",
        "description": "ContentForge Agent 正在重新生成内容",
        "actions": [
          {
            "id": "cancel_generation",
            "label": "取消生成",
            "variant": "ghost"
          }
        ]
      }
    ]
  },
  "trace_id": "req_abc123",
  "timestamp": "2026-06-05T14:30:00Z"
}
```

### 3.5 POST /api/ai/copilot/save-and-submit — 保存并提交审核（新增）

**请求体**:

```json
{
  "task_id": "task_001",
  "title": "猫咪驱虫避坑指南，这3个误区90%的人都不知道",
  "body": "作为一个省钱狗爸，我发现...",
  "hashtags": ["驱虫", "新手养猫", "养宠攻略"],
  "media_urls": ["https://cdn.example.com/img1.jpg"],
  "copilot_suggested": true,
  "card_id": "save-submit-task_001"
}
```

**响应**:

```json
{
  "code": "OK",
  "message": "保存成功，已提交审核",
  "data": {
    "task_id": "task_001",
    "status": "reviewing",
    "content_version": 3,
    "submitted_at": "2026-06-05T14:30:00Z"
  },
  "copilot_followup": {
    "message": "内容已保存并提交审核！合规分 96 分，预计 2 分钟内完成自动审核。",
    "suggested_cards": [
      {
        "type": "navigation",
        "title": "前往审核发布",
        "description": "查看审核进度",
        "actions": [
          {
            "id": "go_review",
            "label": "🛡️ 查看审核",
            "variant": "primary",
            "api": {
              "method": "GET",
              "endpoint": "/api/review-publish-center/conclusions/task_001",
              "payload": {}
            }
          },
          {
            "id": "create_next",
            "label": "➕ 创建新内容",
            "variant": "secondary"
          }
        ]
      }
    ]
  },
  "trace_id": "req_abc123",
  "timestamp": "2026-06-05T14:30:00Z"
}
```

---

## 四、数据模型

### 4.1 业务表扩展字段

**`tasks` 表新增字段**:

| 字段名 | 类型 | 说明 | 默认值 |
|--------|------|------|--------|
| `copilot_suggested_agent` | `VARCHAR(64)` | AI 推荐的 Agent ID | NULL |
| `copilot_priority_score` | `FLOAT` | AI 优先级评分 0~100 | NULL |
| `copilot_context_json` | `JSONB` | 编辑器上下文（建议、保存状态等） | `'{}'` |

**`content_drafts` 表新增字段**:

| 字段名 | 类型 | 说明 | 默认值 |
|--------|------|------|--------|
| `copilot_engagement_prediction` | `JSONB` | AI 互动量预测 | NULL |
| `copilot_viral_probability` | `FLOAT` | 爆款概率 0~1 | NULL |

### 4.2 新增任务：内容生成 Job 表（可选，用于追踪重新生成）

```sql
CREATE TABLE content_regeneration_jobs (
  id VARCHAR(32) PRIMARY KEY,
  task_id VARCHAR(32) NOT NULL REFERENCES tasks(id),
  agent_id VARCHAR(64) NOT NULL,
  style_option VARCHAR(32),
  length_option VARCHAR(32),
  tone_option VARCHAR(32),
  prompt_variables JSONB DEFAULT '{}',
  status VARCHAR(20) NOT NULL DEFAULT 'queued',
  result_content JSONB,
  error_message TEXT,
  started_at TIMESTAMP WITH TIME ZONE,
  completed_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_regen_jobs_task ON content_regeneration_jobs(task_id, created_at);
CREATE INDEX idx_regen_jobs_status ON content_regeneration_jobs(status);
```

---

## 五、WebSocket 事件

### 5.1 内容生产专属事件

| 事件名 | 方向 | 触发场景 | Payload 示例 |
|--------|------|---------|-------------|
| `content.generation.progress` | S→C | 内容生成进度更新 | `{"task_id": "task_001", "progress": 0.6, "layer": "Layer 5: Persona"}` |
| `content.regeneration.complete` | S→C | 重新生成完成 | `{"task_id": "task_001", "job_id": "job_reg_001", "new_content": {...}}` |
| `content.save_status` | S→C | 自动保存状态 | `{"task_id": "task_001", "status": "saved", "version": 3}` |

### 5.2 通用 Copilot 事件（复用）

| 事件名 | 方向 | 说明 |
|--------|------|------|
| `context.update` | C→S | 客户端上报上下文变更 |
| `card.push` | S→C | 服务端主动推送 Action Card |
| `card.execute` | C→S | 客户端请求执行 Card Action |
| `card.result` | S→C | 服务端返回执行结果 |
| `card.progress` | S→C | 长时间任务进度推送 |
| `insight.push` | S→C | AI 洞察主动推送 |
| `workspace.sync` | S→C | 工作区数据同步 |

---

## 六、Copilot Action Cards 配置

### 6.1 看板页默认态

```json
{
  "cards": [
    {
      "id": "create-content-default",
      "type": "action",
      "title": "➕ 新建内容",
      "description": "输入主题+平台，快速创建内容任务",
      "priority": 1,
      "actions": [
        { "id": "quick_create", "label": "快速创建", "variant": "primary" },
        { "id": "open_wizard", "label": "完整向导", "variant": "secondary" }
      ]
    },
    {
      "id": "agent-recommend",
      "type": "info",
      "title": "🤖 Agent 推荐",
      "description": "根据近期数据，小红书图文 Agent 成功率 94%，建议使用",
      "priority": 2
    }
  ],
  "quick_actions": [
    { "icon": "list", "label": "查看全部", "command": "show_all" },
    { "icon": "zap", "label": "紧急任务", "command": "urgent_tasks" }
  ]
}
```

### 6.2 编辑器页（有未保存变更时）

```json
{
  "cards": [
    {
      "id": "save-draft-task_001",
      "type": "action",
      "title": "💾 保存草稿",
      "description": "检测到未保存的修改",
      "priority": 1,
      "actions": [
        { "id": "save", "label": "保存", "variant": "primary" },
        { "id": "discard", "label": "放弃", "variant": "ghost" }
      ]
    },
    {
      "id": "title-optimize-task_001",
      "type": "suggestion",
      "title": "✨ 标题优化建议",
      "description": "加入数字可提升 CTR 15%",
      "priority": 2,
      "diff": {
        "before": "猫咪驱虫避坑指南",
        "after": "猫咪驱虫避坑指南，这3个误区90%的人都不知道"
      },
      "actions": [
        { "id": "apply", "label": "应用修改", "variant": "primary" },
        { "id": "ignore", "label": "忽略", "variant": "ghost" }
      ]
    },
    {
      "id": "submit-review-task_001",
      "type": "action",
      "title": "🚀 提交审核",
      "description": "保存并提交至审核发布中心",
      "priority": 3,
      "actions": [
        { "id": "save_and_submit", "label": "保存并提交", "variant": "primary" },
        { "id": "submit_only", "label": "仅提交（不保存）", "variant": "secondary" }
      ]
    },
    {
      "id": "regenerate-task_001",
      "type": "action",
      "title": "🔄 重新生成",
      "description": "使用不同风格重新生成内容",
      "priority": 4,
      "inputs": [
        { "name": "style", "type": "select", "label": "风格", "options": ["casual", "professional", "humorous"] },
        { "name": "length", "type": "select", "label": "长度", "options": ["short", "medium", "long"] }
      ],
      "actions": [
        { "id": "regenerate", "label": "重新生成", "variant": "primary" }
      ]
    }
  ],
  "quick_actions": [
    { "icon": "save", "label": "保存", "command": "save_draft" },
    { "icon": "send", "label": "提交审核", "command": "submit_review" },
    { "icon": "sparkles", "label": "重新生成", "command": "regenerate" }
  ]
}
```

### 6.3 创建向导页（Step 4 汇总态）

```json
{
  "cards": [
    {
      "id": "confirm-create",
      "type": "confirm",
      "title": "✅ 确认创建",
      "description": "任务：猫咪驱虫避坑指南\n平台：小红书\nAgent：小红书图文生成（成功率 94%）\n账号：小艾养猫记",
      "priority": 1,
      "actions": [
        { "id": "confirm", "label": "确认创建", "variant": "primary" },
        { "id": "back", "label": "返回修改", "variant": "secondary" }
      ]
    },
    {
      "id": "agent-recommend-wizard",
      "type": "info",
      "title": "🤖 推荐 Agent",
      "description": "根据「小红书 + 图文」配置，推荐「小红书图文生成 Agent」，成功率 94%",
      "priority": 2
    }
  ],
  "quick_actions": [
    { "icon": "chevron-left", "label": "上一步", "command": "prev_step" },
    { "icon": "chevron-right", "label": "下一步", "command": "next_step" }
  ]
}
```

---

## 七、性能与容量要求

| 指标 | 要求 | 说明 |
|------|------|------|
| `GET /api/task-hub/tasks` | ≤ 150ms | 含 kanban_stats 聚合 |
| `GET /api/task-hub/tasks/{id}` | ≤ 100ms | 含 copilot_context |
| `POST /api/task-hub/tasks` | ≤ 200ms | 含 Agent 推荐计算 |
| `POST /api/ai/copilot/regenerate-content` | ≤ 100ms | 仅提交，实际生成异步 |
| `POST /api/ai/copilot/save-and-submit` | ≤ 200ms | 原子操作 |
| 内容生成完成（异步） | ≤ 15s（P95） | Pipeline 执行 |
| 重新生成完成（异步） | ≤ 15s（P95） | Pipeline 执行 |
| WebSocket 推送延迟 | ≤ 100ms | 服务端→客户端 |

---

## 八、错误码覆盖

| 错误码 | HTTP 状态 | 触发场景 | 前端处理 |
|--------|----------|---------|---------|
| `TASK_ALREADY_SUBMITTED` | 409 | save-and-submit 时任务已在审核中 | 刷新状态，提示"该任务已提交审核" |
| `TASK_NOT_FOUND` | 404 | 编辑器访问不存在的 taskId | 跳转 404 或看板页 |
| `AGENT_NOT_SUPPORTED` | 400 | regenerate-content 时 Agent 不支持风格选项 | 提示"当前 Agent 不支持该风格" |
| `GENERATION_IN_PROGRESS` | 409 | 重新生成时已有生成任务在执行 | 提示"已有生成任务进行中"，展示进度 |
| `COPILOT_CONTEXT_EXPIRED` | 400 | 上下文超过 30 分钟未更新 | 自动刷新后重试 |

---

## 九、实施计划

### Sprint 1（与审核发布并行，Week 5-6）
- `GET /api/task-hub/tasks` 扩展 `copilot_summary`
- `GET /api/task-hub/tasks/{id}` 扩展 `copilot_context`
- `POST /api/task-hub/tasks` 扩展 `copilot_followup`

### Sprint 2（Week 6）
- `POST /api/ai/copilot/regenerate-content` 实现
- `POST /api/ai/copilot/save-and-submit` 实现
- `content_regeneration_jobs` 表 + Alembic 迁移
- WebSocket `content.generation.progress` / `content.regeneration.complete`

### Sprint 3（Week 6-7）
- 联调测试
- 性能优化
- 文档更新

---

## 十、前后端约定

### 10.1 API 前缀对齐

| 前端调用 | 后端路由 | 备注 |
|---------|---------|------|
| `GET /api/task-hub/tasks` | `GET /task-hub/tasks` | 前端 apiClient 自动补 `/api` |
| `POST /api/ai/copilot/regenerate-content` | `POST /ai/copilot/regenerate-content` | 统一走 `/ai/copilot` 网关 |
| `POST /api/ai/copilot/save-and-submit` | `POST /ai/copilot/save-and-submit` | 统一走 `/ai/copilot` 网关 |

### 10.2 Mock 策略

前端在接口就绪前使用 mock：
- `copilot_summary`：静态 kanban_stats
- `copilot_context`：静态 editor_suggestions
- `copilot_followup`：静态 suggested_cards
- 异步生成：setTimeout 模拟 WebSocket 进度推送

---

*文档版本: v1.0*  
*制定日期: 2026-06-05*  
*状态: 待前后端联合评审*  
*评审通过后进入 Step 2（契约冻结）*
