# EcoDreamOmni 单 ECS 阿里云部署方案 — 专家评估报告

> **评审日期**: 2026-05-31
> **约束条件**: 仅有一台阿里云 ECS 服务器
> **核心目标**: 工程代码与数据存储彻底分离，系统升级零数据风险

---

## 一、执行摘要

在"仅有一台 ECS"的硬约束下，本方案采用 **"单 ECS 容器集群 + 阿里云托管数据服务"** 架构：

- **ECS 上只跑无状态应用容器**（Nginx + FastAPI + Celery Worker/Beat）
- **所有数据外迁到阿里云托管服务**（RDS PostgreSQL + 云数据库 Redis + OSS）
- **升级时仅需替换容器镜像**，数据层完全不受影响

**月费估算**：~350~500 元/月（ECS ~200元 + RDS ~100元 + Redis ~50元 + OSS ~20元）

---

## 二、架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                      阿里云 VPC                              │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              单台 ECS（应用层）                        │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │   │
│  │  │ Nginx       │  │ FastAPI     │  │ Celery      │  │   │
│  │  │ (前端静态)  │  │ (后端API)   │  │ Worker+Beat │  │   │
│  │  │ :80         │  │ :8000       │  │             │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  │   │
│  │              Docker Compose on ECS                  │   │
│  │              特征：无状态，可随时重建                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                         │                                   │
│              ┌──────────┼──────────┐                        │
│              ▼          ▼          ▼                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │ RDS PostgreSQL  │  │ 云数据库 Redis  │  │ OSS         │ │
│  │ (结构化数据)    │  │ (缓存/队列)     │  │ (上传文件)  │ │
│  │ 高可用版/基础版 │  │ 主从版          │  │ + 前端静态  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 分离原则

| 类型 | 位置 | 生命周期 | 升级时 |
|------|------|---------|--------|
| **代码/容器** | ECS Docker Compose | 随版本替换 | 任意重建，无数据风险 |
| **结构化数据** | RDS PostgreSQL | 独立于 ECS | 不受容器重建影响 |
| **缓存/队列** | 云数据库 Redis | 独立于 ECS | 不受容器重建影响 |
| **文件/图片** | OSS | 独立于 ECS | 不受容器重建影响 |
| **配置** | `.env` / SAE Secret | 独立于镜像 | 热更新无需重建 |

---

## 三、组件选型

### 3.1 ECS 配置建议

| 维度 | 建议配置 | 说明 |
|------|---------|------|
| **实例规格** | 2核4G 或 2核8G（突发性能 t6/计算型 c7） | FastAPI + Celery + Nginx 三服务共享 |
| **系统盘** | 40GB SSD（仅装系统+Docker镜像） | 不存任何业务数据 |
| **公网带宽** | 1~5Mbps 按量计费 | 根据实际流量调整 |
| **操作系统** | Alibaba Cloud Linux 3 / Ubuntu 22.04 LTS | 长期支持版本 |
| **安全组** | 仅开放 80/443/22 | 数据库/redis 不暴露公网 |

### 3.2 数据服务选型

| 服务 | 选型 | 月费估算 | 必要性 |
|------|------|---------|--------|
| **RDS PostgreSQL** | 基础版 2核4G 100GB（可先试用免费额度） | ~19元（新用户首年） | 必需 — 替代本地 postgres 容器 |
| **云数据库 Redis** | 256MB 主从版 | ~25元 | 必需 — 替代本地 redis 容器 |
| **OSS** | 标准存储 50GB | ~6元 | 必需 — 替代本地 uploads 目录 |
| **ACR** | 个人版 | 免费 | 推荐 — 镜像仓库 |

### 3.3 为什么不自建数据库？

在单 ECS 场景下，如果在同一台机器上自建 PostgreSQL + Redis：
- ECS 重建/迁移时数据跟随丢失
- 数据库与应用争抢 CPU/内存
- 无自动备份，误操作无法恢复
- 升级应用时必须同时保护数据文件，操作复杂且高风险

**结论**：即使只有一台 ECS，数据库也必须外迁到 RDS。

---

## 四、Docker Compose 生产配置

