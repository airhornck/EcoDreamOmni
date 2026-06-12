# EcoDreamOmni 本地启动指南

> 本文档面向开发者，介绍如何在本地完整启动 EcoDreamOmni 前后端服务进行开发与测试。
> **版本**: V2.7.2 后台页面全面调整版 | **更新日期**: 2026-05-21

---

## 1. 环境要求

| 组件 | 版本要求 | 说明 |
|------|---------|------|
| Docker Desktop | ≥ 4.20 | **必需**，用于启动 PG + Redis + Backend + Frontend |
| Git Bash / PowerShell | — | Windows 推荐 |

> 本项目已全面容器化，**不需要在宿主机安装 Python/Node.js**，所有依赖都在 Docker 镜像内。

---

## 2. 首次启动（从0开始）

### 2.1 确认修复已生效

在启动前，请确认以下修复已存在于本地代码中（V2.7.1-V3.1 部署必需的修复）：

**修复1**: `apps/backend/requirements.txt` 中包含 `email-validator>=2.2.0`

```bash
cd D:\project\EcoDreamOmni\apps\backend
grep "email-validator" requirements.txt
# 应输出: email-validator>=2.2.0
```

**修复2**: `apps/backend/src/services/compliance_engine.py` 顶部导入包含 `Optional`

```bash
cd D:\project\EcoDreamOmni\apps\backend
head -15 src/services/compliance_engine.py | grep "Optional"
# 应输出: from typing import Dict, List, Optional
```

**修复3**: `docker-compose.yml`（项目根目录）已包含 PostgreSQL 服务

```bash
cd D:\project\EcoDreamOmni
grep "ecodream-postgres" docker-compose.yml
# 应输出包含 ecodream-postgres
```

**修复4**: `apps/backend/requirements.txt` 中包含 `bcrypt==3.2.2`（passlib 兼容）

```bash
cd D:\project\EcoDreamOmni\apps\backend
grep "bcrypt" requirements.txt
# 应输出: bcrypt==3.2.2
```

**修复5**: `apps/frontend/nginx.conf` 中 API 代理尾部斜杠正确

```bash
cd D:\project\EcoDreamOmni\apps\frontend
grep "proxy_pass" nginx.conf
# 应输出: proxy_pass http://backend:8000/;   （注意末尾必须有 /）
```

**修复6**: `apps/frontend/vite.config.ts` 中包含开发代理（本地 dev 模式用）

```bash
cd D:\project\EcoDreamOmni\apps\frontend
grep "'/api'" vite.config.ts
# 应输出包含 '/api': { target: 'http://localhost:8000', changeOrigin: true }
```

如果以上任何一项缺失，请从 Git 拉取最新代码后再启动。

### 2.2 启动全栈服务

```bash
cd D:\project\EcoDreamOmni

# 首次启动（构建镜像 + 启动容器）
docker-compose up -d --build

# 查看启动进度
docker-compose logs -f
```

启动成功后，你会看到4个容器：

| 服务 | 容器名 | 本地端口 | 状态 |
|------|--------|---------|------|
| PostgreSQL | ecodream-postgres | 5432 | healthy |
| Redis | ecodream-redis | 6379 | healthy |
| Backend | ecodream-backend | 8000 | healthy |
| Frontend | ecodream-frontend | **5173** | running |

### 2.3 验证服务状态

```bash
# 查看所有容器状态
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 测试后端健康检查（直接访问后端）
curl http://localhost:8000/health
# 期望返回: {"status":"ok","version":"0.1.0"}

# 测试前端 Nginx 代理（通过前端端口访问后端 API）
curl http://localhost:5173/api/health
# 期望返回: {"status":"ok","version":"0.1.0"}

# 测试前端静态页面
curl -s -o /dev/null -w "%{http_code}" http://localhost:5173
# 期望返回: 200
```

---

## 3. 访问服务

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端 | **http://localhost:5173** | 运营平台登录页（Nginx 托管） |
| API 文档 | http://127.0.0.1:8000/docs | Swagger UI（推荐用 127.0.0.1 避免 DNS 问题） |
| 健康检查 | http://127.0.0.1:8000/health | 后端状态（直接访问） |
| 代理检查 | http://localhost:5173/api/health | 验证 Nginx → Backend 代理是否正常 |

> ⚠️ **注意**:
> 1. 如果 `localhost:8000` 无法访问，请使用 `127.0.0.1:8000`。某些浏览器/VPN 对 `localhost` 有特殊的代理处理。
> 2. **Docker 模式（`docker-compose up`）与 Vite Dev 模式（`npm run dev`）都使用 5173 端口，两者不能同时运行**。详见第5节。

---

## 4. 注册账号并登录

### 4.1 通过 Swagger UI 注册（推荐）

