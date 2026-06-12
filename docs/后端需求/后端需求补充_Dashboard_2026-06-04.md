# 后端需求补充文档 — Dashboard（工作台）

> **日期**: 2026-06-04
> **页面**: 工作台 /dashboard
> **前端负责人**: [待填写]
> **后端对接人**: [待填写]
> **来源**: Step 2 契约先行检查发现

---

## 一、缺口概述

前端在重构工作台（DashboardPage）为 v4.0 BentoGrid 布局时，发现以下后端缺口。

---

## 二、API 响应格式标准化（P0）

### 2.1 问题描述

当前 `dashboardStore.ts` 直接访问响应字段（如 `data.metrics`、`data.topics`），未按照 `01-API接口契约.md` §一 的通用响应格式解包 `data.data`。

**当前前端代码（旧）**:
```typescript
const data = await res.json()
set({ coreMetrics: data.metrics })
```

**期望格式（v4.0 契约）**:
```json
{
  "code": "OK",
  "message": "查询成功",
  "data": {
    "metrics": { ... }
  },
  "trace_id": "req_abc123",
  "timestamp": "2026-06-04T10:00:00Z"
}
```

**前端解包方式**:
```typescript
const json = await res.json()
if (json.code !== 'OK') throw new Error(json.message)
set({ coreMetrics: json.data.metrics })
```

### 2.2 影响范围

以下 Dashboard 相关 API 需要确认/调整响应格式：

| API 端点 | 当前状态 | 需求 |
|---------|---------|------|
| `GET /api/dashboard/overview` | 未确认标准格式 | **需确认**返回 `{code, message, data}` |
| `GET /api/dashboard/core-metrics` | 未确认标准格式 | **需确认**返回 `{code, message, data}` |
| `GET /api/dashboard/alerts` | 未确认标准格式 | **需确认**返回 `{code, message, data}` |
| `GET /api/dashboard/activity-log` | 未确认标准格式 | **需确认**返回 `{code, message, data}` |
| `GET /api/dashboard/quick-actions` | 未确认标准格式 | **需确认**返回 `{code, message, data}` |
| `GET /api/trend-scout/topics` | 未确认标准格式 | **需确认**返回 `{code, message, data}` |
| `GET /api/agents` | 未确认标准格式 | **需确认**返回 `{code, message, data}` |
| `GET /api/data-analyst/engagement-trend` | 未确认标准格式 | **需确认**返回 `{code, message, data}` |
| `GET /api/predictions/hit-rate` | 未确认标准格式 | **需确认**返回 `{code, message, data}` |
| `GET /api/persona-stories` | 未确认标准格式 | **需确认**返回 `{code, message, data}` |

### 2.3 建议方案

**方案 A（推荐）**：后端统一调整为标准格式，前端同步修改解包逻辑。影响 1~2 天。

**方案 B（兼容过渡）**：后端在响应头中增加 `X-Response-Format: v2`，前端根据版本选择解包方式。增加复杂度，不推荐。

**前端当前 workaround**：在 `lib/api.ts` 中增加智能解包层，兼容两种格式，待后端统一后移除兼容逻辑。

---

## 三、Dashboard API 契约补充（P0）

以下 API 在 `01-API接口契约.md` 中缺少详细定义，需后端补充 Schema。

### 3.1 `GET /api/dashboard/overview`

**用途**: 工作台顶部概览指标

**期望响应 data 结构**:
```json
{
  "today": {
    "tasksPending": 5,
    "briefsPending": 2,
    "contentsPendingReview": 3,
    "contentsPublished": 12,
    "engagementDelta": 0.15,
    "avgHealthScore": 88
  }
}
```

### 3.2 `GET /api/dashboard/core-metrics`

**用途**: 核心运营指标卡片

**期望响应 data 结构**:
```json
{
  "metrics": {
    "pendingReview": 5,
    "publishedToday": 3,
    "queuedTasks": 8,
    "failedDlq": 0,
    "tokenCostToday": 12.50
  }
}
```

### 3.3 `GET /api/content-drafts?limit=10`（字段扩展）

**用途**: 工作台"最近内容卡片流"

**当前缺失字段**（v4.0 需要）:

| 字段 | 类型 | 说明 |
|------|------|------|
| `compliance_score` | number | 合规分数 0-100 |
| `agent_trace` | AgentTrace[] | Agent 执行链路 |
| `predicted_engagement` | object | 预测互动量 `{likes: [25,60], comments: [5,15]}` |
| `account_name` | string | 账号名称 |
| `platform_id` | string | 平台枚举 xhs/douyin/... |
| `media_url` | string | 封面图 URL |
| `status` | string | ContentDraftStatus 枚举 |

**AgentTrace 结构**:
```json
{
  "agent_name": "TrendScout",
  "status": "success",
  "duration_seconds": 0.8,
  "timestamp": "2026-06-04T10:00:00Z"
}
```

### 3.4 `GET /api/agents/status`（新增/确认）

**用途**: Copilot Agent 状态看板

**期望响应 data 结构**:
```json
{
  "agents": [
    {
      "agent_id": "trend_scout_001",
      "name": "TrendScout",
      "status": "completed",
      "duration_seconds": 0.8,
      "updated_at": "2026-06-04T10:00:00Z"
    },
    {
      "agent_id": "content_forge_001",
      "name": "ContentForge",
      "status": "running",
      "duration_seconds": 8.5,
      "updated_at": "2026-06-04T10:00:00Z"
    }
  ]
}
```

---

## 四、枚举值补充（P1）

### 4.1 ContentDraftStatus 扩展

当前 `01-API接口契约.md` §3.6 已定义 `ContentDraft` 状态枚举，确认工作台场景下需要以下状态：

| 枚举值 | 说明 | 工作台展示 |
|--------|------|-----------|
| `IDLE` | 空闲 | — |
| `GENERATING` | AI 生成中 | 卡片显示 AI 流光边框 + Agent Trace |
| `REVIEWING` | 审核中 | 合规分数条 + 待审标记 |
| `APPROVED` | 已通过 | 可发布状态 |
| `PUBLISHED` | 已发布 | 显示数据回流入口 |

---

## 五、前端 Workaround（不阻塞进度）

在前端 `lib/api.ts` 中增加智能响应解包函数，兼容新旧两种格式：

```typescript
export function unwrapResponse<T>(json: unknown): T {
  if (json && typeof json === 'object' && 'code' in json && 'data' in json) {
    const r = json as { code: string; message: string; data: T }
    if (r.code !== 'OK') throw new Error(r.message)
    return r.data
  }
  return json as T
}
```

待后端统一格式后，移除兼容逻辑。

---

## 六、优先级与排期建议

| 缺口 | 优先级 | 建议排期 | 阻塞影响 |
|------|--------|---------|---------|
| API 响应格式标准化 | P0 | 1 天 | 前端 Store 层无法统一错误处理 |
| Dashboard API 契约补充 | P0 | 1 天 | 联调缺少法律依据 |
| content-drafts 字段扩展 | P1 | 2 天 | ContentCard 部分字段需 mock |
| agents/status 接口确认 | P1 | 0.5 天 | Agent 状态看板数据来源 |

---

*文档模板参考: `docs/提示词模板/03-后端需求补充文档模板.md`*
