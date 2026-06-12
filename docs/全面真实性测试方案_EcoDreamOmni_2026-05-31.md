# EcoDreamOmni 全面真实性测试方案

> **版本**: v1.0  
> **日期**: 2026-05-31  
> **测试类型**: 端到端真实性验证（E2E Reality Test）  
> **覆盖范围**: 任务创建 → 工作流执行 → 人工审核 → 内容再生成 → 封面更换 → 真实发布  

---

## 一、测试目标

| 目标编号 | 目标描述 | 验证维度 |
|----------|----------|----------|
| TG-01 | **账号池合规对抗策略** | 日配额限制、生命周期配额、异常标记、健康分衰减是否生效 |
| TG-02 | **工作流可用性** | 8种模板预设是否正确加载，各节点（trend-scout → publisher）是否正常流转 |
| TG-03 | **平台格式规范接入** | PlatformSchema 动态加载后，字段约束（标题长度/图片数量/正文长度）是否在创建和编辑阶段生效 |
| TG-04 | **生成内容可用性** | LLM 生成内容是否符合平台调性、是否注入品牌知识、是否包含合规红线内容 |
| TG-05 | **人工审核链路** | APPROVE/REJECT/REVISE 决策是否正确驱动状态机，resume_workflow 是否正确唤醒后续节点 |
| TG-06 | **内容再生成与封面更换** | regenerateContent API 是否重新调用 LLM，CoverPicker 是否支持多图替换 |
| TG-07 | **真实发布性** | publisher 节点是否调用真实 XhsClient，cookie/UA/proxy 是否按账号隔离，发布后是否回写状态 |

---

## 二、测试环境清单

### 2.1 基础设施状态（已确认）

| 组件 | 状态 | 访问地址 | 备注 |
|------|------|----------|------|
| PostgreSQL 16 | ✅ Up | `localhost:5432` | `ecodream` 数据库 |
| Redis 7 | ✅ Up | `localhost:6379` | Celery Broker + Cache |
| Backend FastAPI | ✅ Up | `http://localhost:8000` | `/docs` Swagger 可用 |
| Frontend Vite | ✅ Up | `http://localhost:5173` | React 19 + Tailwind |
| Celery Worker | ✅ Up | — | 消费 `celery` queue |
| Celery Beat | ✅ Up | — | 定时任务调度 |

### 2.2 数据库状态（已确认）

| 数据表/集合 | 状态 | 记录数 | 关键发现 |
|-------------|------|--------|----------|
| `platform_schemas` | ✅ 已同步 | 4 | xiaohongshu/douyin/bilibili/wechat_official |
| `platform_content_formats` | ✅ 已同步 | 8 | 各平台格式已就位 |
| `tasks` | ⚠️ 空表 | 0 | 需创建测试任务 |
| `platform_rules` | ⚠️ 空表 | 0 | **合规规则未初始化** |
| `llm_models` | ❓ 未知 | — | 需检查是否配置了模型 |
| `personas` | ❓ 未知 | — | 需至少1个 Persona |
| `content_series` | ❓ 未知 | — | 可选 |

### 2.3 配置状态（已确认）

| 配置项 | 当前值 | 影响 | 测试要求 |
|--------|--------|------|----------|
| `REDNOTE_COOKIE` | `""`（空） | 真实发布将失败 | ⚠️ **必须提供真实Cookie才能测发布链路** |
| `DEEPSEEK_API_KEY` | `""`（空） | LLM 调用将 fallback 到 mock | ⚠️ **必须提供 API Key 才能测真实生成** |
| `LLM_API_KEY_MASTER_KEY` | `""`（空） | LLM Hub 密钥加密不可用 | 低优先级 |

---

## 三、前置条件（需用户审核确认）

### 3.1 必须准备（P0 — 阻塞测试）

