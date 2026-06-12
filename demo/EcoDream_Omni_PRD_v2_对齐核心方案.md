# EcoDream Omni PRD V2.3
## 对齐《文档2_最终可行性完整产品方案_素人号矩阵AI平台》（**v5.0 Final**）

> **变更范围**：以 v5.0 为唯一产品真源，校准需求表述、预测目标、废弃模块与 Phase 边界；并与《开发计划_素人号矩阵AI平台_v2》周次与交付物交叉引用。  
> **V2.3 修订要点**：在 V2.2 基础上增加 **§2.6 工程可靠性边界**——区分「结构预检 / 预发调整闭环」与「数据反馈闭环」的可实现层级；去掉**不可验证的因果增幅**承诺；回流默认**人工导入 + 可选半自动连接器**，覆盖率 KPI 绑定**最小样本量**。  
> **当前基线**：以仓库 CI 当时测试计数为准（历史表述如「154 测试全绿」仅作基线记录，迭代后请在 CI/README 更新数字）。  
> **目标**：MVP 阶段达成 v5.0 **Phase 1** 闭环（20 账号）：选题→生成→**互动量区间（宽先验）**预演→合规→发布→**可获取的实际互动**（导入为主）→**异步**校准；禁止实现 v5.0 已废弃能力。

---

## 〇、方案—PRD—开发计划 对齐矩阵（追溯）

| v5.0 方案章节 / 能力 | PRD 章节 | 开发计划锚点（**v2.2 周次为权威**，与旧版 Excel/截图如有冲突以本文为准） |
|---------------------|----------|--------------|
| 一、定位与边界（小红书 MVP、图文） | 全文约束 | Phase 1 |
| 四～八、四层风控 + AccountPool / PersonaPool | §2 已有增强 + AccountPool | W4–W5、W3.5 |
| 八、TrendScout（先 Mock/可控采集） | §2.1 | **MVP 补全 W11**（Mock + 手动导入） |
| 八、MarketingMethodology（AIPL） | §2.2 | **MVP 补全 W12** |
| 八、PoolPredictor（**互动量区间**，非 L0–L5） | §2.4 | W9 冷启动 + **Phase 2 W18** 探索期模型 |
| 八、DataAnalyst（区间命中、MAPE、归因） | §2.3 | **MVP 补全 W13** |
| 八、PlatformRule L3/L4 | §2.5、§2.6 | W6 已覆盖 L1/L2；**MVP 补全 W14** 做 L3/L4 + 证据链 + Publisher 对齐 |
| 八、SkillSmith / ContentInsight | v5.0 **Phase 2** | **W16、W19**（见开发计划 **v2.2**） |
| 结构预检 + 反馈闭环工程边界 | **§2.6** | W12–W14、W13；Celery 异步校准 |
| 九、LLM Gateway / 多模型路由 | 实现落在 LiteLLM + 自研路由 | 计划 §4–§5 |
| v5.0 **已废弃**：对抗辩论、MetaLearner、记忆联邦、流量池层级/CES 精确承诺 | **本文不出现需求** | Harness/文档索引 **不得** 再引用 MetaLearner、记忆联邦 |

---

## 一、当前代码与方案差距总表

### 1.1 模型层偏差（必须修正）

| 当前实现 | v5.0 方案要求 | 偏差等级 | 修正动作 |
|----------|---------------|----------|----------|
| `LinearRegression` 等简化回归 | **可解释特征**（目标 18 维，**缺失维用默认值并降权**）；输出 **点赞/评论/收藏** 的区间与中位数 + `interval_mode` | 🔴 P0 | 演进 `prediction_engine.py`：优先 **QuantileRegressor** / 先验宽区间；Phase 2+ 再 XGBoost |
| 无区间不确定性量化 | 贝叶斯线性回归或等效 **可信区间** | 🔴 P0 | API 返回 `interval_lower/upper` 或分位数 |
| （旧 PRD）有序 Logit L0–L5 | **v5.0 已废弃**「流量池层级」预测 | ⚫ 不做 | 从数据模型与 UI 移除 L0–L5 |
| 无 ARIMA / 时段竞争 | v5.0 Phase 2+ **时段竞争系数**（ARIMA 为可选实现） | 🟡 P1 | Phase 2：Publisher / 预演面板共用竞争系数服务 |
| Thompson 采样（旧 PRD） | v5.0 未强制；可作为 **策略实验** 可选项 | 🟢 P2 | 不与「L0–L5」绑定；若做，仅用于模板/A/B 臂选择 |

### 1.2 缺失模块（必须新增）

| 模块 | 方案章节 | Phase | 当前状态 | 优先级 |
|------|----------|-------|----------|--------|
| **TrendScout** | 文档2 §8.4 | Phase 1（MVP：Mock + 手动导入） | 视代码基线 | 🔴 P0 |
| **MarketingMethodology** | 文档2 §6 + 架构 MarketingMethod | Phase 1 | 视代码基线 | 🔴 P0 |
| **DataAnalyst** | 文档2 §8.9 | Phase 1 | 视代码基线 | 🔴 P0 |
| **PlatformRule Engine（L3/L4）** | 文档2 §8.3 | Phase 1 | 常仅 L1–L2 | 🔴 P0 |
| **PersonaPool（完整版）** | 文档2 §8.2 | Phase 1 | 基础模型 | 🟡 P1 |
| **SkillSmith** | 文档2 §8.10、§十六 Phase 2 | Phase 2 | 视代码基线 | 🟡 P1 |
| **ContentInsight** | 文档2 §8.11、§十六 Phase 2 | Phase 2 | 视代码基线 | 🟡 P1 |
| ~~**MetaLearner**~~ | **v5.0 已移除** | — | — | ⚫ 不规划 |
| ~~**对抗辩论**~~ | **v5.0 已移除** | — | — | ⚫ 不规划 |

### 1.3 已有模块需增强

| 模块 | 当前能力 | v5.0 要求 | 增强动作 |
|------|----------|-----------|----------|
| **AccountPool** | 指纹+健康评分 | +自动熔断+状态机+IP 代理/配额 | 扩展状态转换、每日配额、warming/restricted |
| **ContentForge** | Voice 注入生成 | +AIPL 阶段模板（MarketingMethodology） | 对接阶段模板与合规标签 |
| **ComplianceGuard** | L1–L3 | +证据链留存 ≥2 年 + PlatformRule L4 动态规则 | 审核记录与动态规则 CRUD |
| **Publisher** | 错峰调度 | +频率阶梯 + 排版随机化；时段可接竞争系数 | 与 PoolPredictor / 规则 L4 对齐 |
| **Dashboard** | 任务看板 | +**互动量区间**预演 + 智能选题 + 昨日战报 | 禁止展示「流量池层级」为预测结论 |
| **Agent Orchestra** | 串行 Pipeline | +ACP + 共享状态（会话级） | **不引入**对抗辩论链路 |

---

## 二、P0 模块详细设计（立即执行）

### 2.1 TrendScout 趋势侦察

**职责**：热点爬取Mock、趋势报告、人设克隆草案

**MVP范围（与开发计划 W11 对齐）**：
- 不提供全量真实爬虫（平台签名与合规边界），提供 **Mock 数据源** + **结构化趋势报告**；与 v5.0「频率控制 + 白名单」一致，真实采集列为 **Phase 2+ 可选能力**，须单独法务评审。
- 运营手动输入/导入热点话题，系统自动生成趋势报告结构。
- **人设来源**：仅允许 **手动创建 + AI 辅助生成**（v5.0 §8.2）；禁止「爬取克隆对标账号」作为默认产品能力。可对「对标笔记 URL」做 **运营粘贴后的脱敏摘要**（标题/话题/结构标签），不自动拉取私密数据。

**API设计**：
```
POST /trend-scout/reports       # 创建趋势报告（输入关键词+阶段）
GET  /trend-scout/reports       # 列表查询
GET  /trend-scout/reports/{id}  # 详情（含热点条目）
POST /trend-scout/persona-draft  # 提交**运营填写的结构化要点**或脱敏后的公开字段摘要，返回人设草案（非爬虫克隆）
```

**数据模型**：
```python
@dataclass
class TrendReport:
    id: str
    query: str                    # 查询关键词
    stage_filter: str             # AWARENESS/INTEREST/PURCHASE/LOYALTY
    crawl_time: str
    results: List[TrendItem]      # 热点条目
    platform_risk_signals: List[RiskSignal]

@dataclass
class TrendItem:
    rank: int
    title: str
    title_structure: str          # 如「数字+痛点+时间跨度」
    engagement_hint: str        # 可选：「高/中/低」或粗粒度分档，非平台真实 CES
    stage: str                    # AWARENESS / INTEREST / PURCHASE / LOYALTY
    tags: List[str]
    post_time: str
    post_day: str
    structural_signals: Dict      # 标题模式、话题簇等（不含流量池层级）
```

### 2.2 MarketingMethodology 方法论中枢

**职责**：AIPL阶段定义、内容结构模板、KPI目标配置

**MVP范围（W12补做）**：
- AIPL四阶段定义（AWARENESS/INTEREST/PURCHASE/LOYALTY）
- 每阶段的内容结构模板（hook/body/cta/disclaimer）
- 阶段转换条件配置
- KPI目标配置

**API设计**：
```
GET  /methodologies              # 列表（AIPL/5A等框架）
GET  /methodologies/{id}/stages  # 某方法论的所有阶段
GET  /methodologies/stages/{stage_id}/template  # 阶段内容模板
POST /methodologies/stages/{stage_id}/evaluate  # 评估内容是否符合阶段要求
```

**数据模型**：
```python
@dataclass
class MethodologyStage:
    id: str
    framework: str                # AIPL
    stage: str                    # AWARENESS
    stage_name: str               # 认知期
    content_template: Dict        # hook/body/cta/disclaimer结构
    kpi_targets: Dict             # exposure、互动率、区间覆盖率等；CES 仅可选派生，不作为 MVP 硬门禁
    compliance_tags: List[str]    # 必须包含的合规标签
    forbidden_elements: List[str] # 禁用元素
    stage_transition_criteria: Dict  # 晋升下阶段条件
    recommended_persona_types: List[str]
```

### 2.3 DataAnalyst 数据分析师

**职责**：24h回流报表、MAPE计算、归因分析、模型校准触发

**MVP范围（与开发计划「MVP 补全冲刺」W13 对齐；扩展归因可延续至 W14）**：
- **实际互动数据入口（工程约束）**：默认 **运营 CSV/表单导入**（`content_id`、时间窗、`likes/comments/saves` 等）；可选「连接器」在 **PlatformAccountManager 合法登录态**下做**只读、低频、可降级**拉取（易随平台改版失效，不作为 MVP 必达能力）。**禁止**将全矩阵无人值守爬取写进 MVP SLA。
- 内容发布后 **T+24h～T+48h** 窗口内生成报告（允许手动触发）；无真数时仍可用**模拟数据**跑通管道与单测。
- **主指标**：点赞/评论/收藏的**实际值 vs 预测区间**；计算**区间覆盖率**与分指标 MAPE；**覆盖率 KPI（如 ≥70%）仅在「有效标注样本 ≥ `N_min`（默认 30，可配置）」子集上考核**（见 §2.6），冷启动宽区间阶段标注为**参考不考核**。
- **CES**（若保留字段）：仅作可选派生展示或内部实验指标，**不作为** MVP 合规验收主指标（v5.0 已废弃「CES 精确承诺」）
- 基础归因分析（Top 特征影响，与 PoolPredictor 特征维度一致）
- 模型校准建议：**异步批任务**（Celery + Redis，**非实时**）检查 MAPE/漂移，超阈值则写入「待重训」队列并由人工或定时任务触发训练脚本；**禁止**承诺「每次发帖后秒级在线学习」。

**API设计**：
```
POST /data-analyst/reports       # 为某篇内容生成24h报告
GET  /data-analyst/reports/{id}  # 查看报告
GET  /data-analyst/dashboard     # 昨日战报聚合
GET  /data-analyst/attribution/{content_id}  # 归因分析
POST /data-analyst/calibrate     # 触发模型校准检查
```

**数据模型**：
```python
@dataclass
class DataReport:
    id: str
    account_id: str
    content_id: str
    period: str                   # 24h/7d
    actual_metrics: Dict          # exposure/likes/saves/comments/shares/follows（+ 可选 ces 派生）
    prediction_comparison: Dict   # 各互动指标的 predicted_interval vs actual、within_range、mape、coverage
    attribution: Dict             # top_features影响
    model_calibration: Dict       # 校准建议
```

### 2.4 PoolPredictor 修正（分位数 / 先验区间为主，开源优先）

**当前问题**：点估计式线性回归无法稳定输出**可用预测区间**，与 v5.0 §8.8「互动量区间」主目标不一致。

**与 v5.0 对齐且工程可落地的硬要求**：
- **冷启动（MVP 必达）**：同类/全库聚合先验 + **刻意放宽**的分位数或残差估计区间（**开源**：`scikit-learn` `QuantileRegressor` / 分位点 + 简单校准，或分段常数先验）；输出必须带 **`interval_mode: prior|fitted`**，UI 对 `prior` 展示「参考区间」文案。
- **MVP 输出**：对**点赞、评论、收藏**分别给出 `lower / median / upper` 与 `confidence`（可基于区间宽度与样本量启发式，**非**平台真实置信）；禁止将「流量池层级 L0–L5」作为产品预测结论。
- **探索期（Phase 2）**：在 **`N_min` 达标**后启用 **XGBoost / 随机森林分位数**、可选 **SHAP**（`vendor/ml-libraries`）；小样本下 **禁止**把深度网络或集成模型写进必达路径。
- **优化建议**：仅允许输出**清单式启发项**（标题长度、标签个数、时段等），**禁止**展示未做随机实验验证的**因果增幅百分比**（如「+18% 互动」）；可选 A/B 为 Phase 2+ 独立模块。
- **Thompson 采样**（可选，P2）：默认关闭；若启用仅用于模板臂选，须法务与产品双签。

**修正方案（接口语义）**：
```python
# 演进 prediction_engine：输出多指标区间 + 覆盖率可测

def predict_engagement_intervals(features: np.ndarray, prior: Dict) -> Dict:
    """返回 likes/comments/saves 的区间与中位数 + confidence + interval_mode；不得输出流量池层级。"""
    ...
```

**API变更**：
```
POST /predictions              # 响应含 likes/comments/saves 的 interval 与 confidence
GET  /predictions/{id}         # 详情与同上；禁止返回 l0_l5_distribution 类字段作为默认 UI 数据源
```

### 2.5 PlatformRule Engine（L3/L4）

**当前**：只有L1法律红线、L2平台规则（静态关键词）

**新增**：
- **L3 账号状态规则**：新号/老号差异化策略（日发频率、时段限制）
- **L4 动态风控规则**：临时风控、节日策略、时段竞争系数
- **规则CRUD**：运营可配置规则
- **违规归因**：规则命中后的归因分析

**API设计**：
```
GET  /platform-rules           # 规则列表（支持按layer过滤）
POST /platform-rules           # 创建规则（需要admin权限）
GET  /platform-rules/{id}      # 规则详情
PATCH /platform-rules/{id}     # 更新规则
DELETE /platform-rules/{id}    # 删除规则
GET  /platform-rules/attribution/{content_id}  # 违规归因
```

### 2.6 工程可靠性：内容结构预检与「预发 / 反馈」双闭环（可用性边界）

> **原则**：开源承担通用能力（校验、ML 基座、队列、LLM 路由），自研只做编排、特征与业务策略。**不承诺**平台黑盒可逆推或全自动无监督优化。

#### A. 结构预测与调整闭环（发布前，**与互动预测解耦**）

| 层级 | 能力 | 开源/自研 | MVP 是否必达 |
|------|------|-----------|--------------|
| **S0 结构合规** | 方法论模板字段是否齐全（hook/body/cta/disclaimer）、Zod/JSON Schema 校验 | Zod（前端）+ 同源 schema（后端）；可选 Pydantic | **必达** |
| **S1 结构质量** | LLM 按 rubric 打分或结构化点评（是否口语化、是否过营销等） | **LiteLLM** 路由多模型；自研 prompt 与 rubric | **推荐** |
| **S2 结构→互动** | 用同一套内容特征进 PoolPredictor | sklearn 等 | **弱相关**；不得在文案中暗示「改结构必涨互动」 |

**调整闭环（可实现）**：用户在预演面板采纳建议 → 调用 ContentForge **regenerate 或 patch**（带 `parent_content_id`）→ 再次走 ComplianceGuard；**禁止** MVP 要求「自动循环改写直至区间收窄」无人值守闭环。

#### B. 数据反馈闭环（发布后）

| 步骤 | MVP 实现 | 说明 |
|------|-----------|------|
| 采集 | **导入为主**；连接器为辅 | 连接器失败须降级为导入，不阻塞发贴 |
| 对齐 | `content_id` 与平台帖映射表 | 自研表结构 |
| 计算 | 覆盖率、MAPE、简单归因（系数/排列重要性） | sklearn；SHAP Phase 2+ |
| 校准 | Celery 定时或手动触发 | **批处理**；与在线推理解耦 |

#### C. 可靠性声明（写入验收说明）

- **系统可用性 ≥99.5%** 仅指**自建 SaaS API** 月度可用性；不含第三方 LLM、住宅代理、平台站点可用性。
- **自动化发布成功率** 依赖登录态与反爬变化，须单独定义「可重试失败」口径。

---

## 三、前端增强设计

### 3.1 流量预演面板（Dashboard新增）

> **与 v5.0 §8.8 / §十三一致**：默认仅展示**互动量区间**与优化建议；**禁止**用「流量池层级 L0–L5」或「CES 精确值」作为预演主结论（已废弃指标，见文档2 §十五「废弃指标」）。

```
┌─────────────────────────────────────────────────────────────┐
│  内容预览：「猫咪驱虫避坑指南，这3个误区90%的人都不知道」        │
├─────────────────────────────────────────────────────────────┤
│  互动量预演（`interval_mode=prior|fitted`；MVP 多为先验宽区间）   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  点赞：预计 25–60（中位数 42）  │ 置信度 65%        │   │
│  │  评论：预计 5–15（中位数 9）    │                   │   │
│  │  收藏：预计 8–20（中位数 13）   │                   │   │
│  └─────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  💡 启发式优化清单（非因果承诺；A/B 验证见 Phase 2+）            │
│  ① 标题含具体数字「3个」→ 与模板 rubric 一致 ✅               │
│  ② 可考虑增加话题标签 #新手养猫（经验规则，不保证增幅）→ [添加] │
│  ③ 发布时段建议：周三 20:00（内部竞争系数启发 0.7）→ [定时]   │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 智能选题推荐（Dashboard新增）

- TrendScout 每日更新热点
- 标注审核松紧度
- 一键生成内容按钮

### 3.3 昨日战报（Dashboard新增）

- DataAnalyst 在 **导入/连接器** 可用数据上的 24h 聚合
- 发布篇数、**预测区间命中率**、平均点赞/评论/收藏、环比；可选派生指标（如 CES）不得作为唯一成功口径
- [查看详细报告] 入口

---

## 四、测试策略

### 4.1 P0模块测试矩阵

| 模块 | 测试文件 | 测试数 | 关键场景 |
|------|----------|--------|----------|
| TrendScout | `test_trend_scout.py` | 5 | 创建报告/查询详情/人设克隆/阶段过滤 |
| MarketingMethodology | `test_methodology.py` | 5 | 阶段模板/内容评估/转换条件 |
| DataAnalyst | `test_data_analyst.py` | 5 | 回流报告/MAPE计算/归因分析/校准触发 |
| PoolPredictor修正 | `test_pool_predictor.py` | +3 | 多指标区间/覆盖率或分位数；Thompson 若未启用则标注 skip |
| PlatformRule | `test_platform_rules.py` | 5 | L3/L4规则CRUD/违规归因/动态生效 |

### 4.2 回归策略

- 基线：154测试全绿
- 每新增一个P0模块，测试数+5，全量回归
- PoolPredictor修正：需更新现有8个测试的数据断言（增加可信区间字段）

---

## 五、执行顺序建议

**第1轮（立即）**：PoolPredictor修正（影响现有测试，先处理）  
**第2轮（并行）**：TrendScout + MarketingMethodology（独立模块，互不影响）  
**第3轮**：DataAnalyst + PlatformRule（依赖前两者数据）  
**第4轮**：前端面板增强（依赖后端API就位）  
**第5轮**：全量E2E验证

---

## 六、专家组终审建议（产品 / 架构 / 算法 / 法务 / 运营）

以下结论以《文档2》v5.0 为真源，用于约束 PRD 与《开发计划》后续迭代。

| 角色 | 建议摘要 |
|------|-----------|
| **产品** | 周次命名以「MVP 补全冲刺」承接文档2 Phase 1 缺口（TrendScout、MarketingMethodology、DataAnalyst、PlatformRule L3/L4），再进入 Phase 2（SkillHub、SkillSmith、ContentInsight、XGBoost 等）；禁止在验收口径中复活 L0–L5 / CES 精确承诺。 |
| **架构** | Agent Harness 与 hermes 复用描述须与 v5.0 一致：**不得**将已移除的 MetaLearner、记忆联邦、对抗辩论纳入需求或对外承诺；跨账号经验沉淀通过 **SkillSmith + PersonaPool + 审计数据** 实现。 |
| **算法** | PoolPredictor / DataAnalyst 的默认指标统一为**点赞/评论/收藏区间 + 覆盖率 + MAPE**；ARIMA 时段竞争、Thompson 臂选为 Phase 2+ 可选项并单独评审。 |
| **法务合规** | TrendScout MVP 维持 **Mock + 手动导入**；任何真实爬虫与签名对抗须独立法务评审与日志留存策略（文档2 §8.4、§十四）。 |
| **工程 / SRE** | 第三方 LLM、代理、平台站点**不计入**自建 99.5% SLA；回流 **导入优先**；预测与校准 **异步解耦**；监控连接器降级路径。 |
| **运营交付** | 驾驶舱文案与报表默认对齐「素人矩阵 + 合规红线 + 区间预演」，避免短剧/视频平台 PRD 路径混入本仓库基线文档索引。 |

**执行决议**：采纳上述约束；本文 **V2.3** 与《开发计划》**v2.2** 同步修订周次、Harness 表述及 **§2.6 双闭环工程边界**。


---

## 七、新增需求：Agent 全生命周期管理、活跃监控与统计（V2.4 增补）

> **变更范围**：在 V2.3 基础上新增 **AgentHub（管理与配置）**、**AgentWatch（活跃监控）**、**AgentMetrics（统计与分析）** 三大模块，补齐 v5.0 方案中「Agent Orchestra」仅描述串行 Pipeline 但缺乏运行时可观测性与治理能力的缺口。  
> **对齐原则**：与现有 Agent Orchestra（串行 Pipeline + ACP + 会话级共享状态）无缝集成；不引入已废弃概念（MetaLearner、对抗辩论、记忆联邦）；默认使用开源/标准协议（OpenTelemetry、Prometheus、Celery），自研仅做编排与业务语义层。  
> **MVP 边界**：Phase 1 达成「注册发现 + 心跳健康 + 基础统计看板」闭环；Phase 2 扩展「链路追踪 + 成本归因 + 自动熔断」。

---

### 7.1 新增模块与现有架构对齐矩阵

| 新增模块 | 职责 | 对接现有模块 | 开发计划锚点 | Phase |
|---------|------|-------------|-------------|-------|
| **AgentHub** | Agent 注册、配置版本化、生命周期、权限 | Agent Orchestra、LLM Gateway、AccountPool / PersonaPool | **MVP 补全 W15** | Phase 1 |
| **AgentWatch** | 心跳健康、实时状态、链路追踪、异常告警 | Agent Orchestra、Celery、Publisher、ComplianceGuard | **MVP 补全 W15–W16** | Phase 1 |
| **AgentMetrics** | 任务统计、Token 成本、质量评分、漂移检测 | DataAnalyst、PoolPredictor、LLM Gateway | **MVP 补全 W16**；成本归因 W19 | Phase 1（基础）+ Phase 2（深度） |
| **Agent Cockpit（前端）** | Agent 驾驶舱：状态看板 + 统计报表 + 配置面板 | Dashboard | **MVP 补全 W17** | Phase 1 |

---

### 7.2 AgentHub — Agent 管理与配置中心

#### 7.2.1 职责与 MVP 范围（W15）

- **Agent 注册与发现**：所有业务 Agent（TrendScout、ContentForge、ComplianceGuard、Publisher、DataAnalyst、PoolPredictor、MarketingMethodology、PlatformRule）在启动时向 AgentHub 注册；支持**手动注册**（MVP）与**服务发现**（Phase 2）。
- **配置版本化**：每个 Agent 的配置（prompt 模板、模型路由参数、超时阈值、重试策略）以**版本化快照**存储；支持「当前生效版本 / 历史版本 / 草稿版本」三态管理；**禁止**无版本记录的在线热改（审计要求）。
- **环境隔离**：同一 Agent 支持 `dev` / `staging` / `prod` 多环境配置隔离；发布流程为「草稿 → staging 灰度 → prod 全量」。
- **权限与访问控制**：基于角色的 Agent 调用权限（RBAC）；区分「编排者（Orchestrator）调用权限」与「运营人员只读权限」；敏感 Agent（如 Publisher 发布、ComplianceGuard 审核通过）须**双人复核**或**审批流**。
- **依赖管理**：声明式管理每个 Agent 的依赖——LLM 模型（通过 LLM Gateway 路由）、外部 Tool（如爬虫连接器、平台 API）、数据源（如 AccountPool、PersonaPool）；依赖缺失或降级时 Agent 状态自动置为 `degraded`。

#### 7.2.2 API 设计

```
# Agent 生命周期
POST   /agent-hub/agents              # 注册 Agent（含配置快照 v1）
GET    /agent-hub/agents              # 列表（支持按 status / role / env 过滤）
GET    /agent-hub/agents/{agent_id}   # 详情（含当前生效配置版本）
PATCH  /agent-hub/agents/{agent_id}   # 更新元数据（非配置内容）
DELETE /agent-hub/agents/{agent_id}   # 注销（软删除，保留审计）

# 配置版本化
POST   /agent-hub/agents/{agent_id}/configs           # 创建新版本配置
GET    /agent-hub/agents/{agent_id}/configs           # 历史版本列表
GET    /agent-hub/agents/{agent_id}/configs/{ver}    # 指定版本详情
POST   /agent-hub/agents/{agent_id}/configs/{ver}/activate  # 激活指定版本
POST   /agent-hub/agents/{agent_id}/configs/{ver}/rollback  # 回滚

# 环境管理
GET    /agent-hub/agents/{agent_id}/envs              # 获取多环境配置映射
PATCH  /agent-hub/agents/{agent_id}/envs/{env}       # 更新某环境指向的配置版本

# 依赖声明
GET    /agent-hub/agents/{agent_id}/dependencies       # 依赖清单（LLM/Tool/Data）
POST   /agent-hub/agents/{agent_id}/health-check      # 手动触发依赖健康探测

# 权限与审批
GET    /agent-hub/agents/{agent_id}/permissions        # 权限矩阵
POST   /agent-hub/agents/{agent_id}/permissions      # 授权/变更权限
GET    /agent-hub/approvals                          # 配置变更审批流列表
POST   /agent-hub/approvals/{id}/approve             # 审批通过
```

#### 7.2.3 数据模型

```python
@dataclass
class AgentRegistration:
    id: str                       # agent 唯一标识，如 "content-forge-v1"
    name: str                     # 可读名称
    role: str                     # TREND_SCOUT / CONTENT_FORGE / COMPLIANCE_GUARD / 
                                  # PUBLISHER / DATA_ANALYST / POOL_PREDICTOR / 
                                  # MARKETING_METHODOLOGY / PLATFORM_RULE / ORCHESTRATOR
    description: str
    owner: str                    # 负责人（邮箱/企业微信ID）
    status: str                   # REGISTERED / ACTIVE / DEGRADED / PAUSED / OFFLINE
    created_at: str
    updated_at: str

@dataclass
class AgentConfigSnapshot:
    id: str
    agent_id: str
    version: int                  # 自增版本号
    env: str                      # dev / staging / prod
    config_payload: Dict          # 具体配置：{prompt_template_id, llm_route, timeout, retries, ...}
    checksum: str                 # SHA-256，防篡改
    created_by: str
    created_at: str
    status: str                   # DRAFT / ACTIVE / ARCHIVED / ROLLED_BACK
    approval_status: str          # PENDING / APPROVED / REJECTED（敏感 Agent 必填）

@dataclass
class AgentDependency:
    agent_id: str
    dep_type: str                 # LLM / TOOL / DATA_SOURCE
    dep_name: str                 # 如 "gpt-4o-mini" / "xhs-connector" / "account_pool"
    dep_status: str               # HEALTHY / DEGRADED / DOWN / UNKNOWN
    last_check: str
    failover_config: Dict         # 降级策略：如 LLM 降级到备用模型

@dataclass
class AgentPermission:
    agent_id: str
    principal: str                # user / service_account
    principal_type: str           # USER / SERVICE
    actions: List[str]            # READ / INVOKE / CONFIG / DELETE
    granted_by: str
    granted_at: str
    expires_at: str               # 可选，临时授权
```

---

### 7.3 AgentWatch — Agent 活跃监控与异常检测

#### 7.3.1 职责与 MVP 范围（W15–W16）

- **心跳与健康检查**：每个 Agent 每 30s 上报心跳（可配置）；心跳缺失超过 3 个周期标记为 `UNHEALTHY`；Orchestrator 在调度前强制检查目标 Agent 健康状态。
- **实时状态看板**：展示所有 Agent 的当前状态（空闲 / 运行中 / 故障 / 熔断）、当前任务、队列堆积数；支持按 role / env 过滤。
- **跨 Agent 链路追踪**：基于 **OpenTelemetry** 标准，对一次内容生产 Pipeline（选题→生成→合规→预演→发布→数据回流）生成统一 `trace_id`；每个 Agent 调用为一个 `span`，包含输入摘要、输出摘要、耗时、Token 数、模型版本；**MVP 仅要求 trace 采集与存储，不要求实时链路图**。
- **异常检测（规则引擎）**：
  - **循环检测**：同一 Agent 在 5 分钟内对同一 `content_id` 重复调用 ≥3 次，触发 `LOOP_ALERT`。
  - **超时检测**：单 Agent 执行超过配置阈值（如 ContentForge 默认 60s），触发 `TIMEOUT_ALERT`。
  - **工具失败检测**：外部 Tool（如平台 API、LLM Gateway）连续失败 ≥3 次，触发 `TOOL_DEGRADED`，并通知 AgentHub 更新依赖状态。
  - **成本异常**：单任务 Token 消耗超过同类任务 p95 的 200%，触发 `COST_ANOMALY`（Phase 2 细化）。
- **告警与通知**：告警通道支持「企业微信 / 钉钉 / 邮件」；分级：
  - `P0`（Publisher 发布失败、ComplianceGuard 绕过）→ 即时电话/短信 + 值班群；
  - `P1`（Agent 离线、工具降级）→ 企业微信；
  - `P2`（成本异常、质量漂移）→ 邮件日报。

#### 7.3.2 API 设计

```
# 心跳与状态
POST   /agent-watch/heartbeat         # Agent 上报心跳（由 Agent SDK 自动调用）
GET    /agent-watch/agents/{agent_id}/status      # 实时状态（含当前任务、队列深度）
GET    /agent-watch/dashboard           # 全量 Agent 状态聚合（前端轮询或 SSE）

# 链路追踪
GET    /agent-watch/traces              # 链路列表（按 trace_id / time_range / content_id）
GET    /agent-watch/traces/{trace_id}   # 链路详情（span 树）
GET    /agent-watch/traces/{trace_id}/spans/{span_id}  # 单 span 详情（含输入/输出摘要）

# 异常与告警
GET    /agent-watch/alerts              # 告警列表（支持按 severity / agent_id / status）
PATCH  /agent-watch/alerts/{id}/ack     # 告警确认
GET    /agent-watch/alerts/{id}/root-cause  # 根因分析（基于规则 + 链路关联）

# 规则配置（运营可配置）
GET    /agent-watch/rules              # 异常检测规则列表
POST   /agent-watch/rules              # 创建规则（需 admin）
PATCH  /agent-watch/rules/{id}        # 更新规则
DELETE /agent-watch/rules/{id}        # 删除规则
```

#### 7.3.3 数据模型

```python
@dataclass
class AgentHeartbeat:
    agent_id: str
    timestamp: str
    status: str                   # HEALTHY / BUSY / IDLE / UNHEALTHY
    current_task_id: Optional[str]
    queue_depth: int              # 待处理任务数
    memory_mb: float              # 可选，容器内存
    cpu_percent: float            # 可选
    version: str                  # 当前运行的代码版本 / 配置版本

@dataclass
class AgentTrace:
    trace_id: str
    content_id: str               # 关联业务内容
    pipeline_type: str            # CONTENT_CREATION / DATA_ANALYSIS / TREND_SCOUT
    start_time: str
    end_time: Optional[str]
    status: str                   # RUNNING / COMPLETED / FAILED / TIMEOUT
    total_tokens: int             # 全链路 Token 合计
    total_cost_usd: float         # 全链路成本估算（Phase 2 精确化）

@dataclass
class AgentSpan:
    span_id: str
    trace_id: str
    parent_span_id: Optional[str]
    agent_id: str
    agent_role: str
    start_time: str
    end_time: str
    duration_ms: int
    status: str                   # OK / ERROR / TIMEOUT
    input_summary: str            # 输入摘要（前 200 字符，禁止存完整 prompt 中的密钥）
    output_summary: str           # 输出摘要
    token_count: int
    model_version: str            # 如 "gpt-4o-2026-05"
    tool_calls: List[Dict]       # 调用的工具列表

@dataclass
class AgentAlert:
    id: str
    severity: str                 # P0 / P1 / P2
    alert_type: str                 # LOOP / TIMEOUT / TOOL_DEGRADED / COST_ANOMALY / HEALTH_CHECK_FAIL
    agent_id: str
    trace_id: Optional[str]
    content_id: Optional[str]
    message: str
    created_at: str
    status: str                     # OPEN / ACKED / RESOLVED / IGNORED
    acked_by: Optional[str]
    resolved_at: Optional[str]
    root_cause: Optional[str]       # 根因摘要（规则生成或人工填写）
