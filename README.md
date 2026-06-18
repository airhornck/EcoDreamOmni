# EcoDreamOmni — 多平台账号矩阵 AI 内容管理与分发平台

> AI 辅助内容生成 · 自动化多平台发布 · 流量预测 · 合规风控

[![Stack](https://img.shields.io/badge/Frontend-React%2019%20%2B%20Vite%206%20%2B%20Tailwind%20v4-blue)](./apps/frontend)
[![Stack](https://img.shields.io/badge/Backend-FastAPI%20%2B%20SQLAlchemy%202.0%20%2B%20Celery-green)](./apps/backend)
[![Stack](https://img.shields.io/badge/Infra-Docker%20%2B%20PostgreSQL%2016%20%2B%20Redis%207-orange)](./docker)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

---

## 1. 项目简介

做矩阵运营，真正的痛苦不是想不出选题，而是选题变成内容的过程太慢、太碎、太容易出错。

一个人要管十几个账号，小红书、抖音、B站、视频号后台来回切；好不容易写出内容，又因为违禁词、虚假宣传被平台打回；数据出来了，却分散在各处，根本没法复盘。

EcoDreamOmni 把这套流程串了起来：选题洞察 → 内容生成 → 合规审核 → 多平台定时发布 → 数据复盘，全部在一个工作台里完成。

它不是为了替代运营人，而是让一个人能管住更多的号，让团队把精力放在真正重要的策略和创意上。

- **适合谁用**：品牌内容团队、MCN 机构、矩阵工作室、代运营团队
- **覆盖平台**：小红书、抖音、B站、视频号
- **技术底座**：hermes-agent（AI 层）+ openclaw（SaaS 层）
- **当前 Sprint**：V2.7.2 需求对齐版 — 详见 [`TASK.md`](./TASK.md)

### 1.1 核心能力

| 能力域 | 说明 | 代表模块 |
|--------|------|----------|
| 🧠 AI 内容生成 | 基于人设、剧本、品牌知识、平台规则生成图文/视频脚本 | ContentForge、PersonaStory、ImageForge |
| 🚀 自动化发布 | 多平台账号池管理、定时排期、一键分发 | Publisher、AccountPool、CronHub |
| 📊 流量预测 | 互动量预测、批量预测、命中率追踪 | Predictions、DataAnalyst |
| 🛡️ 合规风控 | 四层扫描拦截违禁功效宣称、虚假宣传及强监管领域敏感内容 | Compliance、PlatformRule、行业规则库 |
| 🤖 Agent 编排 | Agent 舰队、工作流引擎、Human-in-the-Loop | AgentOrchestra、WorkflowEngine |

### 1.2 合规红线

- **100% 拦截**：违禁功效宣称、虚假/夸大宣传、医疗/药品/金融等强监管领域敏感内容
- **商业内容强制标注**：必须标注「合作/体验/赞助」等声明
- **行业规则库**：可对接行业专属规则库（如兽药批文、化妆品成分等），让敏感宣称有源可溯

---

## 2. 技术栈

### 2.1 前端

- **框架**：React 19 + Vite 6
- **样式**：TailwindCSS v4 + shadcn/ui 组件模式
- **状态**：Zustand（客户端）+ TanStack Query（服务端）
- **表单**：React Hook Form + Zod
- **图表**：Recharts
- **表格**：TanStack Table
- **富文本**：TipTap
- **测试**：Vitest + React Testing Library

### 2.2 后端

- **框架**：FastAPI + Uvicorn
- **ORM**：SQLAlchemy 2.0 + Alembic
- **认证**：JWT + OAuth2 + Passlib
- **任务队列**：Celery + Redis
- **可观测性**：OpenTelemetry + Prometheus
- **测试**：pytest + pytest-asyncio

### 2.3 基础设施

- **容器**：Docker + Docker Compose
- **数据库**：PostgreSQL 16（pgvector 扩展）+ Redis 7
- **向量检索**：pgvector

---

## 3. 项目结构

```
EcoDreamOmni/
├── apps/
│   ├── frontend/          # React 19 + Vite 6 运营平台前端
│   └── backend/           # FastAPI + Python 3.11 后端服务
├── packages/shared/       # 前后端共享类型与工具
├── docker/                # Docker 配置与 override 文件
├── vendor/                # 开源依赖本地离线副本
├── docs/                  # 产品/架构/设计/评审文档（按命名规范组织）
│   ├── README.md           # 文档中心索引
│   ├── PROJECT_NAMING_CONVENTION_v1.0.md  # 文件命名规范
│   ├── 00-index/           # 总纲与索引
│   ├── 01-prd/             # 产品需求文档
│   ├── 02-architecture/    # 架构设计
│   ├── 03-design/          # 前端设计规范
│   ├── 04-requirements/    # 需求分析
│   ├── 05-development/     # 开发计划
│   ├── 06-testing/         # 测试报告
│   ├── 07-reviews/         # 评审报告
│   ├── 08-bugs/            # Bug 记录
│   ├── 09-reports/         # 分析报告
│   ├── 10-deployment/      # 部署文档
│   ├── 11-refactoring/     # 重构方案
│   ├── 12-guides/          # 操作指南
│   ├── 13-data-dictionary/ # 数据词典
│   ├── 14-process-flows/   # 流程图
│   ├── 15-policies/        # 规范约束
│   ├── 16-changelogs/      # 变更记录
│   ├── 17-outputs/         # 输出物
│   └── 99-archives/        # 归档
├── demo/                  # Storybook 组件与页面预览
├── scripts/               # 运营/测试辅助脚本
├── .github/workflows/     # CI/CD 质量门禁
├── AGENTS.md              # Agent 协作手册（必读）
├── TASK.md                # 当前 Sprint 原子任务
└── README.md              # 本文件
```

---

## 4. 快速启动

### 4.1 环境要求

| 组件 | 版本要求 | 说明 |
|------|---------|------|
| Docker Desktop | ≥ 4.20 | 必需，启动全栈服务 |
| Git Bash / PowerShell | — | Windows 推荐 |

> 项目已全面容器化，**无需在宿主机安装 Python/Node.js**。

### 4.2 一键启动

```bash
# 克隆项目后进入根目录
cd EcoDreamOmni

# 首次启动：构建镜像并启动容器
docker-compose up -d --build

# 查看启动日志
docker-compose logs -f
```

启动成功后：

| 服务 | 容器名 | 本地地址 |
|------|--------|----------|
| 前端运营平台 | ecodream-frontend | http://localhost:5173 |
| 后端 API | ecodream-backend | http://127.0.0.1:8000 |
| API 文档（Swagger） | — | http://127.0.0.1:8000/docs |
| PostgreSQL | ecodream-postgres | localhost:5432 |
| Redis | ecodream-redis | localhost:6379 |

### 4.3 注册并登录

1. 打开 Swagger：`http://127.0.0.1:8000/docs`
2. 执行 `POST /auth/register` 注册管理员账号
3. 打开前端 `http://localhost:5173` 登录

> 详细步骤、常见问题与日常开发模式选择，请参阅 [`docs/Local_Startup_Guide.md`](./docs/Local_Startup_Guide.md)。

---

## 5. 日常开发

### 5.1 常用命令

```bash
# 重启所有服务
docker-compose restart

# 停止服务（保留数据）
docker-compose down

# 彻底重置（删除数据库）
docker-compose down -v

# 查看后端日志
docker-compose logs -f backend

# 重建前端镜像
docker-compose up -d --build frontend
```

### 5.2 前端 Vite Dev 模式（热更新）

```bash
cd apps/frontend
npm install
npm run dev
# 访问 http://localhost:5173
# /api 请求自动代理到 localhost:8000
```

> 注意：Docker 前端容器与 Vite Dev Server 都占用 5173 端口，**不能同时运行**。

### 5.3 后端代码热挂载

```bash
# 使用 docker/ 下的 override 配置进行开发调试
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.override.yml up -d
```

---

## 6. 测试

### 6.1 后端测试

```bash
# 在容器内运行（推荐）
docker exec -it ecodream-backend bash
pytest -q

# 或本地运行（需 Python 3.11+）
cd apps/backend
source .venv/Scripts/activate  # Windows Git Bash
pytest -q
```

### 6.2 前端测试

```bash
cd apps/frontend
npm test -- --run

# 覆盖率报告
npm run coverage
```

### 6.3 质量门禁

| 门禁 | 阈值 | 工具 |
|------|------|------|
| 测试覆盖率 | ≥ 80% | vitest / pytest-cov |
| 类型检查 | 0 errors | tsc / mypy |
| Lint | 0 errors | eslint / ruff |
| 构建 | 必须通过 | vite build / docker build |

---

## 7. 文档导航

| 文档 | 路径 | 说明 |
|------|------|------|
| PRD 真源 | [`demo/EcoDream_Omni_PRD_v2_对齐核心方案.md`](./demo/EcoDream_Omni_PRD_v2_对齐核心方案.md) | 产品需求唯一真源 |
| 命名规范 | [`docs/PROJECT_NAMING_CONVENTION_v1.0.md`](./docs/PROJECT_NAMING_CONVENTION_v1.0.md) | 全项目文件命名与版本管理 |
| 文档中心 | [`docs/README.md`](./docs/README.md) | 文档分类索引与入口 |
| Agent 协作手册 | [`AGENTS.md`](./AGENTS.md) | 工程纪律、TDD、提交规范 |
| Cursor 规范 | [`.cursorrules`](./.cursorrules) | IDE 系统级规范提示词 |
| 前端规范 | [`apps/frontend/AGENTS.md`](./apps/frontend/AGENTS.md) | React + Tailwind 专属约定 |
| 后端规范 | [`apps/backend/AGENTS.md`](./apps/backend/AGENTS.md) | FastAPI + SQLAlchemy 专属约定 |
| 共享包规范 | [`packages/shared/AGENTS.md`](./packages/shared/AGENTS.md) | 类型契约与接口约定 |
| Sprint 任务 | [`TASK.md`](./TASK.md) | 当前 Sprint 原子任务分解 |
| 本地启动指南 | [`docs/12-guides/GUIDE-local-startup_v1.0.md`](./docs/12-guides/GUIDE-local-startup_v1.0.md) | 从 0 开始启动全栈 |
| 数据词典 | [`docs/13-data-dictionary/00-数据词典总纲.md`](./docs/13-data-dictionary/00-数据词典总纲.md) | API/Service/Store 映射 |

---

## 8. 工程纪律

本项目遵循 **Simon Willison 红绿灯 TDD** 与 **Agentic Engineering** 纪律：

```
🔴 RED   → 编写失败测试（必须看到失败，证明测试有效）
🟢 GREEN → 最小化实现使测试通过（不允许过度工程）
🔵 BLUE  → 重构，保持测试通过（测试是安全网）
```

### 提交规范

```
feat: 新功能
fix: Bug 修复
test: 测试相关
refactor: 重构（不改变行为）
docs: 文档更新
chore: 构建/工具链
```

### 关键红线

- ❌ 不写测试直接实现功能
- ❌ 修改后不更新数据词典和总纲索引
- ❌ 未遵循 `docs/PROJECT_NAMING_CONVENTION_v1.0.md` 命名规范
- ❌ Agent 直接操作数据库（静态扫描 0 违规）
- ❌ 一次修改多个不相关的模块

更多规范请阅读 [`AGENTS.md`](./AGENTS.md)、[`.cursorrules`](./.cursorrules)。

---

## 9. 关键里程碑

```
W1 → W2 → W3 → W4 → W5 → W6 → W7 → W8 → W9 → W10
初始化 → 登录 → 主页 → 账号池 → 内容生成 → 合规 → 发布 → 驾驶舱 → 预测 → E2E
```

当前阶段已完成后端 **650+ 测试用例**、前端 **29 个核心页面测试**，持续向全链路 E2E 与架构审计推进。

---

> **EcoDreamOmni** — 让每一份矩阵内容，都安全、合规、有据可依。
