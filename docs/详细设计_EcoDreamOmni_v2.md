# EcoDream Omni 详细设计说明书（v2.7.2）

| 属性 | 内容 |
|------|------|
| **真源需求** | `EcoDream_Omni_PRD_v2_对齐核心方案.md`（**V2.7.2**） |
| **真源排期** | `开发计划_素人号矩阵AI平台_v2.md`（**v2.7.2 增补版**） |
| **实现仓库** | `apps/backend`（FastAPI）、`apps/frontend`（React 19 + Vite 6） |
| **版本** | v2.7.2（2026-05-21） |
| **状态** | 编码阶段 |

---

## 〇、V2.7.2 变更摘要

### 0.1 本次更新范围

| 模块 | 变更类型 | PRD章节 | 设计章节 |
|------|---------|---------|----------|
| **LLM Hub** | 重写（精简） | §8 V2.7.2精简版 | 本文档 §一 |
| **PersonaStory** | 新增 | §11 | 本文档 §二 |
| **六大基础功能** | 扩展（5→6） | §一 | 本文档 §二.1 |

### 0.2 与v1.0的关系

- v1.0 基线设计（W1-W14）继续有效，不在本文重复
- 本文仅覆盖 V2.7.2 新增/变更内容
- LLM Hub 原设计（v1.0 §5）被本文 §一 替代

---

## 一、LLM Hub 精简版详细设计

### 1.1 设计目标

将 LLM 配置门槛从「运营需理解三层路由策略、合规分级、预算配额」降低为「2分钟完成一家新模型接入」。

### 1.2 数据模型

#### 1.2.1 `llm_models` 表（精简版）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | UUID | PK | 系统生成 |
| `provider` | VARCHAR(64) | NOT NULL | 厂家：deepseek/aliyun/baidu/zhipu/kimi/openai/anthropic/google |
| `model_name` | VARCHAR(128) | NOT NULL | 模型名：deepseek-chat / gpt-4o / claude-3-5-sonnet |
| `api_key_encrypted` | TEXT | NOT NULL | AES-256-GCM加密 |
| `endpoint_base_url` | VARCHAR(512) | NULL | 自定义API端点，NULL时使用厂家默认 |
| `status` | VARCHAR(16) | DEFAULT 'active' | active / inactive |
| `data_training_opt_out` | BOOLEAN | DEFAULT true | 数据训练授权状态 |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | |
| `updated_at` | TIMESTAMPTZ | DEFAULT now() | |

**移除字段**（原v1.0设计）：capabilities, compliance_tier, max_tokens, cost_per_1k_input, cost_per_1k_output, cost_currency, api_key_ref(Vault引用)

#### 1.2.2 `llm_scope_configs` 表（新增，替代config_layers）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | UUID | PK | |
| `scope_type` | VARCHAR(16) | NOT NULL | 'global' 或 'node' |
| `node_id` | VARCHAR(64) | NULL | agent_id/skill_id；global为NULL |
| `model_id` | UUID | FK→llm_models | 绑定模型 |
| `temperature` | FLOAT | DEFAULT 0.5 | 0.1-1.0 |
| `timeout_seconds` | INT | DEFAULT 60 | |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | |
| `updated_at` | TIMESTAMPTZ | DEFAULT now() | |

**约束**：`scope_type='global'`时`node_id`必须为NULL且全局仅一行；`scope_type='node'`时`node_id`唯一

#### 1.2.3 `llm_usage_logs` 表（替代route_decisions）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | UUID | PK | |
| `model_id` | UUID | FK→llm_models | |
| `node_id` | VARCHAR(64) | NOT NULL | 调用方 |
| `provider_region` | VARCHAR(16) | NOT NULL | 'domestic'/'overseas' |
| `input_tokens` | INT | DEFAULT 0 | |
| `output_tokens` | INT | DEFAULT 0 | |
| `latency_ms` | INT | DEFAULT 0 | |
| `status` | VARCHAR(16) | NOT NULL | success / error |
| `error_message` | TEXT | NULL | |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | |

**TTL策略**：热库保留30天，30天后自动清理（PostgreSQL分区或定时任务）

#### 1.2.4 `llm_pricing` 表（成本计算参考）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `model_name` | VARCHAR(128) | PK | |
| `provider` | VARCHAR(64) | NOT NULL | |
| `input_price_per_1k` | DECIMAL(10,6) | NOT NULL | 单价 |
| `output_price_per_1k` | DECIMAL(10,6) | NOT NULL | |
| `currency` | VARCHAR(8) | DEFAULT 'CNY' | CNY/USD |

### 1.3 服务层接口

```python
class LLMHubService:
    # -- Model Registry --
    async def register_model(self, provider: str, model_name: str, 
                            api_key: str, endpoint_url: Optional[str] = None) -> LLMModel: ...
    async def list_models(self, provider: Optional[str] = None, 
                         status: Optional[str] = None) -> List[LLMModel]: ...
    async def get_model(self, model_id: str) -> Optional[LLMModel]: ...
    async def update_model(self, model_id: str, **fields) -> LLMModel: ...
    async def delete_model(self, model_id: str) -> bool: ...
    async def test_connectivity(self, model_id: str) -> dict: ...  # 新增
    
    # -- Scope Config --
    async def set_global_default(self, model_id: str, temperature: float = 0.5,
                                  timeout: int = 60) -> ScopeConfig: ...  # 新增
    async def set_node_override(self, node_id: str, model_id: str,
                                 temperature: Optional[float] = None) -> ScopeConfig: ...  # 新增
    async def remove_node_override(self, node_id: str) -> bool: ...  # 新增
    async def list_scope_configs(self) -> List[ScopeConfigWithInheritance]: ...  # 新增
    async def resolve_model_for_node(self, node_id: str) -> ResolvedConfig: ...  # 新增
    
    # -- Usage & Cost --
    async def log_usage(self, model_id: str, node_id: str, 
                       input_tokens: int, output_tokens: int, 
                       latency_ms: int, status: str, error: Optional[str] = None) -> UsageLog: ...
    async def get_cost_summary(self, period_days: int = 7) -> CostSummary: ...  # 新增
    async def get_usage_logs(self, model_id: Optional[str] = None,
                             node_id: Optional[str] = None,
                             start_date: Optional[datetime] = None,
                             end_date: Optional[datetime] = None,
                             limit: int = 100) -> List[UsageLog]: ...  # 新增
```

### 1.4 API 路由

```
POST   /llm-hub/models                    → register_model
GET    /llm-hub/models                    → list_models（api_key回显掩码）
GET    /llm-hub/models/{id}               → get_model
PUT    /llm-hub/models/{id}               → update_model
DELETE /llm-hub/models/{id}               → delete_model
POST   /llm-hub/models/{id}/test          → test_connectivity（新增）

POST   /llm-hub/scope-configs             → set_node_override / set_global_default
GET    /llm-hub/scope-configs             → list_scope_configs（含继承关系）
DELETE /llm-hub/scope-configs/{id}        → remove override

POST   /llm-hub/usage-logs                → log_usage（内部调用，也可供调试）
GET    /llm-hub/usage-logs                → get_usage_logs（筛选导出）
GET    /llm-hub/cost-summary              → get_cost_summary（新增）
```

### 1.5 安全设计

- **加密**: `api_key` 使用 AES-256-GCM，master key 来自 `LLM_API_KEY_MASTER_KEY` 环境变量
- **掩码**: API 响应中 `api_key_encrypted` → `"••••••••"` 掩码
- **审计**: 模型增删改写入 `audit_logs`（操作人/时间/类型）
- **等保**: 加密存储 + 访问控制 + 定期轮换（预留接口）

---

## 二、PersonaStory 详细设计

### 2.1 设计目标

为每个 Persona 创建时间轴驱动的故事剧本，ContentForge 生成内容时自动注入故事上下文（前情回顾、情绪基调、下期预告），实现单账号内内容的前后呼应与情感连贯。

