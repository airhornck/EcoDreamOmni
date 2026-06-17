# EcoDreamOmni — 后端开发规范（AGENTS.md）

> 本文档面向在 `apps/backend/` 目录工作的 AI Agent 和人类开发者。
> 与根目录 `AGENTS.md` 互补，侧重后端专属技术约定。

---

## 1. 技术栈速查

| 层级 | 技术 | 版本 |
|------|------|------|
| 框架 | FastAPI | 最新 |
| 服务器 | Uvicorn | 最新 |
| ORM | SQLAlchemy | 2.0 |
| 迁移 | Alembic | 最新 |
| 认证 | JWT + OAuth2 + Passlib | 最新 |
| 任务队列 | Celery + Redis | 最新 |
| 测试 | pytest + pytest-asyncio | 最新 |
| 类型检查 | mypy | 最新 |
| Lint | ruff | 最新 |
| 数据库 | PostgreSQL 16 | — |
| 缓存 | Redis 7 | — |

---

## 2. 代码风格规范

### 2.1 SQLAlchemy 2.0 新风格

```python
# ✅ 正确：type-annotated declarative + Mapped
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey
from src.models.base import Base

class Account(Base):
    __tablename__ = "accounts"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    platform: Mapped[str] = mapped_column(String(20))
    
    # 关系
    posts: Mapped[list["Post"]] = relationship(back_populates="account")

# ❌ 错误：旧风格 Column()、无 Mapped 注解
```

### 2.2 FastAPI 路由规范

```python
# ✅ 正确：Pydantic 模型 + 依赖注入 + 异步 + 统一响应
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas.account import AccountCreate, AccountResponse
from src.services.account_service import AccountService
from src.dependencies import get_db, get_current_user

router = APIRouter(prefix="/accounts", tags=["accounts"])

@router.post("", response_model=AccountResponse)
async def create_account(
    data: AccountCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AccountResponse:
    service = AccountService(db)
    return await service.create(data, user_id=user.id)

# ❌ 错误：同步路由、无 Pydantic 模型、直接操作数据库
```

### 2.3 服务层（Service Layer）

```python
# ✅ 正确：Service 封装业务逻辑，与 API 层分离
class AccountService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = AccountRepository(db)
    
    async def create(self, data: AccountCreate, user_id: int) -> Account:
        # 业务逻辑
        account = Account(**data.model_dump(), user_id=user_id)
        return await self.repo.save(account)

# ❌ 错误：在路由中直接写 SQL 或业务逻辑
```

### 2.4 文件组织

```
src/
├── api/                    # FastAPI 路由（只负责 HTTP 层）
│   ├── __init__.py
│   ├── accounts.py
│   ├── tasks.py
│   └── ...
├── models/                 # SQLAlchemy 2.0 模型
│   ├── base.py             # declarative_base()
│   ├── account.py
│   └── ...
├── schemas/                # Pydantic 请求/响应模型
│   ├── account.py
│   └── ...
├── services/               # 业务逻辑层
│   ├── account_service.py
│   └── ...
├── repositories/           # 数据访问层（可选）
│   ├── account_repository.py
│   └── ...
├── dependencies.py         # FastAPI 依赖（get_db, get_current_user）
├── core/                   # 核心配置（settings, security, logging）
│   ├── config.py
│   ├── security.py
│   └── logging.py
└── main.py                 # 应用入口
```

### 2.5 命名规范

| 类型 | 命名 | 示例 |
|------|------|------|
| 模块文件 | snake_case | `account_service.py` |
| 类 | PascalCase | `AccountService` |
| 函数/方法 | snake_case | `create_account` |
| 常量 | SCREAMING_SNAKE_CASE | `MAX_PAGE_SIZE` |
| 私有方法 | _snake_case | `_validate_username` |
| 测试文件 | `test_{module}.py` | `test_account_service.py` |
| Pydantic 模型 | PascalCase + 后缀 | `AccountCreate`, `AccountResponse` |

---

## 3. 异步规范

