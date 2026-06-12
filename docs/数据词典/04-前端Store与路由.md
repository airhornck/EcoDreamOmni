# 前端 Store 与 API 调用映射

> 自动生成于 2026-05-27

## Store 清单

| Store 文件 | 导出名称 | API 路径 |
|------------|----------|----------|
|  |  | `/api/personas` `/api/account-pool` |
|  |  | - |
|  |  | `/api/pipelines` `/api/workflows` `/agents` |
|  |  | `/api/assets/upload` `/api/assets/upload-file` `/api/assets` |
|  |  | `/api/auth/login` |
|  |  | `/api/brand-knowledge/entries` |
|  |  | `/api/compliance/check` `/api/compliance/history` `/api/compliance/batch-check` `/api/compliance/stats` `/api/compliance/rules` |
|  |  | `/api/content-generate` `/api/content-drafts` `/api/persona-stories?status=active` `/api/llm-hub/models?status=active` `/api/content-series` `/api/personas` |
|  |  | `/api/cron-hub/dlq?limit=100` `/api/cron-hub/executions?limit=100` `/api/cron-hub/jobs` |
|  |  | `/api/dashboard/activity-log` `/api/trend-scout/topics?limit=5` `/api/publish-tasks` `/api/dashboard/core-metrics` `/api/dashboard/quick-actions` `/api/dashboard/overview` `/api/content-drafts` `/api/persona-stories?status=active` `/api/account-pool` `/api/dashboard/alerts` `/api/predictions/hit-rate` `/api/agents` |
|  |  | `/api/data-analyst/account-comparison` `/api/data-analyst/platform-distribution` `/api/data-analyst/dashboard` `/api/data-analyst/calibration-status` `/api/data-analyst/import-history` `/api/data-analyst/mape-trend` `/api/data-analyst/reports` `/api/data-analyst/engagement-distribution` `/api/data-analyst/calibrate` |
|  |  | `/api/llm-hub/scope-configs` `/api/llm-hub/models` |
|  |  | `/api/personas` |
|  |  | `/api/persona-stories` |
|  |  | `/api/platform-rules` |
|  |  | `/api/predictions/accuracy` `/api/predictions/stats` `/api/predictions/batch` `/api/account-pool?status=active` `/api/predictions` |
|  |  | `/api/proxies` |
|  |  | `/api/content-drafts?status=approved` `/api/publish-tasks` `/api/account-pool` |
|  |  | - |
|  |  | - |
|  |  | `/api/skills` `/api/agent-skills` |
|  |  | `/api/cron-hub/dlq` `/api/account-pool` `/api/content-series` `/api/workflow-engine/templates` `/api/personas` `/api/task-hub/tasks` |
|  |  | `/api/timeline/events` |
|  |  | `/api/trend-scout/reports` `/api/trend-scout/topics` `/api/trend-scout/hot-keywords` `/api/trend-scout/stats` `/api/trend-scout/persona-draft` |
|  |  | `/api/vetdrug/drugs` `/api/vetdrug/bulk-import` `/api/vetdrug/validate-claim` |
|  |  | `/api/workflow-engine/templates` `/api/workflow-engine/executions` `/api/task-hub/tasks` |

## 前端路由映射

| 路由路径 | 页面组件 |
|----------|----------|
|  |  |
|  |  |
|  |  |
|  |  |
|  |  |
|  |  |
|  |  |
|  |  |
|  |  |
|  |  |
|  |  |
|  |  |
|  |  |
|  |  |
|  |  |
|  |  |
|  |  |
|  |  |
|  |  |
|  |  |
|  |  |
|  |  |
|  |  |
|  |  |
|  |  |
|  |  |
|  |  |

## 各页面使用的 Store

