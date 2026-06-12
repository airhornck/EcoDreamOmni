# 后端需求补充文档 — 审核发布 Copilot-Driven 改造

> **关联前端任务**: Phase 2-P3 审核发布 `/review` HTML 预览 + React 实现  
> **关联设计文档**: `Copilot-Workspace-交互模式规范_v1.0.md`  
> **提出日期**: 2026-06-04  
> **优先级**: 🔴 P0（阻塞前端 Step 3 开发）  
> **影响范围**: AI 服务层、审核发布服务、Copilot 网关、WebSocket 推送  

---

## 一、需求背景

前端审核发布页面正在进行 v4.0 重构，核心交互范式从「Direct（工作区按钮为主）」升级为 **「Copilot-Driven（副驾驶驱动）」**。此变更要求后端提供配套的 API 能力和数据支持。

**关键变更点**:
1. 审核决策入口从工作区按钮迁移至 Copilot Action Card
2. AI 封面生成从弹框内直接调用改为 Copilot 驱动调用
3. Copilot 需要根据页面上下文主动推送 Action Cards
4. 操作结果需要实时同步到工作区

---

## 二、新增 API 端点

### 2.1 AI 封面生成

```
POST /api/ai/generate-cover
```

**请求体**:
```json
{
  "task_id": "task_abc123",
  "prompt": "温馨可爱的橘猫在草地上，阳光照射，治愈风格",
  "auto_prompt": false,
  "content_summary": "猫咪驱虫避坑指南，3个误区...",
  "style_preset": "cute" | "professional" | "minimal" | null,
  "count": 2,
  "ratio": "3:4"
}
```

**字段说明**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `task_id` | string | 是 | 关联的任务 ID |
| `prompt` | string | 条件 | 用户输入的提示词，`auto_prompt=false` 时必填 |
| `auto_prompt` | boolean | 否 | 是否自动根据内容摘要生成提示词，默认 `false` |
| `content_summary` | string | 否 | 内容摘要，用于 `auto_prompt=true` 时自动生成 |
| `style_preset` | string | 否 | 风格预设 |
| `count` | integer | 否 | 生成数量，默认 2，最大 4 |
| `ratio` | string | 否 | 裁剪比例，默认 `3:4` |

**响应**（异步任务）:
```json
{
  "code": "ACCEPTED",
  "message": "封面生成任务已提交",
  "data": {
    "job_id": "cover_gen_xyz789",
    "status": "queued",
    "estimated_seconds": 8
  },
  "trace_id": "req_..."
}
```

**轮询查询**:
```
GET /api/ai/generate-cover/{job_id}
```

**响应**:
```json
{
  "code": "OK",
  "message": "查询成功",
  "data": {
    "job_id": "cover_gen_xyz789",
    "status": "completed",
    "results": [
      {
        "url": "https://cdn.example.com/covers/abc123.jpg",
        "thumbnail_url": "https://cdn.example.com/covers/abc123_thumb.jpg",
        "ratio": "3:4",
        "prompt_used": "温馨可爱的橘猫在草地上...",
        "seed": 42
      }
    ],
    "completed_at": "2026-06-04T15:32:00Z"
  }
}
```

**WebSocket 推送**（推荐替代轮询）:
```json
{
  "event": "cover.generation.progress",
  "payload": {
    "job_id": "cover_gen_xyz789",
    "task_id": "task_abc123",
    "status": "generating",
    "progress": 65,
    "step": "upscaling"
  }
}
```

**限流策略**:
- 单用户：最多 3 次/分钟
- 单任务：最多 5 次/小时
- 超限返回 `RATE_LIMITED` + `retry_after_seconds`

---

