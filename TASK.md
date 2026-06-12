# 当前 Sprint 与原子任务

> **当前Sprint**: V2.7.2 需求对齐版 — LLM Hub精简 + PersonaStory第六大基础功能  
> **上一版Sprint**: V2.7.1-V3.1对齐版 — 详见 [`docs/TASK_V2.7.1.md`](docs/TASK_V2.7.1.md)  
> **基线**: W1-W22已完成，Phase 1.5+Phase 2基础设施已完成  
> **架构调整**: V3.1基础功能对齐评审已通过（2026-05-19）；V2.7.2 LLM精简评审已通过
> 
> **详细设计**（架构 / 接口 / 评审结论）：
> - V2.7.2 Function层: `详细设计_EcoDreamOmni_v2.md` v2.7.2（待创建）
> - V2.6基线: [`docs/详细设计_EcoDreamOmni_v1.md`](docs/详细设计_EcoDreamOmni_v1.md)
> 
> **开发计划**:
> - V2.7.2对齐版: [`开发计划_素人号矩阵AI平台_v2.md`](开发计划_素人号矩阵AI平台_v2.md) v2.7.2增补
> - V2.7.1-V3.1对齐版: [`开发计划_素人号矩阵AI平台_v2.md`](开发计划_素人号矩阵AI平台_v2.md) v2.7.1-V3.1对齐版 §三
> - V2.2基线: [`开发计划_素人号矩阵AI平台_v2.md`](开发计划_素人号矩阵AI平台_v2.md) §一-八
> 
> **AI上下文包**: [`docs/AI_Context_Packages.md`](docs/AI_Context_Packages.md)
> 
> **评审报告**:
> - 架构对齐评审: [`docs/专家评审报告_开发计划_v2.7.1_V3.1架构对齐.md`](docs/专家评审报告_开发计划_v2.7.1_V3.1架构对齐.md)
> - 架构评审: [`docs/专家评审报告_PRD_V2.7.1_架构审查.md`](docs/专家评审报告_PRD_V2.7.1_架构审查.md)
> - 法务评审: [`docs/法务合规评审报告_PRD_V2.7.1_11项新增需求.md`](docs/法务合规评审报告_PRD_V2.7.1_11项新增需求.md)

---

## V2.7.2 Sprint 概览

| 模块 | 优先级 | 架构层级 | 周次 | 状态 |
|------|--------|----------|------|------|
| **PersonaStory Function** | P0 | **Function层** | **W14** | [ ] |
| LLM Hub 精简版 | P0 | Function层 | **W15** | [ ] |
| LLM Cockpit 前端（精简版） | P0 | 前端 | **W16** | [ ] |
| **全链路E2E + 架构审计** | — | — | **W18** | [ ] |

**V2.7.2 新增需求（2项）**：
1. **PersonaStory 第六大基础功能**：StoryNode / PersonaStoryContext 数据模型、Story Cockpit 前端、内容生成注入链路
2. **LLM Hub 精简版**：原三层配置（Global/Agent/Skill）+ Route Engine + Cost Governor + Circuit Breaker 精简为「厂家选择 + 模型名 + APIKey + 应用范围（全局/节点覆盖）」模式

**V2.7.1 基线任务（延续，详见 TASK_V2.7.1.md）**：
| 模块 | 优先级 | 架构层级 | 周次 | 状态 |
|------|--------|----------|------|------|
| **AssetPool Function** | P0 | **Function层** | **W14** | [x] |
| **BrandKnowledge Function** | P0 | **Function层** | **W14** | [x] |
| **VetDrugDB Function** | P0 | **Function层** | **W14** | [x] |
| **TimelineLibrary Function** | P1 | **Function层** | **W14** | [x] |
| **PlatformRule Function基座** | P0 | **Function层** | **W14** | [x] |
| TrendScout增强 | P0 | Agent层 | **W15** | [ ] |
| MarketingMethodology 5A | P0 | Agent层 | **W15** | [ ] |
| Agent-Function集成 | P0 | 集成层 | **W15** | [ ] |
| ImageForge | P0 | Agent层 | **W16** | [ ] |
| CommentHub合规版 | P1 | Agent层 | **W16** | [ ] |
| ContentSeries | P1 | Agent层 | **W16** | [ ] |
| PlatformRule多平台 | P0 | Function扩展 | **W16** | [ ] |
| Human-in-the-Loop弹性 | P0 | Agent层 | **W17** | [ ] |
| Workflow可视化 | P1 | Function扩展 | **W17** | [ ] |

**自研代码总计**: 约10,100行（Function层4,500行 + Agent层5,100行 + 集成层600行）  
**新增测试**: 75个  
**新增接口**: 69个  
**架构红线**: Agent禁止直接操作数据库（静态扫描0处违规）

---

根目录本文件为导航；详细任务清单见 [`docs/TASK_V2.7.1.md`](docs/TASK_V2.7.1.md)
