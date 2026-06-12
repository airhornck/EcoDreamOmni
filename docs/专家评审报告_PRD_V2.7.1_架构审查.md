# EcoDream Omni PRD V2.7.1 专家评审报告 — 架构合理性审查

> **评审日期**: 2026-05-18  
> **评审对象**: PRD V2.7.1 新增 10 项需求（11项原始需求修正后）  
> **评审团队**: 产品专家 + 架构专家 + 算法专家 + 法务合规专家 + 运营专家  
> **遵循原则**: 开源 + 自研模式，开源承担通用能力，自研只做编排、特征与业务策略层

---

## 一、评审摘要

| 模块 | 评审结论 | 风险等级 | 开源/自研边界 | 关键修正 |
|------|---------|---------|--------------|---------|
| 1. TrendScout 增强 | ✅ 通过 | 低 | 报告渲染: 自研; PDF生成: 开源(WeasyPrint) | Mock数据标注为"参考区间" |
| 2. AssetPool | ✅ 通过 | 中 | 图库API: 第三方; AI生图: LLM Hub; 自研: 版权管理 | 三源混合比例≥70%运营上传 |
| 3. ImageForge | ✅ 通过 | 低 | 推荐算法: 自研; AI生图: LLM Hub | 人工干预节点强制 |
| 4. MarketingMethodology 5A | ✅ 通过 | 低 | 自研: 阶段模板; 开源: 无 | AIPL→5A 平滑迁移方案 |
| 5. ContentSeries | ✅ 通过 | 低 | 自研: 系列管理; 开源: Celery定时 | 禁止矩阵互评互赞 |
| 6. TimelineLibrary | ✅ 通过 | 低 | 自研: 季节库; 开源: croniter | 与CronHub集成 |
| 7. BrandKnowledge | ⚠️ 条件通过 | 高 | RAG: LangChain(仅Loader); 自研: 知识管理 | 兽药批文强制校验 |
| 8. Human-in-the-Loop 弹性单人 | ✅ 通过 | 中 | 自研: 审核台; 开源: 无 | 高风险内容强制双人复核 |
| 9. Workflow 可视化 | ✅ 通过 | 低 | 自研: 前端编排; 开源: React Flow | 后端强制校验human_approval |
| 10. CommentHub | ✅ 通过 | 中 | 自研: 分析; 开源: jieba | 自动评论代码层移除 |
| 11. PlatformRule 多平台 | ✅ 通过 | 中 | 自研: 规则引擎; 开源: 无 | 抖音兽药广告审查号校验 |

**总体结论**: 10项需求全部通过评审，其中BrandKnowledge需附加合规条件。所有需求遵循"开源+自研"原则，自研聚焦业务逻辑层。

---

## 二、分项详细评审

### 2.1 TrendScout 增强 — 选题报告生成

**开源组件选型**:
| 能力 | 选型 | 理由 |
|------|------|------|
| PDF渲染 | WeasyPrint | 开源MIT许可证,HTML转PDF稳定 |
| 报告模板 | Jinja2 + 自研CSS | 复用现有Prompt Registry模板机制 |
| 图表生成 | Recharts(前端) | 已在技术栈中 |

**自研边界**:
- 选题报告数据聚合逻辑
- 5A阶段匹配度计算
- 人群契合度评分
- 品牌Logo注入

**关键约束**:
1. `engagement_interval`必须标注为"内部参考区间，非平台真实数据"
2. 报告PDF下载须增加水印（下载人、时间）
3. Mock数据源与真实采集数据结构一致

---

### 2.2 AssetPool — 三源混合素材库

**开源组件选型**:
| 能力 | 选型 | 理由 |
|------|------|------|
| 图库API | Getty/Unsplash API | 第三方商业授权 |
| AI生图 | LLM Hub多模态路由 | 统一网关，已规划 |
| 图片处理 | Pillow | Python标准库,缩略图生成 |

**自研边界**:
- 版权管理核心逻辑
- 素材-内容匹配推荐
- 三源混合调度策略
- 合规标签体系

**关键约束**:
1. 运营上传占比≥70%，禁止过度依赖爬取/AI生成
2. `license_type`为空或`RESTRICTED`的素材禁止发布
3. AI生成图片强制附加"AI辅助创作"标签
4. 版权链凭证留存≥2年

---

### 2.3 ImageForge — 图片配置引擎

**架构位置**:
```
ContentForge输出正文
    ↓
ImageForge节点(Workflow Engine)
    ├─ AssetPool推荐匹配
    ├─ AI生成备选(LLM Hub)
    ↓
人工审核台(可选干预)
    ↓
ComplianceGuard(含图片合规检测)
```

**开源/自研边界**:
- **自研**: 图片-内容匹配算法、排版配置、人工干预记录
- **LLM Hub**: AI生图路由到境内多模态模型(T0)
- **AssetPool**: 素材来源

