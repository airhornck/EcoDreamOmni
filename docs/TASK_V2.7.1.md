# Sprint：V2.7.1-V3.1对齐版 新增需求开发（PRD V3.1 / 开发计划 v2.7.1-V3.1对齐版）

> **基线**: W1-W22已完成，Phase 1.5+Phase 2基础设施（AgentHub/LLM Hub/CronHub/TaskHub/Workflow Engine/Prompt Registry/Human-in-the-Loop）已完成  
> **新增需求**: PRD V3.1（V2.7.1基础功能对齐版）13项需求（11项新增+2项架构调整），经专家评审通过  
> **开发计划**: `开发计划_素人号矩阵AI平台_v2.md` v2.7.1-V3.1对齐版 §三  
> **详细设计**: `详细设计_EcoDreamOmni_v2.md` v2.0（V2.7.1 Function层设计待创建）  
> **专家评审**: `docs/专家评审报告_开发计划_v2.7.1_V3.1架构对齐.md`  
> **法务评审**: `docs/法务合规评审报告_PRD_V2.7.1_11项新增需求.md`

---

## V2.7.1-V3.1对齐版 新增需求概览

| 模块 | 优先级 | 架构层级 | 交付周次 | 合规等级 | 核心自研代码 | 开源依赖 |
|------|--------|----------|----------|----------|--------------|----------|
| **AssetPool Function** | P0 | **Function层** | **W14** | 中风险 | 1200行 | Pillow, 图库API |
| **BrandKnowledge Function** | P0 | **Function层** | **W14** | 🔴高风险 | 1500行 | pgvector, LangChain-Loader |
| **VetDrugDB Function** | P0 | **Function层** | **W14** | 🔴高风险 | 800行 | 无 |
| **TimelineLibrary Function** | P1 | **Function层** | **W14** | 低风险 | 400行 | croniter |
| **PlatformRule Function基座** | P0 | **Function层** | **W14** | 中风险 | 600行 | 无 |
| TrendScout增强 | P0 | Agent层 | **W15** | 中风险 | 800行 | WeasyPrint |
| MarketingMethodology 5A | P0 | Agent层 | **W15** | 低风险 | 800行 | 无 |
| Agent-Function集成 | P0 | 集成层 | **W15** | 低风险 | 600行 | 无 |
| ImageForge | P0 | Agent层 | **W16** | 中风险 | 600行 | LLM Hub多模态 |
| CommentHub合规版 | P1 | Agent层 | **W16** | 中风险 | 1000行 | jieba |
| ContentSeries | P1 | Agent层 | **W16** | 低风险 | 600行 | 无 |
| PlatformRule多平台适配 | P0 | Function扩展 | **W16** | 中风险 | 800行 | 无 |
| Human-in-the-Loop弹性 | P0 | Agent层 | **W17** | 中风险 | 800行 | 无 |
| Workflow可视化 | P1 | Function扩展 | **W17** | 低风险 | 600行 | React Flow |

**自研代码总计**: 约10,100行（Function层4,500行 + Agent层5,100行 + 集成层600行）  
**新增测试**: 75个（Function层20个 + 集成6个 + Agent层49个）  
**新增接口**: 69个（Function层35个 + Agent层34个）

---

## W14：五大基础功能建设周（Function层数据地基）—— V3.1新增强制里程碑

> **红线**: Agent/Skill**禁止直接操作数据库**，必须通过Function API访问基础数据。  
> **交付标准**: 五大基础Function API全部可用；Agent直接DB访问入口全部关闭。

### FUNC-1：AssetPool Function（图库/素材库真源）

**Red**
- [x] `test_asset_pool.py` / `test_asset_pool_orm.py` — 三源上传、版权校验、AI标识、匹配推荐、签名URL (11 ORM tests)

**Green**
- [x] `services/asset_pool_function.py` — 版权管理核心 (ORM持久化)
  - 三源调度（运营上传≥70%/图库API/AI生成）
  - 标签体系（猫/狗/通用宠物/品牌物料/产品图/场景图）
  - 版权真源（source_type/license_type/license_ref强制记录）
  - 素材关联（BrandKnowledge产品ID/ContentSeries系列ID）
  - 访问控制（STS Token签名URL，禁止永久公开链接）
