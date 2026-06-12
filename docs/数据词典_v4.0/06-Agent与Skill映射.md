# 06-Agent与Skill映射

> **版本**: v4.0
> **生成日期**: 2026-06-03
> **PRD 参考**: `EcoDream_Omni_PRD_v4_AI_Native_Architecture.md` §4-5

---

## 一、Agent 总览（10 常驻 + 1 Meta）

| # | Agent | 职责 | 状态 | 对应 Service |
|---|-------|------|------|-------------|
| 1 | **Meta-Orchestrator** | 意图解析、编排模式选择 | ✅ | `services/agent_orchestra.py` |
| 2 | **TrendScout** | 选题洞察、趋势分析 | 🟡 Mock | `services/api_platform.py` |
| 3 | **MarketingMethodology** | AIPL 营销策略 | 🟡 内存 | `services/data_analyst.py` |
| 4 | **DataAnalyst** | 数据分析、战报生成 | 🟡 降级 | `services/data_analyst.py` |
| 5 | **ContentForge** | 内容生成 | ✅ | `services/content_series.py` |
| 6 | **EngagementSimulator** | 互动预演 | 🟡 Mock | `services/predictionsStore.ts` |
| 7 | **ComplianceGuard** | 合规审核 L1-L4 | ✅ | `services/compliance.py` |
| 8 | **Publisher** | 发布执行 | ✅ | `services/publisher.py` |
| 9 | **EngagementTracker** | 数据回流 | ✅ | `services/engagement_tracking.py` |
| 10 | **PersonaManager** | 人设管理 | ✅ | `services/persona_story.py` |
| 11 | **PlatformRuleEngine** | 平台规则 | ✅ | `services/platform_rule_function.py` |

---

## 二、Skill 总览（22 个）

### 2.1 内容生产级 Skill（13 个）

| # | Skill | 归属 Agent | 调用 Service / Function | 状态 |
|---|-------|-----------|------------------------|------|
| 1 | `content_generate` | ContentForge | `services/content_series.py` | ✅ |
| 2 | `title_optimize` | ContentForge | `services/content_series.py` | ✅ |
| 3 | `hashtag_generate` | ContentForge | `services/content_series.py` | ✅ |
| 4 | `image_generate` | ContentForge | `services/image_forge.py` | ✅ |
| 5 | `video_generate` | ContentForge | `services/image_forge.py` | 🟡 |
| 6 | `brand_knowledge_inject` | ContentForge | `services/brand_knowledge_function.py` | **P4 新增** |
| 7 | `keyword_inject` | ContentForge | `services/workflow_engine.py:_run_skill_node()` | **P4 新增** |
| 8 | `vetdrug_validate` | ComplianceGuard | `services/vetdrug.py` | **P4 新增** |
| 9 | `engagement_simulate` | EngagementSimulator | `services/data_analyst.py` | 🟡 |
| 10 | `trend_analyze` | TrendScout | `services/api_platform.py` | 🟡 |
| 11 | `audience_match` | PersonaManager | `services/persona_story.py` | ✅ |
| 12 | `platform_adapt` | PlatformRuleEngine | `services/platform_rule_function.py` | ✅ |
| 13 | `compliance_check` | ComplianceGuard | `services/compliance.py` | ✅ |

### 2.2 系统级 Skill（9 个）

| # | Skill | 归属 Agent | 调用 Service | 状态 |
|---|-------|-----------|-------------|------|
| 14 | `task_create` | Meta-Orchestrator | `services/task_hub.py` | ✅ |
| 15 | `task_schedule` | Meta-Orchestrator | `services/cron_hub.py` | ✅ |
| 16 | `task_cancel` | Meta-Orchestrator | `services/task_hub.py` | ✅ |
| 17 | `publish_execute` | Publisher | `services/publisher.py` | ✅ |
| 18 | `publish_schedule` | Publisher | `services/cron_hub.py` | ✅ |
| 19 | `data_collect` | DataAnalyst | `services/data_analyst.py` | ✅ |
| 20 | `battle_report_generate` | DataAnalyst | `services/data_analyst.py` | ✅ |
| 21 | `account_health_check` | PlatformRuleEngine | `services/account_health.py` | ✅ |
| 22 | `alert_notify` | Meta-Orchestrator | `services/alert_stream.py` | ✅ |

