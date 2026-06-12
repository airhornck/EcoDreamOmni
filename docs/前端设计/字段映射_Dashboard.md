# 字段映射表 — Dashboard（工作台）

> **页面**: 工作台 /dashboard
> **日期**: 2026-06-04
> **版本**: v4.0

---

## 一、Store 字段 ↔ API 字段映射

### 1.1 概览指标（Overview）

| 前端字段（Zustand/Query） | API 字段 | API 端点 | 说明 |
|-------------------------|---------|---------|------|
| `overview.tasksPending` | `today.tasks_pending` | `GET /api/dashboard/overview` | 待处理任务数 |
| `overview.contentsPendingReview` | `today.contents_pending_review` | `GET /api/dashboard/overview` | 待审内容数 |
| `overview.contentsPublished` | `today.contents_published` | `GET /api/dashboard/overview` | 已发布数 |
| `overview.engagementDelta` | `today.engagement_delta` | `GET /api/dashboard/overview` | 互动量变化率 |
| `overview.avgHealthScore` | `today.avg_health_score` | `GET /api/dashboard/overview` | 平均健康分 |

### 1.2 核心指标（CoreMetrics）

| 前端字段 | API 字段 | API 端点 | 说明 |
|---------|---------|---------|------|
| `coreMetrics.pendingReview` | `metrics.pending_review` | `GET /api/dashboard/core-metrics` | 待审核数 |
| `coreMetrics.publishedToday` | `metrics.published_today` | `GET /api/dashboard/core-metrics` | 今日已发布 |
| `coreMetrics.queuedTasks` | `metrics.queued_tasks` | `GET /api/dashboard/core-metrics` | 队列中任务 |
| `coreMetrics.failedDlq` | `metrics.failed_dlq` | `GET /api/dashboard/core-metrics` | DLQ 失败数 |
| `coreMetrics.tokenCostToday` | `metrics.token_cost_today` | `GET /api/dashboard/core-metrics` | 今日 Token 成本 |

### 1.3 告警（Alerts）

| 前端字段 | API 字段 | API 端点 | 说明 |
|---------|---------|---------|------|
| `alerts[].id` | `alerts[].id` | `GET /api/dashboard/alerts` | 告警 ID |
| `alerts[].level` | `alerts[].level` | `GET /api/dashboard/alerts` | 级别：emergency/warning/info/success |
| `alerts[].title` | `alerts[].title` | `GET /api/dashboard/alerts` | 标题 |
| `alerts[].message` | `alerts[].message` | `GET /api/dashboard/alerts` | 详情 |
| `alerts[].timestamp` | `alerts[].timestamp` | `GET /api/dashboard/alerts` | 时间戳 |

### 1.4 智能选题（SmartTopics）

| 前端字段 | API 字段 | API 端点 | 说明 |
|---------|---------|---------|------|
| `smartTopics[].id` | `topics[].id` | `GET /api/trend-scout/topics` | 选题 ID |
| `smartTopics[].title` | `topics[].title` | `GET /api/trend-scout/topics` | 选题标题 |
| `smartTopics[].estimatedEngagement` | `topics[].estimated_engagement` | `GET /api/trend-scout/topics` | 预估互动量 |
| `smartTopics[].tags` | `topics[].tags` | `GET /api/trend-scout/topics` | 标签列表 |

> **注意**: 后端返回 snake_case `estimated_engagement`，前端 Store 已做 camelCase 转换。

### 1.5 Agent 状态（AgentStatus）

| 前端字段 | API 字段 | API 端点 | 说明 |
|---------|---------|---------|------|
| `agentStatus.activeAgents` | `status.active_agents` | `GET /api/agents` | 活跃 Agent 数 |
| `agentStatus.pendingMessages` | `status.pending_messages` | `GET /api/agents` | 待处理消息 |
| `agentStatus.successRate1h` | `status.success_rate_1h` | `GET /api/agents` | 近1h成功率 |
| `agentStatus.lastExecutionStatus` | `status.last_execution_status` | `GET /api/agents` | 最近执行状态 |

### 1.6 故事线进度（StoryProgress）

| 前端字段 | API 字段 | API 端点 | 说明 |
|---------|---------|---------|------|
| `storyProgress[].id` | `items[].id` / `stories[].id` | `GET /api/persona-stories` | 故事线 ID |
| `storyProgress[].name` | `items[].name` | `GET /api/persona-stories` | 名称 |
| `storyProgress[].currentNode` | `items[].current_node` | `GET /api/persona-stories` | 当前节点 |
| `storyProgress[].currentNodeIndex` | `items[].current_node_index` | `GET /api/persona-stories` | 当前索引 |
| `storyProgress[].totalNodes` | `items[].total_nodes` | `GET /api/persona-stories` | 总节点数 |