```yaml
# docker-compose.prod.yml
# 部署在单台 ECS 上，所有数据层外迁到阿里云托管服务
version: "3.9"

services:
  nginx:
    image: nginx:alpine
    container_name: ecodream-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
      # 注意：前端静态资源建议放 OSS，此处仅作 fallback
    depends_on:
      - backend
    restart: unless-stopped
    networks:
      - ecodream-network

  backend:
    image: ${ACR_REGISTRY}/ecodreamomni-backend:${IMAGE_TAG:-latest}
    container_name: ecodream-backend
    ports:
      - "8000:8000"
    env_file:
      - .env.prod
    environment:
      - ENV=production
    restart: unless-stopped
    networks:
      - ecodream-network
    healthcheck:
      test: ["CMD-SHELL", "python -c 'import urllib.request; urllib.request.urlopen(\"http://localhost:8000/health\")'"]
      interval: 30s
      timeout: 10s
      retries: 3

  celery-worker:
    image: ${ACR_REGISTRY}/ecodreamomni-backend:${IMAGE_TAG:-latest}
    container_name: ecodream-celery-worker
    command: celery -A src.celery_app worker --loglevel=info --concurrency=2
    env_file:
      - .env.prod
    restart: unless-stopped
    networks:
      - ecodream-network

  celery-beat:
    image: ${ACR_REGISTRY}/ecodreamomni-backend:${IMAGE_TAG:-latest}
    container_name: ecodream-celery-beat
    command: celery -A src.celery_app beat --loglevel=info
    env_file:
      - .env.prod
    restart: unless-stopped
    networks:
      - ecodream-network

networks:
  ecodream-network:
    driver: bridge
```

**关键变化**：
1. **移除了 `postgres` 和 `redis` 服务** — 数据层完全外迁
2. **移除了 `volumes` 声明** — ECS 本地不存任何业务数据
3. **使用 `.env.prod` 外置配置** — 数据库连接串、密钥等全部通过环境变量注入
4. **镜像从 ACR 拉取** — 构建在 CI 完成，ECS 只负责拉取和运行

---

## 五、环境变量模板（.env.prod）

```bash
# === 数据库 ===
DATABASE_URL=postgresql+asyncpg://ecodream:${DB_PASSWORD}@${RDS_ENDPOINT}:5432/ecodream

# === Redis ===
REDIS_URL=redis://default:${REDIS_PASSWORD}@${REDIS_ENDPOINT}:6379/0

# === OSS ===
OSS_ACCESS_KEY_ID=LTAIxxxxxxxxxxxxxxxx
OSS_ACCESS_KEY_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OSS_BUCKET=ecodreamomni-prod
OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
OSS_REGION=cn-hangzhou
OSS_CDN_DOMAIN=https://cdn.ecodreamomni.com

# === 安全 ===
JWT_SECRET=your-256-bit-secret-key-here-min-32-chars
COOKIE_VAULT_KEY=your-cookie-vault-key-here

# === 外部 API ===
DEEPSEEK_API_KEY=sk-xxxxxxxx
REDNOTE_COOKIE=your-rednote-cookie
UNSPLASH_API_KEY=your-unsplash-key
LLM_API_KEY_MASTER_KEY=your-master-key

# === 应用 ===
ENV=production
DEBUG=false
UPLOAD_DIR=/tmp/uploads  # 本地临时目录，实际文件走 OSS
```

---

## 六、代码改造清单

| # | 改造项 | 当前状态 | 目标状态 | 工作量 |
|---|-------|---------|---------|--------|
| 1 | **文件存储抽象层** | 直接读写本地文件 | 新增 `storage.py` 统一封装，支持本地/OSS 切换 | 0.5 天 |
| 2 | **file_upload.py** | `open()` 写本地 | 调用 `storage.save()`，返回 OSS URL | 0.5 天 |
| 3 | **main.py 静态文件** | `StaticFiles(directory="uploads")` | 移除本地挂载，文件访问走 OSS CDN | 0.5 天 |
| 4 | **config.py** | 无 OSS 配置 | 新增 OSS 环境变量读取 | 0.5 天 |
| 5 | **asset_pool.py** | 本地路径拼接 | 通过 `storage` 接口读写 | 0.5 天 |
| 6 | **docker-compose.prod.yml** | 无 | 新建生产配置（无 pg/redis） | 0.5 天 |
| 7 | **前端构建脚本** | 构建产物在容器内 | CI 中构建后上传 OSS | 0.5 天 |
| | **总计** | | | **~3.5 人天** |

---

## 七、实施路线图

### Phase 1：紧急修复（1 天）— 立即执行

> 在迁移到阿里云之前，先修复当前最危险的问题，防止数据继续丢失。

- [ ] 为当前 `docker-compose.yml` 的 backend 服务添加 `uploads-data` Named Volume
- [ ] 开启 Redis AOF 持久化（`appendonly yes`）
- [ ] 统一两套 docker-compose.yml（删除 `docker/` 目录下的版本，或使其指向根目录版本）
- [ ] 统一 Dockerfile Python 版本为 3.11

### Phase 2：阿里云资源创建（0.5 天）

- [ ] 创建 RDS PostgreSQL 实例（版本 16，与当前一致）
- [ ] 创建云数据库 Redis 实例（版本 7，与当前一致）
- [ ] 创建 OSS Bucket（标准存储，私有读写）
- [ ] 配置安全组：ECS 可访问 RDS/Redis 内网端口，外部仅开放 80/443/22

