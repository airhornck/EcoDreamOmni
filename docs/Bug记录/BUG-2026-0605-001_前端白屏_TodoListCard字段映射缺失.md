# BUG-2026-0605-001：前端白屏 — Dashboard `TodoListCard` 字段映射缺失导致 `.toLocaleString()` 崩溃

> **发现日期**: 2026-06-05  
> **修复日期**: 2026-06-05  
> **严重级别**: 🔴 P0 — 阻断性（页面完全不可用）  
> **影响范围**: 前端 Dashboard 首页（`/` 路由）  
> **修复者**: Kimi Code CLI  
> **状态**: ✅ 已修复

---

## 一、现象描述

访问 `http://localhost:5173/` 后，页面**一闪后持续白屏**，控制台报错：

```
Uncaught TypeError: Cannot read properties of undefined (reading 'toLocaleString')
    at index-xxx.js:12:44941
    at Array.map (<anonymous>)
```

错误堆栈中包含 `QueryClientProvider` → `setData` → `fetch` 链路，确认是 React Query 数据获取成功后，组件渲染阶段抛出异常。

---

## 二、复现条件

1. 前端开发服务器正常启动（`vite dev`，端口 5173）
2. 后端 `/api/trend-scout/topics?limit=5` 接口返回数据中包含 `estimated_engagement` 字段
3. 用户已登录（`localStorage` 中存在有效 `token`）
4. 路由命中 Dashboard 首页 `/`

**复现率**: 100%（只要后端返回的 topic 数据中 `estimated_engagement` 字段存在但 `estimatedEngagement` 不存在）

---

## 三、根因分析

### 3.1 直接原因

`DashboardPage/TodoListCard.tsx` 第 78 行直接访问 `topic.estimatedEngagement.toLocaleString()`，但该值为 `undefined`：

```tsx
// TodoListCard.tsx (修复前)
<div className="text-sm font-semibold text-primary">
  {topic.estimatedEngagement.toLocaleString()}  {/* ← undefined.toLocaleString() 💥 */}
</div>
```

### 3.2 根本原因 — 前后端字段名不一致 + 数据层未做映射

| 层级 | 字段名 | 说明 |
|------|--------|------|
| **后端 API** | `estimated_engagement` | 蛇形命名，返回给前端 |
| **前端 TypeScript 类型** | `estimatedEngagement` | 驼峰命名，组件层消费 |
| **数据查询层** | ❌ 未映射 | `useDashboardQueries.ts` 直接将原始数据透传，未做字段转换 |

数据流向：

```
后端 /api/trend-scout/topics
  ↓ 返回 { topics: [{ id, title, estimated_engagement, tags }] }
useDashboardQueries.ts (useDashboardSmartTopics)
  ↓ 直接返回 res.topics，未转换字段名
TodoListCard.tsx
  ↓ topic.estimatedEngagement = undefined
  ↓ .toLocaleString() → TypeError → React 渲染崩溃 → 白屏
```

### 3.3 关联风险

同页面其他组件也存在类似**未做空值保护**的数值字段访问：

- `AgentStatusCard.tsx`: `status.activeAgents`、`status.pendingMessages`、`status.successRate1h` — 后端数据缺失时显示为空或 `NaN%`
- `authStore.ts`: `JSON.parse(storedUser)` — localStorage 数据损坏时模块级崩溃
- `api.ts`: `localStorage.getItem()` / `crypto.randomUUID()` — 隐私模式或不安全上下文下可能抛异常

---

## 四、影响评估

| 维度 | 影响 |
|------|------|
| **用户体验** | Dashboard 首页完全无法访问，所有用户登录后白屏 |
| **功能影响** | 工作台、智能选题推荐、异常告警、Agent 状态等 Dashboard 全部模块不可见 |
| **数据安全** | 无数据丢失风险，仅渲染层崩溃 |
| **业务连续性** | 阻断性，必须立即修复 |

---

## 五、修复方案

### 5.1 方案选择

采用**「防御式编程 + 数据层字段映射」**双管齐下：

1. **组件层兜底**（短线防御）：所有数值字段访问加 `?? 0` 空值保护
2. **数据层映射**（长线根治）：Query Hook 中统一做蛇形→驼峰字段映射，确保类型契约与运行时数据一致

### 5.2 修改文件清单

| # | 文件路径 | 修改类型 | 修复内容 |
|---|---------|---------|---------|
| 1 | `src/pages/DashboardPage/TodoListCard.tsx` | 防御式修复 | `topic.estimatedEngagement.toLocaleString()` → `(topic.estimatedEngagement ?? 0).toLocaleString()` |
| 2 | `src/hooks/useDashboardQueries.ts` | 根治修复 | `useDashboardSmartTopics` 中增加 `estimated_engagement → estimatedEngagement` 字段映射 |
| 3 | `src/pages/DashboardPage/AgentStatusCard.tsx` | 防御式修复 | `activeAgents`、`pendingMessages`、`successRate1h` 加 `?? 0` 兜底 |
| 4 | `src/stores/authStore.ts` | 防御式修复 | `JSON.parse(storedUser)` 封装为 `safeParseUser`，异常时清除损坏数据 |
| 5 | `src/lib/api.ts` | 防御式修复 | `localStorage.getItem()` / `crypto.randomUUID()` 加 try-catch |

