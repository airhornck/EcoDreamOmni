# Phase 8 变更记录 — Skill 补齐 + Agent Fleet 基础实现

> **日期**: 2026-06-03
> **任务**: P8-1 ~ P8-3（第一批次并行开发）
> **状态**: ✅ 已完成

---

## 一、新增文件清单

### P8-1: 合规类 Skill（3 个）

| 文件 | 行数 | 说明 |
|------|------|------|
| `src/skills/compliance_check.py` | ~220 | 综合合规检查：L1-L4 规则 + 敏感词 + 兽药宣称预检 |
| `src/skills/platform_compliance_check.py` | ~190 | 平台合规校验：L1 静态规则 + L2 关键词规则 |
| `src/skills/vetdrug_claim_validate.py` | ~210 | 兽药宣称校验：批文一致性 + 夸大宣称检测 |
| `tests/skills/test_compliance_check.py` | ~60 | 7 项测试 |
| `tests/skills/test_platform_compliance_check.py` | ~55 | 6 项测试 |
| `tests/skills/test_vetdrug_claim_validate.py` | ~55 | 7 项测试 |

### P8-2: 内容生成核心 Skill（3 个）

| 文件 | 行数 | 说明 |
|------|------|------|
| `src/skills/content_generate.py` | ~280 | 正文生成：模板拼接 + 六层 Prompt 标记 |
| `src/skills/image_generate.py` | ~160 | 图片生成：文生图/图生图 + 平台封面规格 |
| `src/skills/rag_retrieval.py` | ~130 | RAG 检索：BrandKnowledge 关键词匹配 |
| `tests/skills/test_content_generate.py` | ~70 | 7 项测试 |
| `tests/skills/test_image_generate.py` | ~60 | 6 项测试 |
| `tests/skills/test_rag_retrieval.py` | ~75 | 9 项测试 |

### P8-3: Agent Fleet 基础实现

| 文件 | 行数 | 说明 |
|------|------|------|
| `src/services/agent_fleet.py` | ~380 | AgentFleet 服务：实例池 + Round Robin / Least Load / Capability Match 路由 + 健康检查 + 伸缩评估 |
| `src/api/agent_fleet.py` | ~240 | FastAPI 路由：Fleet CRUD / 实例注册/心跳/路由 / 健康查询 / 伸缩评估 |
| `tests/test_agent_fleet.py` | ~240 | 22 项测试（Fleet CRUD / 实例管理 / 路由 / 健康 / 伸缩） |

### 其他变更

| 文件 | 变更 |
|------|------|
| `src/skills/__init__.py` | 导出 6 个新增 Skill |
| `src/main.py` | 注册 `agent_fleet.router` |
| `docs/契约与数据/01-API接口契约.md` | 新增 §9 Agent Fleet API 契约 |
| `docs/数据词典_v4.0/06-Agent与Skill映射.md` | 新增 P8 6 个 Skill + Agent Fleet 条目 |
| `docs/PRD偏差报告.md` | 新增 §16 Phase 8 偏差，更新 P7-1 为已完成 |

---

## 二、质量门禁结果

| 门禁项 | 结果 |
|--------|------|
| 新增测试 | 70 项全部通过 |
| Phase 7 回归测试 | 13 项全部通过 |
| ruff (新增代码) | 0 errors ✅ |
| mypy (新增代码) | 0 errors ✅ |
| 前端 eslint | 0 新增错误（历史遗留 156 个） ✅ |
| 前端 tsc | 0 errors ✅ |

---

## 三、技术决策记录

1. **Skill MVP 策略**：6 个新增 Skill 均采用模板/规则引擎实现，预留 LLM Hub 接口（`requires_llm=True` 的 Skill 标记为 `template_mvp` 或 `placeholder`）
2. **Agent Fleet 内存存储**：MVP 使用内存字典存储 Fleet/Instance 数据，无 DB 持久化（Phase 9 可接入 ORM）
3. **中文内容优先**：合规类 Skill 的敏感词库、规则库均以中文为主，符合国内平台合规需求

---

*记录人: Kimi Code CLI*  
*关联文档: `docs/架构设计/07-现有代码基线改造设计.md`、`docs/v4.0_开发Checklist.md`*