### 2.2 数据模型

#### 2.2.1 `persona_stories` 表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | UUID | PK | |
| `persona_id` | VARCHAR(64) | NOT NULL | 关联Persona |
| `name` | VARCHAR(256) | NOT NULL | 剧本名称 |
| `description` | TEXT | NULL | 剧本描述 |
| `emotion_curve_template` | VARCHAR(32) | DEFAULT 'gradual_growth' | 情感曲线模板 |
| `status` | VARCHAR(16) | DEFAULT 'draft' | draft/active/completed/archived |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | |
| `updated_at` | TIMESTAMPTZ | DEFAULT now() | |

#### 2.2.2 `story_nodes` 表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | UUID | PK | |
| `story_id` | UUID | FK→persona_stories | |
| `sequence_index` | INT | NOT NULL | 节点顺序 |
| `theme` | VARCHAR(256) | NOT NULL | 本期主题 |
| `emotion_tone` | VARCHAR(16) | NOT NULL | low/medium/high/burst |
| `key_event` | TEXT | NOT NULL | 关键事件 |
| `prev_recap` | TEXT | NULL | 前情回顾（注入内容用） |
| `next_teaser` | TEXT | NULL | 下期预告（注入内容用） |
| `content_draft_id` | UUID | NULL | 关联已生成的内容 |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | |
| `updated_at` | TIMESTAMPTZ | DEFAULT now() | |

**约束**：`(story_id, sequence_index)` 唯一索引

#### 2.2.3 情感曲线模板枚举

| 模板ID | 名称 | 描述 |
|--------|------|------|
| `gradual_growth` | 渐进成长 | 从低到高稳步上升 |
| `valley_comeback` | 低谷逆袭 | 低→高→低→爆发的波浪 |
| `suspense_reveal` | 悬疑揭秘 | 平稳→高潮→回落→再次高潮 |
| `steady_warm` | 平稳温暖 | 持续中低情绪，偶有小高潮 |

### 2.3 服务层接口

```python
class PersonaStoryService:
    # -- Story CRUD --
    async def create_story(self, persona_id: str, name: str, 
                          description: str = "",
                          template: str = "gradual_growth") -> PersonaStory: ...
    async def list_stories(self, persona_id: Optional[str] = None,
                          status: Optional[str] = None) -> List[PersonaStory]: ...
    async def get_story(self, story_id: str) -> Optional[PersonaStory]: ...
    async def update_story(self, story_id: str, **fields) -> PersonaStory: ...
    async def delete_story(self, story_id: str) -> bool: ...
    async def clone_story(self, story_id: str, new_name: str) -> PersonaStory: ...
    async def update_status(self, story_id: str, status: str) -> PersonaStory: ...
    
    # -- Node CRUD --
    async def create_node(self, story_id: str, sequence_index: int,
                         theme: str, emotion_tone: str, key_event: str,
                         prev_recap: Optional[str] = None,
                         next_teaser: Optional[str] = None) -> StoryNode: ...
    async def list_nodes(self, story_id: str) -> List[StoryNode]: ...
    async def update_node(self, node_id: str, **fields) -> StoryNode: ...
    async def delete_node(self, node_id: str) -> bool: ...
    async def reorder_nodes(self, story_id: str, 
                           node_order: List[str]) -> List[StoryNode]: ...
    
    # -- Context Generation (for ContentForge injection) --
    async def get_story_context(self, story_id: str, 
                                current_node_index: Optional[int] = None) -> StoryContext: ...
    async def get_next_available_node(self, story_id: str) -> Optional[StoryNode]: ...
    async def bind_content_to_node(self, node_id: str, 
                                   content_draft_id: str) -> StoryNode: ...
```

### 2.4 API 路由