```

---

### 7.4 AgentMetrics — Agent 统计与质量分析

#### 7.4.1 职责与 MVP 范围（W16；成本归因 W19）

- **任务完成率**：统计每个 Agent 的「成功 / 失败 / 超时 / 人工干预」占比；**任务完成率 = 成功且无人工干预的次数 / 总调用次数**；目标 ≥90%（参考 Anthropic 企业运营数据，人机干预率从 5% 升至 12% 是系统级故障的前兆）。
- **Token 消耗与成本归因**：通过 LLM Gateway 统一采集每个 Agent 每次调用的 Token（input / output）；按 Agent / 按 content_id / 按账号维度聚合成本；**MVP 仅做「按 Agent 日维度」汇总，Phase 2 做 content_id 级精确归因**。
- **延迟分布**：采集每个 Agent 的 `duration_ms`，输出 p50 / p95 / p99；用于识别性能退化。
- **质量评分（Rubric-based）**：
  - 对 ContentForge 输出：按 MarketingMethodology 模板 rubric 自动评分（结构完整性、口语化程度、合规标签命中）。
  - 对 ComplianceGuard：按「误杀率 / 漏杀率」评估（需人工抽样标注）。
  - 对 PoolPredictor：按 DataAnalyst 的 MAPE / 覆盖率评估。
  - **评分由 LLM-as-Judge 或规则引擎完成，禁止仅依赖人工**；MVP 仅对 ContentForge 和 ComplianceGuard 启用自动评分。
- **人机干预率**：记录运营人员在 Dashboard 上「手动修改 Agent 输出 / 跳过 Agent / 强制重试」的次数与比例；**人机干预率是系统健康度的领先指标**。
- **漂移检测（Phase 2）**：对比当前版本与上一版本的「平均质量分 / 平均延迟 / 平均 Token 数」，若差异超过阈值（如质量分下降 >10%），触发 `VERSION_DRIFT_ALERT`。

#### 7.4.2 API 设计

```
# 统计聚合
GET    /agent-metrics/dashboard          # 全局统计看板（日维度）
GET    /agent-metrics/agents/{agent_id}  # 单 Agent 统计（任务率 / 延迟 / 成本 / 质量）
GET    /agent-metrics/agents/{agent_id}/timeseries  # 时序数据（latency / token / success_rate）

# 质量评分
GET    /agent-metrics/agents/{agent_id}/quality-scores   # 质量评分列表
POST   /agent-metrics/agents/{agent_id}/quality-scores/eval  # 手动触发评估（对历史任务）

# 成本归因
GET    /agent-metrics/cost-attribution     # 成本归因报表（按 Agent / 按日）
GET    /agent-metrics/cost-attribution/content/{content_id}  # 单内容成本（Phase 2）

# 人机干预
GET    /agent-metrics/human-interventions  # 干预记录列表
POST   /agent-metrics/human-interventions  # 记录一次干预（由 Dashboard 调用）

# 漂移检测（Phase 2）
GET    /agent-metrics/agents/{agent_id}/drift  # 漂移检测报告
```

#### 7.4.3 数据模型

```python
@dataclass
class AgentDailyMetrics:
    id: str
    agent_id: str
    date: str
    total_invocations: int
    success_count: int
    failure_count: int
    timeout_count: int
    human_intervention_count: int
    task_completion_rate: float   # success / total
    human_intervention_rate: float
    avg_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    total_input_tokens: int
    total_output_tokens: int
    estimated_cost_usd: float
    quality_score_avg: float      # 0–100，若无评分则为 null

@dataclass
class AgentQualityScore:
    id: str
    agent_id: str
    content_id: Optional[str]
    trace_id: str
    evaluator: str                # LLM_JUDGE / RULE_ENGINE / HUMAN
    rubric_version: str
    dimensions: List[Dict]          # [{"dimension": "结构完整性", "score": 85, "weight": 0.3}, ...]
    overall_score: float          # 加权总分
    evaluated_at: str
    evaluated_by: Optional[str]   # 人工评分时记录

@dataclass
class HumanIntervention:
    id: str
    agent_id: str
    content_id: str
    trace_id: str
    intervention_type: str        # MODIFY_OUTPUT / SKIP_AGENT / FORCE_RETRY / OVERRIDE_DECISION
    reason: str                   # 运营填写的理由
    operator: str
    created_at: str
    before_snapshot: Optional[str]  # 干预前摘要
    after_snapshot: Optional[str]   # 干预后摘要

@dataclass
class CostAttribution:
    id: str
    agent_id: str
    content_id: Optional[str]     # Phase 2 必填；MVP 可为 null（仅按 Agent 聚合）
    account_id: Optional[str]
    date: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    currency_rate: float          # 当日汇率（若人民币计价）
```

---

### 7.5 前端增强：Agent Cockpit（驾驶舱）

> **与 v5.0 一致**：默认展示「状态 + 统计 + 配置」三层信息；禁止展示已废弃指标。

#### 7.5.1 Agent 状态看板（Dashboard 新增 Tab）

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Agent 舰队状态                                    [刷新] [批量暂停] [告警] │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐         │
│  │ 🟢 健康 6    │ │ 🟡 降级 1    │ │ 🔴 故障 0    │ │ ⚪ 离线 0    │         │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘         │
├─────────────────────────────────────────────────────────────────────────────┤
│  Agent 名称       │ 角色              │ 状态   │ 当前任务      │ 队列 │ 版本 │
│  ────────────────┼───────────────────┼────────┼───────────────┼──────┼──────│
│  ContentForge-A1  │ CONTENT_FORGE     │ 🟢 运行 │ cf_20260514_03│ 2    │ v1.3 │
│  ComplianceGuard-1│ COMPLIANCE_GUARD  │ 🟢 空闲 │ —             │ 0    │ v2.1 │
│  Publisher-Main   │ PUBLISHER         │ 🟡 降级 │ 等待平台回调  │ 5    │ v1.0 │
│  PoolPredictor-1  │ POOL_PREDICTOR    │ 🟢 空闲 │ —             │ 0    │ v1.5 │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 7.5.2 Agent 统计报表（新增页面）

- **日维度折线图**：任务完成率、平均延迟、Token 消耗、质量评分趋势。
- **成本归因表**：按 Agent 汇总昨日/近 7 日/近 30 日成本；支持导出 CSV。
- **人机干预排行榜**：干预率最高的 Agent TOP5，提示优化方向。
- **告警历史**：按 severity 过滤，支持一键确认与查看根因。

#### 7.5.3 Agent 配置面板（新增页面，Admin 权限）

- **版本列表**：展示配置历史，支持对比 diff、回滚到指定版本。
- **环境切换**：dev / staging / prod 配置一键切换（须审批流）。
- **依赖拓扑图**：展示 Agent → LLM / Tool / DataSource 的依赖关系与健康状态（Phase 2 可视化）。

---

### 7.6 测试策略

#### 7.6.1 新增模块测试矩阵

| 模块 | 测试文件 | 测试数 | 关键场景 |
|------|----------|--------|----------|
| AgentHub | `test_agent_hub.py` | 6 | 注册/配置版本化/激活/回滚/权限/依赖探测 |
| AgentWatch | `test_agent_watch.py` | 6 | 心跳上报/状态聚合/链路追踪/循环检测/超时检测/告警分级 |
| AgentMetrics | `test_agent_metrics.py` | 5 | 任务完成率计算/成本归因/质量评分/人机干预记录/时序聚合 |
| Agent Cockpit（前端） | E2E | 3 | 状态看板渲染/统计图表/配置回滚交互 |

#### 7.6.2 回归与集成要求

- 基线：154 + P0 模块新增测试（V2.3 基线）全绿。
- AgentHub 注册后，Agent Orchestra 调度前**必须**查询 AgentHub 状态；若 Agent 为 `DEGRADED` / `OFFLINE`，Orchestrator 须拒绝调度并记录日志（集成测试覆盖）。
- AgentWatch 心跳缺失须触发告警，告警须写入独立表（不与业务日志混表），便于审计。
- AgentMetrics 的 `estimated_cost_usd` 须与 LLM Gateway 日志交叉验证，误差 ≤5%（容忍第三方计费延迟）。

---

### 7.7 执行顺序建议

**第 1 轮（W15，与 TrendScout 等并行）**：AgentHub（注册 + 配置版本化 + 权限）+ AgentWatch（心跳 + 状态看板 + 基础告警）。  
**第 2 轮（W16）**：AgentMetrics（任务统计 + Token 成本 + 质量评分）+ 链路追踪存储（OpenTelemetry SDK 接入）。  
**第 3 轮（W17）**：Agent Cockpit 前端（状态看板 + 统计报表 + 配置面板）。  
**第 4 轮（W18–W19，Phase 2）**：成本精确归因（content_id 级）、漂移检测、依赖拓扑可视化、自动熔断策略。

---

### 7.8 专家评审意见与决议

> **评审对象**：AgentHub / AgentWatch / AgentMetrics 三大模块及其与现有架构的集成方案。  
> **评审真源**：以 v5.0 为产品真源，以 2026 年行业 Agent Observability 最佳实践（OpenTelemetry、MELT 框架、AI-native 监控）为技术参考。

| 角色 | 评审意见 | 结论 |
|------|---------|------|
| **产品** | 1. 当前 Agent Orchestra 仅有串行 Pipeline 描述，缺乏「谁在用、用得怎样、坏了怎么办」的治理能力；新增模块补齐了运营闭环。  <br>2. **MVP 必须聚焦**：W15–W16 只做「注册 + 心跳 + 基础统计」，禁止把「自动熔断 + 自愈」写进 Phase 1 验收。  <br>3. 人机干预率必须作为一级指标，它是系统健康的领先指标（Anthropic 2025 运营数据支持）。 | ✅ 采纳；Phase 1 聚焦基础治理，Phase 2 再做智能运维。 |
| **架构** | 1. AgentHub 配置版本化与现有「禁止无版本记录热改」的审计要求一致；建议配置快照存储复用现有数据库（或独立 `agent_config` 表），禁止引入额外分布式配置中心（如 Consul/Etcd）增加复杂度。  <br>2. 链路追踪必须基于 **OpenTelemetry** 标准，确保与现有 Prometheus / Grafana 栈兼容；自研仅做业务语义层（trace 关联 content_id）。  <br>3. 告警通道优先复用企业现有通知基础设施（企业微信/钉钉），不强制要求新建 PagerDuty。  <br>4. **禁止**在 AgentWatch 中引入「AI 自动修复 Agent」能力（超出 MVP 边界且与已废弃 MetaLearner 概念易混淆）。 | ✅ 采纳；OTel 标准接入；告警复用现有通道；不承诺自动修复。 |
| **算法 / AI** | 1. 质量评分采用 **Rubric-based + LLM-as-Judge** 是 2026 年主流实践（与人工评分相关性可达 0.85+），但 MVP 仅对 ContentForge / ComplianceGuard 启用，避免全量评分带来的 Token 成本失控。  <br>2. 漂移检测需要「版本对比基线」，建议基线数据至少积累 **7 天**后再启用，避免冷启动误报。  <br>3. 成本估算使用 LLM Gateway 返回的 `usage.prompt_tokens` / `usage.completion_tokens` 结合模型单价表计算；**不承诺**与第三方账单 100% 一致（存在缓存命中、批处理折扣等黑盒因素）。 | ✅ 采纳；MVP 仅两 Agent 自动评分；漂移检测需 7 天基线；成本估算允许 5% 误差。 |
| **运维 / SRE** | 1. 心跳周期 30s 在 20 账号 MVP 规模下合理；若后续扩展至 200+ 账号，须支持批量心跳或长连接（WebSocket）降级。  <br>2. Agent 状态看板数据建议 TTL 7 天，历史状态归档至冷存（S3 / OSS），避免热库膨胀。  <br>3. 告警分级中 P0（Publisher 失败）须绑定值班电话；P1/P2 仅企业微信即可。  <br>4. **第三方 LLM / 平台 API 故障不计入** Agent 自身 SLA；须在 SLA 定义中明确区分「Agent 服务可用」与「下游依赖可用」。 | ✅ 采纳；状态数据 TTL 7 天；P0 绑定电话告警；SLA 边界清晰化。 |
| **法务合规** | 1. 链路追踪的 `input_summary` / `output_summary` 仅存储前 200 字符摘要，**禁止**存储完整用户 prompt 或平台敏感数据（如账号 Cookie、Token）；完整 trace 若需保留，须做**数据脱敏 + 加密 + 访问审计**。  <br>2. 配置版本化的 `approval_status` 对 Publisher / ComplianceGuard 等敏感 Agent 强制启用双人复核，满足内部合规审计要求。  <br>3. Agent 权限矩阵须支持「最小权限原则」，特别是 Publisher 的「发布权限」与 AccountPool 的「账号访问权限」须解耦，防止单点权限过大。  <br>4. 成本归因数据涉及财务信息，须符合公司数据分级保护要求（建议定为「内部机密」级）。 | ✅ 采纳；摘要脱敏；敏感 Agent 强制审批；最小权限原则；成本数据分级保护。 |

**执行决议**：采纳上述全部评审意见；本文 **V2.4** 与《开发计划》**v2.2** 同步增补 W15–W19 周次；Agent 全生命周期管理模块作为 Phase 1 闭环的必要基础设施，与 TrendScout / MarketingMethodology / DataAnalyst / PlatformRule 并行推进。

---
# EcoDream Omni PRD V2.3
## 对齐《文档2_最终可行性完整产品方案_素人号矩阵AI平台》（**v5.0 Final**）

> **变更范围**：以 v5.0 为唯一产品真源，校准需求表述、预测目标、废弃模块与 Phase 边界；并与《开发计划_素人号矩阵AI平台_v2》周次与交付物交叉引用。  
> **V2.3 修订要点**：在 V2.2 基础上增加 **§2.6 工程可靠性边界**——区分「结构预检 / 预发调整闭环」与「数据反馈闭环」的可实现层级；去掉**不可验证的因果增幅**承诺；回流默认**人工导入 + 可选半自动连接器**，覆盖率 KPI 绑定**最小样本量**。  
> **当前基线**：以仓库 CI 当时测试计数为准（历史表述如「154 测试全绿」仅作基线记录，迭代后请在 CI/README 更新数字）。  
> **目标**：MVP 阶段达成 v5.0 **Phase 1** 闭环（20 账号）：选题→生成→**互动量区间（宽先验）**预演→合规→发布→**可获取的实际互动**（导入为主）→**异步**校准；禁止实现 v5.0 已废弃能力。

---

## 〇、方案—PRD—开发计划 对齐矩阵（追溯）

| v5.0 方案章节 / 能力 | PRD 章节 | 开发计划锚点（**v2.2 周次为权威**，与旧版 Excel/截图如有冲突以本文为准） |
|---------------------|----------|--------------|
| 一、定位与边界（小红书 MVP、图文） | 全文约束 | Phase 1 |
| 四～八、四层风控 + AccountPool / PersonaPool | §2 已有增强 + AccountPool | W4–W5、W3.5 |
| 八、TrendScout（先 Mock/可控采集） | §2.1 | **MVP 补全 W11**（Mock + 手动导入） |
| 八、MarketingMethodology（AIPL） | §2.2 | **MVP 补全 W12** |
| 八、PoolPredictor（**互动量区间**，非 L0–L5） | §2.4 | W9 冷启动 + **Phase 2 W18** 探索期模型 |
| 八、DataAnalyst（区间命中、MAPE、归因） | §2.3 | **MVP 补全 W13** |
| 八、PlatformRule L3/L4 | §2.5、§2.6 | W6 已覆盖 L1/L2；**MVP 补全 W14** 做 L3/L4 + 证据链 + Publisher 对齐 |
| 八、SkillSmith / ContentInsight | v5.0 **Phase 2** | **W16、W19**（见开发计划 **v2.2**） |
| 结构预检 + 反馈闭环工程边界 | **§2.6** | W12–W14、W13；Celery 异步校准 |
| 九、LLM Gateway / 多模型路由 | 实现落在 LiteLLM + 自研路由 | 计划 §4–§5 |
| v5.0 **已废弃**：对抗辩论、MetaLearner、记忆联邦、流量池层级/CES 精确承诺 | **本文不出现需求** | Harness/文档索引 **不得** 再引用 MetaLearner、记忆联邦 |

---

## 一、当前代码与方案差距总表

### 1.1 模型层偏差（必须修正）

| 当前实现 | v5.0 方案要求 | 偏差等级 | 修正动作 |
|----------|---------------|----------|----------|
| `LinearRegression` 等简化回归 | **可解释特征**（目标 18 维，**缺失维用默认值并降权**）；输出 **点赞/评论/收藏** 的区间与中位数 + `interval_mode` | 🔴 P0 | 演进 `prediction_engine.py`：优先 **QuantileRegressor** / 先验宽区间；Phase 2+ 再 XGBoost |
| 无区间不确定性量化 | 贝叶斯线性回归或等效 **可信区间** | 🔴 P0 | API 返回 `interval_lower/upper` 或分位数 |
| （旧 PRD）有序 Logit L0–L5 | **v5.0 已废弃**「流量池层级」预测 | ⚫ 不做 | 从数据模型与 UI 移除 L0–L5 |
| 无 ARIMA / 时段竞争 | v5.0 Phase 2+ **时段竞争系数**（ARIMA 为可选实现） | 🟡 P1 | Phase 2：Publisher / 预演面板共用竞争系数服务 |
| Thompson 采样（旧 PRD） | v5.0 未强制；可作为 **策略实验** 可选项 | 🟢 P2 | 不与「L0–L5」绑定；若做，仅用于模板/A/B 臂选择 |

### 1.2 缺失模块（必须新增）

| 模块 | 方案章节 | Phase | 当前状态 | 优先级 |
|------|----------|-------|----------|--------|
| **TrendScout** | 文档2 §8.4 | Phase 1（MVP：Mock + 手动导入） | 视代码基线 | 🔴 P0 |
| **MarketingMethodology** | 文档2 §6 + 架构 MarketingMethod | Phase 1 | 视代码基线 | 🔴 P0 |
| **DataAnalyst** | 文档2 §8.9 | Phase 1 | 视代码基线 | 🔴 P0 |
| **PlatformRule Engine（L3/L4）** | 文档2 §8.3 | Phase 1 | 常仅 L1–L2 | 🔴 P0 |
| **PersonaPool（完整版）** | 文档2 §8.2 | Phase 1 | 基础模型 | 🟡 P1 |
| **SkillSmith** | 文档2 §8.10、§十六 Phase 2 | Phase 2 | 视代码基线 | 🟡 P1 |
| **ContentInsight** | 文档2 §8.11、§十六 Phase 2 | Phase 2 | 视代码基线 | 🟡 P1 |
| ~~**MetaLearner**~~ | **v5.0 已移除** | — | — | ⚫ 不规划 |
| ~~**对抗辩论**~~ | **v5.0 已移除** | — | — | ⚫ 不规划 |

### 1.3 已有模块需增强

| 模块 | 当前能力 | v5.0 要求 | 增强动作 |
|------|----------|-----------|----------|
| **AccountPool** | 指纹+健康评分 | +自动熔断+状态机+IP 代理/配额 | 扩展状态转换、每日配额、warming/restricted |
| **ContentForge** | Voice 注入生成 | +AIPL 阶段模板（MarketingMethodology） | 对接阶段模板与合规标签 |
| **ComplianceGuard** | L1–L3 | +证据链留存 ≥2 年 + PlatformRule L4 动态规则 | 审核记录与动态规则 CRUD |
| **Publisher** | 错峰调度 | +频率阶梯 + 排版随机化；时段可接竞争系数 | 与 PoolPredictor / 规则 L4 对齐 |
| **Dashboard** | 任务看板 | +**互动量区间**预演 + 智能选题 + 昨日战报 | 禁止展示「流量池层级」为预测结论 |
| **Agent Orchestra** | 串行 Pipeline | +ACP + 共享状态（会话级） | **不引入**对抗辩论链路 |

---

## 二、P0 模块详细设计（立即执行）

### 2.1 TrendScout 趋势侦察

**职责**：热点爬取Mock、趋势报告、人设克隆草案

**MVP范围（与开发计划 W11 对齐）**：
- 不提供全量真实爬虫（平台签名与合规边界），提供 **Mock 数据源** + **结构化趋势报告**；与 v5.0「频率控制 + 白名单」一致，真实采集列为 **Phase 2+ 可选能力**，须单独法务评审。
- 运营手动输入/导入热点话题，系统自动生成趋势报告结构。
- **人设来源**：仅允许 **手动创建 + AI 辅助生成**（v5.0 §8.2）；禁止「爬取克隆对标账号」作为默认产品能力。可对「对标笔记 URL」做 **运营粘贴后的脱敏摘要**（标题/话题/结构标签），不自动拉取私密数据。

**API设计**：
```
POST /trend-scout/reports       # 创建趋势报告（输入关键词+阶段）
GET  /trend-scout/reports       # 列表查询
GET  /trend-scout/reports/{id}  # 详情（含热点条目）
POST /trend-scout/persona-draft  # 提交**运营填写的结构化要点**或脱敏后的公开字段摘要，返回人设草案（非爬虫克隆）
```

**数据模型**：
```python
@dataclass
class TrendReport:
    id: str
    query: str                    # 查询关键词
    stage_filter: str             # AWARENESS/INTEREST/PURCHASE/LOYALTY
    crawl_time: str
    results: List[TrendItem]      # 热点条目
    platform_risk_signals: List[RiskSignal]

@dataclass
class TrendItem:
    rank: int
    title: str
    title_structure: str          # 如「数字+痛点+时间跨度」
    engagement_hint: str        # 可选：「高/中/低」或粗粒度分档，非平台真实 CES
    stage: str                    # AWARENESS / INTEREST / PURCHASE / LOYALTY
    tags: List[str]
    post_time: str
    post_day: str
    structural_signals: Dict      # 标题模式、话题簇等（不含流量池层级）
```

### 2.2 MarketingMethodology 方法论中枢

**职责**：AIPL阶段定义、内容结构模板、KPI目标配置

**MVP范围（W12补做）**：
- AIPL四阶段定义（AWARENESS/INTEREST/PURCHASE/LOYALTY）
- 每阶段的内容结构模板（hook/body/cta/disclaimer）
- 阶段转换条件配置
- KPI目标配置

**API设计**：
```
GET  /methodologies              # 列表（AIPL/5A等框架）
GET  /methodologies/{id}/stages  # 某方法论的所有阶段
GET  /methodologies/stages/{stage_id}/template  # 阶段内容模板
POST /methodologies/stages/{stage_id}/evaluate  # 评估内容是否符合阶段要求
```

**数据模型**：
```python
@dataclass
class MethodologyStage:
    id: str
    framework: str                # AIPL
    stage: str                    # AWARENESS
    stage_name: str               # 认知期
    content_template: Dict        # hook/body/cta/disclaimer结构
    kpi_targets: Dict             # exposure、互动率、区间覆盖率等；CES 仅可选派生，不作为 MVP 硬门禁
    compliance_tags: List[str]    # 必须包含的合规标签
    forbidden_elements: List[str] # 禁用元素
    stage_transition_criteria: Dict  # 晋升下阶段条件
    recommended_persona_types: List[str]
```

### 2.3 DataAnalyst 数据分析师

**职责**：24h回流报表、MAPE计算、归因分析、模型校准触发

**MVP范围（与开发计划「MVP 补全冲刺」W13 对齐；扩展归因可延续至 W14）**：
- **实际互动数据入口（工程约束）**：默认 **运营 CSV/表单导入**（`content_id`、时间窗、`likes/comments/saves` 等）；可选「连接器」在 **PlatformAccountManager 合法登录态**下做**只读、低频、可降级**拉取（易随平台改版失效，不作为 MVP 必达能力）。**禁止**将全矩阵无人值守爬取写进 MVP SLA。
- 内容发布后 **T+24h～T+48h** 窗口内生成报告（允许手动触发）；无真数时仍可用**模拟数据**跑通管道与单测。
- **主指标**：点赞/评论/收藏的**实际值 vs 预测区间**；计算**区间覆盖率**与分指标 MAPE；**覆盖率 KPI（如 ≥70%）仅在「有效标注样本 ≥ `N_min`（默认 30，可配置）」子集上考核**（见 §2.6），冷启动宽区间阶段标注为**参考不考核**。
- **CES**（若保留字段）：仅作可选派生展示或内部实验指标，**不作为** MVP 合规验收主指标（v5.0 已废弃「CES 精确承诺」）
- 基础归因分析（Top 特征影响，与 PoolPredictor 特征维度一致）
- 模型校准建议：**异步批任务**（Celery + Redis，**非实时**）检查 MAPE/漂移，超阈值则写入「待重训」队列并由人工或定时任务触发训练脚本；**禁止**承诺「每次发帖后秒级在线学习」。

**API设计**：
```
POST /data-analyst/reports       # 为某篇内容生成24h报告
GET  /data-analyst/reports/{id}  # 查看报告
GET  /data-analyst/dashboard     # 昨日战报聚合
GET  /data-analyst/attribution/{content_id}  # 归因分析
POST /data-analyst/calibrate     # 触发模型校准检查
```

**数据模型**：
```python
@dataclass
class DataReport:
    id: str
    account_id: str
    content_id: str
    period: str                   # 24h/7d
    actual_metrics: Dict          # exposure/likes/saves/comments/shares/follows（+ 可选 ces 派生）
    prediction_comparison: Dict   # 各互动指标的 predicted_interval vs actual、within_range、mape、coverage
    attribution: Dict             # top_features影响
    model_calibration: Dict       # 校准建议
```

### 2.4 PoolPredictor 修正（分位数 / 先验区间为主，开源优先）

**当前问题**：点估计式线性回归无法稳定输出**可用预测区间**，与 v5.0 §8.8「互动量区间」主目标不一致。

**与 v5.0 对齐且工程可落地的硬要求**：
- **冷启动（MVP 必达）**：同类/全库聚合先验 + **刻意放宽**的分位数或残差估计区间（**开源**：`scikit-learn` `QuantileRegressor` / 分位点 + 简单校准，或分段常数先验）；输出必须带 **`interval_mode: prior|fitted`**，UI 对 `prior` 展示「参考区间」文案。
- **MVP 输出**：对**点赞、评论、收藏**分别给出 `lower / median / upper` 与 `confidence`（可基于区间宽度与样本量启发式，**非**平台真实置信）；禁止将「流量池层级 L0–L5」作为产品预测结论。
- **探索期（Phase 2）**：在 **`N_min` 达标**后启用 **XGBoost / 随机森林分位数**、可选 **SHAP**（`vendor/ml-libraries`）；小样本下 **禁止**把深度网络或集成模型写进必达路径。
- **优化建议**：仅允许输出**清单式启发项**（标题长度、标签个数、时段等），**禁止**展示未做随机实验验证的**因果增幅百分比**（如「+18% 互动」）；可选 A/B 为 Phase 2+ 独立模块。
- **Thompson 采样**（可选，P2）：默认关闭；若启用仅用于模板臂选，须法务与产品双签。

**修正方案（接口语义）**：
```python
# 演进 prediction_engine：输出多指标区间 + 覆盖率可测

def predict_engagement_intervals(features: np.ndarray, prior: Dict) -> Dict:
    """返回 likes/comments/saves 的区间与中位数 + confidence + interval_mode；不得输出流量池层级。"""
    ...
```

**API变更**：
```
POST /predictions              # 响应含 likes/comments/saves 的 interval 与 confidence
GET  /predictions/{id}         # 详情与同上；禁止返回 l0_l5_distribution 类字段作为默认 UI 数据源
```

### 2.5 PlatformRule Engine（L3/L4）

**当前**：只有L1法律红线、L2平台规则（静态关键词）

**新增**：
- **L3 账号状态规则**：新号/老号差异化策略（日发频率、时段限制）
- **L4 动态风控规则**：临时风控、节日策略、时段竞争系数
- **规则CRUD**：运营可配置规则
- **违规归因**：规则命中后的归因分析

**API设计**：
```
GET  /platform-rules           # 规则列表（支持按layer过滤）
POST /platform-rules           # 创建规则（需要admin权限）
GET  /platform-rules/{id}      # 规则详情
PATCH /platform-rules/{id}     # 更新规则
DELETE /platform-rules/{id}    # 删除规则
GET  /platform-rules/attribution/{content_id}  # 违规归因
```

### 2.6 工程可靠性：内容结构预检与「预发 / 反馈」双闭环（可用性边界）

> **原则**：开源承担通用能力（校验、ML 基座、队列、LLM 路由），自研只做编排、特征与业务策略。**不承诺**平台黑盒可逆推或全自动无监督优化。

#### A. 结构预测与调整闭环（发布前，**与互动预测解耦**）

| 层级 | 能力 | 开源/自研 | MVP 是否必达 |
|------|------|-----------|--------------|
| **S0 结构合规** | 方法论模板字段是否齐全（hook/body/cta/disclaimer）、Zod/JSON Schema 校验 | Zod（前端）+ 同源 schema（后端）；可选 Pydantic | **必达** |
| **S1 结构质量** | LLM 按 rubric 打分或结构化点评（是否口语化、是否过营销等） | **LiteLLM** 路由多模型；自研 prompt 与 rubric | **推荐** |
| **S2 结构→互动** | 用同一套内容特征进 PoolPredictor | sklearn 等 | **弱相关**；不得在文案中暗示「改结构必涨互动」 |

**调整闭环（可实现）**：用户在预演面板采纳建议 → 调用 ContentForge **regenerate 或 patch**（带 `parent_content_id`）→ 再次走 ComplianceGuard；**禁止** MVP 要求「自动循环改写直至区间收窄」无人值守闭环。

#### B. 数据反馈闭环（发布后）

| 步骤 | MVP 实现 | 说明 |
|------|-----------|------|
| 采集 | **导入为主**；连接器为辅 | 连接器失败须降级为导入，不阻塞发贴 |
| 对齐 | `content_id` 与平台帖映射表 | 自研表结构 |
| 计算 | 覆盖率、MAPE、简单归因（系数/排列重要性） | sklearn；SHAP Phase 2+ |
| 校准 | Celery 定时或手动触发 | **批处理**；与在线推理解耦 |

#### C. 可靠性声明（写入验收说明）

- **系统可用性 ≥99.5%** 仅指**自建 SaaS API** 月度可用性；不含第三方 LLM、住宅代理、平台站点可用性。
- **自动化发布成功率** 依赖登录态与反爬变化，须单独定义「可重试失败」口径。

---

## 三、前端增强设计

### 3.1 流量预演面板（Dashboard新增）

> **与 v5.0 §8.8 / §十三一致**：默认仅展示**互动量区间**与优化建议；**禁止**用「流量池层级 L0–L5」或「CES 精确值」作为预演主结论（已废弃指标，见文档2 §十五「废弃指标」）。

```
┌─────────────────────────────────────────────────────────────┐
│  内容预览：「猫咪驱虫避坑指南，这3个误区90%的人都不知道」        │
├─────────────────────────────────────────────────────────────┤
│  互动量预演（`interval_mode=prior|fitted`；MVP 多为先验宽区间）   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  点赞：预计 25–60（中位数 42）  │ 置信度 65%        │   │
│  │  评论：预计 5–15（中位数 9）    │                   │   │
│  │  收藏：预计 8–20（中位数 13）   │                   │   │
│  └─────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  💡 启发式优化清单（非因果承诺；A/B 验证见 Phase 2+）            │
│  ① 标题含具体数字「3个」→ 与模板 rubric 一致 ✅               │
│  ② 可考虑增加话题标签 #新手养猫（经验规则，不保证增幅）→ [添加] │
│  ③ 发布时段建议：周三 20:00（内部竞争系数启发 0.7）→ [定时]   │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 智能选题推荐（Dashboard新增）

- TrendScout 每日更新热点
- 标注审核松紧度
- 一键生成内容按钮

### 3.3 昨日战报（Dashboard新增）

- DataAnalyst 在 **导入/连接器** 可用数据上的 24h 聚合
- 发布篇数、**预测区间命中率**、平均点赞/评论/收藏、环比；可选派生指标（如 CES）不得作为唯一成功口径
- [查看详细报告] 入口

---

## 四、测试策略

### 4.1 P0模块测试矩阵

| 模块 | 测试文件 | 测试数 | 关键场景 |
|------|----------|--------|----------|
| TrendScout | `test_trend_scout.py` | 5 | 创建报告/查询详情/人设克隆/阶段过滤 |
| MarketingMethodology | `test_methodology.py` | 5 | 阶段模板/内容评估/转换条件 |
| DataAnalyst | `test_data_analyst.py` | 5 | 回流报告/MAPE计算/归因分析/校准触发 |
| PoolPredictor修正 | `test_pool_predictor.py` | +3 | 多指标区间/覆盖率或分位数；Thompson 若未启用则标注 skip |
| PlatformRule | `test_platform_rules.py` | 5 | L3/L4规则CRUD/违规归因/动态生效 |

### 4.2 回归策略

- 基线：154测试全绿
- 每新增一个P0模块，测试数+5，全量回归
- PoolPredictor修正：需更新现有8个测试的数据断言（增加可信区间字段）

---

## 五、执行顺序建议

**第1轮（立即）**：PoolPredictor修正（影响现有测试，先处理）  
**第2轮（并行）**：TrendScout + MarketingMethodology（独立模块，互不影响）  
**第3轮**：DataAnalyst + PlatformRule（依赖前两者数据）  
**第4轮**：前端面板增强（依赖后端API就位）  
**第5轮**：全量E2E验证

---

## 六、专家组终审建议（产品 / 架构 / 算法 / 法务 / 运营）

以下结论以《文档2》v5.0 为真源，用于约束 PRD 与《开发计划》后续迭代。

