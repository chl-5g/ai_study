# B1 - 数据库深度 Demos

15 个可运行 demo，覆盖 PostgreSQL / pgvector / Redis / SQLAlchemy 全部知识点。

## 前置依赖

### 1. 启动 PostgreSQL + pgvector + Redis（Docker Compose）

在本目录下运行：

```bash
docker compose up -d
```

`docker-compose.yml` 会启动：
- `pgvector/pgvector:pg16` — PostgreSQL 16 + pgvector 扩展，监听 `localhost:5433`
- `redis:7-alpine` — Redis 7，监听 `localhost:6380`

> 端口故意错开默认 5432/6379，避免和本机已有服务冲突。

### 2. Python 依赖

```bash
pip install psycopg2-binary asyncpg sqlalchemy[asyncio] alembic redis pgvector numpy
```

Python 3.10+。

### 3. 连接信息（所有 demo 共用）

```python
PG_DSN = "postgresql://demo:demo@localhost:5433/demo"
REDIS_URL = "redis://localhost:6380/0"
```

所有 demo 的顶部都写明了前置条件、运行方式、预期输出。

## Demo 清单

| # | 文件 | 对应理论章节 | 核心知识点 |
|---|------|-------------|-----------|
| 01 | `01_pg_datatypes.py` | 1.1 | PG 数据类型（JSONB/UUID/TIMESTAMPTZ/数组） |
| 02 | `02_pg_indexes.py` | 1.2 | B-tree/GIN/GiST 索引对比，索引未命中案例 |
| 03 | `03_pg_explain.py` | 1.3 | EXPLAIN ANALYZE 读执行计划 |
| 04 | `04_pg_transactions.py` | 1.4 | 四种隔离级别实操、脏读/不可重复读/幻读 |
| 05 | `05_pg_jsonb.py` | 1.5 | JSONB 查询操作符、路径访问、GIN 索引 |
| 06 | `06_pg_fulltext.py` | 1.6 | tsvector/tsquery 全文搜索 |
| 07 | `07_pgvector_basic.py` | 2.1-2.2 | pgvector 建表、插入、余弦相似度查询 |
| 08 | `08_pgvector_hnsw_rag.py` | 2.3-2.5 | HNSW 索引 + 完整 RAG 检索流程 |
| 09 | `09_redis_strings.py` | 3.1 String | 字符串/计数器/分布式锁 |
| 10 | `10_redis_hash_list_zset.py` | 3.1 | Hash/List/Set/ZSet 典型场景 |
| 11 | `11_redis_cache_patterns.py` | 3.2, 3.4 | 缓存击穿/穿透/雪崩及应对 |
| 12 | `12_redis_stream.py` | 3.1 Stream | Redis Stream 作为 Agent 任务队列 |
| 13 | `13_sqlalchemy_basic.py` | 4.1-4.3 | Engine/Session/Model 2.x 风格 |
| 14 | `14_sqlalchemy_relations.py` | 4.4-4.5 | 一对多/多对多/懒加载/急加载/N+1 |
| 15 | `15_sqlalchemy_alembic.py` | 4.6 | Alembic 迁移完整流程 |

## 学习建议

- 按顺序跑，每个 demo 都修改参数观察结果
- 读懂注释后把 `# 为什么这样做` 的问题默答一遍
- 遇到卡壳的地方直接问 AI，不要跳过