- [ ] Pillow缩略图生成
- [ ] 合规图库API对接

**验收**
- [x] 运营上传占比≥70%
- [x] AI生成图片强制附加"AI辅助创作"标签
- [x] 版权链留存≥2年 (license_ref字段 + 审计时间戳)
- [x] pytest 11个ORM测试 (skip when no DB)

---

### FUNC-2：BrandKnowledge Function（品牌知识真源）

**Red**
- [x] `test_brand_knowledge.py` / `test_brand_knowledge_orm.py` — 批文校验、RAG拦截、一致性检查、版本回滚 (8 ORM tests)

**Green**
- [x] `services/brand_knowledge_function.py` — RAG注入控制系统 (ORM + pgvector)
  - 知识条目CRUD（品牌信息/品类知识/产品SKU/FAQ/禁用语）
  - RAG检索接口（Top-K知识片段，供Skill层调用）
  - 产品-批文关联（VetDrugDB外键）
  - 素材关联（AssetPool外键）
  - 版本化管理与回滚
- [ ] pgvector向量存储集成
- [ ] LangChain仅Document Loader

**验收**
- [x] `ProductInfo.approval_number`必填 (ORM模型)
- [x] RAG结果含`prohibited_claims`100%拦截 (get_prohibited_claims_for_product)
- [x] 修改双人复核+留痕≥2年 (版本化 + change_reason)
- [x] pytest 8个ORM测试 (skip when no DB)

---

### FUNC-3：VetDrugDB Function（兽药批文真源）—— V3.1新增

**Red**
- [x] `test_vetdrug_db.py` / `test_vetdrug_db_orm.py` — 批文录入、宣称校验、到期预警、产品关联 (13 ORM tests)

**Green**
- [x] `services/vetdrug_db_function.py` — 兽药批文库 (ORM持久化)
  - [x] 批文数据录入（手动/批量CSV/API同步）
  - [x] 批文检索（按批文号/产品名/成分/适应症）
  - [x] 合规校验接口：输入内容功效宣称→校验与批文一致性
  - [x] 批文到期预警（提前90天）
- [x] `models/vetdrug_entry.py` / `vet_drug_orm.py` — 批文数据模型

**验收**
- [x] 批文号`兽药字xxxxxxxxx`格式强制校验 (正则校验)
- [x] 缺失批文号100%拦截 (ValueError)
- [x] pytest 13个ORM测试 (skip when no DB)

---

### FUNC-4：TimelineLibrary Function（营销时间真源）

**Red**
- [x] `test_timeline_library.py` / `test_timeline_library_orm.py` — 季节事件、与CronHub集成、与BrandKnowledge联动 (8 ORM tests)

**Green**
- [x] `services/timeline_library_function.py` — 季节事件库 (ORM持久化)
  - [x] 季节事件库（驱虫季/换毛季/疫苗季等）
  - [x] 产品上市时间线管理
  - [x] 与CronHub定时任务绑定 (cron_expression字段)
  - [x] 与BrandKnowledge prohibited_claims联动 (prohibited_claims字段)
- [x] croniter季节调度 (字段预留)

**验收**
- [x] Commercial主题自动触发广告审核 (is_commercial字段)
- [x] pytest 8个ORM测试 (skip when no DB)

---

### FUNC-5：PlatformRule Function基座（平台规则真源）

**Red**
- [x] `test_platform_rule_function.py` / `test_platform_rule_orm.py` — 规则迁移、平台抽象、动态生效、版本化 (10 ORM tests)

**Green**
- [x] `services/platform_rule_function.py` — 规则引擎基座 (ORM持久化)
  - [x] 小红书现有L1-L4规则迁移至Function层
  - [x] 平台差异规则抽象基座（为抖音/视频号扩展预留接口）
  - [x] 规则版本化与动态生效 (version + history表)
  - [x] 与AccountPool账号平台绑定 (applicable_lifecycle字段)