### Phase 3：代码改造（2 天）

- [ ] 后端：新增 `storage.py` 抽象层，支持本地/OSS 双模式
- [ ] 后端：改造 `file_upload.py` 和 `asset_pool.py`，所有文件操作走 `storage` 接口
- [ ] 后端：改造 `main.py`，移除 `/uploads` 本地静态文件挂载
- [ ] 后端：改造 `config.py`，新增 OSS 环境变量
- [ ] 创建 `docker-compose.prod.yml`

### Phase 4：数据迁移（0.5 天）

- [ ] PostgreSQL：使用 `pg_dump` 导出本地数据，`psql` 导入 RDS
- [ ] 文件：使用 `ossutil` 将本地 uploads 目录同步到 OSS
- [ ] 验证：检查文件 URL 可访问、数据库记录完整

### Phase 5：部署上线（0.5 天）

- [ ] ECS 上安装 Docker + Docker Compose
- [ ] 上传 `.env.prod` 到 ECS（注意权限 600）
- [ ] 首次部署：`docker-compose -f docker-compose.prod.yml up -d`
- [ ] 配置域名解析到 ECS 公网 IP
- [ ] 配置 Nginx SSL（可选，使用 certbot）

### Phase 6：升级流程标准化（持续）

> 从此以后的任何升级，都遵循以下安全流程：

```bash
# 1. 构建新镜像（在 CI 或本地）
docker build -t ecodreamomni-backend:v1.2.3 ./apps/backend

# 2. 推送到 ACR
docker tag ecodreamomni-backend:v1.2.3 registry.cn-hangzhou.aliyuncs.com/your-namespace/ecodreamomni-backend:v1.2.3
docker push registry.cn-hangzhou.aliyuncs.com/your-namespace/ecodreamomni-backend:v1.2.3

# 3. 在 ECS 上拉取并重启（只替换容器，不触碰任何数据）
ssh ecs-host
cd /opt/ecodreamomni
export IMAGE_TAG=v1.2.3
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d

# 4. 验证健康检查
# 如果异常，立即回滚
docker-compose -f docker-compose.prod.yml up -d --no-deps backend
```

---

## 八、回滚策略

| 场景 | 回滚方式 |
|------|---------|
| 新版本异常 | `docker-compose up -d` 指定上一版本镜像标签，30 秒内完成回滚 |
| 数据库误操作 | RDS 按时间点恢复（最多恢复到 7 天内任意一秒） |
| 文件误删除 | OSS 版本控制恢复（保留历史版本） |
| ECS 宕机 | 创建新 ECS，拉取同版本镜像 + `.env.prod`，10 分钟内恢复 |

---

## 九、成本估算（月度）

| 组件 | 配置 | 月费 |
|------|------|------|
| ECS | 2核4G（突发性能 t6），包年包月 | ~100~150元 |
| RDS PostgreSQL | 基础版 2核4G 100GB（新用户首年） | ~19元 |
| 云数据库 Redis | 256MB 主从版 | ~25元 |
| OSS | 50GB 标准存储 + 10GB 流量 | ~10元 |
| 公网带宽 | 1Mbps 按量 | ~20~30元 |
| ACR | 个人版 | 免费 |
| **合计** | | **~174~234元/月** |

> 注：首年 RDS 基础版有新用户优惠（227元/年），实际月均更低。

---

## 十、风险与缓解

| # | 风险 | 缓解措施 |
|---|------|---------|
| 1 | ECS 单点故障 | ECS 上配置云监控告警；定期备份 `.env.prod`；ECS 宕机时可快速创建新实例恢复 |
| 2 | 数据库连接串泄露 | `.env.prod` 文件权限设为 600；不提交到 Git；使用阿里云 KMS 加密（进阶） |
| 3 | OSS 公网访问费用 | 使用内网 Endpoint（不收费）；开启 CDN 缓存减少回源 |
| 4 | ECS 资源不足 | 监控 CPU/内存使用率；预留升级路径（可随时升配到 4核8G） |
| 5 | 数据迁移失败 | 迁移前全量备份；先在测试库验证；保留原环境运行至少 24h |

---

## 十一、决策建议

> **采用"单 ECS + Docker Compose + 阿里云托管数据服务"方案**
>
> 在"仅有一台 ECS"的硬约束下，这是**唯一满足"代码与数据彻底分离"的方案**。
>
> 关键要点：
> 1. ECS 上**绝不运行** PostgreSQL 和 Redis 容器
> 2. 所有上传文件**绝不存储**在 ECS 本地磁盘
> 3. 升级流程标准化为"仅替换容器镜像"

---

*报告编制: EcoDreamOmni 技术评审委员会*
*版本: v1.0*
*日期: 2026-05-31*