### 2.2 Copilot 上下文上报

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
    "task_id": "task_001",
    "title": "猫咪驱虫避坑指南...",
    "compliance_score": 96,
    "quality_score": 88,
    "status": "human_wait",
    "platform": "xhs",
    "account_name": "小艾养猫记"
  },
  "timestamp": "2026-06-04T15:30:00Z"
}
```

**响应**（后端根据上下文预生成 Action Cards）:
```json
{
  "code": "OK",
  "message": "上下文已更新",
  "data": {
    "suggested_cards": [
      {
        "card_type": "decision",
        "priority": 1,
        "reason": "human_wait 状态，合规分 96 > 85，建议直接通过"
      },
      {
        "card_type": "generation",
        "priority": 2,
        "reason": "当前只有 1 张封面图，可补充"
      }
    ]
  }
}
```

---

### 2.3 Copilot Action Cards 模板获取

```
GET /api/ai/copilot/action-cards?page={page}&task_id={task_id}
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
        "inputs": [],
        "actions": [
          {
            "id": "approve",
            "label": "✅ 审核通过",
            "variant": "primary",
            "api": {
              "method": "POST",
              "endpoint": "/api/human-in-the-loop/tasks/task_001/approve"
            }
          },
          {
            "id": "revise",
            "label": "🔄 打回修改",
            "variant": "secondary",
            "needs_reason": true
          },
          {
            "id": "reject",
            "label": "❌ 驳回",
            "variant": "ghost",
            "needs_reason": true
          }
        ]
      },
      {
        "id": "cover-gen-task_001",
        "type": "generation",
        "title": "🎨 生成封面",
        "description": "让 AI 根据内容生成封面图",
        "inputs": [
          {
            "name": "prompt",
            "label": "描述",
            "type": "textarea",
            "placeholder": "描述你想要的封面风格..."
          }
        ],
        "actions": [
          {
            "id": "generate",
            "label": "生成封面",
            "variant": "primary",
            "api": {
              "method": "POST",
              "endpoint": "/api/ai/generate-cover"
            }
          }
        ]
      }
    ]
  }
}
```

---

### 2.4 审核决策 API 增强

**现有端点**（保持不变，但扩展响应）:
```
POST /api/human-in-the-loop/tasks/{task_id}/approve
POST /api/human-in-the-loop/tasks/{task_id}/reject
POST /api/human-in-the-loop/tasks/{task_id}/revise
```

**增强请求体**（`revise`/`reject`）:
```json
{
  "reason": "标题超出字数限制，需精简",
  "copilot_suggested": true,      // 新增：是否来自 Copilot 建议
  "copilot_card_id": "review-decision-task_001"  // 新增：来源 Card ID
}
```

**增强响应**:
```json
{
  "code": "OK",
  "message": "审核已通过",
  "data": {
    "status": "approved_waiting_publish",
    "next_steps": [
      {
        "action": "confirm_publish",
        "label": "确认发布",
        "available": true
      }
    ],
    "copilot_followup": {
      "message": "审核已通过！要现在发布还是定时发布？",
      "suggested_cards": [
        {
          "type": "decision",
          "title": "发布确认",
          "actions": [
            { "id": "publish_now", "label": "立即发布" },
            { "id": "schedule", "label": "定时发布" }
          ]
        }
      ]
    }
  }
}
```

---

## 三、现有 API 修改

### 3.1 审核详情接口 — 新增 Copilot 相关字段

```
GET /api/review-publish-center/conclusions/{task_id}
```

**响应 `data` 新增字段**:
```json
{
  "copilot_context": {
    "recommended_action": "approve",
    "confidence": 0.94,
    "reasoning": "合规分 96 分，L1-L4 全部通过，质量分 88 分，历史同类内容通过率 94%",
    "risk_factors": [],
    "suggested_improvements": [
      "标题加入具体数字可提升点击率",
      "文末添加驱虫时间表卡片"
    ]
  },
  "available_copilot_cards": [
    "review-decision",
    "cover-generation",
    "title-optimization"
  ]
}
```

### 3.2 审核列表接口 — 新增批量 Copilot 分析

```
GET /api/review-publish-center/conclusions
```

**响应 `data` 新增字段**:
```json
{
  "copilot_summary": {
    "total_pending": 3,
    "recommended_priority": ["task_003", "task_001", "task_002"],
    "batch_suggestion": "3 条待审中，1 条合规分低于 80 分建议优先处理，其余 2 条建议直接通过。"
  }
}
```

---

## 四、WebSocket 事件扩展

### 4.1 事件清单

| 事件名 | 方向 | 说明 | 优先级 |
|--------|------|------|--------|
| `cover.generation.progress` | S→C | 封面生成进度推送 | 🔴 P0 |
| `cover.generation.completed` | S→C | 封面生成完成，附图片 URL | 🔴 P0 |
| `review.decision.completed` | S→C | 审核决策完成，附新状态 | 🟡 P1 |
| `copilot.card.push` | S→C | 服务端主动推送 Action Card | 🟡 P1 |
| `copilot.context.update` | C→S | 客户端上报上下文变更 | 🟡 P1 |
| `workspace.sync` | S→C | 工作区内容同步（多端场景） | 🟢 P2 |

### 4.2 事件格式规范

```typescript
// WebSocket Message 统一格式
interface WSMessage {
  event: string
  payload: Record<string, unknown>
  timestamp: string  // ISO 8601
  trace_id: string
}
```

**示例：封面生成完成**:
```json
{
  "event": "cover.generation.completed",
  "payload": {
    "job_id": "cover_gen_xyz789",
    "task_id": "task_abc123",
    "user_id": "usr_123",
    "results": [
      {
        "url": "https://cdn.example.com/covers/abc123.jpg",
        "thumbnail_url": "https://cdn.example.com/covers/abc123_thumb.jpg",
        "ratio": "3:4"
      }
    ]
  },
  "timestamp": "2026-06-04T15:32:08Z",
  "trace_id": "ws_abc123"
}
```

---

## 五、数据模型变更

### 5.1 新增表：`ai_cover_generation_jobs`

```sql
CREATE TABLE ai_cover_generation_jobs (
  id VARCHAR(32) PRIMARY KEY,
  task_id VARCHAR(32) NOT NULL REFERENCES tasks(id),
  user_id VARCHAR(32) NOT NULL,
  prompt TEXT,
  auto_prompt BOOLEAN DEFAULT FALSE,
  style_preset VARCHAR(32),
  count INTEGER DEFAULT 2,
  ratio VARCHAR(10) DEFAULT '3:4',
  status VARCHAR(20) DEFAULT 'queued',  -- queued/generating/completed/failed
  results JSONB,  -- [{url, thumbnail_url, ratio, seed}]
  error_message TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  completed_at TIMESTAMP WITH TIME ZONE,
  
  -- 限流用索引
  CONSTRAINT unique_user_task_rate UNIQUE (user_id, task_id, created_at)
);