| 角色 | 建议摘要 |
|------|-----------|
| **产品** | 周次命名以「MVP 补全冲刺」承接文档2 Phase 1 缺口（TrendScout、MarketingMethodology、DataAnalyst、PlatformRule L3/L4），再进入 Phase 2（SkillHub、SkillSmith、ContentInsight、XGBoost 等）；禁止在验收口径中复活 L0–L5 / CES 精确承诺。 |
| **架构** | Agent Harness 与 hermes 复用描述须与 v5.0 一致：**不得**将已移除的 MetaLearner、记忆联邦、对抗辩论纳入需求或对外承诺；跨账号经验沉淀通过 **SkillSmith + PersonaPool + 审计数据** 实现。 |
| **算法** | PoolPredictor / DataAnalyst 的默认指标统一为**点赞/评论/收藏区间 + 覆盖率 + MAPE**；ARIMA 时段竞争、Thompson 臂选为 Phase 2+ 可选项并单独评审。 |
| **法务合规** | TrendScout MVP 维持 **Mock + 手动导入**；任何真实爬虫与签名对抗须独立法务评审与日志留存策略（文档2 §8.4、§十四）。 |
| **工程 / SRE** | 第三方 LLM、代理、平台站点**不计入**自建 99.5% SLA；回流 **导入优先**；预测与校准 **异步解耦**；监控连接器降级路径。 |
| **运营交付** | 驾驶舱文案与报表默认对齐「素人矩阵 + 合规红线 + 区间预演」，避免短剧/视频平台 PRD 路径混入本仓库基线文档索引。 |

**执行决议**：采纳上述约束；本文 **V2.3** 与《开发计划》**v2.2** 同步修订周次、Harness 表述及 **§2.6 双闭环工程边界**。


---

## 七、新增需求：Agent 全生命周期管理、活跃监控与统计（V2.4 增补）

> **变更范围**：在 V2.3 基础上新增 **AgentHub（管理与配置）**、**AgentWatch（活跃监控）**、**AgentMetrics（统计与分析）** 三大模块，补齐 v5.0 方案中「Agent Orchestra」仅描述串行 Pipeline 但缺乏运行时可观测性与治理能力的缺口。  
> **对齐原则**：与现有 Agent Orchestra（串行 Pipeline + ACP + 会话级共享状态）无缝集成；不引入已废弃概念（MetaLearner、对抗辩论、记忆联邦）；默认使用开源/标准协议（OpenTelemetry、Prometheus、Celery），自研仅做编排与业务语义层。  
> **MVP 边界**：Phase 1 达成「注册发现 + 心跳健康 + 基础统计看板」闭环；Phase 2 扩展「链路追踪 + 成本归因 + 自动熔断」。

---

### 7.1 新增模块与现有架构对齐矩阵

| 新增模块 | 职责 | 对接现有模块 | 开发计划锚点 | Phase |
|---------|------|-------------|-------------|-------|
| **AgentHub** | Agent 注册、配置版本化、生命周期、权限 | Agent Orchestra、LLM Gateway、AccountPool / PersonaPool | **MVP 补全 W15** | Phase 1 |
| **AgentWatch** | 心跳健康、实时状态、链路追踪、异常告警 | Agent Orchestra、Celery、Publisher、ComplianceGuard | **MVP 补全 W15–W16** | Phase 1 |
| **AgentMetrics** | 任务统计、Token 成本、质量评分、漂移检测 | DataAnalyst、PoolPredictor、LLM Gateway | **MVP 补全 W16**；成本归因 W19 | Phase 1（基础）+ Phase 2（深度） |
| **Agent Cockpit（前端）** | Agent 驾驶舱：状态看板 + 统计报表 + 配置面板 | Dashboard | **MVP 补全 W17** | Phase 1 |

---

### 7.2 AgentHub — Agent 管理与配置中心

#### 7.2.1 职责与 MVP 范围（W15）

- **Agent 注册与发现**：所有业务 Agent（TrendScout、ContentForge、ComplianceGuard、Publisher、DataAnalyst、PoolPredictor、MarketingMethodology、PlatformRule）在启动时向 AgentHub 注册；支持**手动注册**（MVP）与**服务发现**（Phase 2）。
- **配置版本化**：每个 Agent 的配置（prompt 模板、模型路由参数、超时阈值、重试策略）以**版本化快照**存储；支持「当前生效版本 / 历史版本 / 草稿版本」三态管理；**禁止**无版本记录的在线热改（审计要求）。
- **环境隔离**：同一 Agent 支持 `dev` / `staging` / `prod` 多环境配置隔离；发布流程为「草稿 → staging 灰度 → prod 全量」。
- **权限与访问控制**：基于角色的 Agent 调用权限（RBAC）；区分「编排者（Orchestrator）调用权限」与「运营人员只读权限」；敏感 Agent（如 Publisher 发布、ComplianceGuard 审核通过）须**双人复核**或**审批流**。
- **依赖管理**：声明式管理每个 Agent 的依赖——LLM 模型（通过 LLM Gateway 路由）、外部 Tool（如爬虫连接器、平台 API）、数据源（如 AccountPool、PersonaPool）；依赖缺失或降级时 Agent 状态自动置为 `degraded`。

#### 7.2.2 API 设计

```
# Agent 生命周期
POST   /agent-hub/agents              # 注册 Agent（含配置快照 v1）
GET    /agent-hub/agents              # 列表（支持按 status / role / env 过滤）
GET    /agent-hub/agents/{agent_id}   # 详情（含当前生效配置版本）
PATCH  /agent-hub/agents/{agent_id}   # 更新元数据（非配置内容）
DELETE /agent-hub/agents/{agent_id}   # 注销（软删除，保留审计）

# 配置版本化
POST   /agent-hub/agents/{agent_id}/configs           # 创建新版本配置
GET    /agent-hub/agents/{agent_id}/configs           # 历史版本列表
GET    /agent-hub/agents/{agent_id}/configs/{ver}    # 指定版本详情
POST   /agent-hub/agents/{agent_id}/configs/{ver}/activate  # 激活指定版本
POST   /agent-hub/agents/{agent_id}/configs/{ver}/rollback  # 回滚

# 环境管理
GET    /agent-hub/agents/{agent_id}/envs              # 获取多环境配置映射
PATCH  /agent-hub/agents/{agent_id}/envs/{env}       # 更新某环境指向的配置版本

# 依赖声明
GET    /agent-hub/agents/{agent_id}/dependencies       # 依赖清单（LLM/Tool/Data）
POST   /agent-hub/agents/{agent_id}/health-check      # 手动触发依赖健康探测

# 权限与审批
GET    /agent-hub/agents/{agent_id}/permissions        # 权限矩阵
POST   /agent-hub/agents/{agent_id}/permissions      # 授权/变更权限
GET    /agent-hub/approvals                          # 配置变更审批流列表
POST   /agent-hub/approvals/{id}/approve             # 审批通过
```

#### 7.2.3 数据模型

```python
@dataclass
class AgentRegistration:
    id: str                       # agent 唯一标识，如 "content-forge-v1"
    name: str                     # 可读名称
    role: str                     # TREND_SCOUT / CONTENT_FORGE / COMPLIANCE_GUARD / 
                                  # PUBLISHER / DATA_ANALYST / POOL_PREDICTOR / 
                                  # MARKETING_METHODOLOGY / PLATFORM_RULE / ORCHESTRATOR
    description: str
    owner: str                    # 负责人（邮箱/企业微信ID）
    status: str                   # REGISTERED / ACTIVE / DEGRADED / PAUSED / OFFLINE
    created_at: str
    updated_at: str

@dataclass
class AgentConfigSnapshot:
    id: str
    agent_id: str
    version: int                  # 自增版本号
    env: str                      # dev / staging / prod
    config_payload: Dict          # 具体配置：{prompt_template_id, llm_route, timeout, retries, ...}
    checksum: str                 # SHA-256，防篡改
    created_by: str
    created_at: str
    status: str                   # DRAFT / ACTIVE / ARCHIVED / ROLLED_BACK
    approval_status: str          # PENDING / APPROVED / REJECTED（敏感 Agent 必填）

@dataclass
class AgentDependency:
    agent_id: str
    dep_type: str                 # LLM / TOOL / DATA_SOURCE
    dep_name: str                 # 如 "gpt-4o-mini" / "xhs-connector" / "account_pool"
    dep_status: str               # HEALTHY / DEGRADED / DOWN / UNKNOWN
    last_check: str
    failover_config: Dict         # 降级策略：如 LLM 降级到备用模型

@dataclass
class AgentPermission:
    agent_id: str
    principal: str                # user / service_account
    principal_type: str           # USER / SERVICE
    actions: List[str]            # READ / INVOKE / CONFIG / DELETE
    granted_by: str
    granted_at: str
    expires_at: str               # 可选，临时授权
```

---

### 7.3 AgentWatch — Agent 活跃监控与异常检测

#### 7.3.1 职责与 MVP 范围（W15–W16）

- **心跳与健康检查**：每个 Agent 每 30s 上报心跳（可配置）；心跳缺失超过 3 个周期标记为 `UNHEALTHY`；Orchestrator 在调度前强制检查目标 Agent 健康状态。
- **实时状态看板**：展示所有 Agent 的当前状态（空闲 / 运行中 / 故障 / 熔断）、当前任务、队列堆积数；支持按 role / env 过滤。
- **跨 Agent 链路追踪**：基于 **OpenTelemetry** 标准，对一次内容生产 Pipeline（选题→生成→合规→预演→发布→数据回流）生成统一 `trace_id`；每个 Agent 调用为一个 `span`，包含输入摘要、输出摘要、耗时、Token 数、模型版本；**MVP 仅要求 trace 采集与存储，不要求实时链路图**。
- **异常检测（规则引擎）**：
  - **循环检测**：同一 Agent 在 5 分钟内对同一 `content_id` 重复调用 ≥3 次，触发 `LOOP_ALERT`。
  - **超时检测**：单 Agent 执行超过配置阈值（如 ContentForge 默认 60s），触发 `TIMEOUT_ALERT`。
  - **工具失败检测**：外部 Tool（如平台 API、LLM Gateway）连续失败 ≥3 次，触发 `TOOL_DEGRADED`，并通知 AgentHub 更新依赖状态。
  - **成本异常**：单任务 Token 消耗超过同类任务 p95 的 200%，触发 `COST_ANOMALY`（Phase 2 细化）。
- **告警与通知**：告警通道支持「企业微信 / 钉钉 / 邮件」；分级：
  - `P0`（Publisher 发布失败、ComplianceGuard 绕过）→ 即时电话/短信 + 值班群；
  - `P1`（Agent 离线、工具降级）→ 企业微信；
  - `P2`（成本异常、质量漂移）→ 邮件日报。

#### 7.3.2 API 设计

```
# 心跳与状态
POST   /agent-watch/heartbeat         # Agent 上报心跳（由 Agent SDK 自动调用）
GET    /agent-watch/agents/{agent_id}/status      # 实时状态（含当前任务、队列深度）
GET    /agent-watch/dashboard           # 全量 Agent 状态聚合（前端轮询或 SSE）

# 链路追踪
GET    /agent-watch/traces              # 链路列表（按 trace_id / time_range / content_id）
GET    /agent-watch/traces/{trace_id}   # 链路详情（span 树）
GET    /agent-watch/traces/{trace_id}/spans/{span_id}  # 单 span 详情（含输入/输出摘要）

# 异常与告警
GET    /agent-watch/alerts              # 告警列表（支持按 severity / agent_id / status）
PATCH  /agent-watch/alerts/{id}/ack     # 告警确认
GET    /agent-watch/alerts/{id}/root-cause  # 根因分析（基于规则 + 链路关联）

# 规则配置（运营可配置）
GET    /agent-watch/rules              # 异常检测规则列表
POST   /agent-watch/rules              # 创建规则（需 admin）
PATCH  /agent-watch/rules/{id}        # 更新规则
DELETE /agent-watch/rules/{id}        # 删除规则
```

#### 7.3.3 数据模型

```python
@dataclass
class AgentHeartbeat:
    agent_id: str
    timestamp: str
    status: str                   # HEALTHY / BUSY / IDLE / UNHEALTHY
    current_task_id: Optional[str]
    queue_depth: int              # 待处理任务数
    memory_mb: float              # 可选，容器内存
    cpu_percent: float            # 可选
    version: str                  # 当前运行的代码版本 / 配置版本

@dataclass
class AgentTrace:
    trace_id: str
    content_id: str               # 关联业务内容
    pipeline_type: str            # CONTENT_CREATION / DATA_ANALYSIS / TREND_SCOUT
    start_time: str
    end_time: Optional[str]
    status: str                   # RUNNING / COMPLETED / FAILED / TIMEOUT
    total_tokens: int             # 全链路 Token 合计
    total_cost_usd: float         # 全链路成本估算（Phase 2 精确化）

@dataclass
class AgentSpan:
    span_id: str
    trace_id: str
    parent_span_id: Optional[str]
    agent_id: str
    agent_role: str
    start_time: str
    end_time: str
    duration_ms: int
    status: str                   # OK / ERROR / TIMEOUT
    input_summary: str            # 输入摘要（前 200 字符，禁止存完整 prompt 中的密钥）
    output_summary: str           # 输出摘要
    token_count: int
    model_version: str            # 如 "gpt-4o-2026-05"
    tool_calls: List[Dict]       # 调用的工具列表

@dataclass
class AgentAlert:
    id: str
    severity: str                 # P0 / P1 / P2
    alert_type: str                 # LOOP / TIMEOUT / TOOL_DEGRADED / COST_ANOMALY / HEALTH_CHECK_FAIL
    agent_id: str
    trace_id: Optional[str]
    content_id: Optional[str]
    message: str
    created_at: str
    status: str                     # OPEN / ACKED / RESOLVED / IGNORED
    acked_by: Optional[str]
    resolved_at: Optional[str]
    root_cause: Optional[str]       # 根因摘要（规则生成或人工填写）
```

---

### 7.4 AgentMetrics — Agent 统计与质量分析

#### 7.4.1 职责与 MVP 范围（W16；成本归因 W19）

- **任务完成率**：统计每个 Agent 的「成功 / 失败 / 超时 / 人工干预」占比；**任务完成率 = 成功且无人工干预的次数 / 总调用次数**；目标 ≥90%（参考 Anthropic 企业运营数据，人机干预率从 5% 升至 12% 是系统级故障的前兆）。
- **Token 消耗与成本归因**：通过 LLM Gateway 统一采集每个 Agent 每次调用的 Token（input / output）；按 Agent / 按 content_id / 按账号维度聚合成本；**MVP 仅做「按 Agent 日维度」汇总，Phase 2 做 content_id 级精确归因**。
- **延迟分布**：采集每个 Agent 的 `duration_ms`，输出 p50 / p95 / p99；用于识别性能退化。
- **质量评分（Rubric-based）**：
  - 对 ContentForge 输出：按 MarketingMethodology 模板 rubric 自动评分（结构完整性、口语化程度、合规标签命中）。
  - 对 ComplianceGuard：按「误杀率 / 漏杀率」评估（需人工抽样标注）。
  - 对 PoolPredictor：按 DataAnalyst 的 MAPE / 覆盖率评估。
  - **评分由 LLM-as-Judge 或规则引擎完成，禁止仅依赖人工**；MVP 仅对 ContentForge 和 ComplianceGuard 启用自动评分。
- **人机干预率**：记录运营人员在 Dashboard 上「手动修改 Agent 输出 / 跳过 Agent / 强制重试」的次数与比例；**人机干预率是系统健康度的领先指标**。
- **漂移检测（Phase 2）**：对比当前版本与上一版本的「平均质量分 / 平均延迟 / 平均 Token 数」，若差异超过阈值（如质量分下降 >10%），触发 `VERSION_DRIFT_ALERT`。

#### 7.4.2 API 设计

```
# 统计聚合
GET    /agent-metrics/dashboard          # 全局统计看板（日维度）
GET    /agent-metrics/agents/{agent_id}  # 单 Agent 统计（任务率 / 延迟 / 成本 / 质量）
GET    /agent-metrics/agents/{agent_id}/timeseries  # 时序数据（latency / token / success_rate）

# 质量评分
GET    /agent-metrics/agents/{agent_id}/quality-scores   # 质量评分列表
POST   /agent-metrics/agents/{agent_id}/quality-scores/eval  # 手动触发评估（对历史任务）

# 成本归因
GET    /agent-metrics/cost-attribution     # 成本归因报表（按 Agent / 按日）
GET    /agent-metrics/cost-attribution/content/{content_id}  # 单内容成本（Phase 2）

# 人机干预
GET    /agent-metrics/human-interventions  # 干预记录列表
POST   /agent-metrics/human-interventions  # 记录一次干预（由 Dashboard 调用）

# 漂移检测（Phase 2）
GET    /agent-metrics/agents/{agent_id}/drift  # 漂移检测报告
```

#### 7.4.3 数据模型

```python
@dataclass
class AgentDailyMetrics:
    id: str
    agent_id: str
    date: str
    total_invocations: int
    success_count: int
    failure_count: int
    timeout_count: int
    human_intervention_count: int
    task_completion_rate: float   # success / total
    human_intervention_rate: float
    avg_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    total_input_tokens: int
    total_output_tokens: int
    estimated_cost_usd: float
    quality_score_avg: float      # 0–100，若无评分则为 null

@dataclass
class AgentQualityScore:
    id: str
    agent_id: str
    content_id: Optional[str]
    trace_id: str
    evaluator: str                # LLM_JUDGE / RULE_ENGINE / HUMAN
    rubric_version: str
    dimensions: List[Dict]          # [{"dimension": "结构完整性", "score": 85, "weight": 0.3}, ...]
    overall_score: float          # 加权总分
    evaluated_at: str
    evaluated_by: Optional[str]   # 人工评分时记录

@dataclass
class HumanIntervention:
    id: str
    agent_id: str
    content_id: str
    trace_id: str
    intervention_type: str        # MODIFY_OUTPUT / SKIP_AGENT / FORCE_RETRY / OVERRIDE_DECISION
    reason: str                   # 运营填写的理由
    operator: str
    created_at: str
    before_snapshot: Optional[str]  # 干预前摘要
    after_snapshot: Optional[str]   # 干预后摘要

@dataclass
class CostAttribution:
    id: str
    agent_id: str
    content_id: Optional[str]     # Phase 2 必填；MVP 可为 null（仅按 Agent 聚合）
    account_id: Optional[str]
    date: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    currency_rate: float          # 当日汇率（若人民币计价）
```

---

### 7.5 前端增强：Agent Cockpit（驾驶舱）

> **与 v5.0 一致**：默认展示「状态 + 统计 + 配置」三层信息；禁止展示已废弃指标。

#### 7.5.1 Agent 状态看板（Dashboard 新增 Tab）

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Agent 舰队状态                                    [刷新] [批量暂停] [告警] │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐         │
│  │ 🟢 健康 6    │ │ 🟡 降级 1    │ │ 🔴 故障 0    │ │ ⚪ 离线 0    │         │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘         │
├─────────────────────────────────────────────────────────────────────────────┤
│  Agent 名称       │ 角色              │ 状态   │ 当前任务      │ 队列 │ 版本 │
│  ────────────────┼───────────────────┼────────┼───────────────┼──────┼──────│
│  ContentForge-A1  │ CONTENT_FORGE     │ 🟢 运行 │ cf_20260514_03│ 2    │ v1.3 │
│  ComplianceGuard-1│ COMPLIANCE_GUARD  │ 🟢 空闲 │ —             │ 0    │ v2.1 │
│  Publisher-Main   │ PUBLISHER         │ 🟡 降级 │ 等待平台回调  │ 5    │ v1.0 │
│  PoolPredictor-1  │ POOL_PREDICTOR    │ 🟢 空闲 │ —             │ 0    │ v1.5 │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 7.5.2 Agent 统计报表（新增页面）

- **日维度折线图**：任务完成率、平均延迟、Token 消耗、质量评分趋势。
- **成本归因表**：按 Agent 汇总昨日/近 7 日/近 30 日成本；支持导出 CSV。
- **人机干预排行榜**：干预率最高的 Agent TOP5，提示优化方向。
- **告警历史**：按 severity 过滤，支持一键确认与查看根因。

#### 7.5.3 Agent 配置面板（新增页面，Admin 权限）

- **版本列表**：展示配置历史，支持对比 diff、回滚到指定版本。
- **环境切换**：dev / staging / prod 配置一键切换（须审批流）。
- **依赖拓扑图**：展示 Agent → LLM / Tool / DataSource 的依赖关系与健康状态（Phase 2 可视化）。

---

### 7.6 测试策略

#### 7.6.1 新增模块测试矩阵

| 模块 | 测试文件 | 测试数 | 关键场景 |
|------|----------|--------|----------|
| AgentHub | `test_agent_hub.py` | 6 | 注册/配置版本化/激活/回滚/权限/依赖探测 |
| AgentWatch | `test_agent_watch.py` | 6 | 心跳上报/状态聚合/链路追踪/循环检测/超时检测/告警分级 |
| AgentMetrics | `test_agent_metrics.py` | 5 | 任务完成率计算/成本归因/质量评分/人机干预记录/时序聚合 |
| Agent Cockpit（前端） | E2E | 3 | 状态看板渲染/统计图表/配置回滚交互 |

#### 7.6.2 回归与集成要求

- 基线：154 + P0 模块新增测试（V2.3 基线）全绿。
- AgentHub 注册后，Agent Orchestra 调度前**必须**查询 AgentHub 状态；若 Agent 为 `DEGRADED` / `OFFLINE`，Orchestrator 须拒绝调度并记录日志（集成测试覆盖）。
- AgentWatch 心跳缺失须触发告警，告警须写入独立表（不与业务日志混表），便于审计。
- AgentMetrics 的 `estimated_cost_usd` 须与 LLM Gateway 日志交叉验证，误差 ≤5%（容忍第三方计费延迟）。

---

### 7.7 执行顺序建议

**第 1 轮（W15，与 TrendScout 等并行）**：AgentHub（注册 + 配置版本化 + 权限）+ AgentWatch（心跳 + 状态看板 + 基础告警）。  
**第 2 轮（W16）**：AgentMetrics（任务统计 + Token 成本 + 质量评分）+ 链路追踪存储（OpenTelemetry SDK 接入）。  
**第 3 轮（W17）**：Agent Cockpit 前端（状态看板 + 统计报表 + 配置面板）。  
**第 4 轮（W18–W19，Phase 2）**：成本精确归因（content_id 级）、漂移检测、依赖拓扑可视化、自动熔断策略。

---

### 7.8 专家评审意见与决议

> **评审对象**：AgentHub / AgentWatch / AgentMetrics 三大模块及其与现有架构的集成方案。  
> **评审真源**：以 v5.0 为产品真源，以 2026 年行业 Agent Observability 最佳实践（OpenTelemetry、MELT 框架、AI-native 监控）为技术参考。

| 角色 | 评审意见 | 结论 |
|------|---------|------|
| **产品** | 1. 当前 Agent Orchestra 仅有串行 Pipeline 描述，缺乏「谁在用、用得怎样、坏了怎么办」的治理能力；新增模块补齐了运营闭环。  <br>2. **MVP 必须聚焦**：W15–W16 只做「注册 + 心跳 + 基础统计」，禁止把「自动熔断 + 自愈」写进 Phase 1 验收。  <br>3. 人机干预率必须作为一级指标，它是系统健康的领先指标（Anthropic 2025 运营数据支持）。 | ✅ 采纳；Phase 1 聚焦基础治理，Phase 2 再做智能运维。 |
| **架构** | 1. AgentHub 配置版本化与现有「禁止无版本记录热改」的审计要求一致；建议配置快照存储复用现有数据库（或独立 `agent_config` 表），禁止引入额外分布式配置中心（如 Consul/Etcd）增加复杂度。  <br>2. 链路追踪必须基于 **OpenTelemetry** 标准，确保与现有 Prometheus / Grafana 栈兼容；自研仅做业务语义层（trace 关联 content_id）。  <br>3. 告警通道优先复用企业现有通知基础设施（企业微信/钉钉），不强制要求新建 PagerDuty。  <br>4. **禁止**在 AgentWatch 中引入「AI 自动修复 Agent」能力（超出 MVP 边界且与已废弃 MetaLearner 概念易混淆）。 | ✅ 采纳；OTel 标准接入；告警复用现有通道；不承诺自动修复。 |
| **算法 / AI** | 1. 质量评分采用 **Rubric-based + LLM-as-Judge** 是 2026 年主流实践（与人工评分相关性可达 0.85+），但 MVP 仅对 ContentForge / ComplianceGuard 启用，避免全量评分带来的 Token 成本失控。  <br>2. 漂移检测需要「版本对比基线」，建议基线数据至少积累 **7 天**后再启用，避免冷启动误报。  <br>3. 成本估算使用 LLM Gateway 返回的 `usage.prompt_tokens` / `usage.completion_tokens` 结合模型单价表计算；**不承诺**与第三方账单 100% 一致（存在缓存命中、批处理折扣等黑盒因素）。 | ✅ 采纳；MVP 仅两 Agent 自动评分；漂移检测需 7 天基线；成本估算允许 5% 误差。 |
| **运维 / SRE** | 1. 心跳周期 30s 在 20 账号 MVP 规模下合理；若后续扩展至 200+ 账号，须支持批量心跳或长连接（WebSocket）降级。  <br>2. Agent 状态看板数据建议 TTL 7 天，历史状态归档至冷存（S3 / OSS），避免热库膨胀。  <br>3. 告警分级中 P0（Publisher 失败）须绑定值班电话；P1/P2 仅企业微信即可。  <br>4. **第三方 LLM / 平台 API 故障不计入** Agent 自身 SLA；须在 SLA 定义中明确区分「Agent 服务可用」与「下游依赖可用」。 | ✅ 采纳；状态数据 TTL 7 天；P0 绑定电话告警；SLA 边界清晰化。 |
| **法务合规** | 1. 链路追踪的 `input_summary` / `output_summary` 仅存储前 200 字符摘要，**禁止**存储完整用户 prompt 或平台敏感数据（如账号 Cookie、Token）；完整 trace 若需保留，须做**数据脱敏 + 加密 + 访问审计**。  <br>2. 配置版本化的 `approval_status` 对 Publisher / ComplianceGuard 等敏感 Agent 强制启用双人复核，满足内部合规审计要求。  <br>3. Agent 权限矩阵须支持「最小权限原则」，特别是 Publisher 的「发布权限」与 AccountPool 的「账号访问权限」须解耦，防止单点权限过大。  <br>4. 成本归因数据涉及财务信息，须符合公司数据分级保护要求（建议定为「内部机密」级）。 | ✅ 采纳；摘要脱敏；敏感 Agent 强制审批；最小权限原则；成本数据分级保护。 |

**执行决议**：采纳上述全部评审意见；本文 **V2.4** 与《开发计划》**v2.2** 同步增补 W15–W19 周次；Agent 全生命周期管理模块作为 Phase 1 闭环的必要基础设施，与 TrendScout / MarketingMethodology / DataAnalyst / PlatformRule 并行推进。

---


---

## 八、新增需求：LLM 管理与配置中心（V2.5 增补 §8）【V2.7.2 精简版】

> **变更范围**：在 V2.4 基础上新增 **LLM Hub** 模块，补齐 v5.0 方案中「LLM Gateway / 多模型路由」仅有技术实现方向但缺乏**产品级统一管理**的缺口。  
> **V2.7.2 精简说明**：基于 UE 团队与专家评审反馈，原设计的三层路由（Global/Agent/Skill）、成本治理（预算配额/告警/自动降模）、熔断降级（Circuit Breaker）对 MVP 运营人员而言配置负担过重。现精简为**「厂家选择 + 模型名 + APIKey + 应用范围」**四字段模式，降低使用门槛，保留核心能力。复杂路由与成本管控列为 Phase 2 可选能力。  
> **对齐原则**：与现有 LLM Gateway（LiteLLM）集成；支持国产与国外大模型统一纳管；按「全局默认 / 节点级覆盖」配置；不引入已废弃概念。  
> **MVP 边界**：Phase 1 达成「模型注册 + 应用范围配置 + 基础成本看板 + 调用记录」闭环；Phase 2 扩展「三层路由 / 预算配额 / 熔断降级 / 智能路由」。

---

### 8.1 新增模块与现有架构对齐矩阵

| 新增模块 | 职责 | 对接现有模块 | 开发计划锚点 | Phase |
|---------|------|-------------|-------------|-------|
| **LLM Hub** | 模型注册、应用范围配置、基础成本看板、调用记录 | LLM Gateway（LiteLLM）、Agent Orchestra | **MVP 补全 W15** | Phase 1 |
| **Model Registry** | 国产/国外厂家选择、模型名、APIKey 配置 | LLM Hub | **MVP 补全 W15** | Phase 1 |
| **Scope Config** | 应用范围配置：全局默认 / 节点级（Agent/Skill）覆盖 | Agent Orchestra | **MVP 补全 W15** | Phase 1 |
| ~~Route Engine~~ | ~~三层路由 / 故障转移 / 加权随机~~ | ~~Phase 2 可选~~ | ~~W18-W19~~ | ~~Phase 2~~ |
| ~~Cost Governor~~ | ~~预算配额 / 成本告警 / 自动降模~~ | ~~Phase 2 可选~~ | ~~W18-W19~~ | ~~Phase 2~~ |
| ~~Circuit Breaker~~ | ~~熔断降级 / 自动恢复~~ | ~~Phase 2 可选~~ | ~~W18-W19~~ | ~~Phase 2~~ |
| **LLM Cockpit（前端）** | 模型管理面板、应用范围配置、成本看板 | Dashboard | **MVP 补全 W16** | Phase 1 |

---

### 8.2 LLM Hub - 大模型统一管理与配置中心【V2.7.2 精简版】

#### 8.2.1 职责与 MVP 范围（W15）

> **设计原则**：面向运营人员的极简配置。仅需四步完成模型接入：① 选择厂家 ② 填写模型名 ③ 粘贴 APIKey ④ 选择应用范围。

- **厂家选择与模型注册（Model Registry）**：
  - **国内主流厂家**：DeepSeek（深度求索）、阿里云（通义千问）、百度（文心一言）、智谱 AI（GLM）、Moonshot（Kimi）、科大讯飞（星火）等。
  - **国外主流厂家**：OpenAI（GPT-4o / GPT-4o-mini）、Anthropic（Claude-3.5 / Claude-3.7 Sonnet）、Google（Gemini-1.5 Pro / Flash）等。
  - **注册字段（精简为 5 项）**：
    - `provider`：厂家选择（下拉枚举：国内/国外分类展示）
    - `model_name`：模型名（如 `deepseek-chat`、`gpt-4o`）
    - `api_key`：API 密钥（密码输入框，前端掩码显示，后端加密存储）
    - `endpoint_base_url`：API 端点地址（可选，默认厂家官方地址）
    - `status`：ACTIVE / DISABLED（运营可手动启用/停用）
  - **国内/国外分类**：系统自动按厂家归属标记「境内/境外」，境外模型在处理敏感数据时由 ComplianceGuard 提示风险（不强制拦截，由运营确认）。

- **应用范围配置（Scope Config）【核心需求，替代原三层配置】**：
  - **全局默认（Global Default）**：系统下拉选择默认模型，适用于无特殊配置的所有任务。配置项：默认模型 + 温度参数（默认 0.5）+ 超时（默认 60s）。
  - **节点级覆盖（Node Override）**：为特定 Agent 或 Skill 指定不同模型。例如：ContentForge → GPT-4o；ComplianceGuard →  DeepSeek-V3（境内）。
  - **覆盖规则**：若节点未指定模型，则继承全局默认；若指定则使用节点级配置。运营在 LLM Cockpit 中以表格形式一览各节点的模型绑定状态。
  - **移除原三层配置**：原 L1/L2/L3 粒度对运营过于复杂，现简化为「全局 + 节点覆盖」两层，Skill 级配置延后至 Phase 2 SkillSmith 上线后再评估。

- **成本看板（精简版）**：
  - **仅展示消耗**：今日/本月总调用次数、总 Token 数、预估成本（按注册时填写的厂家官方单价自动计算）。
  - **按模型/按节点维度**：饼图展示各模型调用占比、各 Agent 调用 TOP5。
  - **移除原成本治理**：预算配额、成本告警、自动降模等复杂机制延后至 Phase 2。MVP 阶段仅做「展示消耗」，不做「限额管控」。

- **调用记录日志**：
  - 记录每次调用的模型、节点（Agent/Skill）、耗时、Token 数、成本估算，便于运营回溯与排查问题。
  - 日志保留 30 天（热库），支持按模型/节点/时间筛选导出。

#### 8.2.2 API 设计（精简版）

```
# === Model Registry ===
POST   /llm-hub/models                    # 注册新模型（admin）
GET    /llm-hub/models                    # 模型列表（支持按 provider / 境内境外 过滤）
GET    /llm-hub/models/{model_id}         # 模型详情
PATCH  /llm-hub/models/{model_id}         # 更新模型（api_key 单独接口，不走此处）
DELETE /llm-hub/models/{model_id}         # 注销模型（软删除）
POST   /llm-hub/models/{model_id}/test    # 测试连通性（验证 api_key 是否有效）

# === APIKey 独立管理（安全考虑） ===
POST   /llm-hub/models/{model_id}/api-key # 设置/更新 APIKey（后端加密存储，前端不可回显）
GET    /llm-hub/models/{model_id}/api-key/status  # 查询 APIKey 是否已配置（不返回密钥内容）

# === 应用范围配置（Scope Config） ===
GET    /llm-hub/configs/default           # 获取全局默认模型配置
PUT    /llm-hub/configs/default           # 更新全局默认模型（admin）

GET    /llm-hub/nodes/{node_id}/llm-config       # 获取节点级覆盖配置（node_type: agent|skill）
PUT    /llm-hub/nodes/{node_id}/llm-config       # 设置节点级覆盖配置
DELETE /llm-hub/nodes/{node_id}/llm-config       # 删除覆盖，恢复全局默认

GET    /llm-hub/configs/overview          # 一览表：所有节点及其当前绑定模型（全局 or 覆盖）

# === 成本看板 ===
GET    /llm-hub/cost-summary              # 今日/本月总消耗摘要
GET    /llm-hub/cost-by-model             # 按模型维度统计（调用次数/Token/成本）
GET    /llm-hub/cost-by-node              # 按节点维度统计 TOP10
GET    /llm-hub/cost-trend                # 近 7 日/30 日成本趋势（按模型/节点）

# === 调用记录 ===
GET    /llm-hub/usage-logs                # 调用日志列表（支持按 model/node/time 筛选）
GET    /llm-hub/usage-logs/{log_id}       # 单条调用详情
```

#### 8.2.3 数据模型（精简版）

