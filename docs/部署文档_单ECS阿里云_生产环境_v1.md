# EcoDreamOmni 单 ECS 生产环境部署文档

> **版本**: v1.2
> **日期**: 2026-06-01
> **适用场景**: 仅有一台阿里云 ECS，数据库使用 RDS，缓存使用云 Redis，文件存储使用 ECS 本地磁盘 + Docker Volume
> **核心原则**: 容器重建不丢失数据

---

## 目录

1. [架构概览](#一架构概览)
2. [前置准备](#二前置准备)
3. [ECS 环境初始化](#三ecs-环境初始化)
4. [项目部署](#四项目部署)
5. [数据迁移](#五数据迁移)
6. [启动与验证](#六启动与验证)
7. [域名与 SSL](#七域名与ssl可选)
8. [日常运维](#八日常运维)
9. [升级流程](#九升级流程)
10. [备份策略](#十备份策略)
11. [故障排查](#十一故障排查)

---

## 一、架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                        阿里云                                │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              单台 ECS（应用层）                        │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────────────────┐  │   │
│  │  │ Nginx   │  │ FastAPI │  │ Celery Worker+Beat  │  │   │
│  │  │ :80/443 │  │ :8000   │  │                     │  │   │
│  │  └─────────┘  └─────────┘  └─────────────────────┘  │   │
│  │              Docker Compose                         │   │
│  │  数据分离: uploads → Named Volume → /opt/data       │   │
│  └─────────────────────────────────────────────────────┘   │
│                         │                                   │
│              ┌──────────┼──────────┐                        │
│              ▼          ▼          ▼                        │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │ RDS PostgreSQL  │  │ 云数据库 Redis  │                  │
│  │ (高可用/基础版) │  │ (主从版)        │                  │
│  └─────────────────┘  └─────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

### 分离矩阵

| 类型 | 存放位置 | 容器重建时 |
|------|---------|-----------|
| 代码/容器 | ECS Docker | 替换镜像即可 |
| 上传文件 | `/opt/ecodreamomni/data/uploads` (Volume) | **保留** ✅ |
| 数据库 | RDS | **保留** ✅ |
| 缓存/队列 | 云 Redis | **保留** ✅ |
| 代理配置 | RDS `proxy_configs` | **保留** ✅ |
| LLM 模型配置 | RDS `llm_models` | **保留** ✅ |
| 账户池 | RDS `account_pool_entries` | **保留** ✅ |
| 环境变量 | `.env.prod` | **保留** ✅ |

---

## 二、前置准备

### 2.1 阿里云资源清单

你需要提前在阿里云控制台创建以下资源：

#### 1) ECS 实例

| 配置项 | 建议值 |
|--------|--------|
| 实例规格 | 2核4G（突发性能 t6 或计算型 c7） |
| 系统盘 | 40GB ESSD |
| 操作系统 | Ubuntu 22.04 LTS 64位 |
| 公网 IP | 分配公网 IP |
| 带宽 | 1~5Mbps 按量计费 |
| 安全组 | 入站：22(SSH), 80(HTTP), 443(HTTPS) |

#### 2) RDS PostgreSQL

| 配置项 | 建议值 |
|--------|--------|
| 数据库版本 | PostgreSQL 14（与开发环境一致） |
| 实例规格 | 基础版 2核4G（生产验证期）或 高可用版 |
| 存储空间 | 100GB |
| 网络类型 | 与 ECS 同一 VPC |
| 白名单 | 添加 ECS 内网 IP |
| 创建账号 | `ecodream` + 强密码 |
| 创建数据库 | `ecodream` |

> **注意**：创建后记录**内网地址**（如 `pgm-xxxxxxxx.pg.rds.aliyuncs.com`）

#### 3) 云数据库 Redis

| 配置项 | 建议值 |
|--------|--------|
| 架构版本 | Redis 7.0 |
| 实例规格 | 256MB~1GB 主从版 |
| 网络类型 | 与 ECS 同一 VPC |
| 白名单 | 添加 ECS 内网 IP |

> **注意**：创建后记录**连接地址**和**密码**

#### 4) 可选：ACR 镜像仓库

如需从私有仓库拉取镜像，创建 ACR 个人版，配置仓库和密码。

---

### 2.2 本地准备

在本地开发机准备：

```bash
# 1. 确认代码已提交 Git
cd /path/to/EcoDreamOmni
git status

# 2. 确认 .env.prod.example 已按实际值填写
# 稍后会上传到 ECS
```

---

## 三、ECS 环境初始化

### 3.1 连接 ECS

```bash
ssh root@YOUR_ECS_PUBLIC_IP
```

### 3.2 系统更新

```bash
# Ubuntu 22.04
apt update && apt upgrade -y
```

### 3.3 安装 Docker

```bash
# 安装依赖
apt update
apt install -y ca-certificates curl gnupg lsb-release

# 添加 Docker GPG key
mkdir -p /etc/apt/keyrings
curl -fsSL https://mirrors.aliyun.com/docker-ce/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# 添加 Docker apt 仓库
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://mirrors.aliyun.com/docker-ce/linux/ubuntu $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list

# 安装 Docker
apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 启动 Docker
systemctl start docker
systemctl enable docker

# 验证
docker --version
docker compose version
```

### 3.4 安装 Docker Compose (Standalone)

```bash
# 下载（使用国内镜像加速）
curl -L https://mirrors.aliyun.com/docker-toolbox/linux/compose/2.23.0/docker-compose-linux-x86_64 -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose

# 验证
docker-compose --version
```

### 3.5 创建数据目录

```bash
# 创建 uploads 目录（将被挂载为 Docker Volume）
mkdir -p /opt/ecodreamomni/data/uploads
chmod 755 /opt/ecodreamomni/data/uploads

# 创建应用目录
mkdir -p /opt/ecodreamomni/app
cd /opt/ecodreamomni/app
```

### 3.6 配置防火墙

```bash
# 确认安全组已开放 80/443/22
# ECS 内部防火墙也放行
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
```

---

## 四、项目部署

### 4.1 上传项目文件到 ECS

在**本地开发机**执行，将完整项目代码上传到 ECS：

```bash
# 首次部署：使用 scp 上传关键文件
scp docker-compose.prod.yml root@YOUR_ECS_IP:/opt/ecodreamomni/app/
scp docker/nginx.conf root@YOUR_ECS_IP:/opt/ecodreamomni/app/docker/
scp .env.prod root@YOUR_ECS_IP:/opt/ecodreamomni/app/

# 上传后端代码
scp -r apps/backend root@8.141.26.195:/opt/ecodreamomni/app/apps/

# 上传前端代码
scp -r apps/frontend root@8.141.26.195:/opt/ecodreamomni/app/apps/
```

或一次性上传整个项目（排除无需上传的目录）：

```bash
rsync -avz \
  --exclude=node_modules \
  --exclude=__pycache__ \
  --exclude=.git \
  --exclude=demo/node_modules \
  --exclude=demo/dist \
  --exclude=demo/storybook-static \
  --exclude=*.pyc \
  . root@YOUR_ECS_IP:/opt/ecodreamomni/app/
```

上传完成后，ECS 上的目录结构：

```
/opt/ecodreamomni/app/
├── docker-compose.prod.yml    # 生产编排文件
├── .env.prod                  # 环境变量（600权限）
├── docker/
│   └── nginx.conf             # Nginx 配置
├── apps/
│   ├── backend/               # 后端源码 + Dockerfile
│   └── frontend/              # 前端源码 + Dockerfile
└── ...                        # 其他项目文件
```

### 4.2 构建镜像并启动

在**ECS 上**执行：

```bash
cd /opt/ecodreamomni/app

# 构建后端镜像
docker build -t ecodreamomni-backend:latest -f apps/backend/Dockerfile apps/backend

# 构建前端镜像
docker build -t ecodreamomni-frontend:latest -f apps/frontend/Dockerfile apps/frontend

# 启动所有服务
export IMAGE_TAG=latest
docker-compose -f docker-compose.prod.yml up -d
```

> `docker-compose.prod.yml` 中镜像默认为 `ecodreamomni-backend:latest` 和 `ecodreamomni-frontend:latest`，与上述 `docker build` 命令输出的镜像名一致，无需额外配置。

### 4.3 配置文件说明

`.env.prod` 文件内容模板：

```bash
# === Database (RDS PostgreSQL) ===
DATABASE_URL=postgresql+asyncpg://ecodream:YOUR_DB_PASSWORD@pgm-xxxxxxxx.pg.rds.aliyuncs.com:5432/ecodream

# === Cache / Queue (Aliyun Redis) ===
REDIS_URL=redis://:YOUR_REDIS_PASSWORD@r-xxxxxxxx.redis.rds.aliyuncs.com:6379/0

# === Security ===
JWT_SECRET=your-strong-jwt-secret-min-32-chars
COOKIE_VAULT_KEY=your-cookie-vault-key

# === External APIs ===
DEEPSEEK_API_KEY=sk-xxxxxxxx
OPENAI_API_KEY=sk-xxxxxxxx
ANTHROPIC_API_KEY=sk-xxxxxxxx
KIMI_API_KEY=sk-xxxxxxxx
REDNOTE_COOKIE=your-cookie
UNSPLASH_API_KEY=your-key
LLM_API_KEY_MASTER_KEY=your-master-key

# === 住宅轮换代理配置 (Account Pool IP 隔离) ===
# 系统启动时自动创建代理条目并绑定到种子账户
PROXY_HTTP_HOST=51.77.190.247
PROXY_HTTP_PORT=5959
PROXY_HTTP_USER=your-proxy-username
PROXY_HTTP_PASS=your-proxy-password
PROXY_SOCKS5_HOST=51.77.190.247
PROXY_SOCKS5_PORT=9595
PROXY_SOCKS5_USER=your-proxy-username
PROXY_SOCKS5_PASS=your-proxy-password
PROXY_ROTATION_TYPE=rotating

# === Application ===
ENV=production
DEBUG=false
UPLOAD_DIR=/app/uploads
```

> **重要**：`.env.prod` 文件权限必须设为 `600`：
> ```bash
> chmod 600 /opt/ecodreamomni/app/.env.prod
> ```

> **代理 & LLM 自动初始化说明**：
> 首次部署时，若 RDS 中 `proxy_configs` / `llm_models` 表为空，系统会自动读取 `.env.prod` 中的配置创建代理和模型。之后这些数据存储在 RDS 中，容器重启时自动恢复，**无需再次修改 `.env.prod` 中的代理密码或 API Key**（除非需要更换代理或密钥）。

---

## 五、数据迁移

### 5.1 PostgreSQL 迁移（开发环境 → RDS）

#### 版本兼容性说明

> **重要**：本地开发环境使用 **PostgreSQL 14**（`pgvector/pgvector:pg14` 镜像），**阿里云 RDS 必须创建 PostgreSQL 14 实例**以保持版本一致。如果 RDS 已创建为 PostgreSQL 16，需要重新创建 PostgreSQL 14 实例。

#### 方案 A：pg_dump 自定义格式（版本一致时）

如果本地和 RDS 都是 PostgreSQL 14，使用自定义格式（最快）：

##### macOS / Linux

```bash
# 1. 导出本地数据库
cd /path/to/EcoDreamOmni
pg_dump -h localhost -U ecodream -d ecodream -F c -f ecodream_backup.dump

# 2. 上传 dump 文件到 ECS
scp ecodream_backup.dump root@YOUR_ECS_IP:/tmp/
```

##### Windows（未安装 PostgreSQL 客户端）

```powershell
# PowerShell
# 1. 确认本地 postgres 容器正在运行
docker ps

# 2. 在 postgres 容器内执行 pg_dump
$env:PGPASSWORD = "ecodream"
docker exec -i ecodream-postgres pg_dump -U ecodream -d ecodream -F c -f /tmp/ecodream_backup.dump

docker cp ecodream-postgres:/tmp/ecodream_backup.dump ./ecodream_backup.dump

# 3. 上传 dump 文件到 ECS
scp ecodream_backup.dump root@YOUR_ECS_IP:/tmp/
```

**在 ECS 上执行导入：**

```bash
# 安装 PostgreSQL 14 客户端
apt update
apt install -y postgresql-client-14

# 导入到 RDS
PGPASSWORD='YOUR_RDS_PASSWORD' pg_restore \
  -h pgm-xxxxxxxx.pg.rds.aliyuncs.com \
  -U ecodream \
  -d ecodream \
  -v \
  /tmp/ecodream_backup.dump
```

#### 方案 B：Plain SQL 格式（版本降级/跨版本时）

如果本地 PostgreSQL 版本高于 RDS（如本地 pg16 → RDS pg14），**自定义格式 dump 无法恢复**，必须使用纯文本 SQL：

```bash
# 1. 本地导出为纯文本 SQL（兼容所有版本）
pg_dump -h localhost -U ecodream -d ecodream --no-owner --no-privileges -f ecodream_backup.sql

# 2. 上传 SQL 文件到 ECS
scp ecodream_backup.sql root@YOUR_ECS_IP:/tmp/

# 3. 在 ECS 上导入到 RDS
PGPASSWORD='YOUR_RDS_PASSWORD' psql \
  -h pgm-xxxxxxxx.pg.rds.aliyuncs.com \
  -U ecodream \
  -d ecodream \
  -f /tmp/ecodream_backup.sql
```

> **注意**：纯文本 SQL 导出会包含 `CREATE EXTENSION vector`，请确认 RDS pg14 已安装 pgvector 扩展。

#### 迁移后验证

```bash
# 验证表数量
PGPASSWORD='YOUR_RDS_PASSWORD' psql \
  -h pgm-xxxxxxxx.pg.rds.aliyuncs.com \
  -U ecodream \
  -d ecodream \
  -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';"

# 验证关键表数据
PGPASSWORD='YOUR_RDS_PASSWORD' psql \
  -h pgm-xxxxxxxx.pg.rds.aliyuncs.com \
  -U ecodream \
  -d ecodream \
  -c "
  SELECT 'users' as table_name, COUNT(*) as count FROM users
  UNION ALL
  SELECT 'proxy_configs', COUNT(*) FROM proxy_configs
  UNION ALL
  SELECT 'llm_models', COUNT(*) FROM llm_models
  UNION ALL
  SELECT 'account_pool_entries', COUNT(*) FROM account_pool_entries;
  "
```

### 5.2 上传文件迁移（如有）

如果你已经在其他环境有上传文件：

```bash
# 将已有 uploads 目录打包上传到 ECS
scp -r /path/to/existing/uploads/* root@YOUR_ECS_IP:/opt/ecodreamomni/data/uploads/
```

### 5.3 Redis 数据迁移（可选）

Redis 主要存储 Celery 队列和缓存，通常无需迁移（任务队列重建即可）。

如需迁移：

```bash
# 本地导出
redis-cli SAVE
cp /path/to/redis/dump.rdb /tmp/dump.rdb
scp /tmp/dump.rdb root@YOUR_ECS_IP:/tmp/

# 阿里云 Redis 不支持直接导入 RDB，建议：
# 1. 使用 redis-shake 工具迁移
# 2. 或直接让应用重建缓存（推荐）
```

---

## 六、启动与验证

### 6.1 启动服务

```bash
cd /opt/ecodreamomni/app

# 使用显式镜像标签（推荐）
export IMAGE_TAG=latest

# 启动
docker-compose -f docker-compose.prod.yml up -d

# 查看状态
docker-compose -f docker-compose.prod.yml ps

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f backend
```

### 6.2 健康检查

```bash
# 1. API 健康检查
curl http://localhost:8000/health
# 期望输出: {"status":"ok","version":"0.1.0"}

# 2. Nginx 代理检查
curl http://localhost/api/health
# 期望输出: {"status":"ok","version":"0.1.0"}

# 3. 前端访问
curl -I http://localhost/
# 期望: HTTP/1.1 200 OK

# 4. 数据库连接检查
docker-compose -f docker-compose.prod.yml exec backend \
  python -c "import asyncio; from src.core.database import engine; asyncio.run(engine.connect())"

# 5. 代理配置检查（首次部署时应自动从 .env.prod 创建）
curl -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  http://localhost:8000/proxies
# 期望返回 2 条代理（HTTP + SOCKS5）

# 6. LLM 模型配置检查
curl -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  http://localhost:8000/llm/models
# 期望返回 deepseek-chat 等已注册模型
```

### 6.3 浏览器验证

访问 `http://YOUR_ECS_PUBLIC_IP/`，确认：
- [ ] 前端页面正常加载
- [ ] 登录/注册功能正常
- [ ] 创建任务正常
- [ ] 文件上传正常（上传后文件在 `/opt/ecodreamomni/data/uploads`）
- [ ] **代理配置已自动加载**：进入「系统设置」→「代理管理」，可见 HTTP/SOCKS5 代理
- [ ] **账户池可绑定代理**：进入「账号池」→「新增账号」，下拉框可选择代理
- [ ] **LLM 模型已注册**：进入「系统设置」→「LLM Hub」，可见 deepseek 等模型

---

## 七、域名与 SSL（可选）

### 7.1 域名解析

在域名服务商处添加 A 记录：

| 主机记录 | 记录类型 | 记录值 |
|---------|---------|--------|
| @ 或 www | A | YOUR_ECS_PUBLIC_IP |

### 7.2 配置 SSL（Let's Encrypt + certbot）

```bash
# 安装 certbot
apt update
apt install -y certbot

# 申请证书（确保域名已解析到 ECS IP）
certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# 证书位置
# /etc/letsencrypt/live/yourdomain.com/fullchain.pem
# /etc/letsencrypt/live/yourdomain.com/privkey.pem

# 修改 nginx.conf 启用 SSL（取消注释 ssl 相关行）
# 然后重启 nginx
docker-compose -f docker-compose.prod.yml restart nginx

# 设置自动续期
echo "0 2 * * * certbot renew --quiet && docker-compose -f /opt/ecodreamomni/app/docker-compose.prod.yml restart nginx" | crontab -
```

### 7.3 Nginx SSL 配置模板

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    root /usr/share/nginx/html;
    index index.html;

    client_max_body_size 50M;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /uploads/ {
        alias /var/www/uploads/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /api/ {
        proxy_pass http://backend:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 八、日常运维

### 8.1 查看运行状态

```bash
cd /opt/ecodreamomni/app

# 容器状态
docker-compose -f docker-compose.prod.yml ps

# 资源占用
docker stats --no-stream

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f celery-worker

# 进入容器排查
docker-compose -f docker-compose.prod.yml exec backend sh
```

### 8.2 重启服务

```bash
# 重启单个服务
docker-compose -f docker-compose.prod.yml restart backend

# 重启全部
docker-compose -f docker-compose.prod.yml restart
```

### 8.3 查看上传文件

```bash
# 直接查看宿主机目录
ls -la /opt/ecodreamomni/data/uploads/

# 或进入容器查看
docker-compose -f docker-compose.prod.yml exec backend ls -la /app/uploads/
```

---

## 九、升级流程

### 9.1 安全升级原则

```
升级前：确认当前版本稳定运行
    ↓
构建新镜像（本地或 CI）
    ↓
推送到 ECS（或 ACR）
    ↓
更新 docker-compose.prod.yml（如有变更）
    ↓
docker-compose pull && docker-compose up -d
    ↓
验证健康检查
    ↓
异常 → 立即回滚到上一版本镜像
```

### 9.2 具体命令

```bash
cd /opt/ecodreamomni/app

# 1. 备份当前版本标签（用于回滚）
docker-compose -f docker-compose.prod.yml config | grep image

# 2. 更新镜像标签
export IMAGE_TAG=v1.1.0

# 3. 拉取/构建新镜像
docker-compose -f docker-compose.prod.yml pull
# 或本地构建: docker build -t ecodreamomni-backend:v1.1.0 ...

# 4. 平滑升级（先启动新容器，再停止旧容器）
docker-compose -f docker-compose.prod.yml up -d

# 5. 验证
curl -f http://localhost/api/health || echo "UPGRADE FAILED"

# 6. 清理旧镜像（可选）
docker image prune -f
```

### 9.3 回滚

```bash
cd /opt/ecodreamomni/app

# 立即回滚到上一版本
export IMAGE_TAG=v1.0.0
docker-compose -f docker-compose.prod.yml up -d

# 验证
curl http://localhost/api/health
```

> **重要**：回滚时 `uploads` Volume 中的文件**不会**被删除，数据库和缓存也**不会**受影响。

---

## 十、备份策略

### 10.1 上传文件备份

```bash
# 每日凌晨备份 uploads 目录到 OSS（推荐）
# 或使用阿里云云备份服务

# 手动备份示例
rsync -avz /opt/ecodreamomni/data/uploads/ /backup/uploads-$(date +%Y%m%d)/

# 清理 30 天前的备份
find /backup -name "uploads-*" -mtime +30 -exec rm -rf {} \;
```

### 10.2 数据库备份（RDS 自动）

RDS 已内置自动备份：
- 每日自动全量备份
- 支持按时间点恢复（7~730 天保留期）
- 可在阿里云控制台设置备份策略

### 10.3 配置文件备份

```bash
# 备份关键配置文件
cp /opt/ecodreamomni/app/.env.prod /backup/env-$(date +%Y%m%d).prod
cp /opt/ecodreamomni/app/docker-compose.prod.yml /backup/
cp /opt/ecodreamomni/app/docker/nginx.conf /backup/
```

### 10.4 一键备份脚本

创建 `/opt/ecodreamomni/backup.sh`：

```bash
#!/bin/bash
set -e

BACKUP_DIR="/backup/ecodreamomni/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# 1. 备份 uploads
cp -r /opt/ecodreamomni/data/uploads "$BACKUP_DIR/"

# 2. 备份配置
cp /opt/ecodreamomni/app/.env.prod "$BACKUP_DIR/"
cp /opt/ecodreamomni/app/docker-compose.prod.yml "$BACKUP_DIR/"

# 3. 备份数据库（通过 pg_dump）
source /opt/ecodreamomni/app/.env.prod
PGPASSWORD=$(echo $DATABASE_URL | sed 's/.*://; s/@.*//') \
pg_dump -h $(echo $DATABASE_URL | sed 's/.*@//; s/:.*//') \
  -U $(echo $DATABASE_URL | sed 's/.*\/\///; s/:.*//') \
  -d ecodream -F c -f "$BACKUP_DIR/db.dump"

echo "Backup completed: $BACKUP_DIR"
```

```bash
chmod +x /opt/ecodreamomni/backup.sh

# 添加到每日定时任务
crontab -e
# 添加: 0 3 * * * /opt/ecodreamomni/backup.sh >> /var/log/ecodream-backup.log 2>&1
```

---

## 十一、故障排查

### Q1: 容器启动失败

```bash
# 查看具体错误
docker-compose -f docker-compose.prod.yml logs backend

# 常见原因：
# - .env.prod 文件不存在或权限不对
# - 数据库连接串错误
# - Redis 连接失败（白名单未配置）
```

### Q2: 数据库连接失败

```bash
# 测试网络连通性
ping pgm-xxxxxxxx.pg.rds.aliyuncs.com

# 测试端口连通性
telnet pgm-xxxxxxxx.pg.rds.aliyuncs.com 5432

# 检查 RDS 白名单
# 阿里云控制台 → RDS → 数据库连接 → 白名单 → 确认 ECS 内网 IP 已添加
```

### Q3: 上传文件 404

```bash
# 检查文件是否在 Volume 中
ls -la /opt/ecodreamomni/data/uploads/

# 检查容器内是否能访问
docker-compose -f docker-compose.prod.yml exec backend ls -la /app/uploads/

# 检查 nginx 配置是否正确 alias /var/www/uploads/
```

### Q4: 内存不足（ECS 2核4G）

```bash
# 查看内存使用
free -h
docker stats --no-stream

# 如果内存不足，可以：
# 1. 减少 Celery concurrency: --concurrency=1
# 2. 增加 ECS Swap 空间
# 3. 升级 ECS 到 2核8G
```

### Q5: 代理列表为空（重启后代理丢失）

从 v1.2 开始，代理已持久化到数据库。如果代理列表为空：

```bash
# 1. 检查 proxy_configs 表是否存在数据
docker-compose -f docker-compose.prod.yml exec backend \
  python -c "import asyncio; from src.core.database import AsyncSessionLocal; from sqlalchemy import select; from src.models.proxy_config_orm import ProxyConfigORM; async def check(): async with AsyncSessionLocal() as db: r=await db.execute(select(ProxyConfigORM)); print(f'Proxy count: {len(r.scalars().all())}'); asyncio.run(check())"

# 2. 检查 .env.prod 中代理配置是否正确
head -n 20 /opt/ecodreamomni/app/.env.prod | grep PROXY

# 3. 如配置正确但表为空，重启 backend 容器会自动从环境变量 seed
docker-compose -f docker-compose.prod.yml restart backend
```

### Q6: pg_restore 报错（版本不兼容）

错误示例：`pg_restore: [archiver] unsupported version (1.14) in file header`

**原因**：RDS PostgreSQL 版本低于本地开发环境（如本地 pg16，RDS pg14）。

**解决**：使用纯文本 SQL 迁移（见 [5.1 方案 B](#51-postgresql-迁移开发环境--rds)）。

```bash
# 本地重新导出为纯文本 SQL
pg_dump -h localhost -U ecodream -d ecodream --no-owner --no-privileges -f ecodream_backup.sql

# 在 ECS 上直接执行 SQL
PGPASSWORD='YOUR_RDS_PASSWORD' psql -h pgm-xxxxxxxx.pg.rds.aliyuncs.com -U ecodream -d ecodream -f ecodream_backup.sql
```

### Q7: 如何完全重置（清空所有数据）

> **危险操作！仅在全新部署测试时使用！**

```bash
cd /opt/ecodreamomni/app

# 1. 停止并删除容器
docker-compose -f docker-compose.prod.yml down

# 2. 删除 uploads 数据（谨慎！）
rm -rf /opt/ecodreamomni/data/uploads/*

# 3. 重新创建 RDS 数据库（在阿里云控制台操作）
#    注意：创建 PostgreSQL 14 实例，与本地开发环境一致

# 4. 重新启动
docker-compose -f docker-compose.prod.yml up -d
```

---

## 附录

### A. 文件目录结构

```
/opt/ecodreamomni/
├── app/                          # 应用代码和配置
│   ├── docker-compose.prod.yml   # 生产编排
│   ├── .env.prod                 # 环境变量（600权限）
│   └── docker/
│       └── nginx.conf            # Nginx 配置
├── data/
│   └── uploads/                  # 上传文件持久化目录
├── backup.sh                     # 备份脚本
└── backups/                      # 备份存放
```

### B. 关键命令速查

| 操作 | 命令 |
|------|------|
| 启动 | `docker-compose -f docker-compose.prod.yml up -d` |
| 停止 | `docker-compose -f docker-compose.prod.yml down` |
| 查看日志 | `docker-compose -f docker-compose.prod.yml logs -f backend` |
| 重启 | `docker-compose -f docker-compose.prod.yml restart` |
| 进入容器 | `docker-compose -f docker-compose.prod.yml exec backend sh` |
| 查看 Volume | `docker volume ls` |
| 查看资源 | `docker stats` |

### C. 阿里云文档参考

| 主题 | 链接 |
|------|------|
| RDS PostgreSQL 快速入门 | https://help.aliyun.com/zh/rds/apsaradb-rds-for-postgresql/getting-started/quick-start |
| 云数据库 Redis 快速入门 | https://help.aliyun.com/zh/redis/getting-started/quick-start |
| ECS 安全组配置 | https://help.aliyun.com/zh/ecs/user-guide/overview-39 |
| ACR 镜像仓库 | https://help.aliyun.com/zh/acr/getting-started/product-overview |

### D. 持久化数据清单（v1.2 新增）

以下数据在容器重建后**自动恢复**，无需手动重新配置：

| 数据类型 | 存储位置 | 恢复方式 |
|---------|---------|---------|
| 代理配置 | RDS `proxy_configs` 表 | 启动时从 DB 加载到内存 |
| LLM 模型 | RDS `llm_models` 表 | 启动时从 DB 加载 |
| 账户池 | RDS `account_pool_entries` 表 | 启动时从 DB 加载 |
| 上传文件 | `/opt/ecodreamomni/data/uploads/` | Docker Volume 挂载 |

> 首次部署时，若数据库为空，系统会自动从 `.env.prod` 中的环境变量创建代理和 LLM 模型配置。

---

*文档版本: v1.2*
*更新日期: 2026-06-01*

### 版本变更记录

| 版本 | 日期 | 变更内容 |
|------|------|---------|
| v1.2 | 2026-06-01 | 新增代理配置持久化（proxy_configs 表）<br>新增 LLM 多模型环境变量支持<br>PostgreSQL 版本建议改为 14（与本地开发一致）<br>新增纯文本 SQL 迁移方案（跨版本降级）<br>新增代理/LLM 验证步骤 |
| v1.1 | 2026-06-01 | 操作系统改为 Ubuntu 22.04<br>yum → apt，firewall-cmd → ufw<br>新增 Windows pg_dump Docker 方案 |
| v1.0 | 2026-05-31 | 初始版本 |