| # | 前置条件 | 责任人 | 检查方式 | 风险等级 |
|---|----------|--------|----------|----------|
| P0-1 | **小红书真实 Cookie** | 用户 | 提供 `REDNOTE_COOKIE` 环境变量值 | 🔴 高 |
| P0-2 | **LLM API Key**（DeepSeek/OpenAI/其他） | 用户 | 提供 `DEEPSEEK_API_KEY` 或配置 LLM Hub | 🔴 高 |
| P0-3 | **测试用小红书账号** | 用户 | 在账号池创建1个活跃账号，含 cookie + fingerprint | 🔴 高 |
| P0-4 | **至少1个 Persona** | 用户/系统 | `POST /api/personas` 创建或确认已有 | 🟡 中 |

### 3.2 建议准备（P1 — 影响测试深度）

| # | 前置条件 | 责任人 | 说明 |
|---|----------|--------|------|
| P1-1 | **合规规则初始化** | 用户 | 运行 `POST /api/platform-rules/init` 或手动插入 L1-L4 规则 |
| P1-2 | **代理IP配置**（可选） | 用户 | 如需测试多账号隔离，配置 proxy_config |
| P1-3 | **多平台Cookie** | 用户 | 如需测试抖音/视频号发布链路 |

---

## 四、测试用例矩阵

### Phase A: 任务创建链路测试（平台规范 + 账号池）

#### TC-A1: 平台选择动态加载
| 项 | 内容 |
|----|------|
| **目的** | 验证 TaskHubCreatePage 从 PlatformSchema API 动态渲染平台列表 |
| **步骤** | 1. 登录前端 → 导航到 `/task-hub/create` <br> 2. 观察「目标平台」下拉框 <br> 3. 检查选项是否与 `GET /api/platform-schemas` 返回一致 |
| **预期结果** | 下拉框显示：小红书、抖音、哔哩哔哩、微信公众号（与数据库同步数据一致） |
| **验收标准** | ✅ 平台列表与 `platform_schemas` 表数据完全一致 <br> ❌ 硬编码显示 xhs/douyin/wechat_channels |

#### TC-A2: 内容格式二级联动
| 项 | 内容 |
|----|------|
| **目的** | 验证选择平台后，内容格式选项动态加载对应平台的格式 |
| **步骤** | 1. 选择「小红书」 <br> 2. 观察「内容格式」下拉框 <br> 3. 切换为「抖音」，再次观察 |
| **预期结果** | 小红书 → 图文 / 视频 / 仅文字；抖音 → 短视频 / 图文 |
| **验收标准** | ✅ 格式列表与 `platform_content_formats` 中该平台的记录一致 <br> ❌ 硬编码格式选项 |

#### TC-A3: 账号池按平台过滤
| 项 | 内容 |
|----|------|
| **目的** | 验证选择平台后，账号列表只显示该平台账号 |
| **步骤** | 1. 创建2个账号：小红书账号A、抖音账号B <br> 2. 在创建页选择「小红书」 <br> 3. 检查账号下拉框 |
| **预期结果** | 只显示账号A，不显示账号B |
| **验收标准** | ✅ 账号列表按 `platform` 字段过滤 <br> ❌ 显示所有平台账号 |

#### TC-A4: 智能模板推荐（方案B）
| 项 | 内容 |
|----|------|
| **目的** | 验证平台+格式变更后，系统自动推荐模板且用户可覆盖 |
| **步骤** | 1. 选择「小红书」+「图文」→ 检查推荐模板 <br> 2. 切换为「视频」→ 检查推荐模板变化 <br> 3. 手动选择其他模板 |
| **预期结果** | 图文→`content_creation_note_image`；视频→`content_creation_video_original`；手动选择后可覆盖 |
| **验收标准** | ✅ 推荐模板来自 `POST /api/workflow-engine/templates/recommend` <br> ✅ 用户手动选择后，推荐Badge消失 |

#### TC-A5: 账号池日配额对抗
| 项 | 内容 |
|----|------|
| **目的** | 验证 publisher 节点执行时，日配额检查和递增逻辑生效 |
| **步骤** | 1. 创建账号，设置 `daily_quota=1`, `posts_today=0` <br> 2. 创建任务并驱动到发布 <br> 3. 再次创建任务尝试发布 |
| **预期结果** | 第一次发布成功，`posts_today=1`；第二次发布失败或进入排队 |
| **验收标准** | ✅ `posts_today` 递增 <br> ✅ 超过配额时 `quota_exceeded=true` <br> ❌ 无限发布 |