```python
@dataclass
class LLMModel:
    id: str                       # 系统生成，如 "model_001"
    provider: str                 # 厂家：deepseek / openai / anthropic / aliyun / baidu / zhipu / moonshot
    provider_region: str          # DOMESTIC（境内）/ OVERSEAS（境外）
    model_name: str               # 模型名，如 "deepseek-chat" / "gpt-4o"
    display_name: str             # 可读名称，如 "DeepSeek-V3"
    endpoint_base_url: str        # API 端点，默认厂家官方地址，可覆盖
    api_key_encrypted: str        # AES-256 加密存储的 APIKey
    status: str                   # ACTIVE / DISABLED
    default_temperature: float    # 默认温度 0.5
    default_timeout: int          # 默认超时 60s
    created_at: str
    updated_at: str

@dataclass
class LLMScopeConfig:
    # 应用范围配置：全局默认 + 节点级覆盖
    id: str
    scope_type: str               # GLOBAL / AGENT / SKILL
    node_id: Optional[str]        # agent_id 或 skill_id；GLOBAL 为 null
    model_id: str                 # 绑定的模型 ID
    temperature: float            # 该范围下的温度覆盖
    timeout_seconds: int          # 该范围下的超时覆盖
    created_at: str
    updated_at: str

@dataclass
class LLMUsageLog:
    # 调用记录日志
    id: str
    trace_id: str
    model_id: str
    node_type: str                # AGENT / SKILL
    node_id: str                  # agent_id 或 skill_id
    input_tokens: int
    output_tokens: int
    latency_ms: int
    status: str                   # SUCCESS / ERROR / TIMEOUT
    created_at: str
```

---

### 8.3 调用流程与集成点【V2.7.2 精简版】

```
+-----------------------------------------------------------------------------+
|                    LLM 调用流程 - 单次调用（精简版）                           |
+-----------------------------------------------------------------------------+
|                                                                             |
|  1. Agent / Skill 发起调用                                                  |
|     +-> 携带 node_id (agent_id or skill_id)                                 |
|                                                                             |
|  2. 查询应用范围配置                                                         |
|     +-> 查询该 node_id 是否有覆盖配置？                                       |
|     +-> 有 -> 使用覆盖配置的 model_id                                         |
|     +-> 无 -> 使用 Global Default model_id                                    |
|                                                                             |
|  3. 读取模型配置                                                             |
|     +-> 查询 LLMModel 表获取 endpoint_base_url + api_key_decrypted          |
|                                                                             |
|  4. 执行调用 - 通过 LiteLLM Gateway                                         |
|     +-> 记录 LLMUsageLog 调用日志                                            |
|                                                                             |
|  5. 结果回写                                                                |
|     +-> 成功: 更新 AgentMetrics Token 消耗统计                               |
|     +-> 失败: 记录错误状态，返回上游错误信息                                  |
|                                                                             |
+-----------------------------------------------------------------------------+
```

**关键集成点**：
- **与 AgentHub**：Agent 注册时默认继承 Global Default 模型，运营可在 LLM Cockpit 中为 Agent 单独配置覆盖。
- **与 AgentMetrics**：`LLMUsageLog` 表作为成本归因数据源，`latency_ms` 注入 AgentMetrics 延迟分布。
- **与 ComplianceGuard**：境外模型调用时，ComplianceGuard 在审核台提示「当前使用境外模型，请注意数据出境风险」，由运营确认（不强制拦截，降低阻塞率）。

---

### 8.4 前端增强：LLM Cockpit（驾驶舱）【V2.7.2 精简版】

#### 8.4.1 模型管理面板（极简配置）

```
+-----------------------------------------------------------------------------+
|  LLM 模型配置                              [注册模型] [测试连通性]           |
+-----------------------------------------------------------------------------+
|  筛选: [全部 v] [境内 v] [境外 v]                                            |
+-----------------------------------------------------------------------------+
|  模型名称        | 厂家        | 类型   | 状态    | 应用范围      | 操作   |
|  ----------------|-------------|--------|---------|---------------|--------|
|  DeepSeek-V3     | DeepSeek    | 境内   | [G] 启用 | 全局默认      | 编辑   |
|  GPT-4o          | OpenAI      | 境外   | [G] 启用 | ContentForge  | 编辑   |
|  Qwen-Max        | 阿里云      | 境内   | [G] 启用 | 全局默认      | 编辑   |
|  Claude-3.5      | Anthropic   | 境外   | [G] 启用 | ComplianceGuard| 编辑  |
+-----------------------------------------------------------------------------+
```

**注册/编辑模型抽屉（仅 5 个字段）**：
```
┌─────────────────────────────────────────────────────────────┐
│  注册模型                                                   │
├─────────────────────────────────────────────────────────────┤
│  厂家选择 *  [国内 ▼]                                       │
│    └─ DeepSeek / 阿里云 / 百度 / 智谱 / Kimi / 讯飞...       │
│    └─ OpenAI / Anthropic / Google...                        │
│  模型名 *    [deepseek-chat           ]                     │
│  APIKey *    [••••••••••••••••        ] 👁 显示/隐藏        │
│  API端点     [https://api.deepseek.com/v1] （可选，默认官方）│
│  状态        [启用 ●] [停用 ○]                              │
├─────────────────────────────────────────────────────────────┤
│  [取消]                     [保存并测试连通性]              │
└─────────────────────────────────────────────────────────────┘
```

#### 8.4.2 应用范围配置面板

- **全局默认设置**：下拉框选择默认模型 + 温度滑块（0.1-1.0）+ 超时输入框。
- **节点级覆盖表格**：
  ```
  | 节点名称          | 节点类型 | 当前模型      | 操作         |
  |-------------------|----------|---------------|--------------|
  | ContentForge      | Agent    | GPT-4o (覆盖) | 编辑 / 恢复默认 |
  | ComplianceGuard   | Agent    | DeepSeek-V3 (覆盖) | 编辑 / 恢复默认 |
  | PoolPredictor     | Agent    | 继承全局默认   | 编辑         |
  ```

#### 8.4.3 成本看板（精简版）

- **今日概览**：总调用次数 / 总 Token 数 / 预估成本（按厂家官方单价自动计算）。
- **按模型维度**：饼图展示各模型调用占比。
- **按节点维度**：TOP10 Agent/Skill 调用排行。
- **趋势图**：近 7 日调用量折线，支持按模型/节点筛选。
- **移除**：预算进度条、告警阈值、熔断状态（均延后 Phase 2）。

---

### 8.5 测试策略（精简版）

| 模块 | 测试文件 | 测试数 | 关键场景 |
|------|----------|--------|----------|
| Model Registry | `test_llm_model_registry.py` | 4 | 注册/查询/更新/注销模型；api_key 加密存储；连通性测试 |
| 应用范围配置 | `test_llm_scope_config.py` | 3 | 全局默认 CRUD；节点覆盖配置；恢复默认；一览表查询 |
| 成本看板 | `test_llm_cost_summary.py` | 2 | 按模型/节点统计；趋势计算；单价*Token 成本公式验证 |
| 调用记录 | `test_llm_usage_logs.py` | 2 | 调用日志写入；按维度筛选导出；30 天 TTL 清理 |
| LLM Cockpit（前端）| E2E | 3 | 模型注册抽屉（5 字段）/ 应用范围表格 / 成本看板渲染 |

**回归与集成要求**：
- APIKey 必须 AES-256 加密存储，单测验证明文不可回显。
- 应用范围查询须验证：节点有覆盖 → 返回覆盖模型；无覆盖 → 返回全局默认。
- 成本估算按厂家官方单价计算，误差容忍 <=10%（MVP 阶段不做精确对账）。

---

### 8.6 执行顺序建议（精简版）

**第 1 轮（W15）**：Model Registry（极简 5 字段：厂家/模型名/api_key/端点/状态）+ 应用范围配置（全局默认 + 节点覆盖）。  
**第 2 轮（W15 末）**：与 LiteLLM Gateway 集成打通调用链路 + LLMUsageLog 记录 + AgentMetrics 消耗统计注入。  
**第 3 轮（W16）**：LLM Cockpit 前端（模型注册抽屉 / 应用范围一览表 / 成本看板）。  
**第 4 轮（W16 末）**：APIKey 加密存储（AES-256）+ 连通性测试接口 + 全量回归。  
**Phase 2 扩展（W18-W19）**：Route Engine（故障转移/加权随机）、Cost Governor（预算配额/告警）、Circuit Breaker（熔断降级）、模型竞技场。

---

### 8.7 专家评审意见与决议【V2.7.2 精简重审】

> **评审对象**：LLM Hub 精简版（Model Registry 极简 5 字段 + 应用范围配置 + 基础成本看板）及其与现有架构的集成方案。  
> **评审真源**：以 v5.0 为产品真源；以「运营人员可独立配置模型」为可用性目标。
> **重审背景**：原 V2.5 设计（三层路由 + 成本治理 + 熔断降级）经 UE 团队评估，对 MVP 运营人员配置负担过重，现申请精简。

| 角色 | 评审意见 | 结论 |
|------|---------|------|
| **产品** | 1. **精简方向正确**：原三层配置（Global/Agent/Skill）+ 路由策略 + 熔断机制对初级运营过于复杂，配置门槛过高会导致模型接入率低。  <br>2. **「厂家+模型名+APIKey+应用范围」四字段模式足够支撑 MVP**：运营在 2 分钟内可完成一家新模型的接入，极大降低使用门槛。  <br>3. **应用范围「全局+节点覆盖」两层模型清晰易懂**：节点未配置则继承全局，配置则覆盖，符合直觉。Skill 级延后至 Phase 2 合理。  <br>4. **成本看板仅展示不管控是务实选择**：MVP 阶段运营对预算敏感度不高，展示消耗即可；预算配额/告警/自动降模列为 Phase 2 可选项。  <br>5. **境外模型提示（不强制拦截）更合理**：原 T2 强制拦截会导致境外模型完全无法使用，改为「风险提示+运营确认」更灵活。 | ✅ **采纳精简方案**；四字段模式为 MVP 核心；境外模型风险提示替代强制拦截。 |
| **架构** | 1. **极简模式大幅简化后端实现**：移除 Route Engine、Cost Governor、Circuit Breaker 后，后端仅需 Model Registry + Scope Config + Usage Log 三张表，开发周期从 W15-W17 压缩至 W15-W16。  <br>2. **APIKey 加密存储不可妥协**：即使精简，api_key 仍须 AES-256 加密，前端不可回显，这是安全底线。  <br>3. **连通性测试接口是必要补齐**：运营填写 APIKey 后一键测试，避免配置错误导致后续调用全失败。  <br>4. **原三层路由/熔断/成本治理列为 Phase 2 技术债保留**：代码层面预留扩展接口，Phase 2 可无缝升级。 | ✅ **采纳**；极简模式降低实现复杂度；APIKey 加密为安全底线；预留 Phase 2 扩展接口。 |
| **算法 / AI** | 1. **温度参数保留在应用范围配置中是必要的**：不同任务类型对 temperature 的敏感度差异大，ContentForge 创意生成需要 0.5-0.9，ComplianceGuard 审核需要 <=0.3 保证确定性。建议在应用范围配置中预设「任务类型-参数包」快捷选项。  <br>2. **模型选择自由度与效果相关性高**：允许运营为不同节点选择不同模型，是提升整体效果的关键杠杆，精简不应牺牲此能力。 | ✅ **采纳**；应用范围保留温度参数；预设任务类型参数包快捷选项。 |
| **运维 / SRE** | 1. **移除熔断降级后，模型故障的感知能力下降**：建议通过 AgentWatch 监控模型错误率，错误率超过阈值时发送告警（不自动熔断），由运营手动切换模型。  <br>2. **移除预算配额后，成本失控风险增加**：建议在成本看板中增加「本月累计成本」红色高亮阈值（如超过上月 150%），作为软性提醒。  <br>3. **第三方模型 SLA 不计入自建系统 SLA** 的原则继续适用。 | ✅ **采纳**；AgentWatch 模型错误率告警替代自动熔断；成本看板增加环比高亮提醒。 |
| **法务合规** | 1. **APIKey 加密存储须满足等保 2.0 三级要求**：AES-256 + 访问审计 + 定期轮换。  <br>2. **境外模型使用须留痕**：LLMUsageLog 中增加 `provider_region` 字段，便于审计统计境内/境外模型调用比例。  <br>3. **国产模型「数据训练授权」状态仍需标注**：建议在 Model Registry 中增加 `data_training_opt_out` 布尔字段，默认 true（不用于训练）。 | ✅ **采纳**；APIKey 等保三级；调用日志增加境内境外标记；模型标注数据训练授权状态。 |

**执行决议**：采纳精简方案；本文 **V2.7.2** 与《开发计划》同步调整；LLM Hub 精简版作为 Phase 1 闭环基础设施，W15-W16 完成开发，原 Route Engine / Cost Governor / Circuit Breaker 列为 Phase 2 扩展能力。

---

---

## 九、新增需求：定时任务调度中心（V2.5 增补 §9）

> **变更范围**：在 V2.4 基础上新增 **CronHub** 模块，补齐 v5.0 方案中「Celery 异步校准」「Publisher 错峰调度」「DataAnalyst 24h 报告」等虽有定时需求但缺乏**统一调度管理、可视化编排、失败治理**的缺口。当前各模块定时逻辑分散在 Celery beat、crontab、代码硬编码中，无统一真源。  
> **对齐原则**：与现有 Celery 队列、Agent Orchestra、AgentWatch（心跳与告警）、AgentHub（Agent 生命周期）无缝集成；支持 Agent 级定时任务与系统级定时工作流；不引入已废弃概念。  
> **MVP 边界**：Phase 1 达成「Cron 表达式调度 + Agent 任务绑定 + 失败重试 + 基础监控」闭环；Phase 2 扩展「依赖编排（DAG）+ 分布式锁 + 日历调度（节假日跳过）」。

---

### 9.1 新增模块与现有架构对齐矩阵

| 新增模块 | 职责 | 对接现有模块 | 开发计划锚点 | Phase |
|---------|------|-------------|-------------|-------|
| **CronHub** | 定时任务注册、Cron 编排、执行历史、失败治理 | Celery Beat / Redis、Agent Orchestra、AgentWatch | **MVP 补全 W15-W16** | Phase 1 |
| **Job Registry** | 任务模板定义：系统预设 Job + 自定义 Job | CronHub | **MVP 补全 W15** | Phase 1 |
| **Schedule Engine** | Cron 解析、下次执行时间计算、触发器分发 | CronHub、Celery | **MVP 补全 W15** | Phase 1 |
| **Execution Runner** | 任务执行器：调用 Agent / 调用 API / 执行脚本 | Agent Orchestra、LLM Hub | **MVP 补全 W16** | Phase 1 |
| **Retry & Dead Letter** | 失败重试（指数退避）、死信队列、人工介入 | AgentWatch、AgentHub | **MVP 补全 W16** | Phase 1 |
| **Cron Cockpit（前端）** | 定时任务看板、执行历史、手动触发、启停控制 | Dashboard | **MVP 补全 W17** | Phase 1 |

---

### 9.2 CronHub - 定时任务调度中心

#### 9.2.1 职责与 MVP 范围（W15-W16）

- **Job 模板注册（Job Registry）**：
  - **系统预设 Job（开箱即用）**：
    - `trend-scout-daily`：每日 08:00 触发 TrendScout 生成趋势报告（Mock 数据源 + 手动导入热点）。
    - `data-analyst-daily`：每日 10:00 触发 DataAnalyst 生成昨日战报（基于已导入数据）。
    - `account-health-check`：每日 06:00 触发 AccountPool 健康评分更新 + 自动熔断检测。
    - `pool-predictor-calibrate`：每周一 03:00 触发 PoolPredictor 异步校准检查（Celery 批任务）。
    - `compliance-guard-audit`：每日 23:00 触发 ComplianceGuard 审核记录归档 + 证据链完整性检查。
    - `publisher-queue-drain`：每 30 分钟检查 Publisher 发布队列，处理堆积任务。
  - **自定义 Job**：运营可在前端创建自定义定时任务，选择目标 Agent（如 ContentForge）、输入参数模板、Cron 表达式；支持「测试运行（Dry Run）」 - 立即执行一次但不产生副作用（如 Publisher Dry Run 不真发布）。
  - **Job 版本化**：与 AgentHub 配置版本化对齐，Job 定义修改须创建新版本，支持回滚。

- **调度引擎（Schedule Engine）**：
  - **Cron 表达式**：标准 Unix Cron（5 字段）+ 扩展语法（如 `L` 表示月末、`W` 表示最近工作日，Phase 2）。
  - **时区支持**：默认北京时间（Asia/Shanghai）；支持按任务指定时区（如海外账号按当地时间发布）。
  - **并发控制**：同一 Job 的同一执行时间点，禁止重复触发（分布式锁，Redis `SET NX`）；若上次执行未结束，新触发可选择「跳过」或「排队」。
  - **触发器类型**：
    - **Cron 触发**：按表达式周期执行。
    - **一次性触发**：指定时间点执行一次（如「今晚 20:00 发布」）。
    - **事件触发（Phase 2）**：某 Agent 完成后触发下游 Job（如 ContentForge 完成 -> 自动触发 ComplianceGuard）。

- **执行器（Execution Runner）**：
  - **Agent 调用**：通过 Agent Orchestra 调用指定 Agent，携带 Job 参数；执行过程纳入 OpenTelemetry 链路追踪（复用 AgentWatch trace）。
  - **API 调用**：直接调用内部 API（如 POST `/data-analyst/reports`）。
  - **脚本执行（Phase 2）**：执行预置 Python/Shell 脚本（如数据清理、模型重训脚本）。
  - **执行上下文注入**：每次执行自动注入 `job_id`、`execution_id`、`scheduled_at`、`trace_id`，便于全链路追踪。

- **失败重试与死信（Retry & Dead Letter）**：
  - **重试策略**：默认指数退避（1min -> 2min -> 4min -> 8min），最多 3 次；可配置固定间隔或立即重试。
  - **失败分级**：
    - `RETRYABLE`（下游 API 超时、LLM 限流）-> 自动重试。
    - `NON_RETRYABLE`（参数错误、权限不足、合规拦截）-> 直接进死信，不自动重试。
    - `AGENT_DEGRADED`（Agent 状态为 DEGRADED）-> 延迟到 Agent 恢复后重试，或人工介入。
  - **死信队列（DLQ）**：重试耗尽的任务进入 DLQ，保留完整上下文（输入参数、错误堆栈、执行历史）；运营可在 Cron Cockpit 查看 DLQ 并选择「重试」「忽略」「手动执行」。
  - **告警**：任务连续失败 >=3 次或 DLQ 堆积 >=10 条，触发 P1 告警（企业微信）。

- **执行历史与审计**：
  - 每次执行记录：计划时间、实际开始时间、结束时间、耗时、状态（成功/失败/跳过/超时）、输出摘要、错误信息。
  - 历史保留：热库 30 天，冷存 180 天。
  - 支持按 Job / 时间 / 状态 / Agent 维度筛选。

#### 9.2.2 API 设计

```
# === Job 管理 ===
POST   /cron-hub/jobs                 # 创建 Job（自定义或复制系统预设）
GET    /cron-hub/jobs                 # Job 列表（支持按 agent_id / status 过滤）
GET    /cron-hub/jobs/{job_id}        # Job 详情（含 Cron 表达式、下次执行时间）
PATCH  /cron-hub/jobs/{job_id}        # 更新 Job（创建新版本）
DELETE /cron-hub/jobs/{job_id}        # 删除 Job（软删除，保留历史）
POST   /cron-hub/jobs/{job_id}/versions/{ver}/activate  # 激活指定版本
POST   /cron-hub/jobs/{job_id}/trigger  # 手动立即触发（支持 Dry Run）
POST   /cron-hub/jobs/{job_id}/pause    # 暂停调度
POST   /cron-hub/jobs/{job_id}/resume   # 恢复调度

# === 执行历史 ===
GET    /cron-hub/executions           # 执行历史列表
GET    /cron-hub/executions/{exec_id} # 执行详情（含完整日志摘要）
GET    /cron-hub/executions/{exec_id}/logs  # 执行日志（分页）

# === 死信队列 ===
GET    /cron-hub/dead-letter          # DLQ 列表
POST   /cron-hub/dead-letter/{id}/retry    # 死信重试
POST   /cron-hub/dead-letter/{id}/ignore   # 忽略死信
POST   /cron-hub/dead-letter/{id}/manual   # 手动执行（人工介入）

# === 调度状态 ===
GET    /cron-hub/scheduler/status     # 调度器健康状态（Celery Beat 是否存活）
GET    /cron-hub/scheduler/next-runs  # 未来 24h 即将执行的任务清单
```

#### 9.2.3 数据模型

```python
@dataclass
class CronJob:
    id: str
    name: str                     # 可读名称，如 "每日趋势侦察"
    description: str
    job_type: str                 # SYSTEM / CUSTOM
    source_template: Optional[str] # 系统预设模板 ID（如 "trend-scout-daily"）
    target_type: str              # AGENT / API / SCRIPT
    target_id: str                # agent_id 或 API endpoint
    target_params: Dict           # 调用参数模板（支持变量插值，如 {{today}}）
    schedule: str                 # Cron 表达式，如 "0 8 * * *"
    timezone: str                 # Asia/Shanghai
    concurrency_policy: str       # SKIP / QUEUE / ALLOW（默认 SKIP）
    retry_policy: Dict            # {"max_retries": 3, "backoff_type": "exponential", "initial_delay_sec": 60}
    timeout_seconds: int          # 单任务超时
    dry_run_supported: bool       # 是否支持 Dry Run
    status: str                   # ACTIVE / PAUSED / ARCHIVED
    owner: str                    # 创建人
    current_version: int
    created_at: str
    updated_at: str

@dataclass
class JobExecution:
    id: str
    job_id: str
    version: int
    execution_type: str           # SCHEDULED / MANUAL / DRY_RUN / RETRY
    scheduled_at: str             # 计划执行时间
    started_at: Optional[str]
    ended_at: Optional[str]
    duration_ms: Optional[int]
    status: str                   # PENDING / RUNNING / SUCCESS / FAILED / TIMEOUT / SKIPPED / CANCELLED
    output_summary: Optional[str] # 输出摘要（200 字符）
    error_message: Optional[str]
    error_type: Optional[str]     # RETRYABLE / NON_RETRYABLE / AGENT_DEGRADED
    retry_count: int
    trace_id: str
    triggered_by: Optional[str]   # 手动触发时记录操作人
    created_at: str

@dataclass
class DeadLetterJob:
    id: str
    job_id: str
    execution_id: str
    failed_at: str
    error_message: str
    error_type: str
    retry_exhausted: bool
    context_snapshot: Dict        # 执行上下文快照（参数、Agent 状态等）
    status: str                   # PENDING_REVIEW / RETRIED / IGNORED / MANUAL_EXECUTED
    reviewed_by: Optional[str]
    reviewed_at: Optional[str]
    created_at: str

@dataclass
class SchedulerState:
    # 调度器自身状态,用于健康监控
    beat_last_heartbeat: str      # Celery Beat 最后心跳
    beat_status: str              # HEALTHY / STALE / DOWN
    registered_jobs_count: int
    upcoming_24h_executions: int
    dlq_count: int
    last_sync_at: str
```

---

### 9.3 系统预设 Job 与业务模块映射

| 预设 Job ID | 目标 Agent / API | Cron 表达式 | 业务场景 | Phase |
|------------|-----------------|-------------|---------|-------|
| `trend-scout-daily` | TrendScout | `0 8 * * *` | 每日生成趋势报告 | Phase 1 |
| `data-analyst-daily` | DataAnalyst | `0 10 * * *` | 每日生成昨日战报 | Phase 1 |
| `account-health-daily` | AccountPool | `0 6 * * *` | 账号健康评分 + 熔断检测 | Phase 1 |
| `pool-predictor-weekly` | PoolPredictor | `0 3 * * 1` | 每周模型校准检查 | Phase 1 |
| `compliance-audit-daily` | ComplianceGuard | `0 23 * * *` | 审核记录归档 + 证据链检查 | Phase 1 |
| `publisher-drain` | Publisher | `*/30 * * * *` | 每 30 分钟 drain 发布队列 | Phase 1 |
| `agent-metrics-daily` | AgentMetrics | `0 9 * * *` | 每日 Agent 统计报表生成 | Phase 1 |
| `llm-cost-daily` | LLM Hub | `0 9 * * *` | 每日 LLM 成本汇总与告警检查 | Phase 1 |
| `content-insight-weekly` | ContentInsight | `0 4 * * 1` | 每周内容洞察报告（Phase 2） | Phase 2 |
| `skillsmith-eval-weekly` | SkillSmith | `0 5 * * 1` | 每周 Skill 效果评估（Phase 2） | Phase 2 |

---

### 9.4 执行流程与集成点

```
+-----------------------------------------------------------------------------+
|                      定时任务执行流程 - 单次调度                               |
+-----------------------------------------------------------------------------+
|                                                                             |
|  1. Celery Beat 按 Cron 表达式触发                                           |
|     +-> 生成 execution_id，查询 Job 配置版本                                  |
|                                                                             |
|  2. 并发控制 - 分布式锁                                                       |
|     +-> Redis SET NX execution_lock:{job_id}:{scheduled_at}                 |
|     +-> 锁已存在? 按 concurrency_policy 处理（SKIP / QUEUE）                |
|                                                                             |
|  3. 目标健康检查                                                              |
|     +-> 查询 AgentHub：目标 Agent 状态是否为 ACTIVE？                         |
|     +-> DEGRADED / OFFLINE -> 标记 AGENT_DEGRADED，视策略延迟或告警           |
|                                                                             |
|  4. 参数渲染                                                                  |
|     +-> 解析 target_params 模板变量: {{today}}, {{yesterday}}, {{account_list}}|
|                                                                             |
|  5. 执行调用                                                                  |
|     +-> AGENT -> Agent Orchestra 调用（携带 trace_id）                        |
|     +-> API -> 直接 HTTP 调用                                                 |
|     +-> 全程纳入 OpenTelemetry trace（复用 AgentWatch）                      |
|                                                                             |
|  6. 结果处理                                                                  |
|     +-> 成功: 记录 SUCCESS，更新执行历史                                       |
|     +-> 失败: 判断 error_type -> RETRYABLE 则入重试队列 / 否则入 DLQ           |
|                                                                             |
|  7. 告警与通知                                                                |
|     +-> 失败 -> AgentWatch 告警                                               |
|     +-> 连续失败 >=3 次 -> P1 告警                                             |
|     +-> DLQ 堆积 >=10 条 -> P1 告警                                            |
|                                                                             |
+-----------------------------------------------------------------------------+
```

**关键集成点**：
- **与 Celery**：CronHub 作为 Celery Beat 的上层管理面，Job 定义变更后动态 reload Beat schedule（通过 `celery beat --scheduler` 自定义或数据库驱动调度）。
- **与 Agent Orchestra**：Agent 调用须携带 `execution_id` 和 `trace_id`，确保定时任务产生的 Agent 调用可被链路追踪。
- **与 AgentHub**：调度前检查目标 Agent 状态；Job 版本化与 AgentHub 配置版本化对齐。
- **与 AgentWatch**：任务失败、超时、死信堆积均写入 AgentWatch 告警表；执行历史中的异常纳入 AgentMetrics 统计。
- **与 LLM Hub**：若 Job 调用的是 ContentForge 等 LLM Agent，LLM 路由决策须记录 `execution_id` 以便成本归因。

---

### 9.5 前端增强：Cron Cockpit（驾驶舱）

#### 9.5.1 定时任务看板

```
+-----------------------------------------------------------------------------+
|  定时任务中心                                [新建任务] [批量暂停] [刷新]     |
+-----------------------------------------------------------------------------+
|  筛选: [全部状态 v] [目标Agent v] [类型 v]                                   |
+-----------------------------------------------------------------------------+
|  任务名称           | 目标Agent      | Cron表达式    | 下次执行   | 状态   |
|  -------------------|---------------|---------------|-----------|--------|
|  每日趋势侦察       | TrendScout    | 0 8 * * *     | 明天 08:00| [G] 正常|
|  昨日战报生成       | DataAnalyst   | 0 10 * * *    | 明天 10:00| [G] 正常|
|  账号健康检查       | AccountPool   | 0 6 * * *     | 明天 06:00| [G] 正常|
|  发布队列Drain      | Publisher     | */30 * * * *  | 23:30     | [Y] 堆积|
|  模型校准检查       | PoolPredictor | 0 3 * * 1     | 下周一    | [G] 正常|
+-----------------------------------------------------------------------------+
```

#### 9.5.2 执行历史与日志

- 时间轴视图：展示某 Job 近 30 次执行结果（成功绿点 / 失败红点 / 跳过灰点）。
- 执行详情：点击某次执行查看完整参数、输出摘要、错误信息、链路追踪入口。
- 手动触发：支持「立即执行」和「Dry Run」两种模式；Dry Run 明确标注「无副作用」。

#### 9.5.3 死信队列面板

- DLQ 列表：展示待处理的死信任务，含失败原因、重试次数、上下文快照。
- 操作按钮：「重试」「忽略」「手动执行」；手动执行时弹出参数编辑框供运营调整。
- 批量处理：支持批量重试或批量忽略。

#### 9.5.4 调度器健康监控

- Celery Beat 心跳状态：最后心跳时间、状态（健康/僵死/宕机）。
- 未来 24h 执行预览：甘特图或列表展示即将执行的任务。
- 告警看板：任务失败趋势、DLQ 堆积趋势。

---

### 9.6 测试策略

| 模块 | 测试文件 | 测试数 | 关键场景 |
|------|----------|--------|----------|
| Job Registry | `test_cron_job_registry.py` | 4 | 创建/查询/更新/删除 Job；版本化激活 |
| Schedule Engine | `test_cron_schedule_engine.py` | 4 | Cron 解析/下次执行时间/时区/并发锁 |
| Execution Runner | `test_cron_execution_runner.py` | 5 | Agent 调用/API 调用/Dry Run/参数渲染/超时处理 |
| Retry & DLQ | `test_cron_retry_dlq.py` | 4 | 指数退避重试/死信入队/死信重试/批量忽略 |
| Scheduler Health | `test_cron_scheduler_health.py` | 3 | Beat 心跳检测/任务堆积告警/未来执行预览 |
| Cron Cockpit（前端）| E2E | 3 | 任务看板/执行历史/DLQ 操作 |

**回归与集成要求**：
- 定时任务触发 Agent 调用时，`trace_id` 必须贯穿全链路，与 AgentWatch 的 trace 表可关联。
- 分布式锁（Redis）必须在单测中验证：同一 Job 同一时间点禁止重复执行。
- Dry Run 模式须验证：ContentForge Dry Run 不写入数据库，Publisher Dry Run 不真发布。
- 系统预设 Job 的默认 Cron 表达式可在前端修改，但修改须记录审计日志。
- Celery Beat 僵死检测：若 Beat 心跳超过 5 分钟未更新，触发 P0 告警（调度器宕机影响全量定时任务）。

---

### 9.7 执行顺序建议

**第 1 轮（W15，与 AgentHub / LLM Hub 并行）**：Job Registry（系统预设 Job 定义）+ Schedule Engine（Cron 解析 + 分布式锁）+ 基础执行器（API 调用）。  
**第 2 轮（W16）**：Execution Runner（Agent 调用集成）+ Retry & DLQ（指数退避 + 死信队列）+ 系统预设 Job 全部激活。  
**第 3 轮（W16 末）**：与 AgentWatch 集成（失败告警、Beat 心跳监控）+ 与 AgentMetrics 集成（定时任务执行统计）。  
**第 4 轮（W17）**：Cron Cockpit 前端（任务看板 + 执行历史 + DLQ + 手动触发）。  
**第 5 轮（W18-W19，Phase 2）**：DAG 依赖编排（Job A 完成后触发 Job B）、日历调度（节假日跳过）、事件触发。

---

### 9.8 专家评审意见与决议

> **评审对象**：CronHub（Job Registry + Schedule Engine + Execution Runner + Retry & DLQ）及其与现有 Celery / Agent 架构的集成方案。  
> **评审真源**：以 v5.0 为产品真源，以分布式定时调度最佳实践（Celery Beat、Quartz、Airflow 轻量化方案）为技术参考。