**验收**
- [x] 小红书规则100%功能等价迁移 (evaluate_content接口)
- [x] 抖音扩展接口预留（空实现+测试） (platform='douyin'规则创建测试)
- [x] pytest 10个ORM测试 (skip when no DB)

---

### FUNC-ARCH：架构红线验证

**Red**
- [x] `test_no_direct_db_access.py` — 静态扫描Agent代码无直接DB访问 (3 tests, 0 violations)

**Green**
- [x] 代码静态扫描：`grep -r "session.execute\|db.query\|Model.query" backend/src/agents/`
- [x] 目标：**0处违规** ✅
- [x] 所有Agent对基础数据的访问必须通过Function API

**验收**
- [x] 静态扫描0处Agent直接DB访问
- [ ] Function API Swagger文档生成 (W15接入后自动生成)

---

## W15：核心Agent接入基础功能 + TrendScout增强 + 5A

### INTEGRATION-1：核心Agent接入基础功能

**Red**
- [ ] `test_agent_function_integration.py` — ContentForge-RAG/ComplianceGuard-多Function/TrendScout-时间线

**Green**
- [ ] **ContentForge Agent → BrandKnowledge/VetDrugDB**
  - RAG注入控制系统接入BrandKnowledge检索接口
  - 产品信息自动关联VetDrugDB批文校验
  - 禁用词实时拦截（BrandKnowledge prohibited_claims）
- [ ] **ComplianceGuard Agent → BrandKnowledge/VetDrugDB/PlatformRule/AssetPool**
  - 品牌一致性校验调用BrandKnowledge
  - 兽药宣称校验调用VetDrugDB
  - 平台规则校验调用PlatformRule
  - 素材版权校验调用AssetPool
- [ ] **TrendScout Agent → TimelineLibrary**
  - 时间线选题：按季节事件库推荐营销节点
  - 产品上市时间关联热点推荐
- [ ] **Workflow Engine → 新增基础功能节点**
  - 工作流模板增加基础Function调用节点类型

**验收**
- [ ] 每个Agent-Function集成链路至少1个E2E测试
- [ ] pytest 6个测试全绿

---

### TREND-1：TrendScout增强 - 选题报告生成

**Red**
- [ ] `test_trend_scout_v2.py` — PDF生成测试、5A匹配度计算、人群契合度评分、批量报告、水印校验

**Green**
- [ ] `services/trend_scout_v2.py` — 结构化选题报告聚合
  - 热点趋势摘要聚合
  - 竞品内容结构分析
  - 5A阶段匹配度计算算法
  - 目标人群契合度评分算法
  - PoolPredictor先验区间注入（标注"参考区间"）
  - 品牌Logo注入
- [ ] WeasyPrint集成 — HTML转PDF
- [ ] 报告模板CSS — Jinja2模板

**验收**
- [ ] PDF报告含水印（下载人、时间）
- [ ] `engagement_interval`标注为"内部参考区间，非平台真实数据"
- [ ] pytest 6个测试全绿

---

### METH-1：MarketingMethodology 5A - AIPL全面替换

**Red**
- [ ] `test_methodology_5a.py` — 5A阶段模板、AIPL迁移、人群定向

**Green**
- [ ] `services/methodology_5a.py` — 5A模型定义
  - Aware/Appeal/Ask/Act/Advocate五阶段
  - AIPL→5A映射兼容层（存量内容平滑迁移）
  - 阶段-内容模板绑定
- [ ] `models/audience_segment.py` — 人群定向

**验收**
- [ ] AIPL→5A平滑迁移
- [ ] A2模板禁用绝对化用语
- [ ] A4模板禁用促销话术（兽药法规）
- [ ] pytest 5个测试全绿

---

## W16：新增Agent + 多平台扩展 + ContentSeries

### IMAGE-1：ImageForge图片配置引擎

**Red**
- [ ] `test_image_forge.py` — AI推荐、人工干预、排版配置、T2预检

**Green**
- [ ] `services/image_forge.py` — 图片-内容匹配
  - 调用AssetPool推荐接口获取候选素材
  - 排版配置（封面+正文配图）
  - 人工干预闭环
- [ ] LLM Hub多模态路由（AI生图）