#### TC-A6: 账号生命周期配额
| 项 | 内容 |
|----|------|
| **目的** | 验证不同生命周期阶段的默认日配额 |
| **步骤** | 1. 创建 cold_start 账号（默认quota=1）<br> 2. 创建 growth 账号（默认quota=3）<br> 3. 对比 publisher 节点中的配额检查 |
| **预期结果** | cold_start 日限1篇，growth 日限3篇 |
| **验收标准** | ✅ `LIFECYCLE_QUOTAS` 映射生效 |

---

### Phase B: 工作流执行链路测试

#### TC-B1: 标准工作流节点流转
| 项 | 内容 |
|----|------|
| **目的** | 验证 `content_creation_standard` 8节点按序执行，到 HUMAN_APPROVAL 正确暂停 |
| **步骤** | 1. `POST /api/task-hub/tasks/with-workflow` 创建任务 <br> 2. 观察返回的 `status` 和 `current_node_index` <br> 3. 检查 workflow execution 状态 |
| **预期结果** | 任务状态为 `human_wait`，execution 状态为 `PAUSED`，context 中包含 topic_report / outline / generated_content / compliance_result / prediction_result |
| **验收标准** | ✅ `status == "human_wait"` <br> ✅ execution 停在 node_index=6（HUMAN_APPROVAL）<br> ✅ prompt_variables 合并了 workflow context |

#### TC-B2: 新模板加载验证
| 项 | 内容 |
|----|------|
| **目的** | 验证4个新增模板正确加载到内存 |
| **步骤** | 1. `GET /api/workflow-engine/templates` <br> 2. 检查返回列表中是否包含4个新模板 |
| **预期结果** | 返回8个模板（4个原有 + 4个新增） |
| **验收标准** | ✅ `content_creation_note_image` / `content_creation_video_clone` / `content_creation_video_original` / `content_creation_text_article` 均存在 |

#### TC-B3: Celery 驱动工作流恢复
| 项 | 内容 |
|----|------|
| **目的** | 验证 Celery worker 能在 HUMAN_APPROVAL 后正确 resume workflow |
| **步骤** | 1. 创建任务并驱动到 `human_wait` <br> 2. `POST /api/human-in-the-loop/tasks/{id}/approve` <br> 3. 观察 Celery worker 日志 |
| **预期结果** | Celery worker 日志显示 `resume_workflow_execution` 调用，最终驱动 publisher 节点 |
| **验收标准** | ✅ Celery 日志包含 `resume_workflow_execution` <br> ✅ 任务最终状态为 `completed` 或 `approved_waiting_publish` |

#### TC-B4: content_format 注入工作流上下文
| 项 | 内容 |
|----|------|
| **目的** | 验证 task 创建时传入的 `content_format` 被注入 workflow context |
| **步骤** | 1. 创建任务，指定 `content_format="视频"` <br> 2. 检查 `GET /api/task-hub/tasks/{id}` 返回 <br> 3. 检查 workflow execution context |
| **预期结果** | `task.content_format == "视频"`，`generated_content.content_type == "video"` |
| **验收标准** | ✅ `content_format` 字段正确持久化 <br> ✅ `simulate_node_output` 输出中包含 `video_script` / `video_duration` |

---

### Phase C: 人工审核链路测试

#### TC-C1: APPROVE 驱动发布
| 项 | 内容 |
|----|------|
| **目的** | 验证 APPROVE 后 resume_workflow 驱动 publisher 节点 |
| **步骤** | 1. 任务在 `human_wait` 状态 <br> 2. 前端点击「通过」→ `POST /api/human-in-the-loop/tasks/{id}/approve` <br> 3. 观察状态变化 |
| **预期结果** | 状态变为 `approved_waiting_publish` 或 `completed`（取决于是否有定时发布） |
| **验收标准** | ✅ `review_decision == "APPROVE"` <br> ✅ execution 中 HUMAN_APPROVAL 节点完成 <br> ✅ publisher 节点被执行 |