### 1.7 互动趋势（EngagementTrend）

| 前端字段 | API 字段 | API 端点 | 说明 |
|---------|---------|---------|------|
| `engagementTrend[].date` | `trend[].date` | `GET /api/data-analyst/engagement-trend` | 日期 |
| `engagementTrend[].likes` | `trend[].likes` | `GET /api/data-analyst/engagement-trend` | 点赞数 |
| `engagementTrend[].comments` | `trend[].comments` | `GET /api/data-analyst/engagement-trend` | 评论数 |
| `engagementTrend[].collections` | `trend[].collections` | `GET /api/data-analyst/engagement-trend` | 收藏数 |

### 1.8 内容卡片流（ContentStream — v4.0 新增字段）

| 前端字段 | API 字段 | API 端点 | 说明 |
|---------|---------|---------|------|
| `contentDrafts[].id` | `drafts[].id` | `GET /api/content-drafts` | 内容 ID |
| `contentDrafts[].title` | `drafts[].title` | `GET /api/content-drafts` | 标题 |
| `contentDrafts[].complianceScore` | `drafts[].compliance_score` | `GET /api/content-drafts` | 合规分数 0-100 |
| `contentDrafts[].agentTrace` | `drafts[].agent_trace` | `GET /api/content-drafts` | Agent 执行链路 |
| `contentDrafts[].predictedEngagement` | `drafts[].predicted_engagement` | `GET /api/content-drafts` | 预测互动量 |
| `contentDrafts[].accountName` | `drafts[].account_name` | `GET /api/content-drafts` | 账号名称 |
| `contentDrafts[].platformId` | `drafts[].platform_id` | `GET /api/content-drafts` | 平台枚举 |

> **后端缺口**: `content-drafts` 接口当前可能未返回 `compliance_score`、`agent_trace`、`predicted_engagement` 等 v4.0 新增字段。详见 `docs/后端需求/后端需求补充_Dashboard_2026-06-04.md`。

---

## 二、枚举映射

### 2.1 平台枚举（PlatformId → 显示名称）

| API 枚举值 | 前端显示 | 组件 |
|-----------|---------|------|
| `xhs` | 小红书 | ContentCard.platform |
| `douyin` | 抖音 | ContentCard.platform |
| `wechat_official` | 微信公众号 | ContentCard.platform |
| `bilibili` | 哔哩哔哩 | ContentCard.platform |

### 2.2 Alert 级别枚举

| API 枚举值 | 前端显示 | Badge variant |
|-----------|---------|--------------|
| `emergency` | 紧急 | danger |
| `warning` | 警告 | warning |
| `info` | 提示 | info |
| `success` | 成功 | success |

### 2.3 Agent 执行状态（AgentTraceStatus）

| API 枚举值 | 前端显示 | 颜色 |
|-----------|---------|------|
| `success` | ✓ 完成 | 绿色 |
| `running` | ⏳ 运行中 | 紫色（脉冲动画）|
| `pending` | ○ 等待中 | 灰色 |
| `error` | ⚠ 失败 | 红色 |

---

## 三、API 包装层约定

### 3.1 响应解包

所有 Dashboard API 调用通过 `apiClient()` 统一封装，自动解包 `data.data`：

```typescript
const metrics = await apiClient<{ metrics: CoreMetrics }>('/dashboard/core-metrics')
// 返回的是 { metrics: CoreMetrics }，若后端返回标准格式则自动解包
```

### 3.2 错误处理

| 错误码 | 前端行为 |
|--------|---------|
| `UNAUTHORIZED` (401) | 跳转登录页 |
| `FORBIDDEN` (403) | 展示"无权限"提示 |
| `VALIDATION_ERROR` (400) | 高亮错误字段 |
| `RATE_LIMITED` (429) | 展示"操作太频繁"，建议稍后重试 |
| `AGENT_DEGRADED` (503) | 提示"服务暂时不可用"，自动 Handoff |
| `INTERNAL_ERROR` (500) | 提示"服务内部错误"，记录日志 |

---

## 四、变更记录

| 日期 | 版本 | 变更内容 |
|------|------|---------|
| 2026-06-04 | v1.0 | 初始创建：工作台字段映射表，含 v4.0 新增 ContentCard 字段 |
