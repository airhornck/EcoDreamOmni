# EcoDream Omni v4.0 — API 接口契约

> **生成日期**: 2026-06-02
> **版本**: v4.0
> **维护者**: 后端 + 架构师
> **定位**: 前后端并行开发的"法律依据"
> **技术实现**: FastAPI 自动生成 OpenAPI（`/api/docs`），本文档为人工维护真源

---

## 一、通用响应格式

所有 API 响应（除 SSE/WebSocket 外）必须遵循以下格式：

```json
{
  "code": "OK",
  "message": "操作成功",
  "data": { ... },
  "trace_id": "req_abc123def456",
  "timestamp": "2026-06-02T10:30:00Z"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `code` | string | 是 | 业务错误码，见 §二 |
| `message` | string | 是 | 用户可读消息（中文） |
| `data` | any | 否 | 业务数据，失败时可为 null |
| `trace_id` | string | 是 | 链路追踪 ID（UUID v4） |
| `timestamp` | string | 是 | ISO 8601 格式 |

**分页响应扩展**：
```json
{
  "code": "OK",
  "message": "查询成功",
  "data": [ ... ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 156,
    "total_pages": 8
  },
  "trace_id": "req_abc123def456",
  "timestamp": "2026-06-02T10:30:00Z"
}
```

---

## 二、全局错误码字典

### 2.1 错误码分类体系

```
错误码格式: [分类前缀]_[具体错误]

1xx ── 信息性（保留）
2xx ── 成功（OK）
4xx ── 客户端错误
5xx ── Agent/Skill 层错误
6xx ── Function 层错误
7xx ── LLM 层错误
8xx ── 工作流/Pipeline 错误
9xx ── 系统错误
```

### 2.2 完整错误码定义

| 错误码 | HTTP 状态 | 中文说明 | 触发场景 | 前端处理建议 |
|--------|----------|---------|---------|------------|
| **2xx 成功** | | | | |
| `OK` | 200 | 操作成功 | 通用成功 | 正常展示 data |
| `CREATED` | 201 | 创建成功 | POST 新建资源 | 跳转详情页或刷新列表 |
| `ACCEPTED` | 202 | 已接受（异步处理） | 提交 Pipeline / 批量任务 | 展示"处理中"状态，轮询或 WebSocket 监听 |
| **4xx 客户端错误** | | | | |
| `VALIDATION_ERROR` | 400 | 参数校验失败 | 请求参数不符合 Schema | 高亮错误字段，展示具体校验信息 |
| `UNAUTHORIZED` | 401 | 未认证 | Token 缺失/过期 | 跳转登录页或刷新 Token |
| `FORBIDDEN` | 403 | 无权限 | RBAC 拒绝 | 展示"无权限"提示，记录审计日志 |
| `NOT_FOUND` | 404 | 资源不存在 | 查询不存在的 ID | 展示 404 页面或"资源不存在"提示 |
| `CONFLICT` | 409 | 资源冲突 | 唯一键冲突 / 并发写入 | 提示用户数据已变更，建议刷新后重试 |
| `RATE_LIMITED` | 429 | 请求过于频繁 | Token Bucket 限流触发 | 展示"操作太频繁"，建议稍后重试 |
| `PAYLOAD_TOO_LARGE` | 413 | 请求体过大 | 上传文件超过限制 | 提示文件大小限制 |
| **5xx Agent/Skill 层错误** | | | | |
| `AGENT_NOT_FOUND` | 500 | Agent 不存在 | 调用未注册的 Agent ID | 记录日志，提示"服务内部错误" |
| `AGENT_DEGRADED` | 503 | Agent 依赖不健康 | Agent 状态为 DEGRADED | 提示"服务暂时不可用"，自动触发 Handoff |
| `AGENT_TIMEOUT` | 504 | Agent 执行超时 | Agent 执行超过 timeout_seconds | 提示"处理超时"，提供"重试"按钮 |
| `SKILL_NOT_FOUND` | 500 | Skill 不存在 | 调用未注册的 Skill ID | 记录日志，提示"服务内部错误" |
| `SKILL_EXECUTION_ERROR` | 500 | Skill 执行失败 | Skill 内部异常 | 展示 Skill 返回的错误摘要 |
| `SKILL_NOT_BOUND` | 403 | Skill 未绑定到 Agent | Agent 无权调用该 Skill | 记录日志，提示"服务内部错误" |
| **6xx Function 层错误** | | | | |
| `FUNCTION_NOT_FOUND` | 500 | Function 不存在 | 调用未注册的 Function | 记录日志 |
| `FUNCTION_UNAVAILABLE` | 503 | Function 服务不可用 | Function 依赖（如第三方 API）故障 | 提示"部分服务暂不可用"，读取缓存版本 |
| `DATA_INTEGRITY_ERROR` | 500 | 数据完整性错误 | 数据库约束违反 / 外键不存在 | 记录日志，提示"数据异常" |
| **7xx LLM 层错误** | | | | |
| `LLM_MODEL_UNAVAILABLE` | 503 | LLM 模型不可用 | 模型服务宕机 / 供应商限流 | 自动切换兜底模型，前端无感知 |
| `LLM_RATE_LIMITED` | 429 | LLM 限流 | 供应商返回 429 | 指数退避重试，展示"AI 思考中..." |
| `LLM_CONTENT_FILTERED` | 400 | 内容被模型过滤 | 触发供应商内容安全策略 | 提示"生成内容包含敏感信息，请调整输入" |
| `LLM_CONTEXT_OVERFLOW` | 400 | 上下文超限 | Prompt 超过模型上下文窗口 | 自动截断非关键上下文，记录日志 |
| `LLM_COST_EXCEEDED` | 429 | LLM 成本超限 | 单任务 Token 消耗超过预算 | 提示"当前任务消耗过大，建议简化" |
| **8xx 工作流/Pipeline 错误** | | | | |
| `WORKFLOW_NOT_FOUND` | 404 | 工作流模板不存在 | 引用不存在的 template_id | 提示"模板不存在" |
| `WORKFLOW_INVALID_STATE` | 400 | 工作流状态非法 | 在不允许的状态下触发操作 | 提示"当前状态不允许此操作" |
| `WORKFLOW_NODE_FAILED` | 500 | 工作流节点执行失败 | Pipeline 节点执行异常 | 展示失败节点信息，提供"重试/跳过/终止"选项 |
| `WORKFLOW_NODE_TIMEOUT` | 504 | 工作流节点超时 | 节点执行超过 timeout | 提示"节点处理超时"，提供"重试"选项 |
| `HUMAN_APPROVAL_TIMEOUT` | 408 | 人工审核超时 | HITL 节点超过等待时间 | 自动按默认策略处理（FAIL / CONTINUE） |
| `CHECKPOINT_CORRUPTED` | 500 | Checkpoint 损坏 | 恢复时发现 Checkpoint 数据不完整 | 从上一个有效 Checkpoint 恢复 |
| **9xx 系统错误** | | | | |
| `INTERNAL_ERROR` | 500 | 内部服务器错误 | 未捕获的异常 | 记录详细日志，提示"服务内部错误" |
| `SERVICE_UNAVAILABLE` | 503 | 服务不可用 | 数据库连接失败 / Redis 故障 | 提示"服务暂时不可用"，展示预计恢复时间 |
| `TIMEOUT` | 504 | 网关超时 | Nginx/ALB 超时 | 提示"网络超时，请稍后重试" |

### 2.3 错误响应示例

```json
// 参数校验失败
{
  "code": "VALIDATION_ERROR",
  "message": "标题不能为空，且长度不超过20字",
  "data": {
    "field_errors": [
      {"field": "title", "message": "标题不能为空"},
      {"field": "title", "message": "标题长度不能超过20字"}
    ]
  },
  "trace_id": "req_abc123def456",
  "timestamp": "2026-06-02T10:30:00Z"
}