#### TC-C2: REJECT 终止工作流
| 项 | 内容 |
|----|------|
| **目的** | 验证 REJECT 后任务进入 failed 状态 |
| **步骤** | 1. 任务在 `human_wait` 状态 <br> 2. 点击「驳回」并填写原因 <br> 3. 观察状态 |
| **预期结果** | 状态变为 `failed`，`review_reason` 记录驳回原因 |
| **验收标准** | ✅ `status == "failed"` <br> ✅ `review_decision == "REJECT"` |

#### TC-C3: REVISE 回退到配置
| 项 | 内容 |
|----|------|
| **目的** | 验证 REVISE 后任务回退到 configuring 状态 |
| **步骤** | 1. 任务在 `human_wait` 状态 <br> 2. 点击「打回修改」 <br> 3. 观察状态 |
| **预期结果** | 状态变为 `configuring`，可重新编辑后再次启动工作流 |
| **验收标准** | ✅ `status == "configuring"` <br> ✅ 可再次 `POST /task-hub/tasks/{id}/start-workflow` |

#### TC-C4: 内容编辑与保存
| 项 | 内容 |
|----|------|
| **目的** | 验证审核页面可编辑标题/正文/话题，并持久化到任务 |
| **步骤** | 1. 在 ReviewPublishDetailPage 修改标题 <br> 2. 观察「保存中...」提示 <br> 3. 刷新页面检查是否持久化 |
| **预期结果** | `PUT /api/review-publish-center/conclusions/{id}/content` 成功，刷新后内容保持 |
| **验收标准** | ✅ `updateContent` API 返回 `success: true` <br> ✅ 刷新后编辑内容不丢失 |

---

### Phase D: 账号池合规对抗策略验证

#### TC-D1: 日配额硬限制
| 项 | 内容 |
|----|------|
| **目的** | 验证账号当日发布数达到配额后，publisher 节点拒绝执行 |
| **步骤** | 1. 设置 `daily_quota=2`, `posts_today=2` <br> 2. 创建任务并驱动到 publisher 节点 <br> 3. 观察发布结果 |
| **预期结果** | publisher 节点检测到 `quota_exceeded`，返回失败或跳过 |
| **验收标准** | ✅ `account.posts_today >= account.daily_quota` 时阻止发布 <br> ✅ 不调用 XhsClient |

#### TC-D2: 健康分衰减
| 项 | 内容 |
|----|------|
| **目的** | 验证发布失败/违规后健康分下降 |
| **步骤** | 1. 记录初始 `health_score=100` <br> 2. 模拟一次发布失败 <br> 3. 检查健康分变化 |
| **预期结果** | 发布失败后 `health_score` 下降（如 -10） |
| **验收标准** | ✅ `health_score` 有衰减逻辑（当前代码中未见显式衰减，需确认） |

#### TC-D3: 异常标记
| 项 | 内容 |
|----|------|
| **目的** | 验证多次失败后 `anomaly_flags` 被标记 |
| **步骤** | 1. 连续3次发布失败 <br> 2. 检查 `anomaly_flags` <br> 3. 检查 `status` 是否变为 `blocked` |
| **预期结果** | `anomaly_flags` 包含失败标记，`status` 可能变为 `blocked` 或 `warming` |
| **验收标准** | ✅ `anomaly_flags` 非空 <br> ✅ `status` 变化有阈值控制 |

#### TC-D4: Cookie 隔离与指纹隔离
| 项 | 内容 |
|----|------|
| **目的** | 验证多账号时每个账号使用独立的 cookie + fingerprint |
| **步骤** | 1. 创建2个小红书账号，不同 cookie 和 UA <br> 2. 各创建1个任务并驱动到发布 <br> 3. 检查 XhsClient 缓存 key |
| **预期结果** | 两个任务分别使用各自账号的 cookie 和 UA，XhsClient 缓存 key 不同 |
| **验收标准** | ✅ `_get_xhs_client` 的 `cache_key` 包含 cookie 前缀 + UA 前缀 <br> ✅ 不串号 |