1. 打开 **http://127.0.0.1:8000/docs**
2. 找到 `POST /auth/register`，点击 **Try it out**
3. 填入：

```json
{
  "email": "admin@ecodream.com",
  "password": "Admin123!",
  "username": "admin",
  "role": "admin"
}
```

4. 点击 **Execute**
5. 记录返回的 `access_token`（后续 API 调用需要）

### 4.2 通过 curl 注册

```bash
curl -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@ecodream.com","password":"Admin123!","username":"admin","role":"admin"}'
```

### 4.3 登录前端

打开 **http://localhost:5173**，填入：
- **邮箱**: `admin@ecodream.com`
- **密码**: `admin123`

---

## 5. 日常开发（代码修改后重启）

### 5.0 两种开发模式的选择

| 模式 | 启动方式 | 前端端口 | 特点 | 适用场景 |
|------|---------|---------|------|---------|
| **Docker 模式** | `docker-compose up -d --build` | 5173 | Nginx 代理、生产构建、需 rebuild | 验证部署、联调完整链路 |
| **Vite Dev 模式** | `npm run dev` | 5173 | HMR 热更新、Vite 代理、无需 rebuild | 前端 UI 开发、快速迭代 |

> ⚠️ **端口冲突警告**：两种模式都占用宿主机的 **5173** 端口。**不能同时运行**。切换模式前务必停止另一种：
> ```bash
> # 停止 Docker 前端容器
> docker-compose stop frontend
>
> # 或停止 Vite dev server
> # 在运行 npm run dev 的终端按 Ctrl+C
> ```

### 5.1 Docker 模式：修改后端代码后

项目根目录的 `docker-compose.yml` 已是最新完整配置。如需后端代码热挂载（无需 rebuild），使用 `docker/` 目录下的 override 文件：

```bash
cd D:\project\EcoDreamOmni

# 方式A：完整重建（推荐，确保 nginx 配置等变更生效）
docker-compose up -d --build

# 方式B：仅热挂载后端代码（开发调试，不重建镜像）
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.override.yml up -d
# 注意：此方式使用 docker/ 目录下的配置，前端端口为 80，请访问 http://localhost
```

### 5.2 Docker 模式：修改前端代码后

前端是 Nginx 托管的生产构建，**任何代码修改（包括 `nginx.conf`）都必须重建镜像才能生效**：

```bash
cd D:\project\EcoDreamOmni

# 重建前端镜像并重启容器
docker-compose up -d --build frontend

# 验证代理是否生效
curl http://localhost:5173/api/health
```

### 5.3 Vite Dev 模式（前端快速开发）

如需 HMR 热更新：

```bash
cd D:\project\EcoDreamOmni\apps\frontend
npm run dev
# 访问 http://localhost:5173
# 此时 /api 请求由 Vite 代理到 localhost:8000
```

> 确保后端容器已在运行：`docker-compose up -d backend postgres redis`

### 5.4 完整重启所有服务

```bash
cd D:\project\EcoDreamOmni
docker-compose restart
```

---

## 6. 停止与重置

### 6.1 停止服务（保留数据）

```bash
cd D:\project\EcoDreamOmni
docker-compose down
```

### 6.2 彻底重置（删除数据库，从0开始）

```bash
cd D:\project\EcoDreamOmni
docker-compose down -v
```

> `-v` 会删除 PostgreSQL 数据卷。下次 `up` 时 PG 会重新初始化，需要重新注册账号。

### 6.3 查看日志

```bash
# 全部服务日志
docker-compose logs -f

# 仅后端日志
docker-compose logs -f backend

# 仅前端日志
docker-compose logs -f frontend

# 仅 PG 日志
docker-compose logs -f postgres
```

---

## 7. 常见问题

### Q: `docker-compose up` 后端报 `email-validator is not installed`
> `requirements.txt` 中缺少 `email-validator`。请确认本地代码已更新到最新版本（含 `email-validator>=2.2.0`）。

### Q: `docker-compose up` 后端报 `NameError: name 'Optional' is not defined`
> `src/services/compliance_engine.py` 顶部缺少 `Optional` 导入。请确认本地代码已修复：`from typing import Dict, List, Optional`。

### Q: postgres 容器报 `database files are incompatible with server`
> 旧数据卷是 PostgreSQL 15 创建的，与当前 PG 16 镜像不兼容。执行彻底重置：
> ```bash
> docker-compose down -v
> docker-compose up -d --build
> ```

### Q: 后端容器状态 `(unhealthy)`
> 健康检查需要几秒钟，启动后稍等 10-20 秒再访问。如果持续 unhealthy，查看日志：
> ```bash
> docker-compose logs -f backend
> ```

### Q: `localhost:8000/docs` 浏览器打不开，但 `curl http://127.0.0.1:8000/health` 正常
> 某些浏览器/VPN 对 `localhost` 有特殊处理。请使用 `http://127.0.0.1:8000/docs` 访问。检查代理插件（SwitchyOmega/Clash 等）是否干扰。

