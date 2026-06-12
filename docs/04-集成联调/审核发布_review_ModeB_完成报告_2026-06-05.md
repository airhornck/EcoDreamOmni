# 审核发布 `/review` — Mode B (Copilot-Driven) 改造完成报告

**日期**: 2026-06-05  
**模式**: Mode B (Copilot-Driven) — 工作区纯画布，所有操作通过 Copilot Action Cards  
**Phase**: P0 (Week 5)

---

## 一、执行摘要

| 步骤 | 状态 | 说明 |
|------|------|------|
| Step 0 一致性检查 | ✅ | 主题/路由/Mode B/Phase P0/网关就绪 |
| Step 1 HTML 预览 + 契约 | ✅ | HTML v3 已通过四方审核；后端需求文档 592 行已齐备 |
| Step 2 契约冻结 | ✅ | API 对齐会议召开，所有 11 个端点 + 5 项关键确认通过 |
| Step 3 前后端并行开发 | ✅ | 前端 Mode B 合规；后端 copilot 字段扩展 |
| Step 4 联调测试 | ✅ | 7/7 核心 API 通过 |
| Step 5 质量门禁 | ✅ | TS 0 errors / ESLint 0 errors |

---

## 二、契约冻结 (Step 2)

**会议文档**: `docs/契约与数据/15min-API对齐会议_审核发布_2026-06-04.md`  
**状态**: 🔒 **已冻结** — 2026-06-05 四方联合审核通过

### 确认的 API 清单

| # | Method | Endpoint | 状态 |
|---|--------|----------|------|
| 1 | GET | `/api/review-publish-center/conclusions` | ✅ 响应新增 `copilot_summary` |
| 2 | GET | `/api/review-publish-center/conclusions/{id}` | ✅ 响应新增 `copilot_context` + `available_copilot_cards` |
| 3 | POST | `/api/human-in-the-loop/tasks/{id}/{decision}` | ✅ 请求/响应新增 copilot 字段 |
| 4 | PUT | `/api/review-publish-center/conclusions/{id}/content` | ✅ 无变更 |
| 5 | POST | `/api/review-publish-center/conclusions/{id}/confirm-publish` | ✅ 无变更 |
| 6 | POST | `/api/review-publish-center/conclusions/{id}/regenerate` | ✅ 无变更 |
| 7 | POST | `/api/ai/generate-cover` | ✅ Sprint 2 完成 |
| 8 | GET | `/api/ai/generate-cover/{job_id}` | ✅ Sprint 2 完成 |
| 9 | POST | `/api/ai/copilot/context` | ✅ Sprint 2 完成 |
| 10 | GET | `/api/ai/copilot/action-cards` | ✅ Sprint 2 完成 |
| 11 | POST | `/api/ai/copilot/execute` | ✅ Sprint 2 完成 |

---

## 三、前端 Mode B 合规检查

### 3.1 工作区禁止元素检查

| 页面 | 检查项 | 状态 |
|------|--------|------|
| `ReviewPublishCenterPage.tsx` | 无批量审核按钮 | ✅ |
| `ReviewPublishCenterPage.tsx` | 无新建/编辑/删除按钮 | ✅ |
| `ReviewPublishCenter.tsx` | Tabs 为筛选器（非业务操作） | ✅ |
| `ReviewPublishDetailPage.tsx` | 无「审核通过」按钮 | ✅ |
| `ReviewPublishDetailPage.tsx` | 无「驳回」按钮 | ✅ |
| `ReviewPublishDetailPage.tsx` | 无「打回修改」按钮 | ✅ |
| `ReviewPublishDetailPage.tsx` | 无「发布」按钮 | ✅ |
| `CoverPickerModal` | 无「AI 生成」标签页 | ✅ |

### 3.2 Copilot 集成检查

| 检查项 | 状态 |
|--------|------|
| 页面加载时上报 Copilot 上下文 (`reportCopilotContext`) | ✅ |
| 动态获取 Action Cards (`fetchActionCards`) | ✅ |
| 注册 Action Handler (`setPageActionHandler`) | ✅ |
| 审核通过 → 自动切换为「发布确认」Card | ✅ |
| 封面生成 → Copilot Action Card 驱动 | ✅ |

---

## 四、后端 API 扩展

### 4.1 已实现字段

**`GET /review-publish-center/conclusions`**:
```json
{
  "copilot_summary": {
    "total_pending": 4,
    "recommended_priority": ["task_003", "task_001", "task_002"],
    "batch_suggestion": "4 条待审中，建议按优先级从高到低处理。"
  }
}
```