---

### Phase E: 真实发布链路测试

#### TC-E1: 小红书真实发布（图文）
| 项 | 内容 |
|----|------|
| **目的** | 验证 publisher 节点调用真实 XhsClient 发布图文笔记 |
| **前置条件** | P0-1 真实 Cookie 已配置 |
| **步骤** | 1. 创建任务，平台=小红书，格式=图文 <br> 2. 驱动工作流到发布 <br> 3. 检查返回的 `published_url` |
| **预期结果** | 发布成功，返回真实 `note_id` 和 `https://www.xiaohongshu.com/explore/{note_id}` |
| **验收标准** | ✅ `success: true` <br> ✅ `platform_post_id` 非空 <br> ✅ `published_url` 可访问 |
| **⚠️ 风险** | 真实发布将产生公开内容，建议用小号测试，发布后手动删除 |

#### TC-E2: 小红书发布带话题标签
| 项 | 内容 |
|----|------|
| **目的** | 验证标签被正确转换为 `#话题[话题]#` 格式并发布 |
| **步骤** | 1. 创建任务，tags=["宠物健康","养宠日常"] <br> 2. 审核通过后发布 <br> 3. 在小红书APP检查话题标签是否生效 |
| **预期结果** | 笔记正文末尾包含 `#宠物健康[话题]# #养宠日常[话题]#` |
| **验收标准** | ✅ 话题标签可点击跳转 |

#### TC-E3: 多图发布
| 项 | 内容 |
|----|------|
| **目的** | 验证审核阶段添加的多图在发布时全部上传 |
| **步骤** | 1. 审核阶段通过 CoverPicker 添加3张图片 <br> 2. 确认发布 <br> 3. 检查小红书笔记图片数量 |
| **预期结果** | 笔记包含3张图片，首图为封面 |
| **验收标准** | ✅ `images` 数组全部上传 <br> ✅ `cover_image_url` 对应首图 |

#### TC-E4: 发布失败降级
| 项 | 内容 |
|----|------|
| **目的** | 验证发布失败时代理记录和错误回传 |
| **前置条件** | 使用无效 Cookie 或断网 |
| **步骤** | 1. 使用过期/无效 Cookie <br> 2. 驱动到 publisher 节点 <br> 3. 观察返回和代理记录 |
| **预期结果** | 返回 `success: false` + 错误信息，代理记录 `success: false` |
| **验收标准** | ✅ `error` 字段非空 <br> ✅ `record_proxy_result(proxy_id, success=False)` 被调用 |

---

## 五、测试执行计划

### 5.1 执行顺序

```
前置准备 → Phase A → Phase B → Phase C → Phase D → Phase E
   ↓          ↓         ↓         ↓         ↓         ↓
 环境检查   创建任务   驱动执行   审核决策   配额验证   真实发布
```

### 5.2 测试数据准备脚本

```bash
# 1. 检查环境
curl -s http://localhost:8000/health | jq .

# 2. 检查 PlatformSchema
curl -s http://localhost:8000/api/platform-schemas | jq '.schemas[].platform_id'

# 3. 检查账号池（需先登录获取 token）
curl -s http://localhost:8000/api/account-pool -H "Authorization: Bearer $TOKEN" | jq '.accounts'

# 4. 检查工作流模板
curl -s http://localhost:8000/api/workflow-engine/templates | jq '.[].id'

# 5. 检查 LLM 模型配置
curl -s http://localhost:8000/api/llm-hub/models | jq '.[].model_name'

# 6. 检查合规规则
curl -s http://localhost:8000/api/platform-rules | jq '.rules | length'
```

### 5.3 自动化测试脚本位置

测试脚本将生成在 `scripts/e2e_reality_test_2026-05-31.py`，支持：
- API 调用链（无需前端）
- 数据库状态断言
- 日志文件解析（Celery worker）
- 截图对比（如需前端验证）

---

## 六、验收标准汇总