| 角色 | 评审意见 | 结论 |
|------|---------|------|
| **产品** | 1. 当前 PRD 中定时需求确实分散：Celery 异步校准在 2.3、Publisher 错峰在 1.3、DataAnalyst 24h 报告在 2.3，但均无统一管理层。CronHub 是运营闭环的必要补齐。  <br>2. **系统预设 Job 清单合理**：覆盖了 MVP 阶段所有周期性业务场景（趋势侦察、战报、健康检查、校准、归档），降低运营配置负担。  <br>3. **Dry Run 是强需求**：运营在配置新 Job 时必须能「测试运行」验证参数正确性，特别是 Publisher 类任务，避免误发。  <br>4. MVP 禁止实现「复杂 DAG 编排」，须保持单 Job 独立执行，避免引入 Airflow 级别的复杂度；DAG 为 Phase 2 明确边界。 | [OK] 采纳；系统预设 Job 降低运营门槛；Dry Run 为必达功能；DAG 延后 Phase 2。 |
| **架构** | 1. Celery Beat 作为调度引擎是合理选择（团队已有 Celery 基础），但须注意 Beat 单点问题：MVP 可用单 Beat + 监控，Phase 2 考虑 Beat 多副本（RedBeat 或数据库驱动调度）。  <br>2. **分布式锁必须用 Redis Redlock 或至少 SET NX + 过期时间**，避免网络分区导致重复执行；锁过期时间建议为 Job 超时时间的 2 倍。  <br>3. Job 定义存储复用现有数据库，独立 `cron_job`、`job_execution`、`dead_letter_job` 表；执行历史数据量大，热库 30 天 + 冷存 180 天。  <br>4. 与 Agent Orchestra 集成时，须注意定时任务可能产生「执行高峰」（如每天 08:00 多个 Job 同时触发），建议系统预设 Job 的 Cron 表达式错开 5-10 分钟，或在前端给出「时间冲突提示」。  <br>5. **禁止**在 CronHub 中实现「分布式事务」或「saga 模式」，MVP 仅支持单 Job 独立执行，失败即重试或 DLQ。 | [OK] 采纳；Redis SET NX + 过期；执行历史冷热分离；预设 Job 错峰；禁止 MVP 实现分布式事务。 |
| **算法 / AI** | 1. PoolPredictor 的「每周校准检查」Job 须注意：若样本量不足 `N_min`（30），校准任务应自动跳过并记录「样本不足，暂不校准」，避免空跑浪费 Token。  <br>2. DataAnalyst「昨日战报」Job 若遇到「昨日无导入数据」的情况，应生成「无数据报告」而非报错进 DLQ，减少运营干扰。  <br>3. TrendScout「每日趋势侦察」在 MVP 阶段基于 Mock 数据源，须确保 Dry Run 和真实执行的输出格式一致，便于运营验证。 | [OK] 采纳；校准任务样本不足自动跳过；无数据生成空报告；Mock 与真实输出格式一致。 |
| **运维 / SRE** | 1. Celery Beat 僵死是定时调度系统的经典故障模式，必须实现 Beat 心跳监控（Beat 每 60s 写入 Redis 心跳键），失联 5 分钟触发 P0 告警。  <br>2. 定时任务的「执行高峰」可能压垮下游（如 08:00 同时触发 5 个 Agent 调用 LLM），建议：① 预设 Job 错峰；② 每个 Job 配置独立 rate limit；③ LLM Hub 侧做好熔断保护。  <br>3. DLQ 堆积是系统健康的重要指标，须配置「DLQ 堆积 >=10 条 -> P1 告警」和「DLQ 堆积 >=50 条 -> P0 告警」。  <br>4. 任务执行超时须严格管控：ContentForge 生成建议 120s，ComplianceGuard 建议 60s，Publisher 建议 300s（含平台 API 等待）；超时强制终止并标记 TIMEOUT。 | [OK] 采纳；Beat 心跳 P0 告警；执行高峰错峰 + rate limit；DLQ 分级告警；各 Agent 差异化超时。 |
| **法务合规** | 1. 定时任务若涉及「自动发布」（Publisher Job），须严格遵守 PlatformRule L3/L4 的时段限制与频率限制；CronHub 在调度 Publisher Job 前须调用 PlatformRule Engine 预检，违规时段禁止调度。  <br>2. 定时任务生成的报告（如 DataAnalyst 战报、TrendScout 趋势报告）若包含平台爬取数据或用户数据，须符合数据留存策略（2.3 证据链 >=2 年）。  <br>3. 自定义 Job 的创建权限须严格控制：普通运营仅可创建「只读类 Job」（如报告生成），「发布类 Job」「审核类 Job」须 admin 或双人复核。  <br>4. Job 执行日志中的 `output_summary` 须遵守 200 字符限制，禁止存储完整平台数据或用户隐私信息。 | [OK] 采纳；Publisher Job 调度前 PlatformRule 预检；报告数据留存合规；自定义 Job 分级权限；日志脱敏。 |

**执行决议**：采纳上述全部评审意见；本文 **V2.5** 与《开发计划》**v2.2** 同步增补 W15-W17 周次；CronHub 作为 Phase 1 闭环的必要基础设施，与 AgentHub / LLM Hub / AgentWatch 并行推进。

---

> **V2.5 完整修订总结**：本次增补 8 LLM Hub（大模型统一管理与三层配置）与 9 CronHub（定时任务调度中心），补齐了 v5.0 方案中「LLM Gateway 有技术实现但无产品治理」与「定时需求分散但无统一调度」的两大缺口。两个模块均与现有 AgentHub、AgentWatch、AgentMetrics、Agent Orchestra 深度集成，遵循「开源承担通用能力、自研只做编排与业务语义层」的原则，MVP 边界清晰，Phase 2 扩展路径明确。

# EcoDream Omni PRD V2.6
## 对齐《文档2_最终可行性完整产品方案_素人号矩阵AI平台》（**v5.0 Final**）

> **变更范围**：在 V2.5 基础上新增 **TaskHub（任务中心）**、**Workflow Engine（工作流编排）**、**Prompt Registry（Prompt管理）**、**Human-in-the-Loop（人工审核台）** 四大模块，补齐 v5.0 方案中「Agent Orchestra 仅有串行 Pipeline 描述」但缺乏**产品级任务管理、可视化工作流配置、Prompt全生命周期治理**的缺口。  
> **对齐原则**：与现有 AgentHub（配置版本化）、AgentWatch（监控告警）、LLM Hub（模型路由）、CronHub（定时调度）、AgentMetrics（质量统计）深度集成；工作流配置通过 **Prompt模板 + 有限变量插值** 实现，禁止无约束的自然语言编排；不引入已废弃概念。  
> **MVP 边界**：Phase 1 达成「串行工作流模板（选题→结构分析→生成→审核→预演→人工审核→发布）+ Prompt版本化 + 人工审核强制节点 + 任务状态全链路追踪」闭环；Phase 2 扩展「DAG分支编排 / 条件路由 / A/B工作流实验」。

---

## 〇、方案—PRD—开发计划 对齐矩阵（追溯）

| v5.0 方案章节 / 能力 | PRD 章节 | 开发计划锚点（**v2.2 周次为权威**） |
|---------------------|----------|--------------|
| 一、定位与边界（小红书 MVP、图文） | 全文约束 | Phase 1 |
| 四～八、四层风控 + AccountPool / PersonaPool | §2 已有增强 + AccountPool | W4–W5、W3.5 |
| 八、TrendScout（先 Mock/可控采集） | §2.1 | **MVP 补全 W11** |
| 八、MarketingMethodology（AIPL） | §2.2 | **MVP 补全 W12** |
| 八、PoolPredictor（**互动量区间**，非 L0–L5） | §2.4 | W9 冷启动 + **Phase 2 W18** |
| 八、DataAnalyst（区间命中、MAPE、归因） | §2.3 | **MVP 补全 W13** |
| 八、PlatformRule L3/L4 | §2.5、§2.6 | W6 已覆盖 L1/L2；**MVP 补全 W14** |
| 八、SkillSmith / ContentInsight | v5.0 **Phase 2** | **W16、W19** |
| 结构预检 + 反馈闭环工程边界 | **§2.6** | W12–W14、W13 |
| 九、LLM Gateway / 多模型路由 | 实现落在 LiteLLM + 自研路由 | 计划 §4–§5 |
| v5.0 **已废弃**：对抗辩论、MetaLearner、记忆联邦、流量池层级/CES 精确承诺 | **本文不出现需求** | Harness/文档索引 **不得** 再引用 |
| **AgentHub / AgentWatch / AgentMetrics** | **§7** | **MVP 补全 W15–W17** |
| **LLM Hub** | **§8** | **MVP 补全 W15–W17** |
| **CronHub** | **§9** | **MVP 补全 W15–W17** |
| **Task & Workflow Engine** | **§10** | **MVP 补全 W15–W18** |

---

## 一、当前代码与方案差距总表（V2.6 更新）

### 1.1 模型层偏差（必须修正）

| 当前实现 | v5.0 方案要求 | 偏差等级 | 修正动作 |
|----------|---------------|----------|----------|
| `LinearRegression` 等简化回归 | **可解释特征**（目标 18 维，**缺失维用默认值并降权**）；输出 **点赞/评论/收藏** 的区间与中位数 + `interval_mode` | 🔴 P0 | 演进 `prediction_engine.py`：优先 **QuantileRegressor** / 先验宽区间；Phase 2+ 再 XGBoost |
| 无区间不确定性量化 | 贝叶斯线性回归或等效 **可信区间** | 🔴 P0 | API 返回 `interval_lower/upper` 或分位数 |
| （旧 PRD）有序 Logit L0–L5 | **v5.0 已废弃**「流量池层级」预测 | ⚫ 不做 | 从数据模型与 UI 移除 L0–L5 |
| 无 ARIMA / 时段竞争 | v5.0 Phase 2+ **时段竞争系数**（ARIMA 为可选实现） | 🟡 P1 | Phase 2：Publisher / 预演面板共用竞争系数服务 |
| Thompson 采样（旧 PRD） | v5.0 未强制；可作为 **策略实验** 可选项 | 🟢 P2 | 不与「L0–L5」绑定；若做，仅用于模板臂选 |

### 1.2 缺失模块（必须新增）

| 模块 | 方案章节 | Phase | 当前状态 | 优先级 |
|------|----------|-------|----------|--------|
| **TrendScout** | 文档2 §8.4 | Phase 1（MVP：Mock + 手动导入） | 视代码基线 | 🔴 P0 |
| **MarketingMethodology** | 文档2 §6 + 架构 MarketingMethod | Phase 1 | 视代码基线 | 🔴 P0 |
| **DataAnalyst** | 文档2 §8.9 | Phase 1 | 视代码基线 | 🔴 P0 |
| **PlatformRule Engine（L3/L4）** | 文档2 §8.3 | Phase 1 | 常仅 L1–L2 | 🔴 P0 |
| **PersonaPool（完整版）** | 文档2 §8.2 | Phase 1 | 基础模型 | 🟡 P1 |
| **SkillSmith** | 文档2 §8.10、§十六 Phase 2 | Phase 2 | 视代码基线 | 🟡 P1 |
| **ContentInsight** | 文档2 §8.11、§十六 Phase 2 | Phase 2 | 视代码基线 | 🟡 P1 |
| **AgentHub / AgentWatch / AgentMetrics** | §7 | Phase 1 | 新增 | 🔴 P0 |
| **LLM Hub** | §8 | Phase 1 | 新增 | 🔴 P0 |
| **CronHub** | §9 | Phase 1 | 新增 | 🔴 P0 |
| **Task & Workflow Engine** | §10 | Phase 1 | 新增 | 🔴 P0 |
| ~~**MetaLearner**~~ | **v5.0 已移除** | — | — | ⚫ 不规划 |
| ~~**对抗辩论**~~ | **v5.0 已移除** | — | — | ⚫ 不规划 |

---

## 二、P0 模块详细设计（立即执行）

> **注**：§2.1–§2.6 为 V2.3 基线内容，此处省略以保持文档聚焦。完整内容参见 V2.3 版本。本节重点展示 V2.6 新增模块。**

---

## 七、新增需求：Agent 全生命周期管理、活跃监控与统计（V2.4 增补）

> **注**：§7.1–§7.8 为 V2.4 完整内容，包含 AgentHub、AgentWatch、AgentMetrics 三大模块及专家评审意见。此处省略以保持文档聚焦。**

---

## 八、新增需求：LLM 管理与配置中心（V2.5 增补 §8）

> **注**：§8.1–§8.7 为 V2.5 完整内容，包含 Model Registry、Route Engine、Cost Governor、Circuit Breaker 及专家评审意见。此处省略以保持文档聚焦。**

---

## 九、新增需求：定时任务调度中心（V2.5 增补 §9）

> **注**：§9.1–§9.8 为 V2.5 完整内容，包含 Job Registry、Schedule Engine、Execution Runner、Retry & DLQ 及专家评审意见。此处省略以保持文档聚焦。**

---

## 十、新增需求：任务与工作流引擎（Task & Workflow Engine）（V2.6 增补 §10）

### 10.1 新增模块与现有架构对齐矩阵

| 新增模块 | 职责 | 对接现有模块 | 开发计划锚点 | Phase |
|---------|------|-------------|-------------|-------|
| **TaskHub** | 任务创建、生命周期管理、状态机、队列 | Agent Orchestra、Workflow Engine、CronHub | **MVP 补全 W15-W16** | Phase 1 |
| **Workflow Engine** | 工作流模板定义、串行节点调度、上下文传递、失败重试 | AgentHub、Agent Orchestra、LLM Hub | **MVP 补全 W16** | Phase 1 |
| **Prompt Registry** | Prompt模板注册、版本化、变量管理、环境隔离、效果追踪 | LLM Hub、ContentForge、AgentHub | **MVP 补全 W15-W16** | Phase 1 |
| **Human-in-the-Loop** | 人工审核台、强制拦截、反馈回写、双人复核 | ComplianceGuard、Publisher、Workflow Engine | **MVP 补全 W16** | Phase 1 |
| **Workflow Cockpit** | 工作流可视化、任务看板、Prompt编辑、执行监控 | Dashboard、AgentWatch、AgentMetrics | **MVP 补全 W17** | Phase 1 |

### 10.2 核心设计原则与约束（红线）

> **以下约束为专家评审后的强制性边界，任何实现不得突破。**

| 约束项 | 说明 | 违反后果 |
|--------|------|----------|
| **MVP 仅限串行 Pipeline** | 工作流节点必须按线性顺序执行，禁止 DAG 分支、并行节点、条件跳转 | 若引入 DAG，MVP 复杂度将等同于 Airflow，15 周内无法收敛 |
| **人工审核为强制节点** | 任何发布类工作流模板必须包含 `human_approval` 节点，且不可配置为跳过 | 全自动发布违反平台合规与内部风控要求 |
| **Prompt 变量白名单制** | 仅允许预定义变量（如 `{{topic}}`、`{{persona_id}}`、`{{style}}`），禁止自由文本插值到系统 Prompt | 防止 Prompt 注入攻击与模型行为失控 |
| **Prompt 版本化对齐 AgentHub** | Prompt 模板修改必须创建新版本，禁止无版本记录的热改；版本回滚与 AgentHub 配置回滚联动 | 满足审计要求，确保可回滚 |
| **工作流节点间状态传递通过 Redis Context** | 禁止直接内存共享或本地文件传递；每个节点输出写入 Redis `workflow_context:{task_id}` | 支持分布式执行与故障恢复 |

### 10.3 TaskHub — 任务中心

#### 10.3.1 职责与 MVP 范围（W15-W16）

- **任务创建**：运营选择账号池（AccountPool）+ 人设（PersonaPool）+ 工作流模板（Workflow Template）+ Prompt变量 → 创建 Task。
- **任务状态机**：
  ```
  DRAFT -> CONFIGURING -> QUEUED -> RUNNING -> PAUSED -> COMPLETED
                              |         |         |
                              v         v         v
                          FAILED    HUMAN_WAIT   CANCELLED
  ```
  - `PAUSED`：专用于人工审核等待状态，人工介入后转为 `RUNNING` 或 `FAILED`。
  - `HUMAN_WAIT`：到达人工审核节点时的挂起状态。
- **任务队列**：每个账号独立队列（防止同一账号并发发布冲突）；全局队列优先级按账号健康分排序。
- **批量任务**：支持「为 N 个账号创建相同工作流的批量任务」，生成子 Task（`parent_task_id` 关联）。
- **定时任务绑定**：与 CronHub 集成，支持「创建定时重复任务」（如「每日为账号A执行选题工作流」）。

#### 10.3.2 API 设计

```
# === 任务管理 ===
POST   /task-hub/tasks                 # 创建任务（选择工作流模板+Prompt变量）
GET    /task-hub/tasks                 # 任务列表（支持按 status / account_id / workflow_id 过滤）
GET    /task-hub/tasks/{task_id}       # 任务详情（含当前节点、执行历史、上下文快照）
PATCH  /task-hub/tasks/{task_id}       # 更新任务（仅 DRAFT 状态可修改配置）
POST   /task-hub/tasks/{task_id}/cancel  # 取消任务
POST   /task-hub/tasks/{task_id}/retry   # 失败重试（从失败节点或指定节点）

# === 批量任务 ===
POST   /task-hub/batch-tasks           # 创建批量任务
GET    /task-hub/batch-tasks/{id}/progress  # 批量任务进度（完成数/失败数/待处理数）

# === 人工审核接口 ===
POST   /task-hub/tasks/{task_id}/approve    # 人工审核通过
POST   /task-hub/tasks/{task_id}/reject     # 人工审核驳回（须填写理由）
POST   /task-hub/tasks/{task_id}/revise     # 打回修改（指定节点重新执行）

# === 任务上下文（调试/审计） ===
GET    /task-hub/tasks/{task_id}/context    # 获取当前工作流上下文（节点输出摘要）
GET    /task-hub/tasks/{task_id}/node-logs  # 节点执行日志
```

#### 10.3.3 数据模型

```python
@dataclass
class Task:
    id: str
    name: str                     # 任务名称，如「账号A-养猫攻略-20260514」
    workflow_template_id: str     # 绑定工作流模板
    workflow_version: int         # 工作流模板版本（版本化锁定）
    account_id: str               # 目标账号
    persona_id: str               # 使用人设
    prompt_variables: Dict        # 变量值，如 {"topic": "新手养猫", "style": "口语化"}
    status: str                   # DRAFT / CONFIGURING / QUEUED / RUNNING / PAUSED / HUMAN_WAIT / COMPLETED / FAILED / CANCELLED
    current_node_index: int       # 当前执行到第几个节点（0-based）
    parent_task_id: Optional[str] # 批量任务父ID
    priority: int                 # 0-100，账号健康分映射
    scheduled_at: Optional[str]   # 定时执行时间（CronHub绑定）
    created_by: str
    created_at: str
    updated_at: str
    completed_at: Optional[str]

@dataclass
class TaskNodeExecution:
    id: str
    task_id: str
    node_id: str                  # 工作流节点标识
    node_type: str                # AGENT / HUMAN_APPROVAL / CONDITION / TIMER
    agent_id: Optional[str]      # 若为Agent节点
    prompt_template_id: Optional[str]  # 使用的Prompt模板版本
    status: str                   # PENDING / RUNNING / SUCCESS / FAILED / SKIPPED / TIMEOUT / HUMAN_WAIT
    input_context: Dict           # 输入上下文摘要（前500字符）
    output_context: Dict          # 输出上下文摘要（前500字符）
    started_at: Optional[str]
    ended_at: Optional[str]
    duration_ms: Optional[int]
    error_message: Optional[str]
    trace_id: str                 # OpenTelemetry trace_id
    human_decision: Optional[str] # APPROVE / REJECT / REVISE（人工节点）
    human_feedback: Optional[str] # 人工填写的反馈/修改意见
    created_at: str
```

### 10.4 Workflow Engine — 工作流编排引擎

#### 10.4.1 职责与 MVP 范围（W16）

- **工作流模板定义**：运营通过前端配置工作流模板（预设模板 + 有限自定义）。**MVP 禁止**「通过自然语言 Prompt 自由定义工作流拓扑」，仅允许「选择预设节点序列 + 配置节点参数」。
- **预设工作流模板（开箱即用）**：
  - `content_creation_standard`：选题（TrendScout）→ 结构分析（MarketingMethodology）→ 框架生成（ContentForge）→ 正文生成（ContentForge）→ 合规审核（ComplianceGuard）→ 互动预演（PoolPredictor）→ **人工审核** → 发布（Publisher）
  - `content_creation_light`：选题 → 正文生成 → 合规审核 → **人工审核** → 发布（简化版，跳过框架生成）
  - `trend_scout_only`：仅执行 TrendScout 生成趋势报告（无发布）
  - `data_analysis_only`：仅执行 DataAnalyst 生成战报（无发布）
- **节点类型（MVP 限制）**：
  - `agent`：调用指定 Agent；须配置 `agent_id`、`prompt_template_id`、`timeout`、`retry_policy`。
  - `human_approval`：强制人工审核；须配置 `review_type`（内容审核 / 发布确认）、`timeout`（默认 24h，超时自动驳回）。
  - `timer`：等待固定时长（如「发布后等待 24h 再执行 DataAnalyst」）。
  - ~~`condition`~~：**MVP 禁用**（条件分支引入 DAG 复杂度，Phase 2 开放）。
  - ~~`parallel`~~：**MVP 禁用**（并行节点增加分布式锁与合并复杂度，Phase 2 开放）。
- **上下文传递（Context Pipeline）**：
  - 每个节点输出按 JSON Schema 写入 Redis `workflow_context:{task_id}`。
  - 下游节点通过 `{{context.prev_node.output.field}}` 语法读取上游输出。
  - Context 保留 30 天（与执行历史一致），支持任务重试时恢复。
- **失败策略**：
  - `fail_fast`：某节点失败，整个任务失败，进入 DLQ。
  - `continue`：某节点失败，跳过继续下游（仅对非关键节点如 PoolPredictor 开放，默认关闭）。
  - `retry_then_fail`：指数退避重试 3 次后失败（默认策略）。

#### 10.4.2 API 设计

```
# === 工作流模板管理 ===
POST   /workflow-engine/templates              # 创建模板（基于预设复制或空白）
GET    /workflow-engine/templates              # 模板列表
GET    /workflow-engine/templates/{id}         # 模板详情（含节点DAG）
PATCH  /workflow-engine/templates/{id}         # 更新模板（创建新版本）
POST   /workflow-engine/templates/{id}/versions/{ver}/activate  # 激活版本
POST   /workflow-engine/templates/{id}/versions/{ver}/rollback  # 回滚

# === 节点管理（模板内） ===
POST   /workflow-engine/templates/{id}/nodes     # 添加节点（MVP仅限串行追加）
PATCH  /workflow-engine/templates/{id}/nodes/{node_id}  # 更新节点配置
DELETE /workflow-engine/templates/{id}/nodes/{node_id}  # 删除节点（仅草稿版本）

# === 工作流执行 ===
POST   /workflow-engine/executions             # 触发执行（由 TaskHub 调用）
GET    /workflow-engine/executions/{exec_id}   # 执行详情
POST   /workflow-engine/executions/{exec_id}/pause    # 暂停（人工介入前）
POST   /workflow-engine/executions/{exec_id}/resume   # 恢复
POST   /workflow-engine/executions/{exec_id}/skip-node  # 跳过当前节点（admin权限，须留痕）

# === 上下文调试 ===
GET    /workflow-engine/executions/{exec_id}/context    # 获取实时上下文
```

#### 10.4.3 数据模型

```python
@dataclass
class WorkflowTemplate:
    id: str
    name: str                     # 如「标准内容生产工作流」
    description: str
    source_preset: Optional[str]  # 预设模板ID（如 "content_creation_standard"）
    version: int
    status: str                   # DRAFT / ACTIVE / DEPRECATED
    owner: str
    nodes: List[WorkflowNode]   # 节点序列（MVP为List，Phase 2为DAG）
    created_at: str
    updated_at: str
    approval_status: str          # PENDING / APPROVED（发布类工作流须审批）

@dataclass
class WorkflowNode:
    id: str
    template_id: str
    node_index: int               # 串行序号（MVP）
    node_type: str                # AGENT / HUMAN_APPROVAL / TIMER
    node_name: str                # 可读名称，如「合规自动审核」
    agent_id: Optional[str]       # AGENT类型必填
    prompt_template_id: Optional[str]  # AGENT类型必填
    timeout_seconds: int          # 默认 120s
    retry_policy: Dict            # {"max_retries": 3, "backoff": "exponential"}
    fail_strategy: str            # FAIL_FAST / CONTINUE / RETRY_THEN_FAIL
    input_mapping: Dict           # 输入上下文映射规则
    output_mapping: Dict          # 输出上下文写入规则
    human_config: Optional[Dict]  # HUMAN_APPROVAL类型：{review_type, timeout_hours, required_role}

@dataclass
class WorkflowExecution:
    id: str
    task_id: str
    template_id: str
    template_version: int
    status: str                   # RUNNING / PAUSED / COMPLETED / FAILED / CANCELLED
    current_node_index: int
    context_ref: str              # Redis key: workflow_context:{task_id}
    started_at: str
    ended_at: Optional[str]
    created_at: str
```

### 10.5 Prompt Registry — Prompt 全生命周期管理

#### 10.5.1 职责与 MVP 范围（W15-W16）

> **核心解决疑问**：「Prompt 如何管理？」——通过独立 Registry 实现版本化、变量治理、效果追踪。

- **Prompt 模板注册**：
  - 每个 Agent 的 Prompt 模板独立注册（如 `content-forge-v1-标题生成`、`compliance-guard-v2-审核指令`）。
  - 支持 Jinja2 变量语法（严格白名单：`{{topic}}`、`{{persona_voice}}`、`{{structure_template}}` 等）。
  - **变量白名单校验**：模板保存时，系统解析所有 `{{variable}}`，若存在未注册变量，拒绝保存。
- **版本化与环境隔离**：
  - 三态管理：DRAFT / ACTIVE / ARCHIVED。
  - 多环境隔离：`dev` / `staging` / `prod`。
  - 与 AgentHub 配置版本化对齐：Agent 配置回滚时，关联的 Prompt 模板版本同步回滚。
- **Prompt 效果追踪（闭环核心）**：
  - 记录每个 Prompt 版本的任务完成率、人工干预率、质量评分（AgentMetrics）。
  - **Prompt A/B 测试（Phase 2）**：同一工作流可配置两版 Prompt，按流量比例分配。
  - **Prompt 性能看板**：展示各 Prompt 版本的「生成质量分 vs Token 成本」散点图，辅助运营优化。
- **安全约束**：
  - 模板内容须经过 XSS 过滤与 Prompt 注入检测（禁止包含 `ignore previous instructions`、`system override` 等攻击模式）。
  - 敏感 Prompt（如 ComplianceGuard 审核规则）须双人复核。
  - 完整 Prompt 不落日志，仅存储模板 ID + 变量值摘要。

#### 10.5.2 API 设计

```
# === Prompt 模板管理 ===
POST   /prompt-registry/templates           # 创建模板
GET    /prompt-registry/templates           # 列表（按 agent_id / status / env）
GET    /prompt-registry/templates/{id}        # 详情（含版本历史）
PATCH  /prompt-registry/templates/{id}        # 更新（创建新版本）
POST   /prompt-registry/templates/{id}/versions/{ver}/activate  # 激活
POST   /prompt-registry/templates/{id}/versions/{ver}/rollback    # 回滚

# === 变量管理 ===
GET    /prompt-registry/variables             # 全局变量白名单
POST   /prompt-registry/variables             # 注册新变量（admin）
GET    /prompt-registry/templates/{id}/variables  # 模板使用的变量列表

# === 效果追踪 ===
GET    /prompt-registry/templates/{id}/performance  # Prompt版本性能对比
GET    /prompt-registry/templates/{id}/ab-tests       # A/B测试配置（Phase 2）

# === 渲染与调试 ===
POST   /prompt-registry/templates/{id}/render       # 传入变量，渲染最终Prompt（Dry Run）
POST   /prompt-registry/templates/{id}/eval         # 手动触发效果评估（LLM-as-Judge）
```

#### 10.5.3 数据模型

```python
@dataclass
class PromptTemplate:
    id: str
    name: str                     # 如「ContentForge-标题生成-口语化风格」
    agent_id: str                 # 绑定目标 Agent
    version: int
    env: str                      # dev / staging / prod
    template_content: str         # Jinja2模板，含 {{variable}} 占位符
    variables: List[str]          # 白名单变量列表
    system_fingerprint: str       # 模板内容SHA-256，防篡改
    status: str                   # DRAFT / ACTIVE / ARCHIVED
    approval_status: str          # PENDING / APPROVED（敏感Agent必填）
    performance_score: Optional[float]  # 综合质量分（自动计算）
    created_by: str
    created_at: str
    updated_at: str

@dataclass
class PromptVariable:
    name: str                     # 如 "topic"
    description: str              # 变量说明
    type: str                     # STRING / NUMBER / ENUM / JSON
    allowed_values: Optional[List[str]]  # ENUM类型可选值
    max_length: Optional[int]     # 字符串最大长度
    required: bool
    default_value: Optional[str]
    validation_regex: Optional[str]  # 校验正则

@dataclass
class PromptPerformance:
    id: str
    template_id: str
    version: int
    date: str
    invocations: int
    avg_quality_score: float
    avg_token_cost: float
    human_intervention_rate: float
    task_completion_rate: float
    fail_rate: float
```

### 10.6 Human-in-the-Loop — 人工审核台

#### 10.6.1 职责与 MVP 范围（W16）

> **核心解决疑问**：「工作人员审核后一键发布」——人工审核台是连接自动流程与人工决策的关键节点。

- **审核台视图**：
  - 左侧：内容预览（图文排版模拟，非真实平台渲染）。
  - 右侧：Agent 输出摘要（合规审核结果、互动量预演区间、结构质量分）。
  - 底部：Prompt 变量与修改建议（运营可一键修改变量后重新生成）。
- **审核决策**：
  - **通过**：进入 Publisher 发布队列，运营可选择「立即发布」或「定时发布」。
  - **驳回**：任务失败，记录驳回理由，进入 DLQ（可后续分析驳回原因分布）。
  - **打回修改**：选择打回到指定节点（如「打回 ContentForge 重新生成」或「打回 PoolPredictor 调整时段」），保留上下文，重新执行下游节点。
- **双人复核（敏感操作）**：
  - Publisher 发布确认须双人复核（与 AgentHub 权限对齐）。
  - 复核记录留存 ≥2 年（与 ComplianceGuard 证据链对齐）。
- **反馈闭环**：
  - 人工修改后的最终内容 vs Agent 原始输出，差异写入 `human_intervention` 表（复用 AgentMetrics 人机干预模型）。
  - 驳回理由 NLP 聚类（Phase 2），用于反向优化 Prompt 模板。

#### 10.6.2 API 设计

```
# === 审核台 ===
GET    /human-in-loop/tasks               # 待审核任务列表（按账号/优先级/时间）
GET    /human-in-loop/tasks/{task_id}      # 审核详情（内容预览 + Agent输出摘要）
POST   /human-in-loop/tasks/{task_id}/approve   # 通过
POST   /human-in-loop/tasks/{task_id}/reject    # 驳回（须填理由）
POST   /human-in-loop/tasks/{task_id}/revise    # 打回修改（指定回退节点 + 修改参数）

# === 批量审核 ===
POST   /human-in-loop/batch-approve        # 批量通过（须二次确认）
POST   /human-in-loop/batch-reject         # 批量驳回

# === 审核统计 ===
GET    /human-in-loop/stats                # 审核效率统计（人均审核量/平均耗时/驳回率）
GET    /human-in-loop/rejection-reasons    # 驳回理由分布（TOP10）
```

### 10.7 Workflow Cockpit — 工作流驾驶舱（前端）

#### 10.7.1 视图设计

- **任务看板（Kanban）**：
  - 列：待配置 / 队列中 / 执行中 / 人工审核中 / 已完成 / 失败。
  - 卡片：任务名称、账号、当前节点、预计剩余时间、优先级。
- **工作流模板编辑器**：
  - 左侧：节点库（拖拽式，MVP 仅展示可用节点列表，点击追加）。
  - 中间：串行 Pipeline 可视化（纵向时间轴，每个节点显示状态图标）。
  - 右侧：节点配置面板（选择 Agent、选择 Prompt 模板、配置变量映射）。
  - **约束提示**：若运营删除 `human_approval` 节点，系统强制提示「发布类工作流必须包含人工审核」，禁止保存。
- **Prompt 编辑器**：
  - 分屏：左侧 Jinja2 模板编辑，右侧实时渲染预览（传入测试变量）。
  - 变量高亮：已注册变量绿色，未注册变量红色告警。
  - 版本对比：diff 视图展示两版 Prompt 差异。
- **执行监控**：
  - 实时展示任务执行进度（节点级进度条）。
  - 点击节点查看输入/输出摘要、链路追踪入口、AgentMetrics 质量分。

### 10.8 与现有模块集成关系

| 集成模块 | 集成点 | 说明 |
|---------|--------|------|
| **AgentHub** | Workflow Engine 调度 Agent 前，查询 AgentHub 确认 Agent 状态为 ACTIVE；Agent 配置版本化包含 `prompt_template_version` 字段 | 确保 Agent 与 Prompt 版本一致性 |
| **AgentWatch** | 每个工作流节点执行生成 Span；节点超时/失败/循环检测纳入 AgentWatch 告警；人工审核超时触发 P1 告警 | 统一监控 |
| **LLM Hub** | ContentForge / ComplianceGuard 等 Agent 节点调用 LLM 时，通过 LLM Hub 路由；Prompt Registry 的模板渲染后文本作为 LLM 输入 | 模型路由与成本治理 |
| **CronHub** | 支持创建「定时工作流任务」（CronJob 绑定 Workflow Template + Task 参数）；系统预设 Job `workflow-daily-content` | 定时自动化 |
| **AgentMetrics** | 工作流任务完成率、节点耗时、Prompt 版本效果、人机干预率，全部汇入 AgentMetrics 统计 | 质量闭环 |
| **DataAnalyst** | 工作流发布后的内容，自动关联 DataAnalyst 24h 报告；报告结果回写 Task 上下文 | 数据闭环 |
| **PlatformRule** | Publisher 节点执行前，Workflow Engine 调用 PlatformRule Engine 预检（L3/L4），违规则阻断 | 风控闭环 |

### 10.9 测试策略

| 模块 | 测试文件 | 测试数 | 关键场景 |
|------|----------|--------|----------|
| TaskHub | `test_task_hub.py` | 5 | 创建/状态机转换/取消/重试/批量任务 |
| Workflow Engine | `test_workflow_engine.py` | 6 | 模板创建/串行执行/上下文传递/失败策略/版本回滚/节点跳过 |
| Prompt Registry | `test_prompt_registry.py` | 5 | 模板注册/变量白名单校验/版本激活/渲染/Dry Run |
| Human-in-the-Loop | `test_human_in_loop.py` | 4 | 审核通过/驳回/打回修改/双人复核 |
| Workflow Cockpit | E2E | 3 | 看板渲染/模板编辑/节点配置 |
| 集成测试 | `test_workflow_integration.py` | 4 | Task→Workflow→Agent→Human→Publisher 全链路 / CronHub触发 / AgentHub状态检查 / 上下文恢复 |

**回归要求**：基线 154 + V2.5 新增测试全绿；工作流模块新增 27 个测试。

### 10.10 执行顺序建议

**第 1 轮（W15，与 AgentHub / LLM Hub 并行）**：Prompt Registry（变量白名单 + 版本化）+ TaskHub（任务创建 + 状态机）。  
**第 2 轮（W16）**：Workflow Engine（串行模板 + 上下文传递 + 预设模板）+ Human-in-the-Loop（审核台 + 反馈回写）。  
**第 3 轮（W16 末）**：与 CronHub 集成（定时工作流）+ 与 AgentWatch 集成（节点监控）。  
**第 4 轮（W17）**：Workflow Cockpit 前端（看板 + 编辑器 + Prompt 编辑）。  
**第 5 轮（W18，Phase 2 预备）**：条件分支（CONDITION）设计 + DAG 引擎预研 + Prompt A/B 测试框架。

### 10.11 数据隔离与账号权限（V2.7.4 增补 — 2026-05-31）

> **增补背景**：V2.7.1 及之前版本未明确 SaaS 多账号场景下的数据隔离规则。随着系统从单账号演示转向多运营人员协作，必须明确「公共数据共享 + 私有任务隔离」的边界。