```
# Stories
POST   /persona-stories                      → create_story
GET    /persona-stories                      → list_stories
GET    /persona-stories/{id}                 → get_story
PUT    /persona-stories/{id}                 → update_story
DELETE /persona-stories/{id}                 → delete_story
POST   /persona-stories/{id}/clone           → clone_story
PATCH  /persona-stories/{id}/status          → update_status

# Nodes
POST   /persona-stories/{id}/nodes           → create_node
GET    /persona-stories/{id}/nodes           → list_nodes
PUT    /story-nodes/{id}                     → update_node
DELETE /story-nodes/{id}                     → delete_node
POST   /persona-stories/{id}/nodes/reorder   → reorder_nodes

# Context (for ContentForge)
GET    /persona-stories/{id}/context         → get_story_context
GET    /persona-stories/{id}/next-node       → get_next_available_node
POST   /story-nodes/{id}/bind-content        → bind_content_to_node
```

### 2.5 ContentForge 注入链路

```
ContentForge 生成流程:
1. 获取 task 关联的 persona_id
2. 查询该 persona 是否有 active 的 story
   └─ 无 → 跳过故事注入
   └─ 有 → 继续
3. 调用 PersonaStoryService.get_next_available_node(story_id)
   → 返回下一个未绑定内容的节点
4. 调用 PersonaStoryService.get_story_context(story_id, node_index)
   → 返回 StoryContext {
        current_node: StoryNode,
        prev_node_summary: str,   # 前一节点的key_event摘要
        next_node_teaser: str,    # 下一节点的theme预告
        series_theme: str,        # 剧本name
        emotional_arc: str        # 当前情感曲线位置
      }
5. 将 StoryContext 注入 Prompt 变量:
   - {{story.prev_recap}} → prev_node_summary
   - {{story.emotion_tone}} → current_node.emotion_tone
   - {{story.next_teaser}} → next_node_teaser
   - {{story.series_theme}} → series_theme
6. 内容生成完成后，调用 bind_content_to_node(node_id, draft_id)
```

### 2.6 前端组件设计

#### StoryCockpitPage

```typescript
interface StoryCockpitPageProps {}

// 状态
const [stories, setStories] = useState<PersonaStory[]>([]);
const [selectedStory, setSelectedStory] = useState<PersonaStory | null>(null);
const [nodes, setNodes] = useState<StoryNode[]>([]);
const [isEditing, setIsEditing] = useState(false);

// 子组件
<StoryList stories={stories} onSelect={setSelectedStory} onCreate={handleCreate} />
<StoryEditor 
  story={selectedStory}
  nodes={nodes}
  onSave={handleSave}
  onAddNode={handleAddNode}
  onReorderNodes={handleReorderNodes}
  onActivate={handleActivate}
/>
<StoryContextPreview context={previewContext} />
```

---

## 三、测试策略

### 3.1 LLM Hub 精简版测试

| 测试文件 | 测试数 | 场景 |
|----------|--------|------|
| `test_llm_model_registry.py` | 4 | 注册/查询/更新/注销；api_key加密存储；连通性测试 |
| `test_llm_scope_config.py` | 3 | 全局默认CRUD；节点覆盖配置；恢复默认；一览表查询 |
| `test_llm_cost_summary.py` | 2 | 按模型/节点统计；趋势计算；单价*Token成本公式验证 |
| `test_llm_usage_logs.py` | 2 | 调用日志写入；按维度筛选导出；30天TTL清理 |
| `test_llm_api.py` | 2 | 模型注册抽屉5字段；应用范围表格；成本看板接口 |

### 3.2 PersonaStory 测试

| 测试文件 | 测试数 | 场景 |
|----------|--------|------|
| `test_persona_story.py` | 4 | 剧本CRUD；克隆；状态流转；按Persona筛选 |
| `test_story_node.py` | 3 | 节点CRUD；排序调整；绑定内容 |
| `test_story_context.py` | 3 | 上下文生成；前情回顾摘要；下期预告注入 |
| `test_story_integration.py` | 2 | ContentForge注入链路；next_available_node算法 |

---

**版本**: v2.7.2  
**创建日期**: 2026-05-21  
**对齐PRD**: PRD V2.7.2 §8 + §11  
**状态**: 编码阶段
