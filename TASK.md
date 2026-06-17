# EcoDreamOmni 全链路真实性修复任务卡
# Full-Chain Reality Fix Task Card
# 创建时间: 2026-06-16
# 优先级: P0 (阻塞真实发布)

---

## 背景

全链路真实性测试（`scripts/full_chain_reality_test.py`）已执行完毕，发现以下关键阻塞问题：

1. **Cookie 未配置** — 账号池中所有账号 `cookie_encrypted=None`，导致小红书API认证失败（code: -101）
2. **工作流模板API 404** — `/workflow-engine/templates` 路由不存在，模板节点无法通过API验证
3. **LLM API Key 未配置** — 内容生成、合规检查等节点无法执行
4. **互动数据跟踪API未实现** — `/engagement-tracking` 返回404

其中 **Cookie 问题已修复** — 已为测试账号 `喵喵日记` (B1jOQzLp4BpMY00nZ1FyDQ) 注入真实Cookie，健康检查已通过：
- healthy: True
- user_id: 5aa46b2411be10601c86ea96
- nickname: 魔力红鸟

---

## 修复任务清单

### P0-1: 批量注入真实Cookie到所有小红书账号 ✅ DONE
**状态**: 已完成（首个账号验证通过）
**负责人**: AI Agent
**验收标准**:
- [x] 至少1个账号Cookie注入成功
- [x] 健康检查返回 `healthy=True`
- [ ] 所有35个小红书账号Cookie注入完成（需用户提供更多Cookie或确认使用全局Cookie）

**备注**: 用户提供的Cookie已验证有效。建议将Cookie配置到 `.env` 的 `REDNOTE_COOKIE` 环境变量，或批量更新所有账号。

---

### P0-2: 修复工作流模板API路由
**状态**: 待修复
**负责人**: AI Agent
**问题**: `/workflow-engine/templates` 返回 404，但 `main.py` 中已加载 `workflow_engine.load_presets()`
**根因分析**: 
- `workflow_engine.py` 中没有对应的 FastAPI router 被注册到 `main.py`
- 模板数据在内存中，但无API暴露

**修复方案**:
1. 在 `src/api/workflow_engine.py` 新建路由文件（或复用现有路由）
2. 暴露以下端点：
   - `GET /workflow-engine/templates` — 列出所有模板
   - `GET /workflow-engine/templates/{id}` — 获取模板详情
   - `GET /workflow-engine/templates/{id}/nodes` — 获取模板节点列表
   - `POST /workflow-engine/templates/{id}/recommend` — 模板推荐
3. 在 `main.py` 中注册路由

**验收标准**:
- [ ] `GET /workflow-engine/templates` 返回200，包含所有预设模板
- [ ] 能正确识别 `content_creation_standard` 模板中的品牌知识/关键词/合规/预演节点
- [ ] 全链路测试 Phase A 全部通过

---

### P0-3: 配置LLM API Key，使工作流节点能真实执行
**状态**: 待修复
**负责人**: 用户 + AI Agent
**问题**: 任务创建后直接为 `human_wait`，但等待180秒后状态未变化，说明工作流引擎没有驱动节点执行
**根因分析**:
- `task_hub.start_workflow()` 可能依赖LLM调用，但API Key未配置导致节点执行失败
- 或工作流引擎执行逻辑有bug

**修复方案**:
1. 检查 `.env` 中是否配置了 `DEEPSEEK_API_KEY` / `OPENAI_API_KEY` / `KIMI_API_KEY`
2. 检查 `llm_hub` 中模型状态是否为 `active`
3. 检查 `task_hub.start_workflow()` 的执行逻辑，确认节点是否正确驱动
4. 添加工作流执行日志，便于调试

**验收标准**:
- [ ] 任务创建后，工作流能自动执行到 `human_wait` 状态（在60秒内）
- [ ] 内容生成节点能产出真实内容（标题、正文、标签）
- [ ] 合规检查节点能产出合规分数

---

### P0-4: 实现互动数据跟踪API
**状态**: 待修复
**负责人**: AI Agent
**问题**: `/engagement-tracking` 返回404
**修复方案**:
1. 在 `src/api/` 下新建 `engagement_tracking.py` 路由
2. 或复用现有 `data_analyst` / `pool_predictor` 路由
3. 实现以下端点：
   - `GET /engagement-tracking` — 列出所有互动数据记录
   - `GET /engagement-tracking/{task_id}` — 获取特定任务的互动数据
   - `POST /engagement-tracking/{task_id}/fetch` — 手动触发数据抓取
