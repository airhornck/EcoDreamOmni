# EcoDreamOmni — Agent 协作手册

> 本文档面向所有参与本项目开发的 AI Agent 和人类开发者。
> 遵循 Simon Willison 红绿灯 TDD + Agentic Engineering 纪律。

## 1. 项目定位

**EcoDreamOmni** = 宠物健康素人号矩阵 AI 内容管理与分发平台。

- **核心能力**：AI 辅助内容生成 + 自动化发布 + 流量预测 + 合规风控
- **目标平台**：小红书、抖音、视频号
- **技术底座**：hermes-agent（AI 层）+ openclaw（SaaS 层）
- **合规红线**：100% 拦截处方药/诊断/治疗承诺；商业内容强制标注"合作/体验"

## 2. 项目结构

```
EcoDreamOmni/
├── apps/
│   ├── frontend/          # React 19 + Vite 6 + Tailwind v4 + shadcn/ui
│   └── backend/           # FastAPI + Python 3.11 + SQLAlchemy 2.0
├── packages/shared/       # 共享类型与工具（TypeScript + Python stub）
├── docker/                # Docker 配置
├── vendor/                # 开源依赖本地离线副本（25 个项目）
├── .github/workflows/     # CI/CD 质量门禁
├── AGENTS.md              # 本文档
└── TASK.md                # 当前 Sprint 原子任务分解
```

## 3. 工程纪律（Red-Green TDD）

### 3.1 红绿灯循环

```
🔴 RED   → 编写失败测试（必须看到失败，证明测试有效）
🟢 GREEN → 最小化实现使测试通过（不允许过度工程）
🔵 BLUE  → 重构，保持测试通过（测试是安全网）
```

### 3.2 质量门禁（Quality Gates）

| 门禁 | 阈值 | 工具 |
|------|------|------|
| 测试覆盖率 | ≥ 80% | vitest / pytest |
| TypeScript 类型检查 | 0 errors | tsc / mypy |
| Lint | 0 errors | eslint / ruff |
| 构建 | 必须通过 | vite build / docker build |

### 3.3 提交规范

```
feat: 新功能
fix: Bug 修复
test: 测试相关
refactor: 重构（不改变行为）
docs: 文档更新
chore: 构建/工具链
```

## 4. 技术栈速查

### 前端
- **框架**：React 19 + Vite 6
- **样式**：TailwindCSS v4 + shadcn/ui 组件模式
- **状态**：Zustand（客户端）+ TanStack Query（服务端）
- **表单**：React Hook Form + Zod
- **图表**：Recharts
- **表格**：TanStack Table
- **测试**：Vitest + React Testing Library

### 后端
- **框架**：FastAPI + Uvicorn
- **ORM**：SQLAlchemy 2.0 + Alembic
- **认证**：JWT + OAuth2 + Passlib
- **任务队列**：Celery + Redis
- **测试**：pytest + pytest-asyncio

### 基础设施
- **容器**：Docker + Docker Compose
- **数据库**：PostgreSQL 16 + Redis 7
- **监控**：Prometheus + Grafana（Phase 3）

## 5. Agent 开发规范

### 5.1 上下文隔离原则
- 每次会话只处理一个原子任务（见 TASK.md）
- 修改前读取相关 AGENTS.md / TASK.md / 测试文件
- 修改后运行相关测试，确保通过

### 5.2 证据优先
- 每个功能必须有测试覆盖
- 每个 Bug 修复必须先写复现测试
- 每次重构必须在测试保护下进行

### 5.3 需求对齐约束（强制）

> 每段需求处理前，必须加载 `docs/需求对齐约束_通用提示词.md` 作为强制检查清单。
>
> 核心规则：
> 1. **PRD 真源对齐** — Bug/需求必须与 `EcoDream_Omni_PRD_v2_对齐核心方案.md` 一致；新增/偏差需求必须先补充到 PRD
> 2. **技术架构对齐** — 修改仅维护调用关系，不涉及架构调整；涉及架构调整（新增 Router/ORM/Service）必须**暂停实施，请求用户严格审核**
> 3. **文档连锁更新** — 所有变更必须从 `docs/文档总纲.md` 可索引；同步更新数据词典 + 偏差报告
> 4. **变更记录登记** — 实施完成后在 `docs/变更记录/YYYY-MM-DD/` 按模板填写变更总结
>
> 详见：`docs/需求对齐约束_通用提示词.md`

### 5.4 禁止事项
- ❌ 不写测试直接实现功能
- ❌ 跳过红灯阶段（必须看到测试失败）
- ❌ 一次修改多个不相关的模块
- ❌ 删除或修改他人写的测试
- ❌ 修改后不更新数据词典和总纲索引
- ❌ 未按 `docs/测试检测步骤与组织协作规范.md` 执行递进式测试

## 6. 关键路径

```
W1 → W2 → W3 → W4 → W5 → W6 → W7 → W8 → W9 → W10
初始化 → 登录 → 主页 → 账号池 → 内容生成 → 合规 → 发布 → 驾驶舱 → 预测 → E2E
```

当前 Sprint：见 `TASK.md`