**验收**
- [ ] 含产品信息禁止路由T2境外模型
- [ ] 强制经过人工审核
- [ ] pytest 5个测试全绿

---

### COMMENT-1：CommentHub合规版

**Red**
- [ ] `test_comment_hub.py` — 自动评论移除、强制确认、诱导拦截

**Green**
- [ ] `services/comment_hub.py` — 合规评论管理（CommentMonitor Agent）
  - AI建议+人工手动发布
  - 自动评论代码层彻底移除
  - 回复接口强制人工确认
  - 诱导话术自动拦截
- [ ] jieba情感分析

**验收**
- [ ] 自动评论入口不存在（代码层验证）
- [ ] 每日回复频率≤20条/账号
- [ ] pytest 5个测试全绿

---

### SERIES-1：ContentSeries内容系列化

**Red**
- [ ] `test_content_series.py` — 系列上下文、单账号约束、互评拦截

**Green**
- [ ] `services/content_series.py` — 系列管理
  - 系列上下文注入（`{{series.prev_content}}`）
  - 单账号内前后文呼应
  - 矩阵互评互赞代码层拦截

**验收**
- [ ] 仅限单账号内前后文呼应
- [ ] 禁止矩阵账号互评互赞
- [ ] pytest 4个测试全绿

---

### PLATFORM-1：PlatformRule多平台适配

**Red**
- [ ] `test_platform_rule_v2.py` — 抖音规则、广告号校验、平台差异

**Green**
- [ ] `services/platform_rule_douyin.py` — 抖音平台规则
  - 调用PlatformRule Function基座扩展
  - 兽药广告审查号强制校验
  - 引流话术L1拦截
  - 平台差异规则矩阵

**验收**
- [ ] 抖音内容须显著展示兽药广告审查批准文号
- [ ] pytest 5个测试全绿

---

## W17：审核台增强 + Workflow可视化

### HITL-2：Human-in-the-Loop弹性单人

**Red**
- [ ] `test_human_in_loop_v2.py` — 弹性策略、高风险检测、批量管控

**Green**
- [ ] `services/human_in_loop_v2.py` — 弹性审核
  - 弹性审核策略（标准内容单人/高风险双人）
  - 高风险标签自动检测（调用BrandKnowledge/VetDrugDB）
  - batch-approve批量操作管控（含高风险强制逐篇审核）

**验收**
- [ ] 高风险内容`PENDING_REVIEW`状态
- [ ] batch-approve含高风险强制逐篇审核
- [ ] pytest 5个测试全绿

---

### WF-2：Workflow可视化配置

**Red**
- [ ] `test_workflow_visual.py` — 强制校验、版本管理、Dry Run

**Green**
- [ ] `services/workflow_visual.py` — 可视化后端
  - 后端强制校验发布类模板含`human_approval`节点
  - 模板版本化管理
  - Dry Run模拟执行
- [ ] React Flow节点数据接口

**验收**
- [ ] 后端强制校验发布类模板含`human_approval`
- [ ] pytest 4个测试全绿

---

## W18：全链路E2E验证 + 安全审计

### E2E-1：V2.7.1-V3.1全链路集成测试

- [ ] `test_integration_v271.py` — 13项需求端到端验证
- [ ] Function层API可用性验证
- [ ] Agent→Function调用链路验证
- [ ] 工作流全节点跑通验证

### E2E-2：架构合规验收

- [ ] Agent直接数据库访问扫描（静态代码分析）— **必须0处**
- [ ] Function API标准化验证
- [ ] 五大基础Function数据一致性验证

### E2E-3：业务合规验收

- [ ] BrandKnowledge批文校验100%
- [ ] VetDrugDB宣称一致性100%
- [ ] AssetPool AI标识100%
- [ ] ImageForge T2预检100%
- [ ] CommentHub自动评论移除100%
- [ ] PlatformRule抖音广告号校验100%

---

**Sprint启动日期**: 2026-05-19（V3.1评审后）  
**计划完成日期**: 2026-06-22 (W14-W18)  
**评审状态**: 通过（架构对齐评审2026-05-19）  
**版本**: V2.7.1-V3.1对齐版