| 页面文件 | 导入的 Store | 其他关键依赖 |
|----------|--------------|--------------|
|  | `proxyStore`, `accountPoolStore` | `lucide-react` |
|  | - | - |
|  | `agentOrchestraStore` | `lucide-react` |
|  | `assetPoolStore` | `lucide-react` |
|  | `brandKnowledgeStore` | `lucide-react` |
|  | `complianceStore` | `lucide-react` |
|  | `assetPoolStore`, `contentForgeStore` | `lucide-react` |
|  | `cronCockpitStore` | - |
|  | `cronCockpitStore` | `lucide-react` |
|  | - | - |
|  | `authStore`, `dashboardStore` | `lucide-react` |
|  | `dataAnalystStore` | `recharts`, `lucide-react` |
|  | `llmCockpitStore` | - |
|  | `llmCockpitStore` | `lucide-react` |
|  | - | - |
|  | `authStore` | - |
|  | `personaPoolStore`, `personaStoryStore` | `recharts`, `lucide-react` |
|  | - | `lucide-react` |
|  | `platformRulesStore` | `lucide-react` |
|  | `predictionsStore` | `recharts`, `lucide-react` |
|  | `proxyStore` | `lucide-react` |
|  | `publisherStore` | `lucide-react` |
|  | `reviewPublishStore` | `lucide-react` |
|  | `reviewPublishStore` | `lucide-react` |
|  | - | `lucide-react` |
|  | - | - |
|  | `skillHubStore`, `agentOrchestraStore` | `lucide-react` |
|  | `personaStoryStore` | `lucide-react` |
|  | `taskHubStore` | `lucide-react` |
|  | `taskHubStore` | `lucide-react` |
|  | `timelineStore` | `lucide-react` |
|  | `trendScoutStore` | `lucide-react` |
|  | `vetDrugStore` | `lucide-react` |
|  | `workflowCockpitStore` | - |
|  | `workflowCockpitStore` | `lucide-react` |



## 变更记录（2026-05-31）

### ReviewPublishDetailPage 重构

| 页面 | 新增组件 | 新增 API 调用 |
|------|----------|---------------|
| `ReviewPublishDetailPage.tsx` | `NoteEditorPanel`, `NotePreviewPanel`, `AgentSummaryPanel`, `ReviewDecisionPanel` | `GET /api/platform-schemas/{platform_id}` |

### 新增子组件清单

| 组件 | 路径 | 职责 |
|------|------|------|
| `NoteEditorPanel` | `components/review/NoteEditorPanel.tsx` | 笔记发布格式编辑器（封面/标题/正文/话题/地点/可见/声明） |
| `NotePreviewPanel` | `components/review/NotePreviewPanel.tsx` | 小红书笔记预览模拟 |
| `AgentSummaryPanel` | `components/review/AgentSummaryPanel.tsx` | Agent 摘要（合规/预演/质量分/再次生成） |
| `ReviewDecisionPanel` | `components/review/ReviewDecisionPanel.tsx` | 审核决策 + 发布确认 |

### TaskHubCreatePage 平台/格式对齐（2026-05-31 第三轮）

| 页面/Store | 变更内容 | 新增 API 调用 |
|------------|----------|---------------|
| `taskHubStore.ts` | 新增 `PlatformSchema` / `ContentFormat` / `FieldConstraint` 接口；新增 `fetchPlatformSchemas()` action | `GET /api/platform-schemas` |
| `TaskHubCreatePage.tsx` | 平台选择动态化；新增内容格式二级选择；智能推荐工作流模板（可手动覆盖） | `GET /api/platform-schemas` |
| `NoteEditorPanel.tsx` | 新增 `platformSchema` / `contentFormat` props；字段约束动态计算 | `GET /api/platform-schemas/{platform_id}` |
| `ReviewPublishDetailPage.tsx` | 传递 `platformSchema` + `contentFormat` 给 `NoteEditorPanel` | - |


### 互动数据跟踪页面（2026-05-31 第四轮）

| 页面 | 路由路径 | 新增 API 调用 | 关键依赖 |
|------|----------|---------------|----------|
| `EngagementTrackingPage.tsx` | `/engagement-tracking` | `GET /api/data-analyst/engagements?status=&limit=&offset=` | `lucide-react`, `authHeaders` |

| 组件 | 路径 | 职责 |
|------|------|------|
| `EngagementTrackingPage` | `pages/EngagementTrackingPage.tsx` | 互动数据列表：点赞/评论/收藏/分享/阅读量展示；状态筛选；分页；关联内容标题和发布链接 |

### 账号数据隔离 + 审核发布 UX 优化（2026-05-31 第五轮）

| Store / 页面 | 变更内容 | 新增 API 字段 / 交互 |
|--------------|----------|----------------------|
| `reviewPublishStore.ts` | `regenerateContent` 返回 `{ success, message }` | `POST /api/review-publish/conclusions/{id}/regenerate` |
| `ReviewPublishDetailPage.tsx` | 新增 `RegenerateModal` + `LoadingOverlay`（3s 强制等待） | `has_primary_approval` 字段消费 |
| `ReviewDecisionPanel.tsx` | 新增 `hasPrimaryApproval` prop；amber 提示卡「等待二次审核」 | `ReviewDetailResponse.has_primary_approval` |

**关键约束**：前端不再发送 `created_by` / `operator` 硬编码字段，后端从 JWT 自动注入。所有 TaskHub / HITL / ReviewPublish / Publisher API 端点已按角色隔离。