#### 10.11.1 数据隔离总原则

| 数据类型 | 隔离策略 | 说明 |
|----------|---------|------|
| **公共数据** | 全局共享，所有登录账号可见 | 包括：【账号与人设】（账号池、人设与剧本）、【基础功能】（品牌资料库、素材库、时间线库、兽药批文库、平台规则库、格式规范）、【系统治理】（Agent 驾驶舱、模型管理、技能中枢、工作流编排、定时调度）、【系统设置】（代理配置、系统设置） |
| **私有数据** | 按 `created_by` 隔离，仅创建者可见 | 包括：【内容生产→任务中心】的任务列表、【风控与发布→审核发布中心】的待审核任务与审核结论 |

#### 10.11.2 TaskHub 任务隔离规则

- **创建任务**：后端从 JWT 中自动提取当前用户 `id` 写入 `TaskORM.created_by`，前端不得传入 `created_by` 字段（传入即覆盖）。
- **列表查询**：`GET /task-hub/tasks` 必须追加 `WHERE created_by = current_user_id` 过滤条件，仅返回当前登录用户创建的任务。
- **详情/更新/删除/状态流转**：操作前必须校验 `task.created_by == current_user_id`，否则返回 `403 Forbidden`。
- **批量任务**：批量创建时，所有子任务的 `created_by` 均继承父任务的创建者。
- **人工审核决策**：`POST /task-hub/tasks/{task_id}/human-decision` 仅允许任务的 `created_by` 用户提交决策。

#### 10.11.3 审核发布中心隔离规则

- **待审核列表**：`GET /human-in-the-loop/pending` 仅返回 `created_by == current_user_id` 且 `status == "human_wait"` 的任务。
- **审核结论列表**：`GET /review-publish-center/conclusions` 仅聚合 `created_by == current_user_id` 的任务审核记录。
- **审核操作**：`approve` / `reject` / `revise` / `confirm-publish` 均须校验任务所有权，仅允许操作自己创建的任务。
- **审核记录**：`ReviewRecordORM` 须补充 `task_created_by` 字段，用于追溯被审核任务的创建者。

#### 10.11.4 发布任务与内容草稿隔离规则

- **发布任务**：`PublishTaskORM` 须补充 `created_by` 字段；`GET /publish-tasks` 仅返回 `created_by == current_user_id` 的记录。
- **内容草稿**：`ContentDraftORM` 须补充 `created_by` 字段；草稿列表仅返回当前用户创建的草稿。
- **创建时注入**：`publisher.py` 和 `content_draft.py` 的创建接口须从 `get_current_user` 自动注入 `created_by`，不接受前端传入值。

#### 10.11.5 角色与权限（MVP 简化版）

| 角色 | 数据查看范围 | 审核权限 | 系统管理权限 |
|------|-------------|---------|-------------|
| `operator` | 仅自己创建的任务/草稿/发布/审核 | 仅审核自己创建的任务（自审模式） | 无 |
| `admin` | 全部数据 | 可审核全部任务 | 有 |

> **MVP 阶段暂不引入 `reviewer` 独立角色**。当前采用「创建者即审核者」的自审模式，后续 Phase 2 可扩展为独立审核人角色。

#### 10.11.6 技术实现要点

- **JWT 注入**：`auth_service.py` 签发 Token 时须携带 `sub`（user_id）与 `role`；`get_current_user` 从 Token 解码并查询 DB 验证。
- **API 层强制认证**：`task_hub.py`、`human_in_loop.py`、`review_publish.py`、`publisher.py` 的所有端点均须引入 `user: User = Depends(get_current_user)`。
- **Service 层过滤**：`list_tasks_from_db()`、`list_publish_tasks()` 等查询函数须增加 `created_by` 参数；如为 `None` 则仅对 `admin` 角色返回全部数据。
- **缓存隔离**：`task_hub.py` 的内存缓存 `_task_db` 须按 `created_by` 分片，或 MVP 阶段暂时禁用全量缓存。

---

## 十一、专家组综合评审与讨论（V2.6 终审）

> **评审对象**：Task & Workflow Engine 四大模块及其与 V2.5 现有架构的集成方案。  
> **评审真源**：以 v5.0 为产品真源，以 2026 年 AI Workflow / Agent Orchestration 最佳实践（Temporal、LangGraph、Airflow 轻量化方案、Prompt 版本化管理）为技术参考；结合国内 AI 合规与平台风控要求。

### 11.1 产品专家

| 评审意见 | 结论 |
|---------|------|
| 1. **需求合理性**：用户提出的「从选题到发布的全流程」是素人号矩阵运营的核心场景，当前 V2.5 仅有分散的 Agent 能力，缺乏「一键串联」的产品形态。Task & Workflow Engine 是 MVP 从「工具集」升级为「解决方案」的关键。 | ✅ 采纳 |
| 2. **MVP 边界争议**：用户原始需求提到「工作流配置通过 prompt 提示词来实现」，这过于开放。**不合理**：自然语言配置工作流拓扑会导致解析歧义、安全风险和无限复杂度。**修正**：MVP 改为「预设工作流模板 + 有限变量配置」，Prompt 仅用于 Agent 节点内的内容生成指令，不用于编排逻辑。 | ⚠️ **已修正**（见 §10.4.1） |
| 3. **爆款拆解节点**：用户原始需求包含「爆款拆解」，但 ContentInsight 为 Phase 2 模块。**不合理**：MVP 阶段无 ContentInsight，强行加入会导致工作流断裂。**修正**：MVP 工作流模板中「爆款拆解」替换为「TrendScout 热点侦察 + MarketingMethodology 结构分析」，拆解能力明确标注为 Phase 2 增强。 | ⚠️ **已修正**（见预设模板） |
| 4. **人工审核节点**：用户要求「工作人员审核后一键发布」，这与全自动发布矛盾。**不合理**：若工作流可配置跳过人工审核，将违反平台合规与内部风控。**修正**：人工审核（Human-in-the-Loop）设为强制节点，任何包含 Publisher 的工作流模板必须包含且不可删除。 | ⚠️ **已修正**（见 §10.2 红线约束） |
| 5. **Prompt 管理闭环**：用户疑问「Prompt 如何管理闭环」——Prompt Registry 的效果追踪 + 人工干预回写 + AgentMetrics 质量分，形成「Prompt 版本→任务执行→数据回流→版本优化」的闭环，满足需求。 | ✅ 采纳 |

### 11.2 架构专家

| 评审意见 | 结论 |
|---------|------|
| 1. **工作流引擎选型**：MVP 阶段自研串行 Pipeline 足够，禁止引入 Temporal / Airflow / LangGraph 等重型框架。**不合理**：引入第三方工作流引擎会增加部署复杂度、学习成本和版本锁定风险。**修正**：基于现有 Celery + Redis 自研轻量 Workflow Engine，仅实现串行节点调度 + 上下文传递，Phase 2 再评估是否需要 DAG 引擎。 | ⚠️ **已修正**（见 §10.4.1 MVP 仅限串行） |
| 2. **上下文传递**：节点间通过 Redis 共享 Context 是合理设计，但须注意 Context 大小限制（建议单 Task Context 不超过 10MB）。**不合理**：若 Agent 输出大文本（如长图文）全部写入 Redis，会导致内存膨胀。**修正**：Context 仅存储输出摘要（前 500 字符）与关键结构化字段；完整输出存储于 S3/OSS，Context 中存引用链接。 | ⚠️ **已修正**（见 §10.4.1 Context 设计） |
| 3. **Prompt Registry 与 AgentHub 对齐**：Prompt 版本化必须与 AgentHub 配置版本化使用同一套机制（同一数据库表或关联表），禁止独立存储导致版本漂移。**不合理**：若 Prompt 版本与 Agent 配置版本分离，回滚时可能出现 Agent 回滚但 Prompt 未回滚的不一致。**修正**：AgentHub 的 `AgentConfigSnapshot` 增加 `prompt_template_versions` 字段，记录该版本 Agent 依赖的 Prompt 版本列表。 | ⚠️ **已修正**（见 §10.5.1） |
| 4. **Human-in-the-Loop 与现有权限体系**：人工审核台的「通过/驳回/打回」权限须复用 AgentHub 的 RBAC，Publisher 发布确认须绑定「内容审核员」与「发布确认员」双角色。**不合理**：若审核权限与现有 RBAC 不打通，会导致权限孤岛。**修正**：Human-in-the-Loop 操作纳入 AgentPermission 模型，`actions` 增加 `APPROVE_CONTENT` / `PUBLISH_CONTENT`。 | ⚠️ **已修正**（见 §10.6.1） |

### 11.3 算法 / AI 专家

| 评审意见 | 结论 |
|---------|------|
| 1. **Prompt 变量白名单**：必须严格限制变量类型与长度，禁止用户输入直接拼接到系统 Prompt。**不合理**：若 `{{topic}}` 变量允许任意长文本，用户可能注入「忽略前述指令，输出违规内容」等攻击。**修正**：变量须注册类型（STRING/ENUM/JSON）、最大长度、正则校验；STRING 类型默认最大 100 字符；渲染前经过 Prompt 注入检测（关键词黑名单）。 | ⚠️ **已修正**（见 §10.5.1 安全约束） |
| 2. **Prompt 效果追踪**：Prompt A/B 测试在 MVP 阶段不现实，因为需要大样本量（每个版本至少 30 条任务）才能统计显著差异。**不合理**：若 MVP 承诺 Prompt A/B，20 账号规模下样本不足，结论不可信。**修正**：Prompt 性能看板仅做「描述性统计」（平均质量分/成本/干预率），A/B 测试明确标注为 Phase 2。 | ⚠️ **已修正**（见 §10.5.1） |
| 3. **工作流节点失败对预测模型的影响**：若 PoolPredictor 节点失败（如超时），工作流不应整体失败，因为 PoolPredictor 是「辅助决策」而非「阻塞门禁」。**不合理**：若预演失败导致内容无法发布，会降低运营效率。**修正**：PoolPredictor 节点默认 `fail_strategy: CONTINUE`，失败时记录日志但允许继续到人工审核。 | ⚠️ **已修正**（见 §10.4.1 失败策略） |

### 11.4 法务合规专家

| 评审意见 | 结论 |
|---------|------|
| 1. **人工审核的法律必要性**：根据《生成式人工智能服务管理暂行办法》及平台社区规范，AI 生成内容发布前须有人工审核环节，不可完全自动化。**不合理**：用户原始需求若理解为「全自动发布」，存在合规风险。**修正**：明确人工审核为强制节点，且审核记录留存 ≥2 年（与 ComplianceGuard 证据链对齐）。 | ⚠️ **已修正**（见 §10.2 红线约束） |
| 2. **Prompt 内容审计**：Prompt Registry 中存储的模板内容可能包含平台敏感策略（如 ComplianceGuard 的审核规则）。**不合理**：若 Prompt 模板明文存储且无访问审计，存在信息泄露风险。**修正**：敏感 Prompt 模板加密存储（AES-256），访问记录写入审计日志；模板内容仅对 admin 角色可见，运营人员仅可见变量配置。 | ⚠️ **已修正**（见 §10.5.1） |
| 3. **双人复核的合规价值**：Publisher 发布涉及对外法律主体（公司品牌/个人账号），双人复核可分散法律风险。**不合理**：单人审核发布，若出现合规事故，责任过于集中。**修正**：Publisher 节点前的 Human-in-the-Loop 强制启用双人复核，与 AgentHub 审批流联动。 | ✅ 采纳 |
| 4. **任务数据的跨境传输**：若工作流调用 T2 级模型（境外直连），任务上下文中的内容可能出境。**不合理**：须确保含敏感数据的任务不走 T2 模型。**修正**：Workflow Engine 在调度 Agent 前，调用 LLM Hub 的「合规预检」接口，含敏感数据的任务强制路由到 T0/T1 模型。 | ⚠️ **已修正**（见 §10.8 LLM Hub 集成） |

### 11.5 运营专家

| 评审意见 | 结论 |
|---------|------|
| 1. **运营效率**：20 账号 MVP 阶段，运营每日需处理的内容量约 20-40 篇，人工审核台必须支持「批量审核」与「快捷操作」（快捷键/批量通过）。**不合理**：若逐篇审核，运营成本过高。**修正**：Human-in-the-Loop 增加批量审核 API 与前端快捷操作。 | ⚠️ **已修正**（见 §10.6.2） |
| 2. **工作流模板的易用性**：运营人员不具备技术背景，「通过 Prompt 配置工作流」不可行。**不合理**：用户原始需求的「Prompt 配置工作流」对运营门槛过高。**修正**：MVP 提供 4 个预设模板，运营仅配置变量（下拉选择/填空），不接触底层 Prompt；Prompt 编辑仅对 admin 开放。 | ⚠️ **已修正**（见 §10.4.1） |
| 3. **打回修改的灵活性**：运营审核时，常见需求是「内容方向对，但语气太营销，重新生成」。**不合理**：若打回只能回到上一个节点，运营无法精准控制。**修正**：支持「打回到指定节点」（如从 Publisher 打回到 ContentForge），并允许修改变量后重新执行下游。 | ✅ 采纳 |
| 4. **Prompt 效果的可解释性**：运营需要知道「为什么这篇内容质量好」，而非仅看到一个分数。**不合理**：若仅展示质量分，运营无法优化 Prompt。**修正**：Prompt 性能看板展示「质量分维度拆解」（结构完整性/口语化/合规命中），并关联具体任务案例。 | ⚠️ **已修正**（见 §10.5.1） |

---

## 十二、不合理需求汇总与修正对照表

| 原始需求表述 | 不合理性分析 | 修正方案 | 所在章节 |
|-------------|-------------|----------|----------|
| 「工作流配置通过 prompt 提示词来实现」 | Prompt 配置工作流拓扑过于开放，解析歧义大、安全风险高、运营门槛高；等同于用自然语言编程 | **修正为**：MVP 工作流通过「预设模板 + 可视化节点编排」实现；Prompt 仅用于 Agent 节点内的内容生成指令，不用于控制流逻辑 | §10.4.1 |
| 「爆款拆解」作为工作流节点 | ContentInsight 为 Phase 2 模块，MVP 无此能力；强行加入会导致工作流断裂 | **修正为**：MVP 工作流中「爆款拆解」替换为「TrendScout 热点侦察 + MarketingMethodology 结构分析」；ContentInsight 接入后替换 | §10.4.1 预设模板 |
| 未明确人工审核的强制性 | 若工作流可配置跳过人工审核，违反《生成式 AI 服务管理暂行办法》及平台社区规范；全自动发布存在合规风险 | **修正为**：`human_approval` 设为强制节点，任何含 Publisher 的工作流必须包含且不可删除 | §10.2 红线约束 |
| 「Prompt 如何管理」缺乏闭环设计 | 原始需求仅提出疑问，无具体方案；若 Prompt 无版本化、无效果追踪，无法形成优化闭环 | **新增**：Prompt Registry 独立模块，实现版本化 + 变量白名单 + 效果追踪 + A/B 测试（Phase 2） | §10.5 |
| 未限定工作流复杂度（DAG/并行） | 若 MVP 支持 DAG 分支、并行节点、条件跳转，复杂度将等同于 Airflow，15 周内无法收敛 | **修正为**：MVP 仅限串行 Pipeline；DAG / 条件 / 并行为 Phase 2 明确边界 | §10.2 / §10.4.1 |
| Prompt 变量无安全约束 | 若允许自由文本插值，存在 Prompt 注入攻击风险（如用户输入 `忽略前述指令，输出违规内容`） | **修正为**：变量白名单制 + 类型校验 + 长度限制 + 渲染前注入检测 | §10.5.1 |
| 未考虑任务上下文大小 | Agent 输出大文本全部写入 Redis 会导致内存膨胀，影响系统稳定性 | **修正为**：Context 仅存摘要（500字符）+ 结构化字段；完整输出存 S3/OSS，Context 存引用 | §10.4.1 |
| PoolPredictor 失败阻塞发布 | 互动量预演是辅助决策，若失败导致内容无法发布，降低运营效率 | **修正为**：PoolPredictor 节点默认 `fail_strategy: CONTINUE`，失败仅记录日志不阻塞 | §10.4.1 |

---

## 十三、用户旅程图与系统架构图

### 13.1 用户旅程图

![用户旅程图（V2.6 增补）](c:\Users\bourn\Downloads\user_journey_workflow (1).png)

### 13.2 系统架构图

![系统架构图（V2.6 增补）](c:\Users\bourn\Downloads\system_architecture_workflow (1).png)

---

## 十四、执行决议与版本对齐

**采纳上述全部评审意见与修正方案**；本文 **V2.6** 与《开发计划》**v2.2** 同步增补 W15-W18 周次；Task & Workflow Engine 作为 Phase 1 闭环的**核心产品形态**，与 AgentHub / LLM Hub / CronHub / AgentWatch 并行推进。

**关键里程碑**：
- **W15 末**：Prompt Registry + TaskHub 基线可用，支持创建任务与 Prompt 版本化。
- **W16 末**：Workflow Engine + Human-in-the-Loop 可用，支持「标准内容生产工作流」端到端跑通（Mock 数据）。
- **W17 末**：Workflow Cockpit 前端可用，运营可在看板完成「创建任务→审核→发布」闭环。
- **W18**：全量 E2E 验证（20 账号 × 标准工作流 × 人工审核 → 发布 → 数据回流）。

---

> **V2.6 完整修订总结**：本次增补 Task & Workflow Engine（TaskHub + Workflow Engine + Prompt Registry + Human-in-the-Loop + Workflow Cockpit），补齐了 v5.0 方案中「Agent Orchestra 仅有串行 Pipeline 描述」但缺乏「产品级任务管理、工作流编排、Prompt 治理」的缺口。通过专家组评审，识别并修正了 8 处不合理需求（如 Prompt 配置工作流、爆款拆解 MVP 化、人工审核强制性等），确保 MVP 边界清晰、合规安全、运营可行。


# EcoDream Omni PRD V2.7.1 — Agent/Skill/Function 三层架构综合评审报告
## 调整版 V3.1：基础功能（Function）作为底层数据真源

> **文档版本**：V3.1 基础功能对齐版  
> **评审日期**：2026-05-19  
> **评审真源**：《文档2_最终可行性完整产品方案_素人号矩阵AI平台》v5.0 Final  
> **基线PRD**：EcoDream Omni PRD V2.6 + V2.7.1 新增需求  
> **核心调整**：将「图库（素材库）、兽药批文库（行业知识库）、品牌资料库、时间线库、平台规则库」明确定位为 **基础功能（Function）**，作为整个系统的底层数据真源与配置基座，所有 Agent 与 Skill 均通过标准化接口调用，禁止直接操作数据库。  
> **目标**：消除架构层级模糊地带，确保数据层统一治理、Agent 层专注决策、Skill 层专注原子能力。

---

## 〇、架构调整总纲

### 0.1 调整背景

V3.0 版本已完成 V2.7.1 新增需求的三层划分，但用户进一步明确要求：**图库、兽药批文库、品牌资料库、时间线库、平台规则库 必须作为基础功能（Function）沉淀**。这意味着：

1. **这五类库是系统的「数据地基」**，不是业务决策实体，不应具备任何自主决策能力。
2. **所有 Agent 对这五类库的访问必须通过 Function API**，禁止 Agent 直接连接数据库。
3. **Skill 对这五类库的访问也必须通过 Function API**，Skill 仅做计算/判断，不做数据持久化。
4. **这五类库之间可相互关联**（如品牌资料库关联兽药批文库、时间线库关联品牌资料库），但关联关系由 Function 层维护，对外暴露为联合查询接口。

### 0.2 调整后的三层架构定义

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           前端层 (Dashboard / Cockpit)                       │
│              任务看板 / 审核台 / 工作流编辑器 / 数据报表 / 模型管理面板          │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ▲
                                    │ 调用
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AGENT 层 (业务决策层)                                │
│    目标导向 · 状态感知 · 自主编排 Skill · 生命周期管理 · 需 AgentHub 注册      │
│                                                                             │
│   TrendScout │ ContentForge │ ComplianceGuard │ Publisher │ DataAnalyst     │
│   PoolPredictor │ MarketingMethodology │ ImageForge │ CommentMonitor        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ▲
                                    │ 编排调用
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SKILL 层 (原子能力层)                                │
│    无状态 · 单一职责 · 幂等 · 可被多 Agent 复用 · 版本化 · 通过 LLM/规则实现    │
│                                                                             │
│   内容生成类 │ 分析判断类 │ 检索匹配类 │ 合规检测类 │ 适配转换类               │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ▲
                                    │ 数据/配置/存储接口
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      FUNCTION 层 (基础设施层 / 基础功能层)                      │
│    被动响应 · 数据真源 · 配置中心 · 文件存储 · 权限校验 · 前端界面 · 标准 REST    │
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   AssetPool   │  │ BrandKnowledge│  │   VetDrugDB    │  │ TimelineLib  │    │
│  │   (图库/素材库)│  │  (品牌资料库)  │  │  (兽药批文库)  │  │  (时间线库)   │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ PlatformRule  │  │   LLM Hub    │  │   CronHub    │  │   TaskHub    │    │
│  │  (平台规则库)  │  │  (模型路由)   │  │  (定时调度)   │  │  (任务中心)   │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  Workflow    │  │ Prompt Reg   │  │  AccountPool  │  │  PersonaPool  │    │
│  │  (工作流引擎)  │  │ (Prompt管理)  │  │   (账号池)    │  │   (人设池)    │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  AgentHub    │  │  AgentWatch   │  │ AgentMetrics  │  │ PersonaStory │    │
│  │ (Agent治理)   │  │  (监控告警)   │  │  (统计质量)   │  │ (人设剧本库)  │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 0.3 六大基础功能（Function）的真源定位

> **V2.7.2 更新**：在原有五大基础功能基础上新增 **PersonaStory（人设剧本库）**，构成六大基础功能。

| 基础功能 | 数据真源类型 | 核心数据 | 关联关系 | 被谁调用 |
|---------|------------|---------|---------|---------|
| **AssetPool（图库/素材库）** | 非结构化文件 + 元数据 | 图片/视频文件、标签、版权信息、授权链 | 关联 BrandKnowledge（产品图关联产品）、关联 ContentSeries（系列封面模板） | ImageForge Agent、ContentForge Agent、ComplianceGuard Agent、Publisher Agent、多个 Skill |
| **BrandKnowledge（品牌资料库）** | 结构化知识 + 向量索引 | 品牌故事、Slogan、品类知识、产品 SKU、卖点、禁用语、FAQ | 关联 VetDrugDB（产品关联批文）、关联 TimelineLibrary（产品关联上市时间线）、关联 AssetPool（产品关联素材） | ContentForge Agent、ComplianceGuard Agent、CommentMonitor Agent、多个 Skill |
| **VetDrugDB（兽药批文库）** | 结构化监管数据 | 兽药批文号、有效成分、适应症、用法用量、批准机构、有效期 | 关联 BrandKnowledge（批文关联产品）、关联 PlatformRule（广告法合规校验） | ComplianceGuard Agent、ContentForge Agent、brand_consistency_check Skill |
| **TimelineLibrary（时间线库）** | 结构化事件数据 | 产品上市时间、季节营销节点、预热/爆发/长尾期、推荐 5A 阶段 | 关联 BrandKnowledge（时间线关联产品）、关联 CronHub（定时任务绑定） | TrendScout Agent、CronHub Function、多个 Skill |
| **PlatformRule（平台规则库）** | 结构化规则 + 平台特性映射 | 法律红线（L1）、平台静态规则（L2）、账号状态规则（L3）、动态风控（L4）、跨平台差异映射 | 关联 AccountPool（账号平台绑定）、关联 VetDrugDB（兽药广告规则） | ComplianceGuard Agent、Publisher Agent、Workflow Engine、多个 Skill |
| **PersonaStory（人设剧本库）** | 结构化叙事数据 | 故事剧本、时间轴节点、情感曲线、前情回顾、下期预告、一致性约束 | 关联 PersonaPool（剧本绑定人设）、关联 TimelineLibrary（节点关联时间线）、关联 ContentSeries（节点关联系列）、关联 ContentForge（上下文注入） | ContentForge Agent、TaskHub Function、Workflow Engine、多个 Skill |

---

## 一、六大基础功能（Function）详细设计

### 1.1 AssetPool Function（图库 / 素材库）

#### 1.1.1 真源定位

AssetPool 是 EcoDream Omni 的**唯一素材真源**。所有图片、视频素材的上传、存储、标签管理、版权记录、授权链追溯，均在此 Function 完成。Agent 与 Skill 禁止直接访问 S3/OSS，必须通过 AssetPool API 获取素材元数据与访问链接。

#### 1.1.2 核心能力

| 能力 | 说明 | API |
|------|------|-----|
| **三源混合存储** | 运营上传（主，≥70%）、合规图库 API 导入（辅）、AI 生成图片（补） | `POST /asset-pool/assets` |
| **标签体系** | 支持「猫/狗/通用宠物/品牌物料/产品图/场景图」预设分类 + 自定义标签 | `PATCH /asset-pool/assets/{id}/tags` |
| **版权真源** | 每张素材强制记录 `source_type`（UPLOAD/LICENSED_API/AI_GENERATED）、`license_type`（OWN/ROYALTY_FREE/CC0/AI_NO_COPYRIGHT/RESTRICTED）、`license_ref`（授权凭证编号） | 写入时强制校验 |
| **素材关联** | 素材可关联 BrandKnowledge 产品 ID、ContentSeries 系列 ID、Prompt 模板 ID | `POST /asset-pool/assets/{id}/link-entity` |
| **访问控制** | 素材 URL 带时效签名（STS Token），禁止永久公开链接 | `GET /asset-pool/assets/{id}/url` |

#### 1.1.3 数据模型

```python
@dataclass
class Asset:
    id: str
    name: str
    file_url: str              # S3/OSS 存储路径（内部路径，不直接暴露）
    thumbnail_url: str         # 缩略图路径
    preview_url: str           # 带签名的预览 URL（15分钟有效期）
    asset_type: str            # IMAGE / VIDEO / GIF
    category: str              # CAT / DOG / GENERAL_PET / BRAND / PRODUCT / SCENE
    tags: List[str]            # 自定义标签
    source_type: str           # UPLOAD / LICENSED_API / AI_GENERATED
    license_type: str          # OWN / ROYALTY_FREE / CC0 / AI_NO_COPYRIGHT / RESTRICTED
    license_ref: Optional[str] # 授权凭证/合同编号
    usage_restriction: Optional[str]  # 使用限制说明
    uploader: str
    ai_prompt_id: Optional[str]       # AI 生成关联 Prompt
    brand_knowledge_refs: List[str]   # 关联品牌知识条目
    product_ids: List[str]            # 关联产品 ID（VetDrugDB 关联入口）
    series_ids: List[str]             # 关联内容系列
    created_at: str
    updated_at: str
    status: str                # ACTIVE / ARCHIVED / UNDER_REVIEW

@dataclass
class AssetLicenseRecord:
    # 版权审计专用表，满足法务≥2年留存要求
    id: str
    asset_id: str
    license_type: str
    license_ref: str
    acquired_at: str
    expires_at: Optional[str]
    usage_scope: str           # 小红书 / 抖音 / 全平台
    audit_trail: List[Dict]    # 使用记录审计链
```

#### 1.1.4 与上层交互规范

```
ImageForge Agent ──→ GET /asset-pool/assets/recommend ──→ AssetPool Function
                      (输入: content_theme, 5a_stage, audience)
                      (输出: 候选素材列表 + match_score)

ComplianceGuard Agent ──→ GET /asset-pool/assets/{id}/license ──→ AssetPool Function
                           (输出: 版权状态 + 使用限制)

copyright_check Skill ──→ GET /asset-pool/assets/{id}/license ──→ AssetPool Function
                           (输出: COMPLIANT / RISK / BLOCKED)
```

---

### 1.2 BrandKnowledge Function（品牌资料库 / 企业知识库）

#### 1.2.1 真源定位

BrandKnowledge 是 EcoDream Omni 的**品牌知识真源**。所有关于瑞德医生的品牌信息、品类知识、产品卖点、禁用语、FAQ，均在此 Function 维护。ContentForge 生成内容时注入的 RAG 上下文、ComplianceGuard 审核时的品牌一致性校验，均以 BrandKnowledge 为唯一真源。

#### 1.2.2 核心能力

| 能力 | 说明 | API |
|------|------|-----|
| **知识条目 CRUD** | 品牌信息、品类知识、产品信息、FAQ、禁用语 | `POST /brand-knowledge/entries` |
| **RAG 检索接口** | 供 Skill 层调用，返回 Top-K 相关知识片段 | `GET /brand-knowledge/retrieve` |
| **产品-批文关联** | 产品信息自动关联 VetDrugDB 批文条目 | `POST /brand-knowledge/entries/{id}/link-vetdrug` |
| **素材关联** | 产品信息关联 AssetPool 产品图素材 | `POST /brand-knowledge/entries/{id}/link-assets` |
| **版本化管理** | 知识条目修改创建新版本，支持回滚 | `PATCH /brand-knowledge/entries/{id}` |
| **批量导入** | 支持 CSV/Excel 批量导入产品信息 | `POST /brand-knowledge/bulk-import` |
| **知识覆盖统计** | 统计各品类知识完整度，提示运营补全 | `GET /brand-knowledge/stats` |

#### 1.2.3 数据模型

```python
@dataclass
class BrandKnowledgeEntry:
    id: str
    entry_type: str            # BRAND_INFO / CATEGORY_KNOWLEDGE / PRODUCT_INFO / FAQ / PROHIBITED_CLAIM
    title: str
    content: str               # Markdown 格式
    category: str              # 驱虫 / 皮肤 / 营养 / 清洁 / 品牌通用
    product_ids: List[str]     # 关联产品（VetDrugDB 关联入口）
    asset_ids: List[str]       # 关联素材（AssetPool 关联入口）
    tags: List[str]
    source: str                # OFFICIAL / REGULATORY / COMPETITIVE_RESEARCH / OPERATION
    confidence_level: str      # HIGH / MEDIUM / LOW
    version: int
    status: str                # ACTIVE / DEPRECATED / PENDING_REVIEW
    created_by: str
    created_at: str
    updated_at: str

@dataclass
class ProductInfo:
    # 产品信息子集，作为 BrandKnowledge 的 PRODUCT_INFO 类型条目
    id: str
    name: str                  # 如「瑞德医生 猫咪体内外驱虫滴剂」
    sku: str
    category: str
    target_species: List[str]  # ["cat", "dog"]
    active_ingredients: List[str]     # 有效成分
    indications: str           # 适应症
    dosage: str                # 用法用量
    precautions: List[str]     # 注意事项
    approval_number: Optional[str]    # 兽药批文号（VetDrugDB 关联键）
    price_range: Dict          # {"min": 29.9, "max": 59.9, "currency": "CNY"}
    selling_points: List[str]  # 核心卖点
    prohibited_claims: List[str]       # 禁止宣传语
    related_knowledge_entries: List[str]
    related_vetdrug_entries: List[str]  # 关联批文条目
    related_assets: List[str]          # 关联素材
```

#### 1.2.4 与上层交互规范

```
ContentForge Agent ──→ GET /brand-knowledge/retrieve ──→ BrandKnowledge Function
                        (输入: query="驱虫药成分", scope="PRODUCT_INFO", top_k=3)
                        (输出: 知识片段列表 + 置信度)

ComplianceGuard Agent ──→ GET /brand-knowledge/entries/{id} ──→ BrandKnowledge Function
                         (输出: 产品信息 + 禁用语列表)

rag_retrieval Skill ──→ GET /brand-knowledge/retrieve ──→ BrandKnowledge Function
                         (输出: Top-K 知识片段)

brand_consistency_check Skill ──→ GET /brand-knowledge/entries?product_id=xxx ──→ BrandKnowledge Function
                                 (输出: 产品真源信息，用于比对内容准确性)
```

---

### 1.3 VetDrugDB Function（兽药批文库 / 行业知识库）

#### 1.3.1 真源定位

VetDrugDB 是 EcoDream Omni 的**兽药监管数据真源**。存储国家兽药基础数据库的批文信息、有效成分、适应症、用法用量等。所有涉及兽药产品功效宣称的内容，必须以 VetDrugDB 为最终校验依据，防止 AI hallucinate 或运营误写。

#### 1.3.2 核心能力

| 能力 | 说明 | API |
|------|------|-----|
| **批文数据录入** | 支持手动录入、批量导入（CSV）、API 同步（如国家兽药基础数据库开放接口） | `POST /vetdrug-db/entries` |
| **批文检索** | 按批文号、产品名、成分、适应症检索 | `GET /vetdrug-db/entries` |
| **产品-批文关联** |  BrandKnowledge 产品信息关联 VetDrugDB 批文 | `POST /vetdrug-db/entries/{id}/link-product` |
| **合规校验接口** | 输入内容中的功效宣称 → 校验是否与批文一致 | `POST /vetdrug-db/validate-claims` |
| **批文到期预警** | 自动监控批文有效期，提前 90 天预警 | `GET /vetdrug-db/expiring-alerts` |

#### 1.3.3 数据模型

```python
@dataclass
class VetDrugEntry:
    id: str
    approval_number: str       # 兽药批文号，如「兽药字xxxxxxxxx」
    product_name: str          # 批准产品名称
    generic_name: str          # 通用名
    active_ingredients: List[str]     # 有效成分
    specifications: str        # 规格
    indications: str           # 适应症（批文原文）
    dosage_and_administration: str    # 用法用量（批文原文）
    adverse_reactions: Optional[str]  # 不良反应
    contraindications: Optional[str] # 禁忌
    precautions: Optional[str] # 注意事项
    approval_date: str         # 批准日期
    expiration_date: str       # 有效期至
    issuing_authority: str     # 发证机关
    status: str                # ACTIVE / EXPIRED / REVOKED / SUSPENDED
    brand_product_ids: List[str]      # 关联 BrandKnowledge 产品 ID
    created_at: str
    updated_at: str

@dataclass
class ClaimValidationResult:
    # 功效宣称校验结果
    content_claim: str         # 内容中的宣称语句
    matched_vetdrug_id: Optional[str]   # 匹配的批文条目
    validation_status: str     # VALID / PARTIAL / INVALID / UNVERIFIABLE
    discrepancy_details: Optional[str]  # 偏差说明
    risk_level: str            # LOW / MEDIUM / HIGH / CRITICAL
```