| 维度 | 通过标准 | 失败标准 |
|------|----------|----------|
| **账号池** | 日配额拦截生效、健康分有变化、多账号隔离 | 无限发布、串号、健康分恒定为100 |
| **工作流** | 8节点按序执行、PAUSED/RESUME 正确、新模板可用 | 节点跳过、死锁、模板丢失 |
| **平台规范** | 字段约束在创建和编辑阶段生效、动态加载 | 硬编码平台/格式、约束不生效 |
| **生成内容** | 标题+正文非空、有内容预览、含合规检查结果 | 内容为空、无合规检查、LLM报错 |
| **人工审核** | APPROVE/REJECT/REVISE 正确驱动状态机 | 审核后状态不变、resume失败 |
| **真实发布** | 返回真实 note_id、URL 可访问 | 发布失败无错误信息、返回假URL |

---

## 七、风险与降级方案

| 风险编号 | 风险描述 | 概率 | 影响 | 降级方案 |
|----------|----------|------|------|----------|
| R-01 | **无真实 Cookie** | 高 | 🔴 阻断 Phase E | 仅测到 Phase D，publisher 用 mock 验证节点执行 |
| R-02 | **无 LLM API Key** | 高 | 🟡 内容质量不可信 | 接受 mock 内容，但验证数据结构和字段完整性 |
| R-03 | **合规规则未初始化** | 中 | 🟡 合规检查走 fallback | 验证 fallback 逻辑（hardcode 规则）是否生效 |
| R-04 | **XHS API 风控** | 中 | 🟡 真实发布被封 | 使用小号、发布后立即删除、或仅测 health check |
| R-05 | **Celery Worker 未消费** | 低 | 🔴 定时发布不生效 | 检查 Redis queue、worker 日志 |
| R-06 | **账号池为内存存储** | 中 | 🟡 重启后数据丢失 | 每次测试前重新创建账号数据 |

---

## 八、测试产出物

| 产出物 | 位置 | 说明 |
|--------|------|------|
| 测试方案 | `docs/全面真实性测试方案_EcoDreamOmni_2026-05-31.md` | 本文档 |
| 测试脚本 | `scripts/e2e_reality_test_2026-05-31.py` | 自动化 API 测试脚本 |
| 测试数据 | `scripts/test_data_reality_2026-05-31.json` | 测试账号、Cookie、内容样本 |
| 测试报告 | `docs/变更记录/2026-05-31/真实性测试报告_2026-05-31.md` | 执行后的结果报告 |
| 问题清单 | `docs/变更记录/2026-05-31/真实性测试问题清单_2026-05-31.md` | 发现的 bug 和缺陷 |

---

## 九、用户审核检查清单

请逐项确认以下前置条件，标注 ✅/❌：

| # | 审核项 | 用户确认 | 备注 |
|---|--------|----------|------|
| 1 | 已阅读测试方案全文 | [ ] | — |
| 2 | 已准备小红书测试账号 Cookie | [ ] | 用于 Phase E |
| 3 | 已准备 LLM API Key（DeepSeek/OpenAI） | [ ] | 用于真实内容生成 |
| 4 | 已确认账号池中有至少1个活跃账号 | [ ] | 用于 Phase A/D |
| 5 | 已确认 Persona 已创建 | [ ] | 用于任务创建 |
| 6 | 已确认平台规则已初始化（或接受 fallback） | [ ] | 用于合规检查 |
| 7 | 已确认前端可访问 `http://localhost:5173` | [ ] | 用于前端链路测试 |
| 8 | 已确认后端可访问 `http://localhost:8000/docs` | [ ] | 用于 API 测试 |
| 9 | **是否授权进行真实发布测试？** | [ ] | ⚠️ 将产生真实公开内容 |
| 10 | 是否接受用 mock 降级测试 publisher 节点？ | [ ] | 如 Cookie 不可用 |

---

> **下一步动作**: 用户审核确认后，生成自动化测试脚本 `scripts/e2e_reality_test_2026-05-31.py`，按 Phase A→E 顺序执行，逐条输出 PASS/FAIL 并生成测试报告。