```python
# ✅ 正确：async def + await + AsyncSession
async def get_account(db: AsyncSession, account_id: int) -> Account | None:
    result = await db.execute(
        select(Account).where(Account.id == account_id)
    )
    return result.scalar_one_or_none()

# ✅ 正确：Celery 任务也使用异步风格
@app.task
async def process_content_task(content_id: int) -> None:
    async with async_session() as db:
        service = ContentService(db)
        await service.process(content_id)

# ❌ 错误：同步 Session、阻塞 IO
```

---

## 4. 数据库规范

### 4.1 模型定义

```python
# ✅ 正确：完整的 Mapped 注解、约束、文档字符串
class Post(Base):
    """内容发布记录。
    
    关联：Account（多对一）
    """
    __tablename__ = "posts"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    
    account: Mapped["Account"] = relationship(back_populates="posts")
```

### 4.2 迁移规范

```bash
# 生成迁移
alembic revision --autogenerate -m "add_account_platform_index"

# 升级
alembic upgrade head

# 降级（开发环境）
alembic downgrade -1
```

**约束**：
- 每个迁移只做一件事
- 迁移必须包含 upgrade 和 downgrade
- 生产环境禁止删除列的迁移（先标记废弃，后删除）

---

## 5. 认证与授权

```python
# ✅ 正确：统一依赖 + JWT + OAuth2
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await get_user_by_id(db, int(user_id))
    if user is None:
        raise credentials_exception
    return user
```

---

## 6. 测试规范

### 6.1 测试文件位置

```
tests/
├── conftest.py             # pytest fixtures（db, client, user）
├── test_accounts.py        # 对应 api/accounts.py
├── test_account_service.py # 对应 services/account_service.py
└── e2e/
    └── test_content_creation.py  # 端到端测试
```

### 6.2 测试规范

```python
# ✅ 正确：pytest + pytest-asyncio + fixtures
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_account(client: AsyncClient, db: AsyncSession) -> None:
    response = await client.post("/accounts", json={
        "username": "test_user",
        "platform": "xiaohongshu",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "test_user"
    assert "id" in data

# ✅ 正确：使用 fixtures 管理数据库状态
@pytest.fixture
async def test_account(db: AsyncSession) -> Account:
    account = Account(username="test", platform="xiaohongshu")
    db.add(account)
    await db.commit()
    return account
```

### 6.3 覆盖率要求

- 语句覆盖率 ≥ 80%
- API 路由覆盖率 100%
- Service 层核心逻辑覆盖率 100%

---

## 7. 错误处理规范

```python
# ✅ 正确：统一 HTTPException + 结构化错误响应
class EcoDreamException(HTTPException):
    """项目统一异常基类。"""
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: str = "UNKNOWN_ERROR",
    ) -> None:
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code

# 使用示例
raise EcoDreamException(
    status_code=400,
    detail="账号已存在",
    error_code="ACCOUNT_ALREADY_EXISTS",
)

# ❌ 错误：直接返回 dict、使用裸 Exception
```

---

## 8. 质量门禁

```bash
# 每次提交前必须执行
ruff check src/ tests/        # Lint 0 errors
mypy src/                     # 类型检查 0 errors
pytest --cov=src --cov-fail-under=80  # 覆盖率 ≥ 80%
```

---

## 9. 禁止事项

- ❌ 在路由中直接写 SQL 或业务逻辑（必须分层）
- ❌ 使用 SQLAlchemy 1.x 风格（Column、declarative_base()）
- ❌ 同步数据库操作（必须用 AsyncSession）
- ❌ 在代码中硬编码密钥或密码（使用环境变量）
- ❌ 使用裸 `except:` 或 `Exception`
- ❌ 不写类型注解
- ❌ 不写测试直接实现功能
- ❌ 跳过红灯阶段

---

## 10. 上下文加载顺序

修改后端代码前，必须读取：

1. `AGENTS.md`（根目录）→ 项目全局纪律
2. `apps/backend/AGENTS.md`（本文件）→ 后端专属规范
3. `apps/backend/requirements.txt` → 依赖
4. `apps/backend/alembic.ini` → 迁移配置
5. `apps/backend/pytest.ini` → 测试配置
6. 相关测试文件