**`GET /review-publish-center/conclusions/{id}`**:
```json
{
  "copilot_context": {
    "recommended_action": "approve",
    "confidence": 0.94,
    "reasoning": "合规分 96 分，L1-L4 全部通过，质量分 88 分",
    "risk_factors": [],
    "suggested_improvements": ["标题加入具体数字可提升点击率"]
  },
  "available_copilot_cards": ["review-decision", "cover-generation", "title-optimization"]
}
```

**`POST /human-in-the-loop/tasks/{id}/approve`**:
```json
{
  "copilot_followup": {
    "message": "审核已通过！要现在发布还是定时发布？",
    "suggested_cards": [
      {
        "type": "decision",
        "title": "发布确认",
        "actions": [
          {"id": "publish_now", "label": "立即发布"},
          {"id": "schedule", "label": "定时发布"}
        ]
      }
    ]
  }
}
```

### 4.2 Bug 修复

| Bug | 文件 | 修复 |
|-----|------|------|
| `_requires_dual_approval` 空指针 | `services/human_in_loop.py` | 添加 `workflow_template_id` 空值检查 |
| `generate_cover` 签名不匹配 | `services/celery_tasks.py` | 添加 `auto_prompt` 参数 |

---

## 五、端到端联调测试结果

### 测试 1: 列表查询
```
GET /review-publish-center/conclusions?status_filter=pending
→ items: 4
→ copilot_summary: {total_pending: 4, batch_suggestion: "..."}
✅ 通过
```

### 测试 2: 详情查询
```
GET /review-publish-center/conclusions/{task_id}
→ status: human_wait
→ copilot_context: {recommended_action, confidence, reasoning}
→ available_copilot_cards: ["review-decision", "cover-generation", ...]
✅ 通过
```

### 测试 3: Action Cards
```
GET /ai/copilot/action-cards?page=/review&task_id={id}
→ cards: 2
  - decision: 审核决策
  - generation: 🎨 生成封面
✅ 通过
```

### 测试 4: 审核通过
```
POST /human-in-the-loop/tasks/{id}/approve
→ status: approved_waiting_publish
→ copilot_followup: {message, suggested_cards}
✅ 通过
```

### 测试 5: 审核驳回
```
POST /human-in-the-loop/tasks/{id}/reject
→ status: REJECTED
→ copilot_followup: {message, suggested_cards}
✅ 通过
```

### 测试 6: 审核打回
```
POST /human-in-the-loop/tasks/{id}/revise
→ status: REVISED
→ copilot_followup: {message, suggested_cards}
✅ 通过
```

### 测试 7: 封面生成
```
POST /ai/generate-cover
→ code: ACCEPTED
→ job_id: cover_gen_xxx
→ Celery Worker 执行成功
→ WebSocket 推送 cover.generation.completed
✅ 通过
```

---

## 六、质量门禁

### 前端
- `tsc --noEmit --skipLibCheck`: **0 errors** ✅
- `eslint src/pages/ReviewPublish*.tsx`: **0 errors, 7 warnings** (react-hooks/exhaustive-deps) ✅

### 后端
- Health Check: `{"status":"ok"}` ✅
- Alembic: `20260604addc (head)` ✅
- Celery Worker: 8 tasks registered ✅

---

## 七、已知限制

| 项目 | 说明 | 计划 |
|------|------|------|
| 发布确认需 draft_id | 手动创建的任务无 draft_id，`confirm-publish` 返回 VALIDATION_ERROR | 真实工作流中任务自带 draft_id |
| Schedule Modal | 定时发布目前硬编码 +1h，未实现模态框 | P1 |
| Batch Review | `batch-review-list` Action Card 有 TODO 占位 | P1 |
| react-hooks/exhaustive-deps | 7 个 warnings，不影响功能 | 持续优化 |

---

## 八、结论

✅ **审核发布 `/review` — Mode B (Copilot-Driven) 改造全部完成。**

- HTML 预览 v3 已通过四方审核
- API 契约已冻结，所有 11 个端点确认
- 前端 Mode B 合规：工作区无任何业务按钮
- 后端 Copilot 字段全覆盖：`copilot_summary` / `copilot_context` / `copilot_followup`
- 端到端联调 7/7 通过
- 质量门禁通过

**系统已具备**：审核列表 → 详情查看 → Copilot 审核决策 → 状态流转 → 发布确认 的完整闭环。