### Q: `curl http://localhost:5173/api/health` 返回 404，但 `curl http://127.0.0.1:5173/api/health` 正常
> **这是 Windows 上典型的 Vite Dev Server 端口劫持问题**。当 `npm run dev` 遗留的 Node 进程占用了 IPv6 的 `::1:5173` 时，`localhost` 会解析到 Vite 而非 Docker Nginx。
>
> **解决步骤**：
> 1. 查找并终止占用 5173 的 Node 进程：
>    ```bash
>    netstat -ano | grep 5173
>    taskkill //PID <Node_PID> //F
>    ```
> 2. 或直接使用 IPv4 访问：`http://127.0.0.1:5173`
> 3. 确保没有同时运行 `npm run dev` 和 `docker-compose up`

### Q: `curl http://localhost:5173/api/auth/login` 返回 `{"detail":"Not Found"}`
> 1. **确认不是 Vite Dev Server 在响应**（参见上一问的解决方案）
> 2. **确认 nginx 配置已 rebuild 生效**：修改 `nginx.conf` 后必须执行 `docker-compose up -d --build frontend`
> 3. **确认后端路由存在**：直接测试 `curl http://localhost:8000/auth/login`，如果也 404，说明后端路由未注册，检查后端是否健康
> 4. **确认请求路径正确**：Nginx 代理会去掉 `/api/` 前缀。后端路由应注册在 `/auth/login` 而非 `/api/auth/login`

### Q: `netstat` 看不到 8000 端口监听
> Windows 防火墙可能拦截了端口。以管理员身份运行 PowerShell：
> ```powershell
> netsh advfirewall firewall add rule name="EcoDream Backend" dir=in action=allow protocol=TCP localport=8000
> ```

### Q: 前端登录提示 "登录失败"
> 1. 确认后端已启动：`curl http://127.0.0.1:8000/health`
> 2. 确认账号已注册（容器重启后内存用户会丢失，需重新注册）
> 3. 确认输入的邮箱和密码正确

### Q: 容器重启后需要重新注册账号
> 正常现象。当前后端用户是内存存储（MVP 阶段），容器重启后数据丢失。重新注册即可。生产环境会迁移到 PostgreSQL 持久化。

### Q: 前端页面显示 "暂无数据" 但后端已正常启动
> 1. 确认前端 Store 中的 API URL 与后端路由一致。V2.7.2 重构后统一了部分路由前缀（如 `/api/stories` → `/api/persona-stories`）
> 2. 打开浏览器开发者工具 Network 面板，检查 API 请求是否 404
> 3. 如 404，对照本文档第 9 节确认端点是否存在，或检查后端日志确认路由是否注册

### Q: 趋势侦察/数据报表/预测中心页面图表不显示
> 1. 确认后端对应的数据分析 API 已返回数据（如 `/api/data-analyst/publish-trend`）
> 2. 这些页面的图表依赖后端 stub 数据，首次加载时可能为空，属于正常现象
> 3. 导入实际 CSV 数据后，数据报表页面的图表会自动填充

---

## 8. 测试

### 8.1 前提条件

确保 PG 容器在运行：

```bash
docker ps | grep ecodream-postgres
```

### 8.2 运行后端测试

```bash
# 进入后端容器运行测试（推荐，环境一致）
docker exec -it ecodream-backend bash
pytest -q

# 或本地运行（需 Python 3.11+ 和虚拟环境）
cd D:\project\EcoDreamOmni\apps/backend
. .venv/Scripts/activate
pytest -q
```

**当前测试基线**: `后端 650+ passed, 前端 29 新测试覆盖核心页面`

### 8.3 运行前端测试

```bash
cd D:\project\EcoDreamOmni\apps/frontend
npm test -- --run
```

**前端测试覆盖**：Dashboard / TaskHub / ContentForge / AccountPool / Compliance / Publisher 6 个核心页面，共 29 个用例。

---

## 9. 关键 API 端点速查

### 9.1 核心业务模块

| 模块 | 端点前缀 | 说明 |
|------|---------|------|
| Auth | `/auth/*` | 登录/注册/Token刷新 |
| Dashboard | `/dashboard/*` | 首页数据、核心指标、活动日志 |
| TaskHub | `/task-hub/*` | 任务全生命周期、DLQ、批量操作 |
| ContentForge | `/content-drafts`, `/content-generate` | 内容生成与草稿管理 |
| Compliance | `/compliance/*` | 四层风控扫描、规则库、扫描历史 |
| Publisher | `/publish-tasks/*` | 多平台分发、排期、执行 |
| Predictions | `/predictions/*` | 互动量预测、批量预测、命中率追踪 |
| TrendScout | `/trend-scout/*` | 趋势报告、选题库、热词监控 |
| DataAnalyst | `/data-analyst/*` | 数据报表、趋势分析、归因、模型校准 |
| CommentHub | `/comment-hub/*` | 评论管理 |
| ContentSeries | `/content-series/*` | 内容系列化 |
| ImageForge | `/image-forge/*` | 图片配置引擎 |