CREATE INDEX idx_cover_jobs_user_created ON ai_cover_generation_jobs(user_id, created_at);
CREATE INDEX idx_cover_jobs_task ON ai_cover_generation_jobs(task_id);
```

### 5.2 新增表：`copilot_context_sessions`

```sql
CREATE TABLE copilot_context_sessions (
  id VARCHAR(32) PRIMARY KEY,
  user_id VARCHAR(32) NOT NULL,
  session_id VARCHAR(64) NOT NULL UNIQUE,
  page VARCHAR(64) NOT NULL,
  selected_items JSONB DEFAULT '[]',
  selected_content JSONB,
  suggested_cards JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_copilot_sessions_user ON copilot_context_sessions(user_id, updated_at);
```

### 5.3 扩展现有表：`review_conclusions`

```sql
ALTER TABLE review_conclusions
ADD COLUMN copilot_recommended_action VARCHAR(20),
ADD COLUMN copilot_confidence DECIMAL(3,2),
ADD COLUMN copilot_reasoning TEXT,
ADD COLUMN copilot_suggested_improvements JSONB DEFAULT '[]';
```

---

## 六、错误码扩展

### 6.1 新增错误码

| 错误码 | HTTP 状态 | 中文说明 | 触发场景 | 前端处理 |
|--------|----------|---------|---------|---------|
| `COVER_GENERATION_LIMIT_EXCEEDED` | 429 | 封面生成次数超限 | 单用户 3 次/分钟或单任务 5 次/小时 | 展示「生成太频繁，请 X 秒后再试」 |
| `COVER_GENERATION_FAILED` | 500 | 封面生成失败 | AI 图像生成服务异常 | 展示「生成失败」+ [重试] 按钮 |
| `COPILOT_CONTEXT_EXPIRED` | 400 | Copilot 上下文过期 | 上下文超过 30 分钟未更新 | 自动刷新上下文后重试 |
| `INVALID_COPILOT_CARD_ACTION` | 400 | 无效的 Copilot 卡片操作 | 卡片已过期或已被处理 | 刷新页面获取最新卡片 |
| `REVIEW_DECISION_ALREADY_MADE` | 409 | 审核决策已存在 | 并发操作导致重复决策 | 刷新详情页获取最新状态 |

### 6.2 扩展现有错误码含义

| 现有错误码 | 新增场景 |
|-----------|---------|
| `RATE_LIMITED` | AI 封面生成限流 |
| `AGENT_DEGRADED` | 封面生成 Agent 降级 |
| `AGENT_TIMEOUT` | 封面生成超时（>30s） |

---

## 七、性能与容量要求

| 指标 | 要求 | 说明 |
|------|------|------|
| 封面生成接口响应 | ≤ 200ms（ACCEPTED） | 异步任务立即返回 |
| 封面生成完成时间 | ≤ 15s（P95） | 从提交到 completed |
| Copilot 上下文接口 | ≤ 100ms | 轻量级上下文更新 |
| Action Cards 获取 | ≤ 150ms | 含业务逻辑判断 |
| WebSocket 推送延迟 | ≤ 100ms | 服务端→客户端 |
| 封面生成并发 | 50 QPS | 需图片生成服务支撑 |
| Copilot 上下文存储 | 7 天 TTL | 过期自动清理 |

---

## 八、安全与权限

1. **封面生成**: 用户只能为自己拥有的 task 生成封面，需校验 `task_id` 归属
2. **审核决策**: 保留现有 RBAC 权限检查，`approve`/`reject`/`revise` 需对应权限
3. **Copilot 上下文**: 会话级隔离，用户只能访问自己的上下文数据
4. **图片存储**: 生成的封面图需存储在私有 CDN，带签名 URL，有效期 7 天
5. **Prompt 安全**: 用户输入的 prompt 需经过内容安全过滤，防止 Prompt Injection

---

## 九、实施计划

| 阶段 | 任务 | 负责人 | 工期 | 依赖 |
|------|------|--------|------|------|
| **M1** | `ai_cover_generation_jobs` 表设计 + 基础 CRUD | 后端 | 1 天 | 无 |
| **M1** | `POST /api/ai/generate-cover` 接口（异步队列） | 后端 | 2 天 | M1 表 |
| **M1** | 图片生成 Agent（对接 Stable Diffusion / DALL-E） | AI 架构 | 2 天 | M1 接口 |
| **M2** | WebSocket 事件封装（progress/completed） | 后端 | 1 天 | M1 |
| **M2** | `copilot_context_sessions` 表 + 上下文接口 | 后端 | 1 天 | 无 |
| **M2** | `GET /api/ai/copilot/action-cards` 接口 | 后端 | 1 天 | M2 表 |
| **M3** | 审核决策接口增强（copilot 字段） | 后端 | 0.5 天 | 无 |
| **M3** | 审核详情/列表接口增强（copilot 建议字段） | 后端 | 0.5 天 | 无 |
| **M3** | 限流中间件（封面生成） | 后端 | 0.5 天 | 无 |
| **M4** | 联调测试（前端 + 后端 + AI） | 前后端 | 2 天 | M1-M3 |

**总计工期**: 7 个工作日（1.5 周）

---

## 十、前后端约定

### 10.1 接口调用顺序（封面生成场景）

```
1. 前端: POST /api/ai/generate-cover
   → 后端返回 { job_id, status: "queued" }

2. 前端: 展示「生成中...」状态

3. 后端: 通过 WebSocket push cover.generation.progress
   → 前端更新进度条

4. 后端: 完成 push cover.generation.completed
   → 前端展示生成结果缩略图

5. 前端: 用户点击「使用此图」
   → 前端本地更新工作区封面预览
   → 前端调用 PATCH /api/review-publish-center/conclusions/{id}/content
      { cover_image_url: "..." }
```

### 10.2 接口调用顺序（审核决策场景）

```
1. 前端: GET /api/review-publish-center/conclusions/{id}
   → 后端返回详情 + copilot_context（建议 + 置信度）

2. 前端: 将 copilot_context 渲染为 Copilot Action Card

3. 用户: 在 Copilot 中点击「✅ 审核通过」

4. 前端: POST /api/human-in-the-loop/tasks/{id}/approve
   → 请求体: { copilot_suggested: true, copilot_card_id: "..." }

5. 后端: 处理决策 + push review.decision.completed
   → 前端收到后更新状态 + 展示 Toast + 可能推送新 Card（发布确认）
```

---

## 十一、附录

### 11.1 参考前端产物

- `demo/page-preview/review.html`（Copilot-Driven 交互预览）
- `apps/frontend/src/pages/ReviewPublishDetailPage.tsx`（现有实现基线）
- `apps/frontend/src/components/review/`（子组件目录）

### 11.2 参考文档

- `docs/前端设计/Copilot-Workspace-交互模式规范_v1.0.md`
- `docs/契约与数据/01-API接口契约.md`
- `docs/数据词典_v4.0/04-前端Store与路由.md`

### 11.3 前端 mock  workaround

在接口就绪前，前端使用以下 mock 策略继续开发：

```typescript
// hooks/useCoverGeneration.ts
const mockGenerateCover = async (payload: GenerateCoverPayload) => {
  // 模拟异步延迟
  await new Promise(r => setTimeout(r, 2500))
  return {
    job_id: `mock_${Date.now()}`,
    status: 'completed',
    results: [
      { url: 'https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=400', ratio: '3:4' },
      { url: 'https://images.unsplash.com/photo-1573865526739-10659fec78a5?w=400', ratio: '3:4' },
    ]
  }
}
```

---

*文档版本: v1.0*  
*制定日期: 2026-06-04*  
*状态: 待后端负责人评审*  
*评审通过后进入 Sprint 排期*