**关键约束**:
1. 含产品信息的生图禁止路由到T2境外模型
2. 图片配置节点强制经过人工审核
3. 运营干预差异写入`human_intervention`表

---

### 2.4 MarketingMethodology — 5A全面替换AIPL

**迁移策略**:
```python
# 平滑迁移方案
class MethodologyStage:
    framework: str  # "AIPL" | "5A"  支持双轨运行
    stage: str      # AIPL映射到5A的对应阶段
    migration_note: str  # 迁移说明
```

**关键约束**:
1. 预设模板中AIPL→5A的映射关系明确
2. A2(Appeal)模板禁用绝对化用语
3. A4(Act)模板禁用促销话术(兽药法规)
4. 人群定向数据不采集真实用户PII

---

### 2.5 ContentSeries — 内容系列化引擎

**架构集成**:
- **Workflow Engine**: 系列上下文注入(`{{series.prev_content}}`)
- **TimelineLibrary**: 系列与季节营销绑定
- **CronHub**: 系列定时发布

**关键约束**:
1. 仅限单账号内前后文呼应
2. 禁止矩阵账号互评互赞(代码层检测并拦截)
3. 商业系列强制标记`is_commercial_series`
4. 引用用户评论须脱敏

---

### 2.6 TimelineLibrary — 时间线库

**开源集成**:
- **croniter**: Cron表达式解析
- **Celery Beat**: 定时触发

**自研边界**:
- 季节事件库(驱虫季、换毛季等)
- 事件-内容主题映射
- 与BrandKnowledge的`prohibited_claims`联动

**关键约束**:
1. Commercial主题自动触发广告审核流程
2. 科普vs医疗广告界限清晰标注

---

### 2.7 BrandKnowledge — 企业知识库(RAG注入) ⚠️

**高风险点识别**:
| 风险 | 等级 | 缓解措施 |
|------|------|----------|
| 兽药广告审查 | 🔴 | `approval_number`强制校验 |
| RAG内容与批文不一致 | 🔴 | 季度一致性校验机制 |
| 竞品涉密信息 | 🔴 | 竞品信息禁止直接RAG注入 |
| 数据出境 | 🟡 | T2模型预检拦截 |

**开源/自研边界**:
- **LangChain**: 仅用Document Loader,不用Chains(过度封装)
- **向量存储**: PostgreSQL pgvector(已引入)
- **自研**: 知识库管理、批文一致性校验、RAG注入控制

**技术实现**:
```python
# RAG注入前强制校验
class BrandKnowledgeRAG:
    def inject(self, product_id: str, query: str) -> str:
        # 1. 批文号校验
        if not self.verify_approval_number(product_id):
            raise ComplianceError("缺失兽药批文号")
        
        # 2. 禁用词拦截
        if self.contains_prohibited_claims(query):
            raise ComplianceError("含禁用表述")
        
        # 3. 竞品信息隔离
        if self.is_competitive_research(product_id):
            return ""  # 禁止注入
        
        # 4. 执行检索
        return self.retrieve(query)
```

**关键约束**:
1. `ProductInfo.approval_number`必填
2. RAG结果含`prohibited_claims`自动拦截
3. `source==COMPETITIVE_RESEARCH`禁止RAG注入
4. 知识库修改双人复核+留痕≥2年

---

### 2.8 Human-in-the-Loop — 弹性单人审核

**权限模型**:
```
单人审核(标准内容)
    ↓ 触发条件: 高风险标签
双人复核(强制)
    - 医疗声明/价格信息/竞品对比/新SKU首发
```

**关键约束**:
1. Publisher发布确认原强制双人复核
2. 标准内容可弹性单人审核
3. 高风险内容`PENDING_REVIEW`状态，复核人未通过前Publisher拒绝接收
4. `batch-approve`批量操作时，含高风险内容强制逐篇审核

---

### 2.9 Workflow 可视化配置

**开源选型**:
- **React Flow**: 节点拖拽与连线可视化
- **自研**: 模板校验、版本管理、后端强制校验

**关键约束**:
1. MVP仅限串行Pipeline，禁止DAG分支
2. 后端强制校验发布类模板含`human_approval`节点
3. Dry Run模拟执行输入输出摘要≤200字符

---

### 2.10 CommentHub — 评论互动管理中心(合规版)

**红线功能(已彻底否决)**:
- ❌ 自动评论/自动回复
- ❌ 水军刷评/矩阵互评
- ❌ 私信群发

**合规能力**:
- ✅ AI建议+人工手动发布
- ✅ 评论情感分析(开源:jieba)
- ✅ 高价值评论识别
- ✅ 危机评论预警

**关键约束**:
1. 代码层彻底移除自动评论入口
2. 回复接口强制人工确认(`confirmed_by_operator: true`)
3. 含"加微信/扫码/点击链接"自动拦截
4. 每日回复频率≤20条/账号

