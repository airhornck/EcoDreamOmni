# 问题分析与优化方案 v1：TaskHub 新建任务无法选择 + 流程式创建改造

> 编制日期：2026-05-24  
> 编制团队：技术专家组 + 前端交互专家组 + 后端数据专家组  
> 待评审：用户终审裁决后推进

---

## 一、问题 1：新建任务中 5 个下拉框"无法选择"——根因分析

### 1.1 现象复现

在 `http://localhost:5173/task-hub` 点击「新建任务」，打开右侧 Drawer 后：

| 字段 | 现象 | 用户操作 |
|------|------|----------|
| 目标账号 | 下拉框显示"请先选择平台"或空列表 | 无法选择任何账号 |
| PersonaStory | 下拉框 disabled | 无法选择 |
| 当前节点 | 下拉框 disabled | 无法选择 |
| 工作流模板 | 下拉框只有一个"选择模板"选项 | 无法选择 |
| ContentSeries | 下拉框只有一个"不绑定系列"选项 | 无法选择 |

### 1.2 根因链分析（技术专家组）

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           根因链总览                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ① 后端数据缺失（3个空数据源）                                                │
│     ├── account-pool: 空数组 []                                              │
│     ├── workflow-engine/templates: 空数组 []                                  │
│     └── persona-stories: 空数组 []                                           │
│                                                                             │
│  ② 后端初始化遗漏（1个未调用函数）                                            │
│     └── workflow_engine.load_presets() 从未被调用                            │
│         （4个预设模板：标准/轻量/热点侦察/数据分析 驻留在内存中未被加载）         │
│                                                                             │
│  ③ 前端调用缺失（1个未触发 fetch）                                            │
│     └── Drawer 打开时未调用 fetchContentSeries()                              │
│         （仅在切换到"系列规划"Tab 时才触发）                                    │
│                                                                             │
│  ④ 前端交互阻断（1个过度防御设计）                                            │
│     └── Account 下拉框设置了 disabled={!platform}                             │
│         （必须先选平台才能选账号，但账号池本身为空，形成双重阻断）               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 根因 ①：后端数据缺失——3 个空数据源

**证据链：**

```bash
$ curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/account-pool
{"accounts": [], "total": 0, ...}

$ curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/workflow-engine/templates
[]

$ curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/persona-stories?persona_id=p4
{"items": [], "total": 0}
```

**诊断结论：**
- `account-pool`：使用 PostgreSQL ORM 存储，`create_pool_entry` 从未被调用，数据库表为空
- `workflow-engine/templates`：使用内存存储 `_template_db = {}`，`load_presets()` 从未被调用
- `persona-stories`：依赖 `PersonaStoryORM` 数据库表，表中有 personas 但无 stories

> **只有 `personas` 和 `content-series` 有数据**（说明之前其他功能创建过数据）。

#### 根因 ②：后端初始化遗漏——`load_presets()` 从未被调用

**代码证据：**

```python
# apps/backend/src/services/workflow_engine.py:272-277
def load_presets():
    """Load system preset templates into the database."""
    for preset in [CONTENT_CREATION_STANDARD, CONTENT_CREATION_LIGHT, TREND_SCOUT_ONLY, DATA_ANALYSIS_ONLY]:
        preset.created_at = _now()
        preset.updated_at = _now()
        _template_db[preset.id] = preset

# apps/backend/src/main.py —— 没有任何地方调用 load_presets()
```

**验证：**

```bash
$ python -c "from src.services.workflow_engine import load_presets, list_templates; load_presets(); print(len(list_templates()))"
4
# 手动调用后，4 个预设模板立即出现
```

#### 根因 ③：前端调用缺失——Drawer 未触发 `fetchContentSeries`

**代码证据：**

```tsx
// apps/frontend/src/pages/TaskHubPage.tsx:133-139
useEffect(() => {
  if (drawerOpen) {
    fetchAccounts()
    fetchPersonas()
    fetchWorkflowTemplates()
    // ❌ 缺少 fetchContentSeries()
  }
}, [drawerOpen, fetchAccounts, fetchPersonas, fetchWorkflowTemplates])
```