### 9.2 账号与人设模块

| 模块 | 端点前缀 | 说明 |
|------|---------|------|
| AccountPool | `/account-pool/*` | 素人矩阵账号管理、健康度、Persona绑定 |
| PersonaPool | `/personas/*` | 人设池 CRUD |
| PersonaStory | `/persona-stories/*` | 剧本CRUD、节点编排、情感曲线、内容绑定 |

### 9.3 系统治理模块

| 模块 | 端点前缀 | 说明 |
|------|---------|------|
| SkillHub | `/skills/*`, `/agent-skills/*` | 技能注册、Agent绑定、执行测试 |
| AgentOrchestra | `/agents/*`, `/workflows/*`, `/pipelines/*` | Agent舰队、工作流、流水线 |
| LLM Hub | `/llm-hub/*` | 模型管理、应用范围、成本看板、调用日志 |
| WorkflowEngine | `/workflow-engine/*` | 工作流模板、执行监控 |
| Workflow Visual | `/workflow-visual/*` | Workflow可视化配置 |
| CronHub | `/cron-hub/*` | 定时任务、执行历史、死信队列 |
| Human-in-the-Loop | `/human-in-loop/*` | 审核台 |

### 9.4 基础功能模块

| 模块 | 端点前缀 | 说明 |
|------|---------|------|
| AssetPool | `/assets/*` | 素材库 |
| BrandKnowledge | `/brand-knowledge/*` | 品牌知识 |
| VetDrugDB | `/vetdrug/*` | 兽药批文、功效宣称校验 |
| TimelineLibrary | `/timeline/*` | 时间线事件库 |
| PlatformRule | `/platform-rules/*` | 平台规则 |

### 9.5 前端页面与路由对照

| 页面 | 路由 | 状态 |
|------|------|------|
| 驾驶舱 | `/dashboard` | ✅ 重构完成（5指标卡+4快捷操作+智能选题+告警+Agent状态+故事线+趋势图+命中率饼图） |
| 任务中心 | `/task-hub` | ✅ 重构完成（Tab切换+任务列表+系列规划+DLQ+抽屉新建） |
| 内容锻造 | `/content-forge` | ✅ 重构完成（三栏布局+配置/预览/Agent摘要+合规高亮） |
| 趋势侦察 | `/trend-scout` | ✅ 重构完成（趋势报告+选题库+热搜监控） |
| 互动预演 | `/predictions` | ✅ 重构完成（单条/批量预测+历史+命中率追踪） |
| 合规审核 | `/compliance` | ✅ 重构完成（四层统计+单条/批量扫描+历史+规则库） |
| 发布管理 | `/publisher` | ✅ 重构完成（列表/日历视图+草稿选择+内容预览） |
| 数据报表 | `/data-analyst` | ✅ 重构完成（4指标+4图表+排行榜+账号对比+导入+校准） |
| 账号池 | `/account-pool` | ✅ 重构完成（卡片列表+详情抽屉+统计看板） |
| 人设池 | `/personas` | ✅ 增强完成（情感曲线图+冲突检测+活跃指示） |
| 技能中心 | `/skillhub` | ✅ 风格统一（PageHeader+统计看板+搜索+Agent下拉） |
| Agent编排 | `/agent-orchestra` | ✅ 风格统一（PageHeader+统计看板+详情展开+步骤可视化） |
| LLM驾驶舱 | `/llm-cockpit` | ✅ 重构完成（模型/范围/成本/日志 4标签页） |
| 工作流驾驶舱 | `/workflow-cockpit` | ✅ 风格统一（Kanban+模板+执行监控） |
| 定时任务 | `/cron-cockpit` | ✅ 风格统一（统计看板+下次执行时间+状态筛选） |
| 品牌知识 | `/brand-knowledge` | ✅ 新增完成 |
| 时间线 | `/timeline` | ✅ 新增完成 |
| 兽药库 | `/vetdrug` | ✅ 新增完成 |
| 素材库 | `/assets` | ✅ 已有 |
| 平台规则 | `/platform-rules` | ✅ 已有 |
| 审核台 | `/human-in-the-loop` | ✅ 已有 |
| 系统设置 | `/settings` | ✅ 已有 |
| 登录 | `/login` | ✅ 已有 |

---

> 本文档与项目代码同步维护。Sprint V2.7.2 后台页面全面调整版测试基线：`后端 650+ passed, 前端 29 新测试覆盖核心页面`。