// Agent 降级
{
  "code": "AGENT_DEGRADED",
  "message": "ContentForge Agent 依赖不健康，已自动切换备用实例",
  "data": {
    "agent_id": "content_forge_001",
    "status": "DEGRADED",
    "fallback_agent_id": "content_forge_002"
  },
  "trace_id": "req_abc123def456",
  "timestamp": "2026-06-02T10:30:00Z"
}
```

---

## 三、全局枚举值定义

### 3.1 平台枚举

| 枚举值 | 显示名称 | 说明 |
|--------|---------|------|
| `xhs` | 小红书 | 图文笔记 + 视频 |
| `douyin` | 抖音 | 短视频 + 图文 |
| `wechat_official` | 微信公众号 | 图文消息 + 视频 |
| `bilibili` | 哔哩哔哩 | 视频 + 图文 + 专栏 |

### 3.2 内容类型枚举

| 枚举值 | 说明 | 关联平台 |
|--------|------|---------|
| `note_image` | 图文笔记 | xhs, bilibili |
| `note_video` | 视频笔记 | xhs |
| `video_short` | 短视频 | douyin |
| `video_clone` | 视频克隆 | douyin, bilibili |
| `video_original` | 原创视频 | douyin, bilibili |
| `long_article` | 长文章 | wechat_official |
| `text_only` | 纯文本 | wechat_official |

### 3.3 Agent 状态枚举

| 枚举值 | 说明 | 转换条件 |
|--------|------|---------|
| `REGISTERED` | 已注册 | AgentHub 注册成功 |
| `ACTIVE` | 活跃中 | 配置版本激活 + 依赖健康 |
| `DEGRADED` | 降级运行 | 依赖检测失败 / 连续错误率 > 阈值 |
| `PAUSED` | 已暂停 | 人工暂停 / 审批流中 |
| `OFFLINE` | 已离线 | 心跳缺失 > 3 周期 / 人工标记 |

### 3.4 Pipeline 状态枚举

| 枚举值 | 说明 |
|--------|------|
| `PENDING` | 等待执行 |
| `RUNNING` | 执行中 |
| `PAUSED` | 已暂停（人工/断点） |
| `COMPLETED` | 已完成 |
| `FAILED` | 执行失败 |

### 3.5 节点状态枚举

| 枚举值 | 说明 |
|--------|------|
| `SUCCESS` | 执行成功 |
| `FAILED` | 执行失败 |
| `SKIPPED` | 已跳过（条件不满足） |
| `TIMEOUT` | 执行超时 |

### 3.5a 节点类型枚举（v4.0 Phase 4 新增 SKILL）

| 枚举值 | 说明 |
|--------|------|
| `AGENT` | Agent 执行节点 |
| `HUMAN_APPROVAL` | 人工审核节点（HITL） |
| `TIMER` | 定时等待节点 |
| `SKILL` | Skill 调用节点（v4.0 新增） |

### 3.6 ContentDraft 状态枚举

| 枚举值 | 说明 | 可操作 |
|--------|------|--------|
| `IDLE` | 空闲 | 编辑、删除 |
| `GENERATING` | AI 生成中 | 取消、查看进度 |
| `REVIEWING` | 审核中 | 查看、驳回、通过 |
| `ITERATING` | 迭代修改中 | 继续编辑、放弃 |
| `APPROVED` | 已通过 | 发布、定时发布 |
| `PUBLISHED` | 已发布 | 查看数据、归档 |
| `ARCHIVED` | 已归档 | 查看、恢复 |

### 3.7 编排模式枚举

| 枚举值 | 说明 | 委托层 |
|--------|------|--------|
| `PIPELINE` | 固定 DAG 模式 | Pipeline 层 |
| `SWARM` | 批量并行模式 | Worker 层 |
| `DYNAMIC` | 动态 Agent 生成 | 编排层内部 |
| `DIRECT` | 直接调用 | Pipeline 层 |

### 3.8 Skill 模态枚举

| 枚举值 | 说明 | 示例模型 |
|--------|------|---------|
| `text` | 文本生成/理解 | qwen-max, gpt-4o |
| `image` | 图片生成/理解 | 百炼通义万相, DALL-E-3 |
| `video` | 视频生成/理解 | 可灵, Runway |
| `audio` | 音频生成/理解 | — |
| `embedding` | 文本向量化 | BGE-M3, text-embedding-3 |
| `multimodal` | 多模态融合 | qwen-vl-max, gpt-4o-vision |

### 3.9 记忆分层枚举

| 枚举值 | 存储 | TTL | 访问延迟 |
|--------|------|-----|---------|
| `ephemeral` | Redis | 5 min | < 1 ms |
| `working` | PostgreSQL | 7 days | 5-20 ms |
| `semantic` | pgvector | 永久 | 50-200 ms |
| `archive` | S3/OSS | 永久 | 1-5 s |

---

## 四、v4.0 新增 API 契约

### 4.1 PlatformContentTypeStyle API

**基础路径**: `/api/v2/platform-content-type-styles`

#### `GET /api/v2/platform-content-type-styles`

列出当前租户的所有平台内容类型风格。

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `platform_id` | string | 否 | 按平台过滤 |
| `content_type` | string | 否 | 按内容类型过滤 |
| `status` | string | 否 | 按状态过滤 |
| `page` | int | 否 | 页码，默认 1 |
| `page_size` | int | 否 | 每页数量，默认 20 |

**响应**: `PaginatedResponse`
```json
{
  "code": "OK",
  "message": "查询成功",
  "data": [
    {
      "style_id": "style_xhs_note_001",
      "tenant_id": "tenant_abc",
      "platform_id": "xhs",
      "content_type": "note_image",
      "content_dna": {"hook_types": ["反差", "痛点"], "structure_patterns": ["hook-body-cta"]},
      "default_prompt_fragments": ["语气亲切自然，像朋友聊天"],
      "recommended_keywords": {"high_performing": ["养宠攻略"], "trending": ["科学养宠"]},
      "tone_preset": {"formality": 0.3, "enthusiasm": 0.8, "urgency": 0.5, "empathy": 0.9},
      "structure_template": {"paragraphs": 3, "paragraph_1": "hook", "paragraph_2": "body", "paragraph_3": "cta"},
      "avg_engagement_rate": 0.0856,
      "sample_count": 128,
      "is_ai_generated": true,
      "source_template_ids": ["tmpl_001", "tmpl_002"],
      "status": "active",
      "created_by": "user_001",
      "created_at": "2026-06-02T10:30:00Z",
      "updated_at": "2026-06-02T10:30:00Z"
    }
  ],
  "pagination": {"page": 1, "page_size": 20, "total": 1, "total_pages": 1},
  "trace_id": "req_abc123",
  "timestamp": "2026-06-02T10:30:00Z"
}
```

#### `POST /api/v2/platform-content-type-styles`

创建新的平台内容类型风格。

**请求体**:
```json
{
  "platform_id": "xhs",
  "content_type": "note_image",
  "content_dna": {"hook_types": ["反差"], "structure_patterns": ["hook-body-cta"]},
  "default_prompt_fragments": ["语气亲切自然"],
  "recommended_keywords": {"high_performing": [], "trending": [], "seasonal": []},
  "tone_preset": {"formality": 0.3, "enthusiasm": 0.8, "urgency": 0.5, "empathy": 0.9},
  "structure_template": {"paragraphs": 3, "paragraph_1": "hook", "paragraph_2": "body", "paragraph_3": "cta"},
  "status": "active"
}
```

**响应**: `BaseResponse` (code: CREATED)

#### `GET /api/v2/platform-content-type-styles/{style_id}`

获取单个风格详情。

**响应**: `BaseResponse`

#### `PATCH /api/v2/platform-content-type-styles/{style_id}`

部分更新风格。

**请求体**: 同 POST，所有字段可选

**响应**: `BaseResponse`

#### `DELETE /api/v2/platform-content-type-styles/{style_id}`

删除风格（软删除，status → deprecated）。

**响应**: `BaseResponse` (code: OK)

---

### 4.2 ContentTemplate API

**基础路径**: `/api/v2/content-templates`

#### `GET /api/v2/content-templates`

列出当前租户的所有内容模板。

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `platform_content_type_style_id` | string | 否 | 按风格过滤 |
| `status` | string | 否 | 按状态过滤 |
| `page` | int | 否 | 页码，默认 1 |
| `page_size` | int | 否 | 每页数量，默认 20 |

**响应**: `PaginatedResponse`
```json
{
  "code": "OK",
  "message": "查询成功",
  "data": [
    {
      "template_id": "tmpl_001",
      "tenant_id": "tenant_abc",
      "source_platform_id": "xhs",
      "source_content_url": "https://www.xiaohongshu.com/...",
      "source_content_id": "note_abc123",
      "extracted_structure": {"hook_pattern": "痛点反问", "body_structure": "故事线", "cta_pattern": "互动提问"},
      "prompt_template": "你是一个宠物博主，请根据以下结构生成内容：\n{{hook}}\n{{body}}\n{{cta}}",
      "variables": [
        {"name": "hook", "label": "钩子", "type": "text", "default_value": ""},
        {"name": "body", "label": "正文", "type": "text", "default_value": ""},
        {"name": "cta", "label": "号召", "type": "text", "default_value": ""}
      ],
      "engagement_benchmark": {"likes": 1200, "comments": 89, "saves": 456, "shares": 23},
      "platform_content_type_style_id": "style_xhs_note_001",
      "created_by": "ai",
      "usage_count": 15,
      "avg_generated_engagement": {"likes": 800, "comments": 56, "saves": 320},
      "status": "active",
      "created_at": "2026-06-02T10:30:00Z",
      "updated_at": "2026-06-02T10:30:00Z"
    }
  ],
  "pagination": {"page": 1, "page_size": 20, "total": 1, "total_pages": 1},
  "trace_id": "req_abc123",
  "timestamp": "2026-06-02T10:30:00Z"
}
```

#### `POST /api/v2/content-templates`

创建新的内容模板。

**请求体**:
```json
{
  "source_platform_id": "xhs",
  "source_content_url": "https://...",
  "source_content_id": "note_abc123",
  "extracted_structure": {"hook_pattern": "痛点反问", "body_structure": "故事线", "cta_pattern": "互动提问"},
  "prompt_template": "你是一个宠物博主...",
  "variables": [{"name": "hook", "label": "钩子", "type": "text", "default_value": ""}],
  "engagement_benchmark": {"likes": 1200, "comments": 89, "saves": 456, "shares": 23},
  "platform_content_type_style_id": "style_xhs_note_001",
  "status": "active"
}
```

**响应**: `BaseResponse` (code: CREATED)

#### `GET /api/v2/content-templates/{template_id}`

获取单个模板详情。

**响应**: `BaseResponse`

#### `PATCH /api/v2/content-templates/{template_id}`

部分更新模板。

**请求体**: 同 POST，所有字段可选

**响应**: `BaseResponse`

#### `DELETE /api/v2/content-templates/{template_id}`

删除模板（软删除，status → deprecated）。

**响应**: `BaseResponse` (code: OK)

### 4.3 Meta-Orchestrator API

**基础路径**: `/api/v2/orchestrator`

Meta-Orchestrator 是 v4.0 新增的元编排层，**只决策不执行**。负责意图分类、任务分解、动态路由和 Blackboard 状态协调。

#### `POST /api/v2/orchestrator/intent`

**请求体**:
```json
{
  "query": "帮我生成一篇关于猫咪驱虫的小红书笔记",
  "context": {"tenant_id": "tenant_abc", "user_id": "user_001"}
}
```

**响应**:
```json
{
  "code": "OK",
  "data": {
    "intent": "content_creation",
    "confidence": 0.92,
    "sub_intents": ["content_draft", "image_suggestion"],
    "raw_analysis": "用户请求生成内容，涉及文案撰写和图片建议"
  }
}
```

**意图类型枚举**:
| 意图 | 说明 |
|------|------|
| `content_creation` | 内容创作（文案/图片/视频脚本） |
| `data_analysis` | 数据分析（战报/趋势/账号诊断） |
| `account_management` | 账号管理（发布/排期/账号健康） |
| `system_query` | 系统查询（配置/状态/帮助） |

#### `POST /api/v2/orchestrator/decompose`

将已分类的意图分解为可执行的 Todo 列表。

**请求体**:
```json
{
  "intent": "content_creation",
  "context": {"platform": "xhs", "topic": "猫咪驱虫"},
  "sop_template_id": "sop_content_v1"
}
```

**响应**:
```json
{
  "code": "OK",
  "data": {
    "todos": [
      {"id": "td_1", "description": "研究主题关键词", "skill_id": "research", "depends_on": []},
      {"id": "td_2", "description": "生成文案草稿", "skill_id": "draft_writer", "depends_on": ["td_1"]},
      {"id": "td_3", "description": "生成配图建议", "skill_id": "image_suggester", "depends_on": ["td_2"]}
    ],
    "estimated_duration_ms": 15000
  }
}
```

#### `POST /api/v2/orchestrator/route`

根据意图和任务特征选择编排模式。

**请求体**:
```json
{
  "intent": "content_creation",
  "todo_count": 5,
  "priority": "high",
  "requires_realtime": false
}
```

**响应**:
```json
{
  "code": "OK",
  "data": {
    "mode": "PIPELINE",
    "reason": "顺序依赖任务，适合 Pipeline 模式",
    "allowed_modes": ["PIPELINE", "SWARM", "DYNAMIC", "DIRECT"]
  }
}
```

**编排模式枚举**:
| 模式 | 说明 | 适用场景 |
|------|------|---------|
| `PIPELINE` | 线性流水线，顺序执行 | 有依赖关系的任务链 |
| `SWARM` | 蜂群模式，并行执行 | 无依赖的独立子任务 |
| `DYNAMIC` | 动态模式，运行时决策 | 复杂场景，需中途调整 |
| `DIRECT` | 直达模式，单 Agent 执行 | 简单查询或单技能调用 |

#### `GET /api/v2/orchestrator/blackboard/{session_id}`

查询 Blackboard 共享状态。

**响应**:
```json
{
  "code": "OK",
  "data": {
    "session_id": "sess_abc123",
    "entries": {
      "intent": {"value": "content_creation", "updated_at": "..."},
      "todos": {"value": [...], "updated_at": "..."},
      "mode": {"value": "PIPELINE", "updated_at": "..."}
    },
    "agents": ["agt_001", "agt_002"]
  }
}
```

---

## 五、LLM Hub 接口（v4.0 Phase 5 新增）

### 5.1 模型路由接口

#### `POST /api/v1/llm-hub/route`

根据模态自动选择最优模型。国内模型优先，不可用时切换海外兜底。

**请求体**:
```json
{
  "modality": "text",
  "preferred_provider": "openai",
  "node_id": "router_node_001"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `modality` | string | 是 | 模态类型：`text` / `image` / `video` / `embedding` / `multimodal` |
| `preferred_provider` | string | 否 | 优先供应商，如 `openai` / `deepseek` |
| `node_id` | string | 否 | 路由节点标识，用于审计日志 |

**响应**:
```json
{
  "code": "OK",
  "data": {
    "model_id": "mdl_abc123",
    "provider": "deepseek",
    "model_name": "deepseek-chat",
    "region": "domestic",
    "cross_border_risk": false,
    "reason": "domestic_available"
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `model_id` | string | 模型唯一 ID |
| `provider` | string | 供应商名称 |
| `model_name` | string | 模型名称 |
| `region` | string | 区域：`domestic` / `overseas` |
| `cross_border_risk` | boolean | 是否为跨境调用（海外兜底时为 true） |
| `reason` | string | 路由决策原因 |

**错误响应**:
- `400` — `modality` 不合法
- `404` — 无可用模型支持该模态
- `503` — `LLM_MODEL_UNAVAILABLE` — 所有候选模型不可用

### 5.2 模型管理接口（Schema 扩展）

以下接口在 v4.0 Phase 5 中扩展了 `modality_support` 字段：

| 接口 | 变更 |
|------|------|
| `POST /api/v1/llm-hub/models` | 请求体新增 `modality_support: Dict[str, bool]` |
| `PATCH /api/v1/llm-hub/models/:id` | 支持更新 `modality_support` |
| `GET /api/v1/llm-hub/models` | 响应中每个模型包含 `modality_support` |

**`modality_support` 示例**:
```json
{
  "text": true,
  "image": false,
  "video": false,
  "embedding": true,
  "multimodal": false
}
```

---

## 六、MCP Gateway 接口（v4.0 Phase 5 预留）

> **状态**: 接口已定义，返回 `501 Not Implemented`，Phase 2 正式实现。

### 6.1 服务端点

#### `POST /api/v1/mcp-gateway/servers`

注册 MCP Server。

**请求体**:
```json
{
  "name": "weather-server",
  "url": "http://localhost:3001/sse",
  "description": "天气查询 MCP Server"
}
```

**响应** (`501`):
```json
{
  "status": "not_implemented",
  "error": "MCP Gateway 将在 Phase 2 实现"
}
```

#### `GET /api/v1/mcp-gateway/servers/{server_id}/tools`

发现 Server 提供的 Tools。

**响应** (`501`):
```json
{
  "status": "not_implemented",
  "error": "MCP Gateway 将在 Phase 2 实现"
}
```

#### `POST /api/v1/mcp-gateway/tools/call`

调用 MCP Tool。

**请求体**:
```json
{
  "server_id": "weather-server",
  "tool_name": "get_weather",
  "arguments": { "city": "北京" }
}
```

**响应** (`501`):
```json
{
  "status": "not_implemented",
  "error": "MCP Gateway 将在 Phase 2 实现"
}
```

### 6.2 实验室 端点（v4.0 Phase 6 新增）

#### `POST /api/v1/lab/parse`

解析爆款内容，提取结构特征。

**请求体**:
```json
{
  "url": "https://www.xiaohongshu.com/...",
  "text": "（可选，直接粘贴文案）",
  "screenshot": "（可选，base64 图片）"
}
```

**响应**:
```json
{
  "code": "OK",
  "data": {
    "hook_pattern": "痛点反问式开场",
    "body_structure": "问题描述 → 解决方案 → 使用体验 → 效果对比",
    "cta_pattern": "引导评论互动 + 收藏暗示",
    "tone": "亲切/专业",
    "keywords": ["驱虫", "狗狗", "省钱", "养宠"]
  }
}
```

#### `POST /api/v1/lab/generate`

基于模板和变量一键生成内容。

**请求体**:
```json
{
  "template_id": "tmpl_001",
  "variables": {
    "persona": "省钱狗爸",
    "problem": "狗狗驱虫贵",
    "solution": "平价驱虫药",
    "pet_name": "豆豆",
    "duration": "3个月",
    "effect": "非常好"
  }
}
```

**响应**:
```json
{
  "code": "OK",
  "data": {
    "title": "【豆豆驱虫攻略】平价方案大揭秘",
    "body": "作为一名省钱狗爸，我发现很多铲屎官都在为狗狗驱虫贵烦恼...",
    "hashtags": ["驱虫", "养狗", "省钱攻略", "宠物健康"]
  }
}
```

#### `GET /api/v1/lab/templates`

获取预设 ContentTemplate 列表。

**响应**:
```json
{
  "code": "OK",
  "data": [
    {
      "id": "tmpl_001",
      "name": "驱虫种草模板",
      "prompt_template": "作为一名{{persona}}，我发现...",
      "variables": [
        { "key": "persona", "label": "人设", "default_value": "省钱狗爸" }
      ]
    }
  ]
}
```

#### `POST /api/v1/lab/analyze` ⭐ 增强分析模式新增

爆款笔记深度分析（LLM 主路径 + 规则校准）。

**请求体**:
```json
{
  "title": "猫咪驱虫避坑指南，这3个误区90%的人都不知道",
  "content": "作为一个养了3年猫的铲屎官...",
  "cover_image_url": "https://...",
  "category": "宠物健康",
  "tags": ["驱虫", "新手养猫"],
  "metrics": { "likes": 12500, "collects": 3400, "comments": 890 }
}
```

**响应**:
```json
{
  "code": "OK",
  "data": {
    "note_id": "note_abc123",
    "structure_type": "避坑排雷型",
    "structure_confidence": 0.87,
    "viral_score": 82,
    "scoring_breakdown": {
      "completeness": 35,
      "keyword_richness": 28,
      "emotion_curve": 18,
      "interaction_weight": 12,
      "emoji_strategy": 8
    },
    "keyword_matches": {
      "structure": [{"keyword": "避坑", "position": 5, "weight": 1.2}],
      "function": [{"keyword": "指南", "position": 8, "weight": 1.0}],
      "emotion": [{"keyword": "焦虑", "position": 45, "weight": 0.9, "intensity": 0.7}],
      "industry": [{"keyword": "驱虫", "position": 2, "weight": 1.5}],
      "effect": [{"keyword": "省钱", "position": 120, "weight": 1.1}]
    },
    "title_analysis": {"pattern": "痛点+数字+结果", "contains_number": true, "length": 18},
    "hook_analysis": {"hook_type": "身份认同式", "effectiveness": 0.75},
    "body_analysis": {"sections": 4, "has_story": true, "has_data": false},
    "cta_analysis": {"cta_type": "互动引导", "effectiveness": 0.68},
    "emoji_analysis": {"emoji_count": 8, "emoji_density": "2.1/100字"},
    "emotion_curve": [
      {"segment": 0, "emotion": "焦虑", "intensity": 0.8},
      {"segment": 1, "emotion": "信任", "intensity": 0.6},
      {"segment": 2, "emotion": "惊喜", "intensity": 0.7},
      {"segment": 3, "emotion": "共鸣", "intensity": 0.75}
    ],
    "success_factors": [
      "标题含具体数字，提升点击率",
      "开篇建立身份认同，增强信任",
      "使用 emoji 标记重点，提升可读性"
    ]
  }
}
```

#### `POST /api/v1/lab/template` ⭐ 增强分析模式新增

从分析报告生成 ContentTemplate 草稿。

**请求体**:
```json
{
  "analysis_report": { /* 完整 AnalysisReport 对象 */ },
  "template_name": "驱虫避坑模板"
}
```

**响应**:
```json
{
  "code": "OK",
  "data": {
    "template_id": "tmpl_draft_001",
    "name": "驱虫避坑模板",
    "source": "viral_analyzer",
    "source_content_id": "note_abc123",
    "structure_type": "避坑排雷型",
    "prompt_template": "作为一个养了{{养宠年限}}年{{宠物类型}}的{{人设}}...",
    "variables": [
      {"name": "养宠年限", "label": "养宠年限", "type": "number", "default_value": "3"},
      {"name": "宠物类型", "label": "宠物类型", "type": "text", "default_value": "猫"}
    ],
    "constraints": {
      "title_length": [10, 30],
      "body_section_min": 3,
      "emoji_density": "2-3/100字",
      "hook_length": [20, 60]
    }
  }
}
```

#### `GET /api/v1/lab/keywords` ⭐ 增强分析模式新增

查询关键词库（供前端高亮配色）。

**查询参数**: `?dimension=structure&structure_type=避坑排雷型`

**响应**:
```json
{
  "code": "OK",
  "data": {
    "keywords": [
      {"keyword": "避坑", "dimension": "structure", "weight": 1.2, "color": "#3B82F6"},
      {"keyword": "误区", "dimension": "structure", "weight": 1.1, "color": "#3B82F6"},
      {"keyword": "指南", "dimension": "function", "weight": 1.0, "color": "#10B981"}
    ]
  }
}
```

#### `GET /api/v1/lab/categories` ⭐ 增强分析模式新增

获取赛道分类列表（复用现有分类枚举）。

**响应**:
```json
{
  "code": "OK",
  "data": ["宠物健康", "新手养猫", "省钱攻略", "宠物食品", "宠物用品"]
}
```

---

## 七、接口幂等性规范

### 7.1 幂等性要求矩阵

| HTTP Method | 幂等性要求 | 实现方式 | 示例 |
|-------------|-----------|---------|------|
| `GET` | 天然幂等 | 无 | `GET /contents` |
| `PUT` | 必须幂等 | 全量替换 | `PUT /contents/:id` |
| `DELETE` | 必须幂等 | 重复删除返回 OK | `DELETE /contents/:id` |
| `PATCH` | 建议幂等 | 基于状态的增量更新 | `PATCH /contents/:id/status` |
| `POST` | **非幂等** | 需显式处理 | `POST /contents` |

### 7.2 非幂等 POST 接口的幂等性实现

**方案：Idempotency-Key 请求头**

```
POST /api/v1/contents
Headers:
  X-Idempotency-Key: uuid-v4-generated-by-client
  Content-Type: application/json

Body:
  { "title": "...", "body": "..." }
```

**服务端行为**：
1. 检查 Redis：`idempotency:{key}` 是否存在
2. 存在 → 返回缓存的响应（不重复执行）
3. 不存在 → 执行业务逻辑 → 将响应缓存到 Redis（TTL 24h）→ 返回响应

**适用接口**：
- `POST /api/v1/contents` — 创建内容
- `POST /api/v1/tasks` — 创建任务
- `POST /api/v1/lab/generate` — 一键生成
- `POST /api/v1/publisher/publish` — 发布内容
- `POST /api/v1/ai/conversations/:id/messages` — AI 对话消息

### 7.3 幂等性响应规范

```json
// 首次请求
{
  "code": "CREATED",
  "message": "创建成功",
  "data": { "content_id": "cnt_abc123" },
  "trace_id": "req_001",
  "idempotency_key": "idem_xyz789"
}

// 重复请求（相同 Idempotency-Key）
{
  "code": "OK",
  "message": "请求已处理，返回缓存结果",
  "data": { "content_id": "cnt_abc123" },
  "trace_id": "req_002",
  "idempotency_key": "idem_xyz789",
  "cached": true
}
```

---

## 八、接口限流规范

### 8.1 限流层级

```
┌─────────────────────────────────────────────┐
│              三层限流架构                      │
├─────────────────────────────────────────────┤
│                                             │
│  L1: 网关层（Nginx/ALB）                     │
│  ├── 按 IP 限流：100 req/min                 │
│  └── 按路径限流：/api/v1/ai/stream 10 req/min│
│                                             │
│  L2: 应用层（FastAPI Middleware）            │
│  ├── 按租户限流：1,000 req/min/tenant        │
│  └── 按用户限流：100 req/min/user            │
│                                             │
│  L3: 业务层（Agent SDK Token Bucket）        │
│  ├── 按 Agent 限流：50 req/min/agent         │
│  ├── 按 Skill 限流：30 req/min/skill         │
│  └── 按 Model 限流：20 req/min/model         │
│                                             │
└─────────────────────────────────────────────┘
```

---

## 九、Agent-任务接口契约（v4.0 Agent-First 重构新增）

> **变更背景**：任务创建从「工作流模板驱动」升级为「Agent 驱动」。
> `workflow_template_id` 降级为 Agent 内部元数据，不再由前端传入。

### 9.0 Agent 查询与推荐

#### GET /api/agents — 查询可用 Agent 列表

```yaml
GET /api/agents
  query:
    platform: str = null          # 按平台筛选，如 "xiaohongshu"
    format: str = null            # 按格式筛选，如 "图文"
    capability: str = null        # 按能力标签筛选
    status: str = "ACTIVE"        # 按状态筛选
    recommended: bool = false     # 是否只返回推荐 Agent
  response: BaseResponse
    data: [{
      id: str,                    # 如 "content_forge_xhs_image"
      name: str,                  # "小红书图文生成 Agent"
      role: str,                  # "content_generation"
      description: str,
      avatar_url: str | null,
      skills: [str],
      supported_platforms: [str],
      supported_formats: [str],
      success_rate: float,        # 0.0 ~ 1.0
      recent_tasks_1h: int,
      status: str,               # "ACTIVE" | "DEGRADED" | "OFFLINE"
      created_at: str,
      updated_at: str
    }]
```

#### GET /api/agents/recommend — 智能推荐 Agent

```yaml
GET /api/agents/recommend
  query:
    platform: str                # 必填
    format: str                  # 必填
    persona_id: str = null       # 可选
    account_id: str = null       # 可选
  response: BaseResponse
    data: {
      recommended_agent_id: str,
      confidence: float,          # 0.0~1.0
      reason: str,                # 推荐理由（自然语言）
      alternatives: [{
        agent_id: str,
        name: str,
        confidence: float,
        reason: str
      }],
      matched_capabilities: [str]
    }
```

**推荐算法权重设计（v4.0 确认版）**：

```
综合评分 = 全局成功率 × 0.40
         + Persona 历史偏好 × 0.30
         + 负载均衡因子 × 0.20
         + 账号历史偏好 × 0.10
```

| 因子 | 权重 | 计算方式 |
|------|------|----------|
| 全局成功率 | 40% | Agent 最近 24h 成功率 `success_rate` |
| Persona 历史偏好 | 30% | 该 Persona 近 30 天使用此 Agent 的次数 + 成功率；次数越多、成功率越高，权重越大（上限 10 次达到满加成） |
| 负载均衡因子 | 20% | `1 - recent_tasks_1h / max_concurrent_tasks`，负载越低得分越高 |
| 账号历史偏好 | 10% | 该账号近 30 天使用此 Agent 的成功率 |

**推荐理由生成规则**：
- 若 Persona 历史使用次数 > 5："该 Persona 过去 30 天使用过此 Agent X 次，成功率 Y%"
- 若负载较低（recent_tasks_1h < 5）：附加"当前负载较低，响应更快"
- 默认："此 Agent 最近 24 小时成功率 X%"

### 9.1 任务创建（Agent-First 重构）

#### POST /api/task-hub/tasks — 创建任务

```yaml
POST /api/task-hub/tasks
  request:
    name: str
    agent_id: str                    # ★ 新增，必填
    # workflow_template_id: str      # ★ 移除，不再由前端传入
    account_id: str
    persona_id: str
    platform: str
    content_format: str
    priority: int = 50
    prompt_variables: Dict = {}     # Agent 声明的变量
    persona_story_id: str = null
    node_id: str = null
    content_series_id: str = null
    new_series_name: str = null
    scheduled_at: datetime = null
    cron_schedule: str = null
  
  response: BaseResponse
    data: {
      task_id: str,
      status: str,
      agent_id: str,
      agent_name: str,
      estimated_completion_at: datetime | null
    }
  
  errors:
    - code: "AGENT_NOT_FOUND"        # agent_id 不存在
    - code: "AGENT_NOT_SUPPORTED"    # Agent 不支持该平台/格式
    - code: "AGENT_DEGRADED"        # Agent 状态不健康，已自动切换备用
```

#### GET /api/task-hub/tasks — 任务列表（扩展）

```yaml
GET /api/task-hub/tasks
  query:
    status: str = null
    platform: str = null
    agent_id: str = null            # ★ 新增，按 Agent 筛选
  response: BaseResponse
    data: [{
      # ... 现有字段 ...
      agent_id: str | null,         # ★ 新增
      agent_name: str | null,       # ★ 新增（JOIN agents 表）
      # workflow_template_name 保留但标记 deprecated
    }]
```

---

## 十、内容生产 API 契约（v4.0 Step 2 冻结 — 2026-06-05）

> **关联文档**: `docs/后端需求/后端需求补充_内容生产_Copilot-Driven_2026-06-05.md`  
> **页面**: `/generate`（Mode C: Hybrid）  
> **子页面**: 看板 `/generate`、创建向导 `/generate/create`、编辑器 `/generate/editor/:taskId`

### 10.1 已有 API 扩展（`copilot_*` 字段）

#### GET /api/task-hub/tasks — 看板任务列表

**响应扩展**:
```yaml
response: BaseResponse
  data:
    items: [TaskItem]
    copilot_summary:
      kanban_stats: {draft: int, reviewing: int, approved: int, published: int}
      recommended_focus: str          # "draft" | "reviewing" | "approved"
      ai_insight: str                 # 自然语言洞察
      suggested_actions: [{type: str, label: str, reason: str}]
```

#### GET /api/task-hub/tasks/{id} — 任务详情

**响应扩展**:
```yaml
response: BaseResponse
  data:
    # ... 现有字段 ...
    copilot_context:
      editor_suggestions: [
        {type: str, confidence: float, reason: str, suggested_title: str | null, suggested_tags: [str] | null}
      ]
      save_status: str                 # "saved" | "unsaved_changes" | "saving"
      recommended_next: str            # "save_draft" | "submit_review" | "regenerate"
      generation_progress: {layer: str, progress: float} | null
```

#### POST /api/task-hub/tasks — 创建任务

**响应扩展**:
```yaml
response: BaseResponse
  data:
    task_id: str
    status: str
    agent_id: str
    agent_name: str
    estimated_completion_at: datetime | null
  copilot_followup:
    message: str
    suggested_cards: [CopilotActionCard]
```

### 10.2 新增 API

#### POST /api/ai/copilot/regenerate-content — Copilot 驱动重新生成

```yaml
POST /api/ai/copilot/regenerate-content
  request:
    task_id: str
    style_option: str = "casual"      # casual | professional | humorous
    length_option: str = "medium"     # short | medium | long
    tone_option: str = "friendly"     # friendly | serious | playful
    prompt_variables: Dict = {}
    copilot_suggested: bool = false
    card_id: str = null
  response: BaseResponse
    data:
      job_id: str
      task_id: str
      status: str                      # queued | running | completed | failed
      estimated_seconds: int
    copilot_followup:
      message: str
      suggested_cards: [CopilotActionCard]
  errors:
    - code: "AGENT_NOT_SUPPORTED"      # Agent 不支持该风格选项
    - code: "GENERATION_IN_PROGRESS"   # 已有生成任务在执行
```

#### POST /api/ai/copilot/save-and-submit — 保存并提交审核

```yaml
POST /api/ai/copilot/save-and-submit
  request:
    task_id: str
    title: str
    body: str
    hashtags: [str] = []
    media_urls: [str] = []
    copilot_suggested: bool = false
    card_id: str = null
  response: BaseResponse
    data:
      task_id: str
      status: str                      # reviewing
      content_version: int
      submitted_at: datetime
    copilot_followup:
      message: str
      suggested_cards: [CopilotActionCard]
  errors:
    - code: "TASK_ALREADY_SUBMITTED"   # 任务已提交审核
    - code: "VALIDATION_ERROR"         # 标题/正文为空或超长度限制
```

### 10.3 WebSocket 事件（内容生产专属）

| 事件名 | 方向 | 触发场景 | Payload |
|--------|------|---------|---------|
| `content.generation.progress` | S→C | 内容生成进度更新 | `{task_id, progress: 0.6, layer: "Layer 5: Persona"}` |
| `content.regeneration.complete` | S→C | 重新生成完成 | `{task_id, job_id, new_content: {...}}` |
| `content.save_status` | S→C | 自动保存状态 | `{task_id, status: "saved", version: 3}` |

### 10.4 错误码

| 错误码 | HTTP 状态 | 触发场景 |
|--------|----------|---------|
| `TASK_ALREADY_SUBMITTED` | 409 | save-and-submit 时任务已在审核中 |
| `TASK_NOT_FOUND` | 404 | 编辑器访问不存在的 taskId |
| `AGENT_NOT_SUPPORTED` | 400 | regenerate-content 时 Agent 不支持风格选项 |
| `GENERATION_IN_PROGRESS` | 409 | 重新生成时已有生成任务在执行 |
| `COPILOT_CONTEXT_EXPIRED` | 400 | 上下文超过 30 分钟未更新 |

---

## 十一、Agent Fleet API 契约（v4.0 Phase 8 新增）

### 9.1 Fleet 管理

```yaml
POST /agent-fleet/fleets
  request:
    agent_type: str          # Agent 类型标识
    tenant_id: str
    min_instances: int = 1
    max_instances: int = 10
    routing_strategy: str = "round_robin"  # round_robin | least_load | capability_match
    auto_scale_enabled: bool = false
  response: BaseResponse
    data: {fleet_id, agent_type, min_instances, max_instances, routing_strategy}

GET /agent-fleet/fleets
  query: tenant_id: str = ""
  response: BaseResponse
    data: [{fleet_id, agent_type, instance_count, routing_strategy, auto_scale_enabled}]

GET /agent-fleet/fleets/{fleet_id}
  response: BaseResponse
    data: {fleet_id, agent_type, instance_count, health}

DELETE /agent-fleet/fleets/{fleet_id}
  response: BaseResponse
```

### 9.2 实例管理

```yaml
POST /agent-fleet/fleets/{fleet_id}/instances
  request:
    agent_id: str
    capabilities: List[str] = []
    max_tasks: int = 5
    metadata: Dict = {}
  response: BaseResponse
    data: {instance_id, agent_id, status, capabilities, max_tasks}

DELETE /agent-fleet/fleets/{fleet_id}/instances/{instance_id}
  response: BaseResponse

GET /agent-fleet/fleets/{fleet_id}/instances
  query: status: str = null
  response: BaseResponse
    data: [{instance_id, agent_id, status, current_tasks, max_tasks, load_ratio, cpu_percent, memory_percent, capabilities}]
```

### 9.3 心跳与路由

```yaml
POST /agent-fleet/fleets/{fleet_id}/instances/{instance_id}/heartbeat
  request:
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    current_tasks: int = 0
    status: str = null   # healthy | degraded | offline | busy
  response: BaseResponse

POST /agent-fleet/fleets/{fleet_id}/route
  request:
    required_capabilities: List[str] = []
  response: BaseResponse
    data: {instance_id, agent_id, status, current_tasks, max_tasks, capabilities}
    # 无可用实例时 code="SERVICE_UNAVAILABLE"
```

### 9.4 健康与伸缩

```yaml
GET /agent-fleet/fleets/{fleet_id}/health
  response: BaseResponse
    data: {fleet_id, agent_type, total_instances, healthy_count, degraded_count, offline_count, busy_count, avg_cpu_percent, avg_memory_percent, total_queue_depth, routing_strategy}

GET /agent-fleet/fleets/{fleet_id}/scaling
  response: BaseResponse
    data: {fleet_id, recommendation, reason, current_health, limits}
    # recommendation: maintain | scale_up | scale_down | manual
```

### 9.5 错误码

| 错误码 | 说明 | 触发场景 |
|--------|------|---------|
| `FLEET_NOT_FOUND` | 舰队不存在 | 查询/操作不存在的 fleet_id |
| `INSTANCE_NOT_FOUND` | 实例不存在 | 查询/操作不存在的 instance_id |
| `FLEET_CAPACITY_EXCEEDED` | 舰队容量已满 | 注册实例时超过 max_instances |

---

### 8.2 限流响应规范

```json
{
  "code": "RATE_LIMITED",
  "message": "请求过于频繁，请稍后重试",
  "data": {
    "limit": 100,
    "remaining": 0,
    "reset_at": "2026-06-02T10:31:00Z",
    "retry_after": 60
  },
  "trace_id": "req_abc123def456",
  "timestamp": "2026-06-02T10:30:00Z"
}
```

**响应头**：
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1717324260
Retry-After: 60
```

### 8.3 特殊接口限流规则

| 接口 | 限流规则 | 说明 |
|------|---------|------|
| `POST /api/v1/ai/conversations/:id/messages` | 10 req/min/user | AI 对话消息，防止刷消息 |
| `POST /api/v1/llm-hub/generate` | 20 req/min/tenant | LLM 生成，成本控制 |
| `POST /api/v1/lab/parse` | 5 req/min/user | 爆款解析，防止滥用 |
| `POST /api/v1/image-forge/generate` | 10 req/min/tenant | 图片生成，成本高 |
| `WS /ws/stream` | 1 conn/user | WebSocket 连接数限制 |
| `SSE /api/v1/ai/stream` | 5 conn/user | SSE 流式连接数限制 |

---

## 九、认证与请求头规范

### 9.1 必需请求头

| 请求头 | 必填 | 说明 | 示例 |
|--------|------|------|------|
| `Authorization` | 是 | Bearer JWT Token | `Bearer eyJhbGciOiJIUzI1NiIs...` |
| `X-Tenant-ID` | 是 | 租户 ID | `tenant_abc123` |
| `X-Request-ID` | 是 | 请求唯一 ID（UUID v4） | `req_abc123def456` |
| `X-Idempotency-Key` | 否 | 幂等性 Key（POST 建议携带） | `idem_xyz789` |
| `Content-Type` | 是 | 内容类型 | `application/json` |
| `Accept` | 否 | 接受类型 | `application/json` |

### 9.2 可选请求头

| 请求头 | 说明 | 示例 |
|--------|------|------|
| `X-Agent-ID` | 当前调用方 Agent ID | `agent_content_forge_001` |
| `X-Skill-ID` | 当前调用方 Skill ID | `skill_content_generate` |
| `X-User-ID` | 当前用户 ID | `user_abc123` |
| `Accept-Language` | 语言偏好 | `zh-CN` |

---

## 十、版本控制规范

### 10.1 API 版本策略

**URL 路径版本化**（推荐）：
```
/api/v1/contents           ← 当前版本
/api/v2/contents           ← 新版本（v4.0 新增接口使用）
```

**v4.0 新增接口统一使用 `/api/v2/` 前缀**，保留 `/api/v1/` 接口 1 个 Sprint 的兼容期。

### 10.2 版本兼容性规则

| 变更类型 | 兼容性 | 处理方式 |
|---------|--------|---------|
| 新增字段（响应） | 兼容 | 直接添加，旧客户端忽略 |
| 新增可选参数（请求） | 兼容 | 直接添加，默认值为 null |
| 新增必填参数（请求） | 不兼容 | 新 API 版本 |
| 删除字段 | 不兼容 | 标记 deprecated，Phase 2 删除 |
| 修改字段类型 | 不兼容 | 新 API 版本 |
| 修改枚举值 | 不兼容 | 新 API 版本 |

---

## 十一、审核发布 API 契约（v4.0 Copilot-Driven）

> **适用范围**: `/review` 页面（列表 + 详情）
> **模式**: Mode B（Copilot-Driven）— 工作区无业务按钮，所有操作通过 Copilot Action Cards
> **关联文档**: `docs/后端需求/后端需求补充_审核发布_Copilot-Driven_2026-06-04.md`
> **状态**: 🔒 **已冻结** — 2026-06-05 四方联合审核通过，变更需重新签字

---

### 11.0 通用响应扩展：`copilot_followup` 字段

**所有业务 API 响应（除 SSE/WebSocket 外）可选携带 `copilot_followup` 字段**，用于驱动 Copilot 下一步交互。

```json
{
  "code": "OK",
  "message": "操作成功",
  "data": { ... },
  "copilot_followup": {
    "message": "审核已通过！要现在发布还是定时发布？",
    "suggested_cards": [
      {
        "type": "decision",
        "title": "发布确认",
        "actions": [
          { "id": "publish_now", "label": "立即发布", "variant": "primary" },
          { "id": "schedule", "label": "定时发布", "variant": "secondary" }
        ]
      }
    ],
    "context_update": {
      "page": "/review",
      "selected_items": ["task_001"]
    }
  },
  "trace_id": "req_abc123",
  "timestamp": "2026-06-04T10:30:00Z"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `copilot_followup` | object | 否 | 当操作触发 Copilot 状态变化时携带 |
| `copilot_followup.message` | string | 是 | Copilot 展示给用户的自然语言消息 |
| `copilot_followup.suggested_cards` | array | 否 | 建议的 Action Cards 列表 |
| `copilot_followup.context_update` | object | 否 | 需要同步更新的上下文 |

**触发时机**:
- 审核决策完成（approve → 推送发布确认 Card）
- 内容更新保存（→ 推送优化建议 Card）
- 封面生成完成（→ 推送应用/重新生成 Card）
- 重新生成提交（→ 推送进度跟踪 Card）

---

### 11.1 审核列表接口

#### `GET /api/review-publish-center/conclusions`

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `status_filter` | string | 否 | 状态过滤：`all`/`pending`/`approved`/`rejected`/`revise`，默认 `all` |
| `platform` | string | 否 | 平台过滤：`xhs`/`douyin`/`wechat_channels`/... |
| `page` | int | 否 | 页码，默认 1 |
| `page_size` | int | 否 | 每页数量，默认 20 |

**响应 `data`**:
```json
{
  "items": [
    {
      "task_id": "task_abc123",
      "task_name": "猫咪驱虫避坑指南",
      "content_title": "猫咪驱虫避坑指南，这3个误区90%的人都不知道",
      "platform": "xhs",
      "account_name": "小艾养猫记",
      "status": "human_wait",
      "review_decision": null,
      "reviewed_at": null,
      "reviewer": null,
      "review_reason": null,
      "content_preview": "作为一个养猫3年的铲屎官...",
      "waiting_since": "2026-06-04T10:00:00Z",
      "priority": 80,
      "risk_level": "low",
      "can_publish_now": false,
      "has_cron_job": false,
      "compliance_score": 96,
      "quality_score": 88,
      "cover_image_url": "https://cdn.example.com/cover1.jpg"
    }
  ],
  "copilot_summary": {
    "total_pending": 3,
    "recommended_priority": ["task_003", "task_001", "task_002"],
    "batch_suggestion": "3 条待审中，1 条合规分低于 80 分建议优先处理，其余 2 条建议直接通过。"
  }
}
```

---

### 11.2 审核详情接口

#### `GET /api/review-publish-center/conclusions/{task_id}`

**响应 `data`**:
```json
{
  "task_id": "task_abc123",
  "task_name": "猫咪驱虫避坑指南",
  "platform": "xhs",
  "status": "human_wait",
  "content_preview": "作为一个养猫3年的铲屎官...",
  "generated_content": {
    "title": "猫咪驱虫避坑指南，这3个误区90%的人都不知道",
    "body": "正文内容...",
    "tags": ["驱虫", "新手养猫", "养宠攻略"],
    "platform": "xhs",
    "content_type": "note_image",
    "cover_image_url": "https://cdn.example.com/cover1.jpg",
    "cover_image_ratio": "3:4",
    "images": ["https://cdn.example.com/img1.jpg"]
  },
  "agent_summary": "Agent 执行摘要...",
  "compliance_result": {
    "level": "pass",
    "violations": [],
    "l1_check": true,
    "l2_check": true,
    "l3_check": true,
    "l4_check": true
  },
  "prediction_result": {
    "engagement_interval": { "likes": "25-60", "comments": "5-15", "saves": "10-30" },
    "viral_probability": 0.72,
    "best_publish_time": "18:00"
  },
  "quality_score": {
    "overall": 88,
    "dimensions": {
      "title_attractiveness": 85,
      "body_completeness": 90,
      "tag_relevance": 88,
      "readability": 92,
      "engagement_potential": 86,
      "compliance": 96
    }
  },
  "topic_report": {
    "report_id": "rpt_001",
    "selected_topic": "猫咪驱虫",
    "topics": [...],
    "5a_stage": "action",
    "audience_fit_score": 0.91
  },
  "review_history": [
    {
      "reviewer": "admin_001",
      "decision": "approve",
      "reason": null,
      "publish_mode": "immediate",
      "scheduled_at": null,
      "created_at": "2026-06-04T09:30:00Z"
    }
  ],
  "risk_level": "low",
  "can_publish": true,
  "has_primary_approval": false,
  "account_id": "acc_001",
  "account_name": "小艾养猫记",
  "draft_id": "draft_001",
  "cron_schedule": null,
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
  "available_copilot_cards": ["review-decision", "cover-generation", "title-optimization"]
}
```

---

### 11.3 审核决策接口

#### `POST /api/human-in-the-loop/tasks/{task_id}/{decision}`

| `decision` | 说明 | 触发后状态 |
|-----------|------|-----------|
| `approve` | 审核通过 | `human_wait` → `approved_waiting_publish` |
| `reject` | 驳回 | `human_wait` → `rejected` |
| `revise` | 打回修改 | `human_wait` → `revision_requested` |

**请求体**:
```json
{
  "reason": "标题超出字数限制，需精简",
  "copilot_suggested": true,
  "copilot_card_id": "review-decision-task_001"
}
```

**响应 `data`**:
```json
{
  "status": "approved_waiting_publish",
  "task_id": "task_abc123",
  "next_steps": [
    { "action": "confirm_publish", "label": "确认发布", "available": true },
    { "action": "schedule_publish", "label": "定时发布", "available": true }
  ]
}
```

**响应 `copilot_followup`（approve 时）**:
```json
{
  "message": "审核已通过！合规分 96 分，质量优秀。要现在发布还是定时发布？",
  "suggested_cards": [
    {
      "type": "decision",
      "title": "发布确认",
      "actions": [
        { "id": "publish_now", "label": "立即发布", "variant": "primary" },
        { "id": "schedule", "label": "定时发布", "variant": "secondary" }
      ]
    }
  ]
}
```

---

### 11.4 内容更新接口

#### `PUT /api/review-publish-center/conclusions/{task_id}/content`

**请求体**:
```json
{
  "title": "新标题",
  "body": "新正文",
  "tags": ["标签1", "标签2"],
  "cover_image_url": "https://cdn.example.com/new_cover.jpg"
}
```

**响应**: `BaseResponse`，`data.updated_at`

---

### 11.5 发布确认接口

#### `POST /api/review-publish-center/conclusions/{task_id}/confirm-publish`

**请求体**:
```json
{
  "operator": "user_001",
  "publish_mode": "immediate",
  "scheduled_at": null,
  "cron_schedule": null
}
```

**响应 `data`**:
```json
{
  "publish_task_id": "pub_001",
  "cron_job_id": null,
  "status": "published"
}
```

---

### 11.6 重新生成接口

#### `POST /api/review-publish-center/conclusions/{task_id}/regenerate`

**响应 `data`**:
```json
{
  "status": "regenerating",
  "message": "已提交重新生成，预计 30 秒完成"
}
```

---

### 11.7 封面生成接口

#### `POST /api/ai/generate-cover`

**请求体**:
```json
{
  "task_id": "task_abc123",
  "prompt": "温馨可爱的橘猫在草地上，阳光照射，治愈风格",
  "auto_prompt": false,
  "content_summary": "猫咪驱虫避坑指南...",
  "style_preset": "cute",
  "count": 2,
  "ratio": "3:4"
}
```

**响应**: `BaseResponse`（code: `ACCEPTED`）
```json
{
  "code": "ACCEPTED",
  "message": "封面生成任务已提交",
  "data": {
    "job_id": "cover_gen_xyz789",
    "status": "queued",
    "estimated_seconds": 8
  }
}
```

#### `GET /api/ai/generate-cover/{job_id}`

**响应 `data`**:
```json
{
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
```

---

### 11.8 Copilot 通用网关

> **状态**: Sprint 1 基础设施，所有页面共享

#### `POST /api/ai/copilot/context`

客户端上报当前页面上下文，后端返回建议的 Action Cards。

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
    "status": "human_wait",
    "compliance_score": 96,
    "quality_score": 88
  },
  "workspace_state": {
    "active_tab": "pending",
    "editor_dirty": false
  },
  "timestamp": "2026-06-04T15:30:00Z"
}
```

**响应 `data`**:
```json
{
  "context_id": "ctx_abc456",
  "suggested_cards": [
    {
      "card_type": "decision",
      "priority": 1,
      "target_page": "/review",
      "reasoning": "human_wait 状态，合规分 96 > 85"
    }
  ],
  "ai_insights": ["3 条待审中，1 条合规分低于 80 分建议优先处理"]
}
```

#### `GET /api/ai/copilot/action-cards`

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `page` | string | 是 | 当前页面路由 |
| `context_id` | string | 否 | 上下文 ID |
| `task_id` | string | 否 | 当前选中任务 ID |

**响应 `data`**:
```json
{
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
          "api": { "method": "POST", "endpoint": "/api/human-in-the-loop/tasks/task_001/approve", "payload": {} }
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
    }
  ]
}
```

#### `POST /api/ai/copilot/execute`

通用 Action 执行网关，透传到底层业务 API。

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

**响应**: 同底层 API 响应格式，可选携带 `copilot_followup`

---

### 11.9 WebSocket 事件（审核发布相关）

| 事件名 | 方向 | 说明 | 优先级 |
|--------|------|------|--------|
| `cover.generation.progress` | S→C | 封面生成进度推送 `{job_id, progress, step}` | P0 |
| `cover.generation.completed` | S→C | 封面生成完成 `{job_id, results[]}` | P0 |
| `review.decision.completed` | S→C | 审核决策完成 `{task_id, new_status, decision}` | P1 |
| `copilot.card.push` | S→C | 服务端主动推送 Action Card | P1 |
| `workspace.sync` | S→C | 工作区内容同步（多端） | P2 |

**统一消息格式**:
```json
{
  "event": "cover.generation.completed",
  "payload": { ... },
  "timestamp": "2026-06-04T15:32:08Z",
  "trace_id": "ws_abc123"
}
```

---

### 11.10 审核发布新增错误码

| 错误码 | HTTP 状态 | 中文说明 | 触发场景 | 前端处理 |
|--------|----------|---------|---------|---------|
| `COVER_GENERATION_LIMIT_EXCEEDED` | 429 | 封面生成次数超限 | 单用户 3 次/分钟或单任务 5 次/小时 | 展示冷却倒计时 |
| `COVER_GENERATION_FAILED` | 500 | 封面生成失败 | AI 图像服务异常 | 展示「生成失败」+ [重试] |
| `COPILOT_CONTEXT_EXPIRED` | 400 | Copilot 上下文过期 | >30min 未更新 | 自动刷新后重试 |
| `INVALID_COPILOT_CARD_ACTION` | 400 | 无效 Card 操作 | 卡片过期或已处理 | 刷新页面获取最新卡片 |
| `REVIEW_DECISION_ALREADY_MADE` | 409 | 审核决策已存在 | 并发重复决策 | 刷新详情页获取最新状态 |
| `AI_INSIGHT_UNAVAILABLE` | 503 | AI 洞察暂不可用 | LLM 服务降级 | 降级为静态提示 |

---

## 十二、变更记录

| 日期 | 版本 | 变更内容 | 变更人 |
|------|------|---------|--------|
| 2026-06-02 | v1.0 | 初始创建：全局错误码、枚举定义、幂等性、限流、认证规范 | Kimi Code CLI |
| 2026-06-03 | v1.1 | Phase 5 新增：§五 LLM Hub 路由接口、§六 MCP Gateway 预留接口、节点类型枚举 SKILL | Kimi Code CLI |
| 2026-06-03 | v1.2 | Phase 6 新增：§6.2 实验室 端点（parse / generate / templates） | Kimi Code CLI |
| 2026-06-05 | v1.3 | 实验室 增强分析模式新增：§6.2 `analyze` / `template` / `keywords` / `categories`；复用 `content-templates` 保存 | Kimi Code CLI |
| 2026-06-05 | v1.3 | 实验室 增强分析模式新增：§6.2 `analyze` / `template` / `keywords` / `categories`；复用 `content-templates` 保存 | Kimi Code CLI |
| 2026-06-04 | v1.3 | Dashboard API 缺口记录 | Kimi Code CLI |
| **2026-06-04** | **v1.4** | **Step 2 契约冻结：§十一 审核发布 API（Copilot-Driven）+ copilot_followup 字段规范 + 新增错误码 + WebSocket 事件** | **Kimi Code CLI** |

---

*最后更新: 2026-06-04*
*关联文档: `docs/契约与数据/02-数据库ER图.md`, `docs/契约与数据/03-核心业务状态流转.md`, `docs/后端需求/后端需求补充_审核发布_Copilot-Driven_2026-06-04.md`*