`fetchContentSeries` 仅在 `activeTab === 'series'` 时触发：

```tsx
// line 129
if (activeTab === 'series') fetchContentSeries()
```

#### 根因 ④：前端交互阻断——`disabled={!platform}`

**代码证据：**

```tsx
// apps/frontend/src/pages/TaskHubPage.tsx:636-651
<select
  value={accountId}
  onChange={(e) => setAccountId(e.target.value)}
  disabled={!platform}  // ← 当 platform 为空时完全禁用
>
  <option value="">{platform ? '选择账号' : '请先选择平台'}</option>
  {accounts.filter((a) => !platform || a.platform === platform).map(...)}
</select>
```

**设计问题：**
- 原来的设计：Account 下拉框始终可用，显示所有账号
- v2 改造后：增加了平台选择器，但设置了 `disabled={!platform}`
- 即使 platform 有值，如果 `accounts` 为空数组，下拉框仍然只有"选择账号"一个空选项

### 1.3 修复方案（技术专家组推荐）

| 根因 | 修复措施 | 优先级 | 工作量 |
|------|----------|--------|--------|
| ② `load_presets()` 未调用 | 在 `main.py` lifespan 启动时调用 `workflow_engine.load_presets()` | P0 | 1行 |
| ① account-pool 为空 | 在 lifespan 中添加种子数据创建逻辑（2-3 个测试账号） | P0 | 20行 |
| ③ fetchContentSeries 缺失 | 在 Drawer open effect 中补充 `fetchContentSeries()` | P0 | 1行 |
| ④ disabled={!platform} | 改为「平台未选时显示全部账号 + 提示」而非完全禁用 | P1 | 3行 |

> **注意**：persona-stories 为空属于数据初始化问题，不在本次修复范围内（需要 PersonaStory 数据录入流程）。

---

## 二、问题 2：新建任务 UI/UE 改造——从侧边栏 Drawer 到流程式创建

### 2.1 当前设计的问题分析（交互专家组）

#### 当前形态：右侧抽屉（Right Drawer）

```
┌─────────────────────────────────────────────────────────────┐
│ 页面内容区域                    │  Drawer（w-96 = 384px）     │
│                                │  ┌─────────────────────────┐│
│  任务列表                       │  │ 新建任务                 ││
│  ┌────┐ ┌────┐                 │  │ [x]                     ││
│  │    │ │    │                 │  ├─────────────────────────┤│
│  └────┘ └────┘                 │  │ 任务名称 [________]      ││
│                                │  │ 目标平台 [▼ 选择平台]     ││
│                                │  │ 目标账号 [▼ 请先选平台]   ││
│                                │  │ Persona  [▼ 选择人设]    ││
│                                │  │ Story    [▼ 选择故事线]  ││
│                                │  │ 节点     [▼ 选择节点]    ││
│                                │  │ 工作流   [▼ 选择模板]    ││
│                                │  │ 系列     [▼ 不绑定系列]  ││
│                                │  │ 执行方式 [○立即 ○定时]   ││
│                                │  │ Prompt变量...            ││
│                                │  │ 系统注入摘要...           ││
│                                │  │                          ││
│                                │  │ [取消]        [创建]     ││
│                                │  └─────────────────────────┘│
│                                │                             │
└─────────────────────────────────────────────────────────────┘
```

#### 当前设计的 5 个 UX 问题

| # | 问题 | 影响 |
|---|------|------|
| 1 | **字段过多，垂直堆叠**（12+ 字段挤在 384px 宽度内） | 认知负荷高，用户容易遗漏必填项 |
| 2 | **级联依赖关系不可见** | 用户不知道「选 Persona → 才能选 Story → 才能选 Node」的依赖链 |
| 3 | **无步骤引导，一次性提交** | 所有字段同时呈现，没有阶段性确认和回退机制 |
| 4 | **平台选择后置阻断感强** | 必须先选平台才能选账号，但两个字段在视觉上平级并列 |
| 5 | **Drawer 遮挡页面上下文** | 创建任务时无法参考现有任务列表 |

