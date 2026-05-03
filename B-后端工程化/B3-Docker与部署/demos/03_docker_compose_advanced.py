#!/usr/bin/env python3
"""
Docker Compose 编排演示——把多个服务串成一个本地开发环境

运行方式：docker compose up (需要 Docker 环境)
或阅读本文件理解 docker-compose.yml 各个部分的作用
"""


# ============================================================
# 完整 docker-compose.yml 带逐行注释
# ============================================================

demo_compose = """
# docker-compose.yml
# 这是一个完整的 AI Agent 后端开发环境：FastAPI + PostgreSQL + Redis + pgvector

version: "3.9"
#   ↑ Compose 文件格式版本，3.9 兼容性好

# ============================================================
# 网络定义
# ============================================================
networks:
  ai-network:
    driver: bridge
    # bridge 网络：每个容器有自己的 IP，容器间可以通过服务名互相访问
    # 比如 FastAPI 可以用 postgres:5432 连接数据库（不用记 IP）

# ============================================================
# 持久化卷定义
# ============================================================
volumes:
  pgdata:
    # PostgreSQL 的数据文件存这里。容器删了数据还在。
    # Docker 管理，在宿主机上的位置：docker volume inspect pgdata
  redisdata:
    # Redis 的 RDB/AOF 持久化文件

# ============================================================
# 服务定义
# ============================================================
services:

  # --- 数据库：PostgreSQL + pgvector ---
  postgres:
    image: pgvector/pgvector:pg16
    #   ↑ 官方 pgvector 镜像（PostgreSQL 16 + pgvector 扩展）

    container_name: ai_postgres
    #   ↑ 容器名字，方便 docker logs ai_postgres

    environment:
      # 这些环境变量会被 PostgreSQL 容器自动读取，初始化数据库
      POSTGRES_USER: ai_app
      POSTGRES_PASSWORD: ${DB_PASSWORD:-dev_password}
      #   ↑ ${DB_PASSWORD:-dev_password} 意思是：
      #      优先读 .env 文件里的 DB_PASSWORD
      #      读不到就用 dev_password（仅开发环境！生产不要这样）
      POSTGRES_DB: ai_platform

    ports:
      - "5432:5432"
      #   ↑ 宿主机端口:容器端口
      #   5432 是 PG 默认端口

    volumes:
      - pgdata:/var/lib/postgresql/data
      #   ↑ 把卷 pgdata 挂到容器里的数据目录
      #   这样 docker compose down 不会丢数据

      - ./init.sql:/docker-entrypoint-initdb.d/init.sql:ro
      #   ↑ 初始化脚本：容器首次启动时自动执行
      #   :ro = read-only，防止容器内误改

    networks:
      - ai-network

    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ai_app -d ai_platform"]
      interval: 10s
      timeout: 5s
      retries: 5
      # pg_isready 是 PG 自带工具，检查数据库是否准备好接受连接

  # --- 缓存：Redis ---
  redis:
    image: redis:7-alpine
    #   ↑ alpine 版本：基于 Alpine Linux，超级小（~30MB）
    container_name: ai_redis

    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    #   ↑ --appendonly yes：开启 AOF 持久化
    #   ↑ --maxmemory 256mb：最多用 256MB 内存
    #   ↑ --maxmemory-policy allkeys-lru：超限时淘汰最久未使用的 key

    ports:
      - "6379:6379"

    volumes:
      - redisdata:/data

    networks:
      - ai-network

    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  # --- API 服务：FastAPI ---
  api:
    build:
      context: .
      #   ↑ Dockerfile 在哪个目录（当前目录）

      dockerfile: Dockerfile
      #   ↑ 用哪个 Dockerfile

      target: development
      #   ↑ 多阶段构建里的 stage 名字
      #   ↑ 可以选择用 development（带热重载）还是 production（优化过的）

    container_name: ai_api

    environment:
      DATABASE_URL: postgresql+asyncpg://ai_app:${DB_PASSWORD:-dev_password}@postgres:5432/ai_platform
      #   ↑ 注意 host 写的是 postgres（服务名！不是 localhost）
      #   在 Compose 网络里，服务名会自动解析为容器的内网 IP

      REDIS_URL: redis://redis:6379/0
      #   ↑ /0 是 Redis 的数据库编号（0-15）

    ports:
      - "8000:8000"

    volumes:
      - .:/app
      #   ↑ 开发模式：当前目录挂载到容器的 /app
      #   好处：改了代码不用重建镜像，容器里直接生效
      #   生产模式要去掉这行！

    depends_on:
      postgres:
        condition: service_healthy
        # condition: service_healthy 是 Compose v3.9+ 的特性
        # 等 postgres 的健康检查通过后才启动 api
        # 比 depends_on 不加条件可靠得多！
      redis:
        condition: service_healthy

    networks:
      - ai-network

    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    #   ↑ --reload：代码变化自动重启（仅开发环境！生产用 gunicorn）

# ============================================================
# 常用命令速查
# ============================================================
# docker compose up          启动所有服务（前台）
# docker compose up -d       后台启动
# docker compose down        停止并删除容器（数据卷保留）
# docker compose down -v     停止并删除容器 + 数据卷（⚠️ 数据清空）
# docker compose logs -f api 实时看 api 服务的日志
# docker compose ps          查看所有服务的状态
# docker compose exec api bash  进 api 容器里执行命令
# docker compose build       重新构建镜像
# docker compose restart api 重启单独一个服务
"""

print(demo_compose)
print("\n✅ 将上面的内容保存为 docker-compose.yml，然后在同目录运行：docker compose up -d")