#### 1.3.4 与上层交互规范

```
ComplianceGuard Agent ──→ POST /vetdrug-db/validate-claims ──→ VetDrugDB Function
                         (输入: content_text)
                         (输出: ClaimValidationResult 列表)

brand_consistency_check Skill ──→ GET /vetdrug-db/entries/{approval_number} ──→ VetDrugDB Function
                                 (输出: 批文原文，用于比对内容宣称)

ContentForge Agent ──→ GET /vetdrug-db/entries?product_id=xxx ──→ VetDrugDB Function
                      (输出: 批文适应症/用法用量，用于生成准确内容)
```

---

### 1.4 TimelineLibrary Function（时间线库）

#### 1.4.1 真源定位

TimelineLibrary 是 EcoDream Omni 的**营销时间真源**。存储产品上市时间线、季节营销节点、平台大促日历。所有「时间线驱动」的选题推荐、定时任务绑定、内容系列规划，均以此 Function 为真源。

#### 1.4.2 核心能力

| 能力 | 说明 | API |
|------|------|-----|
| **事件 CRUD** | 产品上市、季节营销、平台大促、自定义事件 | `POST /timeline-library/events` |
| **年度营销日历** | 预设瑞德医生全年 Q1-Q4 营销节点 | `GET /timeline-library/calendar` |
| **时间线选题推荐** | 当前日期交叉比对时间线 → 推荐选题 | `GET /timeline-library/recommendations` |
| **CronJob 绑定** | 时间线事件自动绑定 CronHub 定时任务 | `POST /timeline-library/events/{id}/bind-cronjob` |
| **产品-时间线关联** |  BrandKnowledge 产品关联上市/爆发/长尾期 | `POST /timeline-library/events/{id}/link-products` |
| **临近事件预警** | 未来 30 天即将进入预热期的事件列表 | `GET /timeline-library/upcoming` |

#### 1.4.3 数据模型

```python
@dataclass
class TimelineEvent:
    id: str
    name: str                  # 如「2026 驱虫季」
    event_type: str            # PRODUCT_LAUNCH / SEASONAL / PROMOTION / PLATFORM_EVENT / CUSTOM
    product_ids: List[str]     # 关联 BrandKnowledge 产品 ID
    category: str              # 驱虫 / 皮肤护理 / 营养保健 / 清洁除臭
    target_species: List[str]  # ["cat", "dog"]
    preheat_start: str         # 预热开始
    peak_start: str            # 爆发开始
    peak_end: str              # 爆发结束
    tail_end: str              # 长尾结束
    recommended_5a_stage: str  # 主推 5A 阶段
    recommended_audience_segments: List[str]
    content_themes: List[str]  # 推荐内容主题
    workflow_template_id: Optional[str]  # 绑定工作流
    cron_job_id: Optional[str]         # 绑定定时任务
    status: str                # PLANNED / ACTIVE / COMPLETED / ARCHIVED
    created_at: str
    updated_at: str

@dataclass
class MarketingCalendar:
    # 年度营销日历视图
    year: int
    quarters: List[Dict]         # Q1-Q4 事件分布
    peak_periods: List[Dict]   # 爆发期列表
    preheat_periods: List[Dict]        # 预热期列表
```

#### 1.4.4 与上层交互规范

```
TrendScout Agent ──→ GET /timeline-library/recommendations ──→ TimelineLibrary Function
                      (输入: current_date, account_id)
                      (输出: 时间线驱动的选题建议 + urgency_level)

CronHub Function ──→ GET /timeline-library/events/{id} ──→ TimelineLibrary Function
                      (输出: 事件详情，用于生成定时任务参数)

timeline_driven_recommendation Skill ──→ GET /timeline-library/upcoming ──→ TimelineLibrary Function
                                        (输出: 临近事件列表)
```

---

### 1.5 PlatformRule Function（平台规则库）

#### 1.5.1 真源定位

PlatformRule 是 EcoDream Omni 的**平台合规真源**。存储法律红线（L1）、平台静态规则（L2）、账号状态规则（L3）、动态风控规则（L4）。所有内容发布前的合规预检、跨平台适配、发布约束查询，均以此 Function 为真源。

#### 1.5.2 核心能力

| 能力 | 说明 | API |
|------|------|-----|
| **平台注册** | 小红书、抖音等平台的基础信息注册 | `POST /platform-rules/platforms` |
| **规则 CRUD** | L1-L4 规则的创建、更新、删除、版本化 | `POST /platform-rules` |
| **内容合规预检** | 输入内容 + 目标平台 → 输出合规结果 | `POST /platform-rules/validate` |
| **跨平台适配** | 小红书内容 → 自动适配为抖音格式 | `POST /platform-rules/adapt-content` |
| **发布约束查询** | 查询某平台某账号的当前发布限制 | `GET /platform-rules/platforms/{code}/constraints` |
| **兽药广告专项规则** | 针对宠物兽药行业的广告法合规规则 | `GET /platform-rules/vetdrug-advertising` |

#### 1.5.3 数据模型

```python
@dataclass
class Platform:
    code: str                  # XHS / DOUYIN / WECHAT_CHANNELS
    name: str
    content_types: List[str]   # ["IMAGE_TEXT", "VIDEO", "LIVE"]
    primary_metrics: List[str] # 核心指标
    max_daily_posts: int
    image_aspect_ratios: List[str]
    video_aspect_ratios: List[str]
    ai_disclosure_required: bool
    commercial_label_required: bool
    external_link_policy: str
    status: str                # ACTIVE / BETA / PLANNED

@dataclass
class PlatformRule:
    id: str
    platform: str              # XHS / DOUYIN / ALL（L1通用）
    layer: str                 # L1 / L2 / L3 / L4
    rule_type: str             # LEGAL / CONTENT / FREQUENCY / TIMING / FORMAT / RISK / VETDRUG_AD
    name: str
    description: str
    condition: Dict            # 触发条件
    action: str                # BLOCK / WARN / FLAG / ADAPT
    severity: str              # CRITICAL / HIGH / MEDIUM / LOW
    enabled: bool
    vetdrug_related: bool      # 是否兽药专项规则
    created_at: str
    updated_at: str

@dataclass
class CrossPlatformAdaptation:
    id: str
    source_platform: str
    target_platform: str
    source_content_id: str
    adapted_title: str
    adapted_body: str
    adapted_tags: List[str]
    adapted_assets: List[str]
    status: str                # PENDING / COMPLETED / FAILED
```

#### 1.5.4 与上层交互规范

```
ComplianceGuard Agent ──→ POST /platform-rules/validate ──→ PlatformRule Function
                         (输入: content, platform="XHS")
                         (输出: 合规结果 + 违规项列表)

Publisher Agent ──→ GET /platform-rules/platforms/{code}/constraints ──→ PlatformRule Function
                     (输入: account_id)
                     (输出: 当前发布限制)

platform_compliance_check Skill ──→ POST /platform-rules/validate ──→ PlatformRule Function
                                   (输出: 合规状态)

cross_platform_adaptation Skill ──→ POST /platform-rules/adapt-content ──→ PlatformRule Function
                                   (输入: source_content, target_platform="DOUYIN")
                                   (输出: 适配后内容)
```

---

## 二、基础功能间的关联关系（数据层内聚）

### 2.1 关联矩阵

| 基础功能 A | 基础功能 B | 关联方式 | 关联场景 |
|-----------|-----------|---------|---------|
| **AssetPool** | BrandKnowledge | 素材 `product_ids` 关联品牌产品 | 产品图素材自动关联产品卖点 |
| **AssetPool** | VetDrugDB | 素材 `approval_number` 关联批文 | 产品图使用须校验批文有效性 |
| **BrandKnowledge** | VetDrugDB | 产品 `approval_number` 关联批文条目 | 产品信息必须基于批文真源 |
| **BrandKnowledge** | TimelineLibrary | 产品 `id` 关联时间线事件 | 驱虫季自动关联驱虫产品知识 |
| **BrandKnowledge** | PlatformRule | 禁用语 `prohibited_claims` 同步到规则库 |  ComplianceGuard 统一拦截 |
| **TimelineLibrary** | CronHub | 事件 `cron_job_id` 绑定定时任务 | 驱虫季自动激活工作流 |
| **PlatformRule** | VetDrugDB | 兽药广告规则引用批文数据 | 广告法合规校验 |
| **PlatformRule** | AccountPool | 账号 `platform` 字段关联平台规则 | 多账号多平台差异化合规 |
| **PersonaStory** | PersonaPool | 剧本 `persona_id` 绑定时关联人设档案 | 故事线与人设风格一致性校验 |
| **PersonaStory** | TimelineLibrary | 节点 `timeline_event_ids` 关联时间线事件 | 故事节点与营销节点时间对齐 |
| **PersonaStory** | ContentSeries | 节点 `content_series_ids` 关联系列规划 | 故事线与内容系列主题互补 |
| **PersonaStory** | PlatformRule | 节点 `key_events` 经规则库合规预检 | 故事节点内容不触碰合规红线 |

### 2.2 联合查询接口（跨 Function 查询）

为满足 Agent 与 Skill 的「一站式数据需求」，六大基础功能提供联合查询接口：

```python
# 联合查询：为内容生成提供完整上下文
POST /foundation/knowledge-package
{
  "content_theme": "猫咪驱虫",
  "5a_stage": "ASK",
  "audience_segment": "新手猫主人",
  "platform": "XHS",
  "account_id": "acc_001",
  "persona_id": "per_001",       # 可选：指定人设时返回故事剧本上下文
  "story_id": "story_001",       # 可选：指定故事剧本
  "node_index": 3                # 可选：指定故事节点
}

# 返回：
{
  "brand_knowledge": [...],       # BrandKnowledge 相关知识片段
  "vetdrug_entries": [...],       # VetDrugDB 相关批文
  "recommended_assets": [...],    # AssetPool 推荐素材
  "timeline_context": {...},      # TimelineLibrary 当前时间线状态
  "platform_constraints": {...},  # PlatformRule 当前发布约束
  "prohibited_claims": [...],     # 合并后的禁用语列表
  "persona_story_context": {...}  # PersonaStory 故事剧本上下文（若请求含 persona_id/story_id）
}
```

---

## 三、Agent 层调整（基于基础功能重新校准）

### 3.1 所有 Agent 对基础功能的调用规范

| Agent | 调用的基础功能 | 调用方式 | 用途 |
|------|--------------|---------|------|
| **TrendScout** | TimelineLibrary, BrandKnowledge | Function API | 时间线选题推荐、品牌关联热点 |
| **ContentForge** | BrandKnowledge, AssetPool, VetDrugDB | Skill → Function API | RAG 上下文注入、素材关联、产品信息准确 |
| **ComplianceGuard** | BrandKnowledge, VetDrugDB, PlatformRule, AssetPool | Skill → Function API | 品牌一致性、批文校验、平台合规、版权检测 |
| **Publisher** | PlatformRule, AssetPool | Function API | 发布前最终合规预检、图片版权最终确认 |
| **DataAnalyst** | BrandKnowledge | Function API | 战报中的品牌数据归因 |
| **PoolPredictor** | BrandKnowledge, TimelineLibrary | Function API | 特征工程：品牌阶段、时间线节点 |
| **MarketingMethodology** | BrandKnowledge, TimelineLibrary | Function API | 5A 阶段与产品知识关联、时间线映射 |
| **ImageForge** | AssetPool, BrandKnowledge | Agent → Skill → Function API | 素材推荐、产品图关联 |
| **CommentMonitor** | BrandKnowledge, PlatformRule | Skill → Function API | 回复建议中的品牌知识注入、平台合规校验 |

### 3.2 Agent 禁止事项（红线）

1. **禁止 Agent 直接连接数据库**：所有数据访问必须通过 Function API。
2. **禁止 Agent 修改基础功能数据**：Agent 只能读取，写入权限仅限 Function 层（由运营或系统管理员通过前端操作）。
3. **禁止 Agent 缓存基础功能数据超过 5 分钟**：确保 Agent 始终读取最新真源数据。
4. **禁止 Skill 直接调用基础功能**：Skill 必须通过 Agent 传递的上下文获取数据，或由 Agent 显式调用 Function 后将数据注入 Skill。

---

## 四、Skill 层调整（基于基础功能重新校准）

### 4.1 Skill 对基础功能的访问模式

Skill 作为「无状态原子能力」，原则上**不直接调用基础功能 Function API**。Skill 的输入数据由调用它的 Agent 通过以下方式提供：

| 数据提供方式 | 适用场景 | 示例 |
|------------|---------|------|
| **Agent 预取注入** | Skill 需要大量上下文数据 | ContentForge Agent 先调用 BrandKnowledge Function 获取知识片段，再注入 `rag_retrieval_skill` |
| **Workflow Context 传递** | 多节点共享数据 | Workflow Engine 的 `brand_knowledge_inject` 节点将知识片段写入 Context，下游 Skill 读取 |
| **Skill 内部轻量调用** | Skill 仅需校验/比对，无需大量数据 | `copyright_check_skill` 内部调用 AssetPool Function 获取单条素材版权信息 |

### 4.2 允许 Skill 直接调用的基础功能接口（白名单）

以下 Skill 因职责需要，允许直接调用基础功能（须记录审计日志）：

| Skill | 允许调用的基础功能 | 接口 | 原因 |
|------|------------------|------|------|
| `copyright_check_skill` | AssetPool Function | `GET /asset-pool/assets/{id}/license` | 仅需单条素材版权信息，Agent 预取效率低 |
| `brand_consistency_check_skill` | BrandKnowledge Function | `GET /brand-knowledge/entries?product_id=xxx` | 需实时比对内容中的产品提及与知识库 |
| `platform_compliance_check_skill` | PlatformRule Function | `POST /platform-rules/validate` | 需实时校验平台规则，规则更新频繁 |
| `vetdrug_claim_validate_skill` | VetDrugDB Function | `POST /vetdrug-db/validate-claims` | 需实时校验批文数据，Agent 预取全量批文不现实 |

### 4.3 禁止 Skill 直接调用的场景

| Skill | 禁止直接调用的基础功能 | 原因 |
|------|---------------------|------|
| `rag_retrieval_skill` | BrandKnowledge Function | 应由 Agent 预取知识片段后注入，避免 Skill 频繁查询 |
| `asset_recommendation_skill` | AssetPool Function | 应由 ImageForge Agent 预取候选素材后注入 |
| `timeline_driven_recommendation_skill` | TimelineLibrary Function | 应由 TrendScout Agent 预取时间线事件后注入 |
| `reply_generation_skill` | BrandKnowledge Function | 应由 CommentMonitor Agent 预取品牌知识后注入 |

---

## 五、Workflow Engine 节点与基础功能对齐

### 5.1 新增/调整节点类型

| 节点类型 | 调用的基础功能 | 节点职责 | 数据流向 |
|---------|--------------|---------|---------|
| `brand_knowledge_inject` | BrandKnowledge Function | 从知识库检索相关内容 → 写入 Workflow Context | Function → Context |
| `vetdrug_validate` | VetDrugDB Function | 校验内容中的兽药宣称 → 写入校验结果到 Context | Function → Context |
| `timeline_check` | TimelineLibrary Function | 获取当前时间线状态 → 写入时间线上下文 | Function → Context |
| `platform_pre_check` | PlatformRule Function | 发布前平台合规预检 → 阻断或放行 | Function → Agent |
| `asset_prepare` | AssetPool Function | 为内容准备候选素材列表 → 写入 Context | Function → Context |
| `copyright_final_check` | AssetPool Function | 发布前最终版权校验 → 阻断或放行 | Function → Agent |

### 5.2 标准工作流（含基础功能节点）

```
[START]
  │
  ▼
[选题: TrendScout Agent] 
  │ 调用: TimelineLibrary Function（时间线选题推荐）
  ▼
[5A阶段确认: MarketingMethodology Agent]
  │ 调用: BrandKnowledge Function（产品-阶段关联）
  ▼
[品牌知识检索: brand_knowledge_inject 节点]
  │ 调用: BrandKnowledge Function → 写入 Context
  ▼
[兽药宣称预检: vetdrug_validate 节点]
  │ 调用: VetDrugDB Function → 写入 Context
  ▼
[结构分析: MarketingMethodology Agent]
  │ 调用: content_structure_eval_skill（注入 Context 中的知识）
  ▼
[正文生成: ContentForge Agent]
  │ 调用: rag_retrieval_skill（使用 Context 中的知识片段）
  ▼
[素材准备: asset_prepare 节点]
  │ 调用: AssetPool Function → 写入候选素材到 Context
  ▼
[图片配置: ImageForge Agent]
  │ 调用: asset_recommendation_skill（使用 Context 中的候选素材）
  ▼
[合规审核: ComplianceGuard Agent]
  │ 调用: platform_compliance_check_skill, brand_consistency_check_skill, 
  │       copyright_check_skill, vetdrug_claim_validate_skill
  ▼
[互动预演: PoolPredictor Agent]
  │ 调用: stage_matching_skill（使用 Context 中的 5A 阶段）
  │ 失败策略: CONTINUE
  ▼
[审核风险扫描: audit_risk_scan 节点]
  │ 调用: audit_risk_detection_skill
  ▼
[人工审核: human_approval 节点]
  │ 调用: Human-in-the-Loop Console Function
  │ 强制节点，不可删除
  ▼
[发布前平台预检: platform_pre_check 节点]
  │ 调用: PlatformRule Function
  ▼
[版权最终校验: copyright_final_check 节点]
  │ 调用: AssetPool Function
  ▼
[发布: Publisher Agent]
  │ 调用: PlatformRule Function（最终发布约束确认）
  ▼
[定时等待: 24h]
  │ 调用: CronHub Function
  ▼
[数据回流: DataAnalyst Agent]
  │ 调用: BrandKnowledge Function（品牌数据归因）
  ▼
[评论监控: CommentMonitor Agent（异步）]
  │ 调用: BrandKnowledge Function（回复建议知识注入）
  │ 调用: PlatformRule Function（回复合规校验）
  ▼
[END]
```

---

## 六、数据一致性治理（基础功能层）

### 6.1 数据更新传播机制

当基础功能数据更新时，须通知相关 Agent/Skill 刷新缓存：

| 基础功能更新 | 影响范围 | 传播机制 |
|------------|---------|---------|
| BrandKnowledge 产品信息更新 | ContentForge, ComplianceGuard, CommentMonitor | AgentWatch 推送 `KNOWLEDGE_UPDATED` 事件 |
| VetDrugDB 批文状态变更（到期/撤销） | ComplianceGuard, ContentForge | AgentWatch 推送 `VETDRUG_EXPIRED` 事件 |
| AssetPool 素材版权变更 | ImageForge, ComplianceGuard, Publisher | AgentWatch 推送 `ASSET_LICENSE_CHANGED` 事件 |
| TimelineLibrary 事件状态变更 | TrendScout, CronHub | CronHub 自动重载定时任务 |
| PlatformRule 规则更新 | ComplianceGuard, Publisher, Workflow Engine | AgentWatch 推送 `RULE_UPDATED` 事件 |

### 6.2 数据版本化与回滚

所有基础功能均须支持数据版本化：

```python
@dataclass
class DataVersion:
    entity_type: str           # ASSET / BRAND_KNOWLEDGE / VETDRUG / TIMELINE / PLATFORM_RULE
    entity_id: str
    version: int
    change_type: str         # CREATE / UPDATE / DELETE
    changed_by: str
    changed_at: str
    diff: Dict               # 变更内容 diff
    rollback_available: bool # 是否可回滚
```

---

## 七、测试策略（基础功能视角）

### 7.1 基础功能层测试矩阵

| 基础功能 | 测试文件 | 测试数 | 关键场景 |
|---------|----------|--------|----------|
| **AssetPool** | `test_asset_pool_function.py` | 6 | 上传/标签/版权/关联/签名URL/批量导入 |
| **BrandKnowledge** | `test_brand_knowledge_function.py` | 6 | CRUD/RAG检索/产品-批文关联/版本化/批量导入/知识覆盖统计 |
| **VetDrugDB** | `test_vetdrug_db_function.py` | 5 | 批文录入/检索/宣称校验/到期预警/产品关联 |
| **TimelineLibrary** | `test_timeline_library_function.py` | 5 | 事件CRUD/日历视图/选题推荐/Cron绑定/临近预警 |
| **PlatformRule** | `test_platform_rule_function.py` | 6 | 平台注册/规则CRUD/合规预检/跨平台适配/兽药专项/约束查询 |
| **联合查询** | `test_foundation_knowledge_package.py` | 3 | 完整知识包组装/跨库关联准确性/缓存一致性 |

### 7.2 数据一致性测试

| 测试场景 | 验证内容 |
|---------|---------|
| BrandKnowledge 产品更新 → ContentForge 缓存刷新 | 产品卖点更新后，ContentForge 5 分钟内不再使用旧数据 |
| VetDrugDB 批文到期 → ComplianceGuard 拦截 | 批文到期后，提及该产品的内容自动被 ComplianceGuard 阻断 |
| AssetPool 版权变更 → Publisher 发布拦截 | 素材版权变为 RESTRICTED 后，Publisher 自动拦截含该素材的内容 |
| PlatformRule 规则更新 → Workflow 预检生效 | 新规则发布后，Workflow 中的 platform_pre_check 节点立即生效 |

### 7.3 回归要求

- 基础功能层新增 **25** 个测试。
- 所有基础功能 API 须通过 `test_foundation_api_contract.py` 契约测试（请求/响应格式、错误码、限流策略）。
- 基础功能数据更新传播延迟 ≤ 5 分钟（通过 AgentWatch 事件验证）。

---

## 八、执行计划（基础功能先行）

### 8.1 周次安排（调整版）

**W14（基础功能基线建设）**：
- **AssetPool Function**：三源混合存储、标签体系、版权管理、素材关联。
- **BrandKnowledge Function**：知识条目 CRUD、RAG 索引、产品-批文关联框架、批量导入。
- **VetDrugDB Function**：批文数据模型、录入接口、宣称校验框架。
- **TimelineLibrary Function**：事件 CRUD、年度营销日历预设、CronHub 绑定框架。
- **PlatformRule Function**：小红书规则全面迁移、平台适配器架构、兽药专项规则。
- **联合查询接口**：`POST /foundation/knowledge-package` 基线可用。

**W15（Agent 接入基础功能）**：
- **TrendScout Agent**：接入 TimelineLibrary（时间线选题）。
- **ContentForge Agent**：接入 BrandKnowledge（RAG 注入）、VetDrugDB（产品信息准确）。
- **ComplianceGuard Agent**：接入 BrandKnowledge（品牌一致性）、VetDrugDB（宣称校验）、PlatformRule（平台合规）、AssetPool（版权检测）。
- **MarketingMethodology Agent**：接入 BrandKnowledge（5A-产品关联）、TimelineLibrary（时间线映射）。
- **Workflow Engine**：新增 `brand_knowledge_inject`、`vetdrug_validate`、`asset_prepare` 节点。

**W16（新增 Agent + 多平台扩展）**：
- **ImageForge Agent**：接入 AssetPool（素材推荐）、BrandKnowledge（产品图关联）。
- **PlatformRule Function**：抖音规则适配（L1-L3）。
- **Publisher Agent**：接入 PlatformRule（发布约束）、AssetPool（版权最终校验）。
- **PoolPredictor Agent**：接入 BrandKnowledge（特征工程）、TimelineLibrary（时间线特征）。

**W17（CommentMonitor + 审核台）**：
- **CommentMonitor Agent**：接入 BrandKnowledge（回复知识注入）、PlatformRule（回复合规）。
- **Human-in-the-Loop Console**：接入 BrandKnowledge（品牌一致性高亮）、AssetPool（图片干预）。
- **数据一致性治理**：AgentWatch 事件推送机制上线。

**W18（全链路 E2E + 安全审计）**：
- 20 账号 × 标准工作流 × 六大基础功能全链路验证（含 PersonaStory 故事剧本注入）。
- 数据一致性测试：批文到期拦截、版权变更拦截、规则更新生效。
- 性能测试：联合查询接口 P95 < 500ms；基础功能 API 可用性 ≥ 99.9%。

### 8.2 关键里程碑

| 里程碑 | 时间 | 验收标准 |
|--------|------|---------|
| M0 | W14 末 | 六大基础功能 Function 全部可用（五大原有 + PersonaStory）；联合查询接口基线通过；25 个基础功能测试全绿。 |
| M1 | W15 末 | ContentForge、ComplianceGuard、TrendScout 全部接入基础功能；AIPL 全面下线；Workflow 新增基础功能节点可用。 |
| M2 | W16 末 | ImageForge Agent 可用；抖音规则上线；AssetPool 三源混合跑通。 |
| M3 | W17 末 | CommentMonitor Agent + 审核台上线；数据一致性事件推送机制可用。 |
| M4 | W18 末 | 全量 E2E 验证通过；数据一致性 100%；联合查询 P95 < 500ms；合规拦截率 100%。 |

---

## 九、专家评审综合决议（V3.1 调整版）

### 9.1 产品专家

1. **六大基础功能作为数据真源的定位清晰**：AssetPool、BrandKnowledge、VetDrugDB、TimelineLibrary、PlatformRule、PersonaStory 共同构成了 EcoDream Omni 的「数据地基」，所有上层业务均在此基础上构建，确保了数据一致性。新增 PersonaStory 补齐了叙事层面的数据真源，使「人设档案（PersonaPool）+ 故事剧本（PersonaStory）」形成完整的人设治理闭环。
2. **联合查询接口是产品亮点**：`POST /foundation/knowledge-package` 为 Agent 提供了一站式数据获取能力，避免了 Agent 多次调用不同 Function 的复杂度。
3. **兽药批文库的独立定位合理**：将批文数据从品牌资料库中独立出来，强化了合规真源的权威性，满足了宠物兽药行业的强监管要求。

### 9.2 架构专家

1. **基础功能层的数据内聚设计合理**：六大基础功能之间的关联关系（产品-批文、素材-产品、时间线-产品、规则-批文、故事线-时间线/系列）由 Function 层维护，对外暴露为联合查询，避免了跨层耦合。PersonaStory 与 TimelineLibrary、ContentSeries 的关联为内容叙事提供了时间维度的内聚。
2. **Agent 禁止直接操作数据库的红线必要**：确保了数据访问的统一入口，便于审计、权限控制、缓存治理。
3. **Skill 直接调用基础功能的白名单机制合理**：仅允许需要实时校验的 Skill（如版权检测、批文校验）直接调用，其余 Skill 由 Agent 预取注入，平衡了效率与治理。
4. **数据更新传播机制（AgentWatch 事件推送）是必要补齐**：避免了 Agent 缓存脏数据导致的合规风险。

### 9.3 算法 / AI 专家

1. **RAG 检索的质量保障**：BrandKnowledge 的 RAG 接口为 ContentForge 提供了准确的上下文，降低了 hallucinate 风险；VetDrugDB 的宣称校验为 ComplianceGuard 提供了量化依据。
2. **基础功能数据作为特征输入**：PoolPredictor 引入 BrandKnowledge（品牌阶段）和 TimelineLibrary（时间线节点）作为特征，丰富了预测维度。
3. **Prompt 变量与基础功能数据的映射**：Prompt Registry 中的变量（如 `{{product_name}}`、`{{approval_number}}`）直接关联基础功能数据，确保生成内容的数据准确性。

### 9.4 法务合规专家

1. **兽药批文库作为独立真源是合规刚需**：宠物兽药行业受《兽药管理条例》严格监管，所有功效宣称必须以国家批文为依据，独立 VetDrugDB 确保了合规可追溯。
2. **版权管理链路完整**：AssetPool（版权记录）→ `copyright_check_skill`（合规判定）→ ComplianceGuard（拦截）→ Publisher（最终校验），四层防护。
3. **数据更新传播机制防止「过期合规」**：批文到期、规则更新、版权变更的实时推送，避免了系统使用过期数据导致的合规事故。
4. **平台规则库的兽药专项规则**：针对宠物兽药行业的广告法要求（禁止治愈率宣称、禁止比较广告等）独立维护，确保跨平台一致性。

### 9.5 运营专家

1. **基础功能的批量导入能力降低运营负担**：BrandKnowledge 支持 CSV/Excel 批量导入产品信息，VetDrugDB 支持批文批量同步，大幅降低了初始化工作量。
2. **知识覆盖统计提示运营补全**：BrandKnowledge 的 `GET /brand-knowledge/stats` 可展示各品类知识完整度，指导运营优先补充缺失知识。
3. **年度营销日历预设降低策划负担**：TimelineLibrary 预设瑞德医生全年 Q1-Q4 营销节点，运营仅需微调，无需从零规划。
4. **素材库的三源混合模式符合运营习惯**：运营上传自有素材为主，确保品牌调性一致；AI 生图用于封面创意，降低设计成本。

---

## 十、版本对齐与执行决议

**采纳上述全部评审意见与架构调整方案**。  
本文档作为 **EcoDream Omni PRD V2.7.1 — Agent/Skill/Function 三层架构综合评审报告 V3.1（基础功能对齐版）**，与《开发计划》**v2.7.1-V3.1对齐版**同步执行。

**关键执行决议**：
1. **W14 为「基础功能建设周」**：六大基础功能 Function 必须优先于 Agent/Skill 开发完成，作为后续开发的「数据地基」。PersonaStory 与五大原有基础功能同步建设，确保内容生成链路在 W15 即可接入故事剧本上下文。
2. **基础功能 API 契约冻结**：W14 末前，六大基础功能的 API 接口、数据模型、错误码、限流策略必须冻结，后续 Agent/Skill 开发以此为准。PersonaStory 的 `/persona-stories/{id}/context` 接口须在 W15 初冻结，供 ContentForge 接入。
3. **联合查询接口作为 Agent 数据获取的首选方式**：鼓励 Agent 通过 `POST /foundation/knowledge-package` 一站式获取所需数据，减少多次调用。
4. **数据一致性事件推送机制 W17 必达**：AgentWatch 必须支持 `KNOWLEDGE_UPDATED`、`VETDRUG_EXPIRED`、`ASSET_LICENSE_CHANGED`、`RULE_UPDATED` 四类事件推送。
5. **基础功能测试覆盖率 ≥ 90%**：W14 末前，六大基础功能的单元测试覆盖率须达到 90%，作为后续 Agent/Skill 开发的信任基线。PersonaStory 新增 25 个测试（见 §11.4），纳入全量基线。

---

## 十一、新增基础功能：PersonaStory 人设剧本管理（V2.7.2 增补）

> **变更范围**：在 V2.7.1 V3.1「五大基础功能」架构基础上，新增 **PersonaStory（人设剧本管理）** 作为第六大基础功能（Function），补齐 v5.0 方案中「PersonaPool 仅管理人设定格档案（静态属性）」但缺乏**时间轴驱动的故事线治理**的缺口。当前素人号矩阵的内容生产虽可通过 PersonaPool 统一语言风格，却无法在宏观叙事层面保证「同一账号前后内容呼应、多账号间故事线互补」。PersonaStory 作为**人设故事线的唯一真源**，为 ContentForge 提供 `persona_story_context` 注入，实现「单篇内容在宏观故事线中不自洽断裂」的产品目标。
> 
> **对齐原则**：与现有 PersonaPool（人设档案）、ContentForge（内容生成）、TimelineLibrary（时间线库）、ContentSeries（系列规划）深度集成；遵循 Function 层「被动响应 · 数据真源 · 标准 REST」的定位，禁止在 PersonaStory 中引入任何自主决策逻辑；不引入已废弃概念。
> 
> **MVP 边界**：Phase 1 达成「故事剧本 CRUD + 时间轴节点管理 + persona_story_context 注入 ContentForge + 冲突检测」闭环；Phase 2 扩展「AI 辅助故事线生成 / 情感曲线自动优化 / 多账号故事矩阵编排」。

---

### 11.1 新增模块与现有架构对齐矩阵

| 新增模块 | 职责 | 对接现有模块 | 开发计划锚点 | Phase |
|---------|------|-------------|-------------|-------|
| **PersonaStory** | 人设故事剧本注册、时间轴节点管理、情感曲线配置、故事上下文生成 | PersonaPool、ContentForge、TimelineLibrary、ContentSeries、TaskHub | **MVP 补全 W14-W15** | Phase 1 |
| **Story Node Registry** | 故事节点定义：每期主题、情绪基调、关键事件、前情回顾、下期预告 | PersonaStory | **MVP 补全 W14** | Phase 1 |
| **Story Context Engine** | 根据当前进度自动生成 `persona_story_context`（当前节点/前情回顾/下期预告/情绪基调） | ContentForge、Prompt Registry | **MVP 补全 W15** | Phase 1 |
| **Conflict Detector** | 故事线与时间线/ContentSeries/PlatformRule 的冲突检测 | TimelineLibrary、ContentSeries、PlatformRule | **MVP 补全 W15** | Phase 1 |
| **Story Cockpit（前端）** | 故事剧本管理面板、时间轴可视化编辑器、情感曲线图 | Dashboard、PersonaPool 前端 | **MVP 补全 W16** | Phase 1 |

---

### 11.2 PersonaStory Function — 人设剧本管理

#### 11.2.1 真源定位

PersonaStory 是 EcoDream Omni 的**人设故事线真源**。所有素人账号的宏观叙事剧本（如「新手养猫第 1–12 周的真实记录」「流浪狗救助 30 天日记」）均在此 Function 维护。ContentForge 生成内容时注入的 `persona_story_context`、TaskHub 创建任务时的故事剧本绑定、运营在 Story Cockpit 中对故事线的调整，均以 PersonaStory 为唯一真源。

**与 PersonaPool 的边界划分**：

| 维度 | PersonaPool（人设池） | PersonaStory（人设剧本） |
|------|----------------------|-------------------------|
| **数据类型** | 静态档案：身份/语言风格/专业领域/禁忌话题 | 动态故事线：时间轴/情感曲线/叙事节点 |
| **更新频率** | 低频（创建后极少修改） | 中频（按内容发布进度推进故事节点） |
| **核心目标** | 保证「谁在说」的一致性 | 保证「说了什么、前后是否呼应」的一致性 |
| **注入内容** | `persona_voice`（语言风格模板） | `persona_story_context`（故事上下文） |
| **绑定关系** | 1 个 Persona 对应 1 个档案 | 1 个 Persona 可绑定 0~N 个故事剧本 |