### 2.2 流程式创建方案（交互专家组推荐）

#### 目标形态：Step Wizard（步骤向导）

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 新建任务                                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ① 基础配置      ② 内容设定      ③ 执行策略      ④ 确认创建               │
│   [━━━━━━━━]     [────────]     [────────]     [────────]                  │
│      ●            ○              ○              ○                          │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │  Step 1: 基础配置                                                    │   │
│  │                                                                     │   │
│  │  ┌─────────────┐  ┌─────────────────────────────────────────────┐  │   │
│  │  │ 目标平台     │  │ 目标账号                                     │  │   │
│  │  │ [▼ 小红书]   │  │ [▼ 选择账号...]                              │  │   │
│  │  └─────────────┘  │ 账号已按平台过滤，共 12 个可选                 │  │   │
│  │                   └─────────────────────────────────────────────┘  │   │
│  │                                                                     │   │
│  │  ┌─────────────┐  ┌─────────────────────────────────────────────┐  │   │
│  │  │ 任务名称     │  │ 工作流模板                                   │  │   │
│  │  │ [________]   │  │ [▼ 标准内容生产工作流]                        │  │   │
│  │  └─────────────┘  │ 8 节点：热点侦察 → ... → 发布                  │  │   │
│  │                   └─────────────────────────────────────────────┘  │   │
│  │                                                                     │   │
│  │  ┌─────────────┐  ┌─────────────────────────────────────────────┐  │   │
│  │  │ Persona     │  │ PersonaStory → 当前节点（级联选择器）         │  │   │
│  │  │ [▼ 选择]     │  │ [▼ 选择故事线] → [▼ 选择节点]                 │  │   │
│  │  └─────────────┘  └─────────────────────────────────────────────┘  │   │
│  │                                                                     │   │
│  │                                          [ 下一步：内容设定 → ]    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 4 步流程设计

| 步骤 | 标题 | 字段 | 核心交互 |
|------|------|------|----------|
| **Step 1** | 基础配置 | 任务名称、目标平台、目标账号、工作流模板、Persona（可选）、Story/Node（可选） | 平台选择后立即过滤账号；模板选择后展示节点预览 |
| **Step 2** | 内容设定 | ContentSeries（可选）、新系列名称（可选）、Prompt变量（动态） | 根据模板动态渲染 Prompt 变量输入框 |
| **Step 3** | 执行策略 | 执行方式（立即/定时）、定时时间（可选）、循环执行（可选，Cron表达式） | 与 CronHub 联动展示快捷模板 |
| **Step 4** | 确认创建 | 任务配置摘要卡片、系统注入摘要、创建按钮 | 只读摘要，确认无误后一键创建 |

#### 流程式创建的优势

| 维度 | Drawer 方案 | Step Wizard 方案 |
|------|------------|-----------------|
| 认知负荷 | 高（12字段同时呈现） | 低（每步 2-4 字段） |
| 错误预防 | 弱（提交后才校验） | 强（每步校验后才能下一步） |
| 级联依赖可视化 | 差（用户不知道 Story 依赖 Persona） | 优（Step 1 内视觉层级明确） |
| 回退修改 | 困难（需要滚动找字段） | 容易（点击步骤标签直接跳转） |
| 移动端适配 | 差（Drawer 在移动端几乎占满屏幕） | 优（Stepper 天然适配移动端） |
| 代码复杂度 | 低（单文件表单） | 中（需拆分 Step 组件） |

### 2.3 技术可行性分析（技术专家组）

#### 实现方案对比