4. 调用 `xhs_note_data_extraction.py` 中的 `fetch_note_engagement()`

**验收标准**:
- [ ] `GET /engagement-tracking` 返回200
- [ ] 能正确展示点赞、评论、收藏、分享、阅读量字段
- [ ] 发布后24小时能自动抓取互动数据（Celery任务）

---

### P1-1: 为所有账号配置独立代理（避免IP关联风控）
**状态**: 待优化
**负责人**: 用户 + AI Agent
**问题**: 部分账号未配置代理，会回退到全局代理或直接连接
**修复方案**:
1. 为每个小红书账号分配独立代理
2. 或配置 `REDNOTE_COOKIE` 到 `.env` 作为全局回退
3. 检查代理健康状态

**验收标准**:
- [ ] 所有小红书账号都有 `proxy_id` 配置
- [ ] 代理健康检查通过

---

### P1-2: 开启自动互动数据抓取开关
**状态**: 待优化
**负责人**: AI Agent
**问题**: `auto_engagement_fetch=False` 默认关闭
**修复方案**:
1. 批量更新账号：`auto_engagement_fetch=True`
2. 或在前端增加开关UI，让用户手动开启

**验收标准**:
- [ ] 账号 `auto_engagement_fetch=True`
- [ ] 发布后24小时Celery任务自动触发

---

### P1-3: 前端展示浏览器指纹信息
**状态**: 待优化
**负责人**: 前端开发者
**问题**: 前端无浏览器指纹/设备指纹展示UI
**修复方案**:
1. 在账号池详情页面增加指纹信息卡片
2. 展示：UA、Viewport、Locale、Timezone、Canvas Noise、WebGL Noise

**验收标准**:
- [ ] 账号详情页能看到完整指纹配置
- [ ] 指纹信息与实际发布时使用的配置一致

---

### P2-1: Playwright迁移（高级指纹对抗）
**状态**: 长期规划
**负责人**: 架构师
**问题**: `canvas_noise / webgl_noise` 当前HTTP客户端不支持
**修复方案**:
1. 将 `xhs_publisher` 从 `requests-based` 迁移到 `Playwright-based`
2. 使用 `browser_pool.py` 中的 `build_context_config()`
3. 真实注入 Canvas/WebGL 噪声

**验收标准**:
- [ ] 发布时使用真实浏览器环境
- [ ] Canvas/WebGL 指纹差异化生效

---

## 当前状态速查

| 检查项 | 状态 | 备注 |
|--------|------|------|
| Cookie真实有效 | ✅ 已通过 | 账号 `B1jOQzLp4BpMY00nZ1FyDQ` 健康检查通过 |
| 指纹配置完整 | ✅ 通过 | 44个账号全部配置UA/Viewport/Locale/TZ |
| 代理配置 | ⚠️ 部分 | 部分账号有代理，部分无 |
| 工作流模板API | ❌ 404 | 需新建路由 |
| LLM内容生成 | ❌ 未验证 | 需配置API Key |
| 真实发布 | ❌ 未验证 | 依赖LLM节点执行 |
| 互动数据抓取 | ❌ 未实现 | API不存在 |

---

## 下一步行动建议

### 立即执行（今天）
1. **修复工作流模板API** — 新建 `/workflow-engine/templates` 路由
2. **检查LLM配置** — 确认 `.env` 中API Key是否配置，模型是否active
3. **批量更新Cookie** — 将用户提供的Cookie更新到所有小红书账号（或配置全局REDNOTE_COOKIE）

### 本周完成
4. **验证完整发布链路** — 从任务创建到真实发布到小红书
5. **实现互动数据跟踪API** — 完成数据闭环

### 后续优化
6. **独立代理配置** — 为每个账号分配独立代理
7. **前端指纹展示** — 提升运营可见性
8. **Playwright迁移** — 增强风控对抗能力

---

## 附件

- 测试脚本: `scripts/full_chain_reality_test.py`
- 测试报告: `docs/full_chain_reality_test_report_2026-06-16_14-39-34.md`
- 原始E2E测试: `scripts/e2e_reality_test_2026-05-31.py`