### 5.3 关键代码 Diff

#### 修复 1：TodoListCard.tsx（组件层兜底）

```diff
- {topic.estimatedEngagement.toLocaleString()}
+ {(topic.estimatedEngagement ?? 0).toLocaleString()}
```

#### 修复 2：useDashboardQueries.ts（数据层映射）

```diff
  export function useDashboardSmartTopics() {
    return useQuery({
      queryKey: dashboardKeys.smartTopics(),
      queryFn: async () => {
-       const res = await apiClient<{ topics: SmartTopic[] }>(
+       const res = await apiClient<{
+         topics: Array<{
+           id: string;
+           title: string;
+           estimated_engagement?: number;
+           estimatedEngagement?: number;
+           tags?: string[];
+         }>;
          >("/trend-scout/topics?limit=5");
-       return res.topics ?? [];
+       return (res.topics ?? []).map((t) => ({
+         id: t.id,
+         title: t.title,
+         estimatedEngagement: t.estimated_engagement ?? t.estimatedEngagement ?? 0,
+         tags: t.tags ?? [],
+       }));
      },
    });
  }
```

#### 修复 3：authStore.ts（localStorage 安全解析）

```diff
+ function safeParseUser(raw: string | null) {
+   if (!raw) return null
+   try {
+     return JSON.parse(raw) as AuthState['user']
+   } catch {
+     localStorage.removeItem('user')
+     return null
+   }
+ }

  export const useAuthStore = create<AuthState>((set) => ({
    // ...
-   user: storedUser ? JSON.parse(storedUser) : null,
+   user: safeParseUser(storedUser),
```

---

## 六、验证步骤

1. [x] 清除浏览器缓存 / 无痕模式打开 `http://localhost:5173/`
2. [x] 确认页面正常渲染，Dashboard Bento Grid 布局可见
3. [x] 确认「智能选题推荐」卡片正常显示，预估互动量数字正确格式化
4. [x] 确认浏览器控制台无红色报错
5. [x] 确认 `npm run build` 构建通过，TypeScript 0 errors

---

## 七、预防措施

### 7.1 编码规范（新增）

1. **数值字段强制兜底**：所有从 API 获取的数值在渲染前必须做 `?? 0` 保护
   ```tsx
   // ❌ 禁止
   {value.toLocaleString()}
   
   // ✅ 必须
   {(value ?? 0).toLocaleString()}
   ```

2. **Date 字段强制校验**：所有 `new Date(apiValue)` 前校验字段存在性
   ```tsx
   // ✅ 必须
   {apiValue ? new Date(apiValue).toLocaleString() : '—'}
   ```

3. **数据层字段映射标准化**：Query Hook 层必须统一处理蛇形→驼峰命名转换，禁止将原始 API 数据直接透传给组件

4. **localStorage 安全读取**：所有 `localStorage.getItem() + JSON.parse()` 必须封装为安全函数

### 7.2 检查清单（Code Review 新增项）

- [ ] 新增/修改的组件中，所有从 props 或 API 获取的数值字段是否有空值保护？
- [ ] 新增/修改的 Query Hook 中，是否对后端返回的字段名做了映射转换？
- [ ] 是否引入了新的 `localStorage` 读取逻辑？是否有异常处理？
- [ ] Dashboard 相关组件修改后，是否在**后端 API 未启动**或**返回空数据**的场景下验证过？

### 7.3 工程化建议（中长期）

1. **引入运行时类型校验**：在 `apiClient` 层集成 `zod` 或 `valibot`，对 API 响应做运行时校验，早发现字段缺失/类型不匹配
2. **统一前后端命名规范**：全链路统一使用驼峰命名（前端主导），或后端统一返回驼峰（推荐）
3. **E2E 测试覆盖**：增加「后端 API 返回最小可用数据」场景的 E2E 测试，确保字段缺失时前端不崩溃

---

## 八、经验教训

1. **TypeScript 类型≠运行时安全**：即使 `SmartTopic` 接口声明了 `estimatedEngagement: number`，运行时后端可能返回不同字段名，TypeScript 无法拦截。
2. **数据层是字段映射的最佳位置**：在 Query Hook 层做字段转换，比在每个组件中做防御更集中、更可维护。
3. **白屏 = 渲染期崩溃**：React 应用白屏几乎总是「渲染阶段抛异常」，优先检查 `.map()` 遍历中的字段访问。
4. **Dashboard 是首屏高频路径**：任何影响 Dashboard 的 bug 都是 P0 级，因为所有用户登录后的第一页就是这里。

---

## 九、关联文档

| 文档 | 位置 | 说明 |
|------|------|------|
| **数据词典 — 前端 Store 与路由** | `docs/数据词典_v4.0/04-前端Store与路由.md` | Dashboard Store → API 映射定义 |
| **API 接口契约** | `docs/契约与数据/01-API接口契约.md` | `/trend-scout/topics` 接口契约 |
| **工程纪律 v4.0** | `docs/工程纪律_v4.0.md` | 编码规范与架构红线 |
| **前端设计总纲** | `docs/前端设计/00-前端设计总纲.md` | Dashboard Bento Grid 布局设计 |

---

*最后更新: 2026-06-05*  
*修复提交: 5 文件修改，1 目录新增（Bug记录/）*