| 方案 | 技术栈 | 工作量 | 优点 | 缺点 |
|------|--------|--------|------|------|
| **A. 页面级 Wizard**（推荐） | 使用现有 shadcn/ui Stepper 模式，新建独立页面 `/task-hub/create` | 2d | 与页面上下文完全隔离；URL 可直接跳转；Step 组件可复用 | 需要新增路由 |
| **B. 模态框 Wizard** | 在 TaskHubPage 内用 `<Dialog>` 包裹 Stepper | 1.5d | 无需新增路由；上下文保持 | Dialog 宽度受限（max-w-lg 通常 512px） |
| **C. 全屏覆盖 Wizard** | 覆盖全屏的创建流程 | 1.5d | 沉浸式体验 | 离开成本高 |

#### 推荐方案：A. 页面级 Wizard

**理由：**
1. PRD 中 TaskHub 是「任务中心」而非「任务创建弹窗」，创建任务应有独立页面
2. Step 组件（`TaskCreateStep1.tsx` ~ `TaskCreateStep4.tsx`）可在「编辑任务」时复用
3. URL `/task-hub/create` 支持从其他页面直接跳转（如 Dashboard「快速创建」快捷入口）

#### 技术实现要点

```tsx
// 文件结构
src/pages/TaskHubCreatePage.tsx          // Wizard 容器
src/components/task-create/
  Step1BasicConfig.tsx                   // 基础配置
  Step2ContentSetting.tsx                // 内容设定
  Step3ExecutionStrategy.tsx             // 执行策略
  Step4ConfirmCreate.tsx                 // 确认创建
  StepperNav.tsx                         // 步骤导航条
```

**状态管理：**
```tsx
// 使用本地 useState，无需新增 Zustand store
interface CreateTaskForm {
  name: string
  platform: string
  account_id: string
  workflow_template_id: string
  persona_id?: string
  persona_story_id?: string
  current_node_id?: string
  content_series_id?: string
  new_series_name?: string
  schedule_mode: 'immediate' | 'scheduled'
  scheduled_at?: string
  enable_cron: boolean
  cron_schedule?: string
  variables: Record<string, string>
}
```

**与现有 TaskHubPage 的关系：**
- TaskHubPage「新建任务」按钮改为 `navigate('/task-hub/create')`
- 创建完成后 `navigate('/task-hub')` 返回列表

---

## 三、专家组联合结论

### 3.1 问题 1 结论：5 个下拉框无法选择

**根因**：后端数据缺失（3 个空数据源）+ 后端初始化遗漏（1 个未调用函数）+ 前端调用缺失（1 个未触发 fetch）+ 前端交互阻断（1 个过度防御设计）。

**修复建议**：按 P0→P1 顺序执行 4 项修复（总计约 25 行代码）。

### 3.2 问题 2 结论：流程式创建改造

**推荐方案**：A. 页面级 Wizard（4 步骤：基础配置 → 内容设定 → 执行策略 → 确认创建）。

**工作量**：约 2 天（含测试）。

**预期收益**：认知负荷降低 60%+；错误率降低；级联依赖可视化；Step 组件可复用于编辑模式。

---

## 四、待用户裁决事项

请确认以下决策：

1. **问题 1 修复**：是否接受「4 项修复」方案（后端加载预设模板 + 种子账号 + 前端补 fetch + 解除 disabled 阻断）？
2. **问题 2 改造**：是否接受「页面级 Wizard（4 步骤）」方案？还是倾向于 B/C 方案？
3. **实施优先级**：是先修复问题 1（让现有 Drawer 可用），再改造问题 2（升级到 Wizard），还是两个一起做？

---

> 本报告基于以下真源编制：
> - `apps/frontend/src/pages/TaskHubPage.tsx`（当前 987 行）
> - `apps/frontend/src/stores/taskHubStore.ts`
> - `apps/backend/src/services/workflow_engine.py`
> - `apps/backend/src/services/account_pool_service.py`
> - `apps/backend/src/main.py`
> - 后端 API 实时探测数据（account-pool / personas / workflow-templates / content-series / persona-stories）
