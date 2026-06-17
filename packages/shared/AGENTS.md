# EcoDreamOmni — 共享包开发规范（AGENTS.md）

> 本文档面向在 `packages/shared/` 目录工作的 AI Agent 和人类开发者。
> 与根目录 `AGENTS.md` 互补，侧重共享类型与接口约定。

---

## 1. 定位

`packages/shared/` 是前后端的 **类型与接口契约层**：

- **TypeScript 类型**：供前端消费，定义 API 请求/响应、Store 状态、组件 Props
- **Python stub / Pydantic 模型**：供后端消费，定义数据库模型、API Schema、服务接口
- **工具函数**：前后端通用的纯函数（日期格式化、常量定义、校验规则）

**核心原则**：
- 共享包是 **契约层**，不是业务逻辑层
- 禁止在共享包中引入框架级依赖（React、FastAPI、SQLAlchemy 等）
- 修改共享包必须同步通知前后端，可能触发双方类型检查

---

## 2. 目录结构

```
packages/shared/
├── src/
│   ├── types/              # TypeScript 类型定义
│   │   ├── api.ts          # API 请求/响应类型
│   │   ├── models.ts       # 领域模型类型
│   │   └── index.ts        # 统一导出
│   ├── schemas/            # Pydantic / Zod 共享校验
│   │   ├── account.py      # Python Pydantic 模型
│   │   ├── account.ts      # TypeScript Zod schema
│   │   └── index.ts
│   ├── constants/          # 前后端通用常量
│   │   ├── platforms.ts    # 平台枚举
│   │   ├── platforms.py    # Python 枚举
│   │   └── index.ts
│   ├── utils/              # 纯函数工具
│   │   ├── date.ts         # 日期格式化
│   │   ├── date.py         # Python 日期工具
│   │   └── index.ts
│   └── index.ts            # 统一入口
├── tsconfig.json           # TypeScript 配置
└── package.json            # 包配置（type: module）
```

---

## 3. 类型契约规范

### 3.1 TypeScript 类型

```typescript
// ✅ 正确：interface + 完整文档 + 与后端字段一致
export interface Account {
  /** 账号 ID，对应数据库 accounts.id */
  id: number;
  /** 平台类型：xiaohongshu | douyin | weixin */
  platform: PlatformType;
  /** 平台用户名 */
  username: string;
  /** 创建时间，ISO 8601 格式 */
  createdAt: string;
}

export type PlatformType = 'xiaohongshu' | 'douyin' | 'weixin';

// ❌ 错误：type 定义对象、字段名与后端不一致、无文档
```

### 3.2 Python Pydantic 模型

```python
# ✅ 正确：与 TypeScript 类型字段名一致（snake_case）
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class PlatformType(str, Enum):
    XIAOHONGSHU = "xiaohongshu"
    DOUYIN = "douyin"
    WEIXIN = "weixin"

class Account(BaseModel):
    """账号模型，与前端 Account interface 对应。"""
    id: int = Field(description="账号 ID，对应数据库 accounts.id")
    platform: PlatformType = Field(description="平台类型")
    username: str = Field(description="平台用户名")
    created_at: datetime = Field(description="创建时间，ISO 8601 格式")
    
    class Config:
        from_attributes = True
```

### 3.3 字段命名映射

| 前端（TS） | 后端（Python） | 说明 |
|-----------|---------------|------|
| `createdAt` | `created_at` | 时间戳 |
| `updatedAt` | `updated_at` | 时间戳 |
| `userId` | `user_id` | 外键 |
| `accountId` | `account_id` | 外键 |
| `platformType` | `platform_type` | 枚举 |
| `isActive` | `is_active` | 布尔值 |

**约定**：
- 前端使用 camelCase
- 后端使用 snake_case
- API 层负责转换（FastAPI 的 `alias_generator` 或前端拦截器）

---

## 4. 常量规范

```typescript
// ✅ 正确：readonly + 枚举 + 文档
export const PLATFORMS = {
  XIAOHONGSHU: 'xiaohongshu',
  DOUYIN: 'douyin',
  WEIXIN: 'weixin',
} as const;

export type Platform = typeof PLATFORMS[keyof typeof PLATFORMS];

export const MAX_CONTENT_LENGTH = 2000;  // 小红书正文最大字数
export const COMPLIANCE_KEYWORDS = [
  '处方药',
  '诊断',
  '治疗',
  '治愈',
] as const;
```

```python
# ✅ 正确：Enum + 常量
from enum import Enum

class Platform(str, Enum):
    XIAOHONGSHU = "xiaohongshu"
    DOUYIN = "douyin"
    WEIXIN = "weixin"

MAX_CONTENT_LENGTH = 2000
COMPLIANCE_KEYWORDS = ["处方药", "诊断", "治疗", "治愈"]
```

---

## 5. 工具函数规范

```typescript
// ✅ 正确：纯函数、完整类型、文档、测试
/**
 * 格式化日期为平台展示格式。
 * @param date - ISO 8601 日期字符串
 * @returns 格式化后的中文日期，如 "2026年6月18日"
 */
export function formatDisplayDate(date: string): string {
  const d = new Date(date);
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日`;
}
```

```python
# ✅ 正确：纯函数、类型注解、文档、测试
from datetime import datetime

def format_display_date(date_str: str) -> str:
    """格式化日期为平台展示格式。
    
    Args:
        date_str: ISO 8601 日期字符串
        
    Returns:
        格式化后的中文日期，如 "2026年6月18日"
    """
    dt = datetime.fromisoformat(date_str)
    return f"{dt.year}年{dt.month}月{dt.day}日"
```

---

## 6. 版本管理

```
packages/shared/
└── package.json
```

```json
{
  "name": "@ecodream/shared",
  "version": "1.0.0",
  "type": "module",
  "main": "src/index.ts",
  "exports": {
    ".": "./src/index.ts",
    "./types": "./src/types/index.ts",
    "./schemas": "./src/schemas/index.ts",
    "./constants": "./src/constants/index.ts",
    "./utils": "./src/utils/index.ts"
  }
}
```

**约定**：
- 共享包版本独立管理
- 破坏性变更（字段删除、类型修改）必须升级主版本号
- 新增字段升级次版本号

---

## 7. 禁止事项

- ❌ 在共享包中引入 React、FastAPI、SQLAlchemy 等框架依赖
- ❌ 在共享包中写业务逻辑（数据库查询、API 调用）
- ❌ 修改共享包后不更新前后端类型检查
- ❌ 前后端字段命名不一致（必须遵循 camelCase / snake_case 映射）
- ❌ 不写类型注解或文档
- ❌ 不写测试直接实现工具函数

---

## 8. 上下文加载顺序

修改共享包前，必须读取：

1. `AGENTS.md`（根目录）→ 项目全局纪律
2. `packages/shared/AGENTS.md`（本文件）→ 共享包专属规范
3. `packages/shared/package.json` → 包配置
4. `packages/shared/tsconfig.json` → TS 配置
5. 前后端对应的类型使用位置（确认影响范围）
