# EcoDreamOmni — 前端开发规范（AGENTS.md）

> 本文档面向在 `apps/frontend/` 目录工作的 AI Agent 和人类开发者。
> 与根目录 `AGENTS.md` 互补，侧重前端专属技术约定。

---

## 1. 技术栈速查

| 层级 | 技术 | 版本 |
|------|------|------|
| 框架 | React | 19 |
| 构建工具 | Vite | 6 |
| 样式 | TailwindCSS | v4 |
| 组件库 | shadcn/ui | 最新 |
| 状态（客户端）| Zustand | 最新 |
| 状态（服务端）| TanStack Query | 最新 |
| 表单 | React Hook Form | 最新 |
| 校验 | Zod | 最新 |
| 图表 | Recharts | 最新 |
| 表格 | TanStack Table | 最新 |
| 路由 | React Router | v6 |
| 测试 | Vitest + React Testing Library | 最新 |
| 类型检查 | TypeScript | 5.x |
| Lint | ESLint | 9.x (flat config) |

---

## 2. 代码风格规范

### 2.1 组件规范

```typescript
// ✅ 正确：函数组件 + 显式返回类型 + interface Props
interface UserCardProps {
  userId: string;
  onSelect: (id: string) => void;
}

export function UserCard({ userId, onSelect }: UserCardProps): JSX.Element {
  const { data, isLoading } = useUserQuery(userId);
  
  if (isLoading) return <Skeleton className="h-20 w-full" />;
  
  return (
    <Card onClick={() => onSelect(userId)}>
      <CardHeader>{data.name}</CardHeader>
    </Card>
  );
}

// ❌ 错误：类组件、隐式返回、type Props
```

### 2.2 文件组织

```
src/
├── api/                    # API 调用层（TanStack Query hooks）
├── components/
│   ├── ui/                 # shadcn/ui 基础组件（只复制不改源码）
│   ├── layout/             # 布局组件（Header, Sidebar, WorkspaceLayout）
│   ├── ai-copilot/         # AI Copilot 相关组件
│   ├── dashboard/          # Dashboard 专属组件
│   └── lab/                # 实验室相关组件
├── hooks/                  # 自定义 Hooks
├── lib/                    # 工具函数、配置、常量
├── pages/                  # 页面级组件（与路由一一对应）
│   ├── DashboardPage/
│   │   ├── hooks/          # 页面专属 hooks
│   │   └── components/     # 页面专属组件
│   └── ...
├── stores/                 # Zustand stores
├── types/                  # 全局类型定义
└── main.tsx                # 应用入口
```

### 2.3 命名规范

| 类型 | 命名 | 示例 |
|------|------|------|
| 组件文件 | PascalCase | `UserCard.tsx` |
| 组件 Props | PascalCase + Props | `UserCardProps` |
| Hooks 文件 | camelCase + use | `useUserQuery.ts` |
| 工具函数 | camelCase | `formatDate.ts` |
| 常量 | SCREAMING_SNAKE_CASE | `MAX_RETRY_COUNT` |
| Store 文件 | camelCase + Store | `authStore.ts` |
| 测试文件 | `{源文件名}.test.tsx` | `UserCard.test.tsx` |
| 样式 | Tailwind 工具类 | 禁止独立 CSS 文件 |

### 2.4 样式规范

```
- 使用 TailwindCSS v4 工具类，禁止内联 style
- 复杂布局使用 cn() 工具合并类名（来自 shadcn/ui）
- 主题色使用 CSS 变量，禁止硬编码颜色值
- 响应式断点：sm(640) / md(768) / lg(1024) / xl(1280)
- 间距使用 Tailwind 标准刻度：1=0.25rem, 2=0.5rem, 4=1rem
```

---

## 3. 状态管理规范

### 3.1 Zustand（客户端状态）

```typescript
// ✅ 正确：带类型、持久化、动作命名清晰
interface AuthState {
  token: string | null;
  user: User | null;
  setToken: (token: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      setToken: (token) => set({ token }),
      logout: () => set({ token: null, user: null }),
    }),
    { name: 'auth-storage' }
  )
);
```

### 3.2 TanStack Query（服务端状态）

```typescript
// ✅ 正确：统一在 api/ 目录封装，页面只消费 hooks
export function useUserQuery(userId: string) {
  return useQuery({
    queryKey: ['user', userId],
    queryFn: () => fetchUser(userId),
    enabled: !!userId,
  });
}

// 禁止在组件内直接写 axios/fetch 调用
```

---

## 4. 表单规范

```typescript
// ✅ 正确：React Hook Form + Zod
const formSchema = z.object({
  title: z.string().min(1, '标题不能为空').max(100),
  content: z.string().min(10, '内容至少10字'),
});

type FormValues = z.infer<typeof formSchema>;

export function ContentForm() {
  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
  });
  
  return (
    <Form {...form}>
      <FormField name="title" render={...} />
    </Form>
  );
}
```

---

## 5. 测试规范

### 5.1 测试文件位置

- 与源文件同目录：`UserCard.tsx` → `UserCard.test.tsx`
- 页面测试放在 `pages/__tests__/` 或页面目录内

### 5.2 测试规范

```typescript
// ✅ 正确：描述清晰、模拟外部依赖、测试行为而非实现
describe('UserCard', () => {
  it('点击时触发 onSelect 回调', async () => {
    const onSelect = vi.fn();
    render(<UserCard userId="123" onSelect={onSelect} />);
    
    await waitFor(() => {
      expect(screen.getByText('用户名')).toBeInTheDocument();
    });
    
    await userEvent.click(screen.getByRole('button'));
    expect(onSelect).toHaveBeenCalledWith('123');
  });
});
```

### 5.3 覆盖率要求

- 语句覆盖率 ≥ 80%
- 分支覆盖率 ≥ 70%
- 关键路径（登录、内容生成、发布）必须 100% 覆盖

---

## 6. 质量门禁

```bash
# 每次提交前必须执行
npm run lint          # ESLint 0 errors
npx tsc --noEmit      # TypeScript 0 errors
npm run test -- --run --coverage  # 覆盖率 ≥ 80%
npm run build         # 构建通过
```

---

## 7. 禁止事项

- ❌ 使用类组件
- ❌ 在组件内直接调用 axios/fetch（必须用 TanStack Query）
- ❌ 使用 `any` 类型
- ❌ 内联 style 或独立 CSS 文件
- ❌ 修改 `components/ui/` 下的 shadcn/ui 源码（应复制后修改）
- ❌ 不写测试直接实现功能
- ❌ 跳过红灯阶段

---

## 8. 上下文加载顺序

修改前端代码前，必须读取：

1. `AGENTS.md`（根目录）→ 项目全局纪律
2. `apps/frontend/AGENTS.md`（本文件）→ 前端专属规范
3. `apps/frontend/package.json` → 依赖与脚本
4. `apps/frontend/vite.config.ts` → 构建配置
5. `apps/frontend/eslint.config.js` → Lint 规则
6. 相关测试文件