---

### 2.11 PlatformRule — 多平台适配(XHS+抖音)

**平台差异矩阵**:
| 规则 | 小红书 | 抖音 | 实现 |
|------|--------|------|------|
| L1法律红线 | ✅ | ✅ | 统一规则 |
| L2平台规则 | ✅ | ✅ | 平台特定 |
| L3账号策略 | ✅ | ✅ | 平台特定 |
| L4动态风控 | ✅ | ✅(增强) | 平台特定 |
| 兽药广告审查号 | 可选 | 强制 | 抖音强制校验 |
| 引流话术 | 限制 | 严格禁止 | 抖音L1拦截 |

**关键约束**:
1. 抖音内容须显著展示兽药广告审查批准文号
2. "处方药/治疗/治愈"词汇抖音按L1拦截
3. 多平台发布须分别走PlatformRule预检
4. 跨平台适配后重新走ComplianceGuard审核

---

## 三、开源+自研模式总览

### 3.1 新增开源组件清单

| 组件 | 版本 | 许可证 | 支撑模块 | 自研边界 |
|------|------|--------|---------|---------|
| WeasyPrint | 59.0 | MIT | TrendScout PDF | 报告模板CSS |
| Pillow | 10.x | HPND | AssetPool缩略图 | 版权管理逻辑 |
| pgvector | 0.2.x | PostgreSQL License | BrandKnowledge向量检索 | RAG注入控制 |
| React Flow | 12.x | MIT | Workflow可视化 | 后端校验 |

### 3.2 自研代码量预估

| 模块 | 自研代码行数(预估) | 核心自研逻辑 |
|------|-------------------|-------------|
| TrendScout增强 | 800 | 报告聚合,5A匹配度计算 |
| AssetPool | 1200 | 版权管理,三源调度 |
| ImageForge | 600 | 图片-内容匹配,排版配置 |
| MarketingMethodology 5A | 800 | 阶段模板,AIPL迁移 |
| ContentSeries | 600 | 系列上下文管理 |
| TimelineLibrary | 400 | 季节事件库 |
| BrandKnowledge | 1500 | 批文校验,RAG控制 |
| Human-in-the-Loop | 800 | 弹性审核逻辑 |
| Workflow可视化 | 600 | 后端强制校验 |
| CommentHub | 1000 | 合规分析(无自动) |
| PlatformRule多平台 | 800 | 平台差异规则 |
| **合计** | **~8500行** | 业务逻辑层 |

---

## 四、架构风险与缓解

### 4.1 高风险项

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| BrandKnowledge批文不一致 | 法律合规 | 中 | 季度校验+`approval_number`强制 |
| AssetPool版权纠纷 | 法律/财务 | 低 | 三源比例控制+授权链留存 |
| CommentHub误开启自动评论 | 平台封号 | 低 | 代码层移除入口+接口强制校验 |
| T2模型数据出境 | 监管处罚 | 低 | LLM Hub预检拦截 |

### 4.2 技术债务预警

1. **AIPL→5A迁移**: 需在Phase 2完成全量迁移,保留双轨运行成本
2. **BrandKnowledge向量库**: MVP用pgvector,Phase 2评估专用向量数据库
3. **多平台规则膨胀**: 每新增平台规则复杂度O(n²),需设计规则继承机制

---

## 五、开发计划周次对齐

| 周次 | 新增模块 | 前置依赖 | 关键里程碑 |
|------|---------|---------|-----------|
| W15 | TrendScout增强,MarketingMethodology 5A,BrandKnowledge | AgentHub基线 | 选题报告PDF生成,5A模板可用 |
| W16 | AssetPool,ImageForge,ContentSeries,TimelineLibrary,PlatformRule多平台 | LLM Hub多模态 | 三源素材库可用,图文配置跑通 |
| W17 | Human-in-the-Loop弹性单人,Workflow可视化,CommentHub | Workflow Engine | 弹性审核配置,可视化编排上线 |
| W18 | 全链路E2E | 全部模块 | 11项需求端到端验证 |

---

## 六、执行决议

1. **全部通过**: V2.7.1 10项需求通过专家评审,可进入开发计划
2. **BrandKnowledge附加条件**: 必须实现`approval_number`强制校验和季度一致性检查
3. **开源边界确认**: 新增4个开源组件,全部符合MIT/HPND商用友好许可证
4. **自研聚焦**: 约8500行业务逻辑代码,聚焦编排/特征/策略层
5. **周次同步**: 开发计划v2.2更新W15-W18周次,详细设计v2同步架构

---

**评审人**: 产品专家/架构专家/算法专家/法务专家/运营专家(联合签署)  
**评审日期**: 2026-05-18  
**状态**: ✅ 通过(BrandKnowledge带条件)