---

## 三、Agent → Skill 调用矩阵

| Agent | Skill |
|-------|-------|
| Meta-Orchestrator | `task_create`, `task_schedule`, `task_cancel`, `alert_notify` |
| TrendScout | `trend_analyze` |
| MarketingMethodology | —（Function 层） |
| DataAnalyst | `data_collect`, `battle_report_generate` |
| ContentForge | `content_generate`, `title_optimize`, `hashtag_generate`, `image_generate`, `video_generate`, `brand_knowledge_inject`, `keyword_inject` |
| EngagementSimulator | `engagement_simulate` |
| ComplianceGuard | `compliance_check`, `vetdrug_validate` |
| Publisher | `publish_execute`, `publish_schedule` |
| EngagementTracker | —（直接 DB） |
| PersonaManager | `audience_match` |
| PlatformRuleEngine | `platform_adapt`, `account_health_check` |

---

## 四、Skill 调用路径（v4.0 架构红线）

```
Agent (禁止直接 DB)
  └── Skill
        ├── Function API（允许 DB 访问）
        │     └── PostgreSQL / Redis
        └── 或
              LLM Hub（必须通过路由）
                    └── 国内/海外模型
```

**关键约束**：
- Agent 层 → Skill 层：通过 `workflow_engine.py` `_run_skill_node()` 路由
- Skill 层 → Function 层：直接调用 `*_function.py`
- Function 层 → DB：唯一允许直接 ORM 访问的层

---

## 五、v4.0 新增/变更

| 变更 | 说明 | Phase |
|------|------|-------|
| `NodeType.SKILL` | Workflow 新增 Skill 节点类型 | P4 |
| `brand_knowledge_inject` | 品牌知识注入 Skill | P4 |
| `keyword_inject` | 关键词注入 Skill | P4 |
| `vetdrug_validate` | 兽药合规校验 Skill | P4 |
| `DataAnalyst` 降级 | Agent → Function+Skill | P3 |
| `image-forge` | 图片生成 Skill 集成到 Pipeline | P4 |
| `compliance_check` | 综合合规检查 Skill（L1-L4 + 敏感词 + 兽药预检） | **P8 新增** |
| `platform_compliance_check` | 平台合规校验 Skill（L1-L2 规则引擎） | **P8 新增** |
| `vetdrug_claim_validate` | 兽药宣称校验 Skill（批文一致性） | **P8 新增** |
| `content_generate` | 正文生成 Skill（模板拼接 + 六层 Prompt） | **P8 新增** |
| `image_generate` | 图片生成 Skill（文生图/图生图 + 平台规格） | **P8 新增** |
| `rag_retrieval` | RAG 检索 Skill（BrandKnowledge 语义查询） | **P8 新增** |
| `Agent Fleet` | Agent 舰队管理（实例池 + 负载均衡 + 健康检查） | **P8 新增** |
| `brand_consistency_check` | 品牌一致性校验 Skill（关键词 + 调性 + 禁用词） | **P9 新增** |
| `fingerprint_generate` | 内容指纹生成 Skill（SimHash MVP） | **P9 新增** |
| `engagement_predict` | 互动量预测 Skill（点赞/评论/收藏区间估计） | **P9 新增** |
| `publish_schedule` | 发布排期 Skill（最佳时段算法） | **P9 新增** |
| `health_score` | 账号健康分 Skill（五维度加权评分） | **P9 新增** |
| `xhs_note_data_extraction` | 小红书笔记采集 Skill（Mock 数据） | **P9 新增** |
| `Handoff Protocol` | Agent 间交接协议（DELEGATE/COLLABORATE/ESCALATE/RETURN） | **P9 新增** |
| `Swarm Mode` | Fan-out/Fan-in 并行执行（merge/best/vote/average） | **P9 新增** |
