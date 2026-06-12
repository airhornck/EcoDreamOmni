# EcoDreamOmni 演示版

> **EcoDreamOmni** = 宠物健康素人号矩阵 AI 内容管理与分发平台  
> 本演示为完整产品 UI/UX 展示，供用户体验全流程功能。

## 项目简介

基于 PRD V2.3 与详细设计文档构建的交互式前端演示，覆盖从登录→驾驶舱→内容生成→合规→发布→数据回流的完整用户旅程。

## 核心功能模块

| 模块 | 功能描述 | PRD 对应 |
|------|---------|---------|
| 🔐 登录 | 运营平台登录 | W1 |
| 📊 驾驶舱 | 今日概览(4项指标)、快捷操作、任务看板、昨日战报、智能选题、实时告警 | W8 / PRD §3 |
| ✍️ 内容库 | 内容列表管理、状态筛选、状态流转(提交审核/通过/驳回/去发布)、详情查看 | W5 |
| 🪄 AI 生成 | 输入话题+AIPL阶段+人设 → 生成图文 → 合规检测 → 互动预演 → 保存到库 | W5 / PRD §3.1 |
| 📤 发布管理 | 待发布队列、发布前二次确认、已发布列表、回流状态 | W6 |
| 👤 账号池 | 账号卡片、健康评分、生命周期、设备指纹 | W4 |
| 🔮 互动预演 | 输入内容特征，预测点赞/评论/收藏区间 + 启发式优化清单 | W9 / PRD §2.4 |
| 📈 数据分析 | 发布趋势、互动趋势、覆盖率/MAPE、内容归因、CSV导入 | W13 / PRD §2.3 |
| 🛡️ 合规中心 | 四层扫描说明、审核记录、证据链展示 | W6+W14 / PRD §2.5 |
| 🔥 趋势侦察 | 热点排行、阶段过滤、风险标注、一键生成 | W11 / PRD §2.1 |
| ⚙️ 规则中心 | L1-L4 规则 CRUD、启用/禁用、优先级管理 | W14 / PRD §2.5 |
| 🧠 技能中枢 | 四层架构展示、技能库浏览、Agent 绑定预览 | W15 / PRD §9.3 |

## 用户引导 (Onboarding)

首次访问自动触发 7 步交互式引导，覆盖：欢迎 → 导航栏 → 驾驶舱 → 内容生成 → 发布管理 → 数据回流 → 开始体验。可随时点击右上角「重新引导」重播。

## Storybook 组件库

已引入 Storybook + Vite，可独立预览所有 UI 组件：

```bash
npm run storybook    # 开发模式 http://localhost:6006
npm run build-storybook  # 构建静态站点
```

### 已有 Stories

| 分类 | 组件 |
|------|------|
| UI 原子 | Badge、Button、Card、Modal |
| 业务通用 | StatCard、StatusBadge |

## 快速开始

```bash
# 安装依赖
npm install

# 开发模式
npm run dev

# 生产构建
npm run build

# 预览构建产物
npm run preview
```

开发服务器默认运行在 http://localhost:3000

**演示账号**：`demo@ecodream.omni` / `demo123`

## 技术栈

- React 19 + TypeScript
- Vite 6
- Tailwind CSS v3
- React Router v7
- Lucide React (图标)
- Storybook 8.6 + Vite builder
- clsx + tailwind-merge

## 设计对齐

- **PRD V2.3 §3.1**：互动量预演面板（区间 + 置信度 + 启发式清单，禁止 L0-L5）
- **PRD V2.3 §3.2**：智能选题推荐（TrendScout 热点）
- **PRD V2.3 §3.3**：昨日战报（覆盖率、MAPE、区间命中）
- **PRD §2.5**：四层合规扫描（L1/L2/L3/L4）
- **PRD §2.6**：工程边界声明（导入为主、异步校准、先验宽区间）
- **详细设计 §5.5**：PlatformRule L3/L4 规则管理
- **开发计划 §9.3**：Harness / SkillHub 集成概念

## 优化记录 (v2.0)

### 布局优化
- Dashboard 统计卡片：6 列 → 4 列，gap-3 → gap-5
- 右侧栏精简：只保留昨日战报 + 实时告警
- 全局内容区增加 `max-w-6xl mx-auto` 居中约束
- 模块间距 space-y-5 → space-y-8

### 流程闭环
- 内容生成页增加「保存到内容库」按钮（localStorage）
- 内容生成页增加「保存并去发布」快捷入口
- 内容库增加状态流转操作（提交审核/通过/驳回/去发布）
- 发布页增加发布前二次确认弹窗
- 全局 Toast 反馈（保存成功/合规拦截/发布成功）

### 组件化
- 提取 7 个原子 UI 组件（Badge, Button, Card, Modal, EmptyState, SearchInput, AlertBanner）
- 提取 6+ 业务通用组件（StatCard, PageHeader, StatusBadge, PredictionResult, ComplianceResult, TaskItem）
- 引入 Storybook 独立展示

### 导航优化
- 10 项导航按业务域分组：运营中心 / 智能辅助 / 数据与配置
- 支持分组折叠展开

### 视觉升级
- 全局移除 emoji，统一 Lucide 图标
- 统计图标统一为 `text-primary`
- 快捷操作统一 `bg-secondary` 去除彩色背景

## 约束声明

- 本演示为**纯前端展示**，所有数据为本地 mock，不涉及真实后端 API。
- 所有「AI 生成」结果均为基于模板的模拟输出。
- 互动预演为基于启发式的模拟预测，非真实模型输出。
- L4 Evolved 技能展示的是设计概念，SkillSmith 引擎为 Phase 2+ 目标。
- MetaLearner、记忆联邦等 v5.0 已废弃模块未在本演示中出现。