#### 11.2.2 核心能力

| 能力 | 说明 | API |
|------|------|-----|
| **故事剧本 CRUD** | 创建/查询/更新/删除故事剧本；绑定目标 Persona | `POST /persona-stories` |
| **时间轴节点管理** | 为剧本定义有序节点序列（第1期/第2期/...）；支持拖拽调整顺序 | `POST /persona-stories/{id}/nodes` |
| **情感曲线配置** | 为每个节点配置情绪基调（如「困惑→惊喜→安心→期待」） | `PATCH /persona-stories/{id}/nodes/{node_id}` |
| **故事上下文生成** | 根据当前进度自动生成 `persona_story_context` | `GET /persona-stories/{id}/context` |
| **冲突检测** | 故事节点主题与 TimelineLibrary 事件/ContentSeries 规划冲突时预警 | `POST /persona-stories/{id}/conflicts` |
| **节点进度追踪** | 记录当前执行到第几个节点；内容发布后自动推进 | `POST /persona-stories/{id}/advance` |
| **剧本版本化** | 故事剧本修改创建新版本，支持回滚（与 AgentHub 版本化对齐） | `POST /persona-stories/{id}/versions` |

#### 11.2.3 数据模型

```python
@dataclass
class PersonaStory:
    id: str
    name: str                     # 如「新手养猫第1-12周的真实记录」
    description: str              # 剧本概述
    persona_id: str               # 绑定目标 Persona
    story_type: str               # LINEAR_TIME（线性时间轴）/ EVENT_DRIVEN（事件驱动）/ CHARACTER_ARC（人物弧光）
    total_nodes: int              # 总节点数
    current_node_index: int       # 当前执行到第几个节点（0-based）
    status: str                   # ACTIVE / PAUSED / COMPLETED / ARCHIVED
    emotion_curve: List[Dict]     # 情感曲线：每节点情绪值 [{"node_index": 0, "emotion": "困惑", "intensity": 0.7}]
    owner: str                    # 创建人
    current_version: int
    created_at: str
    updated_at: str

@dataclass
class StoryNode:
    id: str
    story_id: str
    node_index: int               # 在剧本中的顺序（0-based）
    node_name: str                # 节点名称，如「第3周：第一次带猫体检」
    theme: str                    # 本期主题
    key_events: List[str]         # 关键事件清单
    emotion_tone: str             # 情绪基调，如「紧张中带着期待」
    content_angle: str            # 内容切入角度
    target_5a_stage: str          # 目标 5A 阶段（AWARENESS / ASK / ACT / ADVOCATE）
    previous_recap: str           # 前情回顾（运营填写或 AI 自动生成）
    next_teaser: str              # 下期预告（为下一节点埋钩子）
    timeline_event_ids: List[str] # 关联 TimelineLibrary 事件
    content_series_ids: List[str] # 关联 ContentSeries
    publish_after: Optional[str]  # 该节点内容最早发布时间（关联 CronHub）
    publish_before: Optional[str] # 最晚发布时间
    status: str                   # PENDING / PUBLISHED / SKIPPED
    published_content_id: Optional[str]  # 实际发布的内容 ID（回填）
    created_at: str
    updated_at: str

@dataclass
class PersonaStoryContext:
    # 注入 ContentForge 的故事上下文结构
    story_id: str
    current_node: StoryNode       # 当前节点完整信息
    previous_recap: str           # 前情回顾（已发布节点的内容摘要）
    next_teaser: str              # 下期预告（为下一节点埋钩子）
    emotion_tone: str             # 当前节点情绪基调
    story_progress: str           # 如「第3周/共12周」
    consistency_rules: List[str]  # 一致性约束（如「必须提及上周体检结果」「避免与第1周观点矛盾」）
    persona_voice_hint: str       # 在当前故事节点下的人设语音微调建议
```

#### 11.2.4 与上层交互规范

**A. ContentForge 注入链路（核心链路）**

```
TaskHub 创建任务
  └──→ 绑定 story_id + 指定目标 node_index（可选，默认 current_node_index）
         └──→ Workflow Engine 执行到 ContentForge 节点
                └──→ ContentForge Agent 调用 PersonaStory Function
                       GET /persona-stories/{story_id}/context?node_index={idx}
                       └──→ PersonaStory 返回 PersonaStoryContext
                              └──→ ContentForge 将 context 注入 Prompt
                                     └──→ LLM Hub 生成带故事线约束的内容
```

**注入 Prompt 示例**：
```
【人设故事剧本上下文】
- 当前进度：第3周/共12周
- 本期主题：第一次带猫体检的真实经历
- 情绪基调：紧张中带着期待，略带自责（觉得没照顾好猫）
- 前情回顾：第2周你发了「新手养猫必备清单」，评论区有人提醒体检很重要，你决定这周带猫去。
- 下期预告：下周分享「体检后医生推荐的喂养调整」。
- 一致性约束：
  1. 必须提及上周清单中的「猫包」实际使用体验
  2. 语气保持「新手妈妈的真实记录」，避免像专家科普
  3. 不涉及具体医院名称（隐私保护）
```

**B. 节点进度自动推进**

```
Publisher 成功发布内容
  └──→ POST /persona-stories/{story_id}/advance
         └──→ PersonaStory 校验：
                - 发布内容与当前节点 theme 匹配度 >= 阈值（规则引擎）
                - 通过校验：current_node_index += 1，标记节点 PUBLISHED
                - 未通过：返回警告，建议运营确认是否跳过节点
```

**C. 冲突检测链路**

```
运营保存/更新 StoryNode
  └──→ POST /persona-stories/{id}/conflicts
         └──→ Conflict Detector 校验：
                1. TimelineLibrary：node.publish_after/publish_before 与 timeline_event 时间冲突？
                2. ContentSeries：node.theme 与同 series 其他节点主题重复/矛盾？
                3. PlatformRule：node.key_events 含禁用话题（如处方药推荐）？
                4. PersonaPool：node.emotion_tone 与 persona 语言风格冲突？
         └──→ 返回冲突列表（级别：WARNING / BLOCKING）
```

#### 11.2.5 冲突检测与治理机制

| 冲突类型 | 检测规则 | 级别 | 处理策略 |
|---------|---------|------|---------|
| **时间线冲突** | StoryNode.publish_after/before 与 TimelineLibrary 事件时间窗口重叠 | WARNING | 提示运营调整发布时间或故事节点顺序 |
| **系列主题冲突** | 同 ContentSeries 内多个 StoryNode 主题重复率 > 50% | WARNING | 建议合并节点或调整切入角度 |
| **合规冲突** | StoryNode.key_events / content_angle 命中 PlatformRule 禁用话题 | BLOCKING | 禁止保存，须修改后才能提交 |
| **人设风格冲突** | StoryNode.emotion_tone 与 PersonaPool 定义的 persona_voice 严重不符 | WARNING | 提示运营确认是否为人设突破（如「成长弧光」刻意设计） |
| **故事线断裂** | 当前节点的 previous_recap 与上一节点实际发布内容摘要差异 > 阈值 | WARNING | 提示更新前情回顾或检查是否跳过了节点 |
| **节点超期** | StoryNode.publish_before 已过但未发布 | WARNING | 建议续写、跳过或延长截止时间 |

---

### 11.3 前端增强：PersonaStory 管理面板（Story Cockpit）

#### 11.3.1 故事剧本列表页

```
+-----------------------------------------------------------------------------+
|  人设故事剧本管理                              [新建剧本] [批量归档] [刷新]   |
+-----------------------------------------------------------------------------+
|  筛选: [全部状态 v] [人设 v] [故事类型 v]                                    |
+-----------------------------------------------------------------------------+
|  剧本名称                  │ 绑定人设   │ 进度    │ 状态   │ 下次节点主题   │
|  --------------------------|-----------|---------|--------|---------------|
|  新手养猫第1-12周记录      │ 小艾养猫记 │ 3/12    │ [G] 进行中│ 第一次体检经历 │
|  流浪狗救助30天日记        │ 阿明救助站 │ 12/30   │ [G] 进行中│ 第12天：找到领养人│
|  打工人养狗省钱攻略        │ 省钱狗爸   │ 5/8     │ [Y] 暂停 │ 自制狗粮避坑   │
|  老年犬护理100天           │ 温柔老李   │ 0/100   │ [G] 未开始│ 第1天：初识老狗狗│
+-----------------------------------------------------------------------------+
```

#### 11.3.2 时间轴编辑器（核心页面）

- **纵向时间轴**：左侧展示节点序号 + 发布状态图标（未发布灰点 / 已发布绿点 / 跳过黄点）。
- **节点卡片**：右侧展示节点详情（主题/情绪/关键事件/前情回顾/下期预告），支持 inline 编辑。
- **拖拽排序**：节点可上下拖拽调整顺序；拖拽后触发冲突检测，若与时间线/系列冲突则弹出警告。
- **情感曲线图**：底部展示情绪强度折线图（基于 emotion_curve 数据），运营可点击节点调整情绪值。
- **快捷操作**：「插入节点」「删除节点」「复制节点」「从当前节点生成内容」一键创建 TaskHub 任务。

#### 11.3.3 故事上下文预览（调试面板）

- 分屏：左侧选择节点，右侧实时渲染 `persona_story_context`（模拟 ContentForge 收到的注入内容）。
- 变量高亮：已绑定变量（`{{previous_recap}}`、`{{emotion_tone}}`）高亮显示。
- Dry Run：支持「模拟生成」——调用 ContentForge 的 Dry Run 接口，查看带故事上下文的内容效果，不产生副作用。

---

### 11.4 测试策略

| 模块 | 测试文件 | 测试数 | 关键场景 |
|------|----------|--------|----------|
| Story CRUD | `test_persona_story.py` | 4 | 创建/查询/更新/删除故事剧本；Persona 绑定 |
| Node Management | `test_story_nodes.py` | 5 | 节点增删改/拖拽排序/情感曲线更新/进度推进 |
| Context Engine | `test_story_context.py` | 4 | 上下文生成/前情回顾自动摘要/下期预告继承/注入格式校验 |
| Conflict Detector | `test_story_conflicts.py` | 5 | 时间线冲突/系列冲突/合规冲突/人设冲突/故事线断裂检测 |
| Integration | `test_persona_story_integration.py` | 4 | ContentForge 注入链路/TaskHub 绑定/Publisher 推进/Workflow 集成 |
| Story Cockpit（前端）| E2E | 3 | 时间轴渲染/节点编辑/情感曲线调整 |

**回归与集成要求**：
- PersonaStory 创建后，ContentForge 生成内容必须包含 `persona_story_context` 字段，且内容须体现故事线约束（由 LLM-as-Judge 或规则引擎验证）。
- 节点自动推进机制：Publisher 发布后 `current_node_index` 必须正确递增（单测模拟 Publisher 回调）。
- 冲突检测拦截率：合规冲突（BLOCKING 级别）拦截率须达 100%；WARNING 级别冲突须正确提示但不阻断。
- 故事剧本版本化：修改剧本后旧版本须可回滚，回滚后 ContentForge 注入的上下文须恢复为旧版本。

---

### 11.5 执行顺序建议

**第 1 轮（W14，与六大基础功能并行）**：Story CRUD + Node Management（故事剧本与节点的基础数据层）。
**第 2 轮（W15）**：Context Engine（`persona_story_context` 自动生成）+ Conflict Detector（基础冲突规则）。
**第 3 轮（W15 末）**：与 ContentForge 集成（注入链路打通）+ 与 TaskHub 集成（任务创建时绑定故事剧本）。
**第 4 轮（W16）**：Story Cockpit 前端（时间轴编辑器 + 情感曲线图 + 上下文预览）。
**第 5 轮（W16 末）**：与 Publisher 集成（节点自动推进）+ 全链路 E2E 验证。
**第 6 轮（W17-W18，Phase 2）**：AI 辅助故事线生成（基于 Persona + TimelineLibrary 自动提案故事剧本）、情感曲线自动优化（基于历史互动数据调整情绪强度）、多账号故事矩阵编排（矩阵内多账号的故事线互补设计）。

---

### 11.6 专家评审意见与决议

> **评审对象**：PersonaStory（人设剧本管理）模块及其与 PersonaPool、ContentForge、TimelineLibrary、ContentSeries 的集成方案。  
> **评审真源**：以 v5.0 为产品真源，以叙事学「人物弧光（Character Arc）」与内容营销「系列化叙事」最佳实践为业务参考；以 Function 层「数据真源 · 被动响应 · 标准 REST」为架构约束。

| 角色 | 评审意见 | 结论 |
|------|---------|------|
| **产品** | 1. **PersonaStory 是需求 7「整体呼应与前后互动」的核心杠杆**：当前仅靠 ContentSeries 做结构层面的系列规划，缺乏叙事层面的情感连贯性。PersonaStory 通过「前情回顾 + 下期预告」机制，让单篇内容在宏观故事中有锚点，显著提升用户追更意愿。  <br>2. **与 PersonaPool 的边界划分清晰**：PersonaPool 管「是谁」，PersonaStory 管「经历了什么」，两者互补不重叠。建议在 PersonaPool 前端增加「关联故事剧本」快捷入口，降低运营切换成本。  <br>3. **MVP 禁止过度工程**：W14-W16 只做「线性时间轴 + 手动节点管理 + 基础冲突检测」，禁止在 MVP 引入「AI 自动写完整故事线」（虽然技术上可行，但运营对故事线的把控是品牌调性的核心，不能全自动化）。  <br>4. **情感曲线的运营价值**：情感曲线不仅是可视化装饰，更是指导 ContentForge 情绪调性的关键输入。建议在 Story Cockpit 中预设几种经典情感曲线模板（如「低谷逆袭」「渐进成长」「悬疑揭秘」），降低运营配置门槛。 | ✅ 采纳；PersonaPool 前端增加关联入口；MVP 故事线必须人工主导；预设情感曲线模板。 |
| **架构** | 1. **PersonaStory 定位为 Function 层合理**：故事剧本是数据真源，不是决策实体。Context Engine 的「自动生成上下文」本质是数据组装（前情回顾拼接 + 情绪基调提取），不是 AI 决策，符合 Function 层约束。  <br>2. **与 ContentForge 的注入链路须通过 Prompt Registry**：`persona_story_context` 的渲染应通过 Prompt Registry 的模板机制完成（如 Prompt 模板中预留 `{{persona_story_context}}` 变量），禁止 ContentForge 硬编码拼接逻辑。这样 PersonaStory 的上下文格式变更时，仅需更新 Prompt 模板版本，无需修改 ContentForge 代码。  <br>3. **节点进度自动推进须保守设计**：Publisher 发布成功后自动推进节点是合理的，但须支持「手动回退」和「跳过节点」两种运营干预操作。禁止设计为「只能前进不能后退」的线性强制流程。  <br>4. **冲突检测规则建议复用现有规则引擎**：合规冲突可直接调用 PlatformRule Function；时间线冲突调用 TimelineLibrary API；人设冲突调用 PersonaPool 的风格校验 Skill。避免在 PersonaStory 内部重复实现规则逻辑。 | ✅ 采纳；注入链路通过 Prompt Registry；支持节点回退/跳过；冲突检测复用现有规则引擎。 |
| **算法 / AI** | 1. **前情回顾的自动生成可用 LLM 摘要，但须人工确认**：上一节点发布内容的「摘要」用于生成 `previous_recap`，可用 LLM 自动生成，但建议作为草稿供运营确认，避免 AI 摘要遗漏关键剧情线索（如「猫体检发现轻微贫血」这个细节如果摘要漏掉，下期内容就会断裂）。  <br>2. **情感曲线的量化表示建议采用离散标签 + 强度值**：而非连续浮点数，因为 LLM 对「0.7 的期待」理解不稳定，对「期待（强度：强）」理解更一致。  <br>3. **故事线与互动数据的关联分析（Phase 2）**：可探索「情感曲线峰值与互动量关系」，但 MVP 禁止将此作为预测模型的输入特征（样本不足，易过拟合）。 | ✅ 采纳；前情回顾 AI 生成后人工确认；情感曲线用离散标签+强度；Phase 2 再做故事线-互动关联。 |
| **运维 / SRE** | 1. **StoryNode 数据量预估**：20 账号 × 每人设 2 个剧本 × 每剧本 50 节点 = 2000 节点，数据量极小，现有 PostgreSQL 完全可承载，无需独立存储。  <br>2. **persona_story_context 的生成是轻量计算**：主要是字段拼接 + 简单规则，无复杂模型推理，API 响应时间目标 < 100ms。  <br>3. **版本化数据膨胀可控**：故事剧本版本化后，旧版本节点数据可归档（状态置为 ARCHIVED），热库仅保留 ACTIVE 版本，避免表膨胀。 | ✅ 采纳；复用 PostgreSQL；响应目标 <100ms；旧版本归档。 |
| **法务合规** | 1. **故事剧本中的「真实经历」须标注虚构声明**：若故事线设计为「新手养猫真实记录」但实际为品牌策划的叙事，须在账号简介或内容中适当标注「内容基于真实养猫经验改编」，避免被平台或用户判定为虚假人设。  <br>2. **故事节点中的 key_events 若涉及宠物医疗场景，须经过 VetDrugDB 与 PlatformRule 双重校验**：特别是「体检结果」「疾病治疗」等节点，禁止出现处方药推荐、治愈率宣称等内容。  <br>3. **前情回顾中引用的用户评论（如「评论区有人提醒体检」）须确保脱敏**：不得引用真实用户的昵称或头像，可用「网友提醒」「粉丝建议」等泛化表述。  <br>4. **剧本数据涉及运营创意策略，建议定为「内部机密」级**：特别是未发布节点的主题规划，泄露可能导致竞品模仿。 | ✅ 采纳；虚构声明标注；医疗节点双重校验；用户评论脱敏；剧本数据分级保护。 |
| **运营专家** | 1. **故事剧本的「复制」功能是强需求**：同一品牌下多个素人账号可能采用相似的叙事框架（如「新手养猫」），运营需要「复制剧本 → 微调节点 → 绑定不同 Persona」的能力，避免从零创建。  <br>2. **「从节点一键生成内容」是效率关键**：在时间轴编辑器中选中节点后，直接弹出「创建 TaskHub 任务」弹窗，预填 story_id + node_index，减少运营在多个页面间切换。  <br>3. **情感曲线模板的运营语言**：不要用「情绪强度 0.7」这种技术语言，而用「低落 / 平稳 / 高涨 / 爆发」四级标签，更直观。  <br>4. **故事线进度看板需求**：Dashboard 中增加「各账号故事线进度」 widget，运营一眼看到哪些账号的故事线快断了（长时间未推进），及时干预。 | ✅ 采纳；剧本复制功能；节点一键生成任务；情感四级标签；Dashboard 故事线进度 widget。 |

**执行决议**：采纳上述全部评审意见；本文 **V2.7.2** 与《开发计划》同步增补 W14-W16 周次；PersonaStory 作为第六大基础功能（Function）纳入架构真源，与 AssetPool、BrandKnowledge、VetDrugDB、TimelineLibrary、PlatformRule 并列，共同构成 EcoDream Omni 的数据地基。

---

> **文档结束**。本文档作为 V2.7.1-V2.7.2 新增需求与原有架构深度融合、并以**六大基础功能**为数据真源的最终架构真源，与《开发计划》**v2.7.1-V3.1对齐版**同步执行，约束所有后续开发迭代。

---

## 十二、五大基础模块标准化评估与修复计划（V2.7.3 增补）

> **变更范围**：基于 2026-05-25 四专家组联合评审报告（`docs/专家评审报告_五大基础模块标准化评估_v1.md`），将代码实现与 PRD 设计的差距、已知缺陷、修复优先级同步纳入 PRD，作为后续开发迭代的约束真源。  
> **评审团队**：组织架构专家组 x 技术专家组 x 业务专家组 x UI/UE专家组  
> **核心结论**：当前五大基础模块"模型设计层较为完善，API执行层严重滞后，Agent集成层完全空白"。核心CRUD已实现约60%，但批量导入/文件解析/Agent集成/RAG检索均未实现。  

---

### 12.1 执行摘要：代码现状 vs PRD设计

| 评估维度 | 整体评分 | 核心问题 |
|---------|---------|---------|
| **模块边界清晰度** | ★★★★ | 五模块职责定义明确，ORM模型与PRD对齐度高 |
| **API标准化程度** | ★★★ | 标准CRUD齐全，但缺乏批量导入、文件上传、向量检索等进阶接口 |
| **前后端一致性** | ★★ | 字段命名映射混乱、状态值大小写不一致、Schema字段缺失 |
| **与PRD需求对齐** | ★★★ | 核心CRUD已实现约60%，批量导入/文件解析/Agent集成/RAG检索均未实现 |
| **代码质量** | ★★★ | ORM层测试覆盖较好，但存在缩进Bug、死代码测试、双重commit等问题 |

**关键风险**：五个模块均停留在"人工录入+单条查询"阶段，距离"AI驱动内容生产"的架构目标差距显著。特别是 **BrandKnowledge向量检索缺失** 和 **Agent-Function集成链路未打通**，是阻塞W15-W16交付的两条核心瓶颈。

---

### 12.2 模块职责矩阵（当前实现 vs PRD定义）

| 模块 | PRD定义职责 | 当前实际职责 | 职责漂移风险 |
|------|------------|-------------|-------------|
| **BrandKnowledge** | 品牌/品类/SKU/FAQ/禁用语的知识真源；RAG检索Top-K | 仅实现文本CRUD+LIKE搜索 | **高** — RAG职责未履行，ComplianceGuard直接硬编码规则 |
| **AssetPool** | 三源混合素材管理（运营上传≥70%、图库API、AI生成）；版权链≥2年 | 仅实现URL录入+单条管理 | **高** — 无本地上传、无图库API对接、无缩略图生成 |
| **TimelineLibrary** | 季节事件库；产品上市时间线；CronHub绑定；BrandKnowledge联动 | 仅实现事件CRUD | **中** — CronHub/联动均未实现，但字段已预留 |
| **VetDrugDB** | 批文录入/检索/宣称校验/到期预警 | 实现CRUD+宣称校验，预警无定时任务 | **中** — 到期预警函数已就绪但无调度 |
| **PlatformRule** | 多平台规则基座；L1-L4分层；版本化；动态生效 | 实现CRUD+evaluate，但L1/L2在合规引擎硬编码 | **高** — 合规引擎与规则库两套体系并行 |
| **PersonaStory** | 剧本编排+节点管理+情感曲线+内容绑定 | 后端完整，前端无独立页面 | **中** — 后端就绪但运营无法使用 |

---

### 12.3 关键代码缺陷清单（已确认）

| 序号 | 缺陷 | 位置 | 严重度 | 影响 |
|------|------|------|--------|------|
| 1 | `_asset_to_dict` 缩进错误 | `api/asset_pool.py` L251-L258 | **高** | AI元数据处理代码在函数体外，永远不可达 |
| 2 | `test_brand_knowledge.py` 死代码 | `tests/test_brand_knowledge.py` | **高** | 测试不存在的端点（`/bulk-import`、`/products`），运行时skip |
| 3 | `create_entry` 双重commit | `brand_knowledge_function.py` + API层 | **中** | 服务层commit后API层又commit，设计不当 |
| 4 | `list_entries` total语义失真 | `api/brand_knowledge.py` | **中** | search模式下用`len(items)`当total，无分页语义 |
| 5 | VetDrug状态值大小写不一致 | 前端小写 / 后端大写 | **高** | 前端筛选可能失效 |
| 6 | 前端宣称校验与API不兼容 | `VetDrugPage.tsx` vs `api/vetdrug.py` | **高** | 前端传`{claim_text}`，后端要`{approval_number, claimed_indications[]}` |
| 7 | PlatformRule归因空实现 | `api/platform_rules.py` | **中** | `/attribution/{content_id}`直接返回`[]` |
| 8 | 合规引擎与规则库割裂 | `compliance_engine.py` vs `platform_rule_function.py` | **高** | L1/L2硬编码 vs L3/L4 ORM，数据不互通 |

---

### 12.4 前后端字段映射规范（必须统一）

| 前端字段 | 前端含义 | 后端字段 | 后端含义 | 当前一致度 | 修复要求 |
|---------|---------|---------|---------|--------|---------|
| `name` | 素材名称 | `filename` | 文件名 | 部分 | 后端Schema增加`name`别名或前端统一改用`filename` |
| `type` | 素材类型(image/video) | `category` | 宠物分类(cat/dog) | **不匹配** | 紧急修复：前端`type`映射后端`source_type`+`_derive_asset_type` |
| `type` | 素材类型 | `source_type` | 来源类型(OPERATOR_UPLOAD) | **不匹配** | 同上 |
| `url` | 素材URL | `file_url` | 文件URL | 匹配 | 保持 |
| `status` | active/expired/deprecated | `status` | ACTIVE/EXPIRED/REVOKED | 大小写不一致 | 统一为大写枚举 |
| `entry_type` | "BRAND_INFO"(全大写) | `entry_type` | "brand_info"(小写) | 大小写不一致 | 统一为小写存储 |

---

### 12.5 PRD需求对齐差距表（逐模块）

#### BrandKnowledge vs FUNC-2

| PRD需求 | 当前状态 | 差距 |
|---------|---------|------|
| 知识条目CRUD | ✅ 已实现 | — |
| **PDF/Word/Excel知识导入** | ❌ 未实现 | 无文件上传接口，无解析库集成 |
| **LangChain Document Loader** | ❌ 未实现 | TASK标记为未完成 |
| **pgvector向量检索 Top-K** | ⚠️ 字段预留 | `embedding`从未写入，`search_by_content`仅为LIKE |
| **RAG注入控制** | ⚠️ 部分实现 | `search_by_content`为文本匹配，无语义检索 |
| **批文一致性季度校验** | ❌ 未实现 | 无定时任务 |
| **双人复核+留痕≥2年** | ⚠️ 部分实现 | 版本化已就绪，但无审批流状态机 |

#### AssetPool vs FUNC-1

| PRD需求 | 当前状态 | 差距 |
|---------|---------|------|
| 三源混合模型 | ⚠️ 字段预留 | 仅有`source_type`标记，无图库API对接 |
| **本地上传（Multipart）** | ❌ 未实现 | 只能输入URL |
| **批量导入（CSV/Excel）** | ❌ 未实现 | — |
| **Pillow缩略图生成** | ❌ 未实现 | `_generate_thumbnail_url`仅为字符串拼接 |
| **合规图库API对接** | ❌ 未实现 | Getty/Unsplash未接入 |
| **STS Token签名URL** | ❌ 未实现 | `file_url`为永久公开链接 |
| **AI标识强制附加** | ✅ 已实现 | `_ensure_ai_disclosure`自动添加 |

#### VetDrugDB vs FUNC-3

| PRD需求 | 当前状态 | 差距 |
|---------|---------|------|
| 批文CRUD | ✅ 已实现 | — |
| 批文号格式强制校验 | ✅ 已实现 | 正则匹配 |
| 宣称一致性校验 | ✅ 已实现 | `verify_claims`已就绪 |
| **批量CSV导入** | ❌ 未实现 | `data_source`预留`csv_import`但无API |
| **国家兽药API同步** | ❌ 未实现 | `data_source`预留`api_sync`但无同步逻辑 |
| **到期预警（提前90天）** | ⚠️ 函数就绪 | `get_expiry_warnings()`已就绪但无API端点/定时任务 |

#### PlatformRule vs FUNC-5

| PRD需求 | 当前状态 | 差距 |
|---------|---------|------|
| 规则CRUD+版本化 | ✅ 已实现 | 自动历史快照+版本递增 |
| 小红书L1-L4规则迁移 | ⚠️ 部分实现 | 内置5条默认规则（L3/L4），L1/L2在合规引擎硬编码 |
| **严禁词独立词库** | ❌ 未实现 | 严禁词散落在`condition_json.pattern`正则中 |
| **文章规范分类管理** | ❌ 未实现 | 无`content_guideline`表，规范仅在YAML文件中 |
| **YAML配置加载** | ❌ 未实现 | `lumina/data/platforms/`有4个YAML文件，代码零引用 |
| **违规归因** | ❌ MVP空实现 | `/attribution/{content_id}`直接返回`[]` |

---

### 12.6 技术债务总览

```
架构断层 1: 无文件上传基础设施（UploadFile / OSS / S3）
架构断层 2: 无向量检索基础设施（embedding写入 / pgvector查询）
架构断层 3: 无Agent-Function调用协议
架构断层 4: 合规双轨制（硬编码引擎 vs ORM规则库）
架构断层 5: 前端字段映射混乱（name<->filename / type<->category）
```

---

### 12.7 修复优先级与执行计划

#### P0（阻塞交付，1-2周）— 必须修复的代码缺陷

| 任务ID | 任务 | 模块 | 工作量 | 验收标准 |
|--------|------|------|--------|---------|
| P0-1 | 修复素材库 `_asset_to_dict` 缩进Bug | AssetPool | 0.1天 | AI元数据处理代码在函数体内可执行；测试通过 |
| P0-2 | 修复VetDrug前后端状态值大小写 | VetDrugDB | 0.2天 | 前端统一使用大写枚举；筛选功能正常 |
| P0-3 | 修复VetDrug宣称校验UI与API不匹配 | VetDrugDB | 0.5天 | 前端增加批文号选择和宣称数组拆分；调用后端正确API |
| P0-4 | 统一前后端字段映射（name/filename, type/category, entry_type大小写） | 全局 | 0.5天 | `_mapAsset`正确映射；API Schema对齐；筛选/显示正常 |
| P0-5 | 清理死代码测试 `test_brand_knowledge.py` | BrandKnowledge | 0.2天 | 删除不存在端点的测试；补充实际端点的测试 |

#### P1（需求补齐，2-3周）— 补齐PRD定义的缺失能力

| 任务ID | 任务 | 模块 | 工作量 | 验收标准 |
|--------|------|------|--------|---------|
| P1-1 | 新增文件上传基础设施（UploadFile + 本地存储） | 全局 | 2天 | FastAPI UploadFile可用；本地存储目录可配置；文件可上传下载 |
| P1-2 | BrandKnowledge PDF/Word/Excel导入 | BrandKnowledge | 1.5天 | 支持上传文件解析为条目；批量创建；保留原文档附件 |
| P1-3 | VetDrugDB CSV批量导入 + 到期预警API | VetDrugDB | 1.5天 | CSV上传解析；批量创建；`/expiry-warnings`端点返回预警列表 |
| P1-4 | AssetPool本地上传 + 缩略图生成 | AssetPool | 1.5天 | UploadFile上传图片；Pillow生成缩略图；缩略图URL正确返回 |
| P1-5 | PlatformRule YAML配置加载 | PlatformRule | 1天 | PyYAML读取`lumina/data/platforms/`；自动创建/更新规则条目 |
| P1-6 | PersonaStory前端管理页面（Story Cockpit） | PersonaStory | 2天 | App.tsx新增路由；列表/详情/节点编辑页面可用 |

#### P2（架构升级，3-4周）— 技术架构升级

| 任务ID | 任务 | 模块 | 工作量 | 验收标准 |
|--------|------|------|--------|---------|
| P2-1 | BrandKnowledge向量检索（embedding写入+pgvector查询） | BrandKnowledge | 2天 | 创建/更新时自动写embedding；`search_by_content`支持语义检索Top-K |
| P2-2 | 统一Agent-Function调用协议 | 全局 | 3天 | 定义`Function.call(agent_context)`标准接口；ComplianceGuard调用BrandKnowledge/VetDrugDB/PlatformRule |
| P2-3 | 合规引擎与PlatformRule数据合并 | PlatformRule | 2天 | `compliance_engine.py` L1/L2规则迁移至ORM；引擎优先读取ORM规则 |
| P2-4 | 严禁词独立词库 + 文章规范表 | PlatformRule | 1.5天 | 新增`prohibited_words`表和`content_guidelines`表；合规引擎引用 |
| P2-5 | AssetPool图库API对接（Unsplash/Getty） | AssetPool | 2天 | API密钥管理；搜索/下载/授权链记录 |

---

### 12.8 与现有执行计划的关联

**P0 修复必须前置**：在W15 Agent接入基础功能之前，必须先完成P0代码缺陷修复，否则Agent调用Function API时可能遇到字段映射错误、API不兼容等问题。

**P1 需求补齐与W14并行**：P1中的文件上传基础设施（P1-1）是W14基础功能基线建设的必要能力；BrandKnowledge导入（P1-2）和VetDrugDB CSV导入（P1-3）降低运营初始化负担；Story Cockpit（P1-6）与W16前端计划对齐。

**P2 架构升级列为W18-W19**：向量检索（P2-1）和Agent-Function协议（P2-2）是Phase 2的核心能力，不影响Phase 1 MVP交付。

---

### 12.9 专家组签字（评审报告同步）

| 专家组 | 评审结论 | 状态 |
|--------|----------|------|
| **组织架构专家组** | 五模块职责边界清晰，ORM设计达到生产级。但Agent集成层完全空白，模块间联动仅停留在字段预留阶段，需尽快建立Function调用协议。 | ✅ 已通过 |
| **技术专家组** | 标准CRUD API齐备，但存在缩进Bug、死代码测试、前后端字段映射混乱等低级错误。文件上传、向量检索、批量操作三大基础设施缺失，技术债务较重。 | ✅ 已通过 |
| **业务专家组** | 与PRD对比，核心CRUD已实现约60%，但PDF/Word导入、批量CSV、向量检索、RAG注入、定时预警等关键业务功能均未实现，距离"AI驱动内容生产"目标差距显著。 | ✅ 已通过 |
| **UI/UE专家组** | 前端页面基本可用，但存在严重的字段映射混乱和状态值不一致问题。VetDrug宣称校验UI与API完全不兼容。PersonaStory缺少独立管理页面，运营无法使用剧本功能。全局缺乏错误提示和空状态引导。 | ✅ 已通过 |

**执行决议**：采纳上述全部评审意见与修复计划；本文 **V2.7.3** 与《开发计划》同步增补修复任务；P0缺陷修复作为**最高优先级阻塞项**，必须在任何Agent接入前完成。

---

> **文档结束**。本文档作为 V2.7.1-V2.7.3 新增需求与原有架构深度融合、并以**六大基础功能**为数据真源的最终架构真源，与《开发计划》**v2.7.1-V3.1对齐版**同步执行，约束所有后续开发迭代。
