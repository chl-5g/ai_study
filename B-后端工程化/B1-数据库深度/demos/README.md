# B1 数据库深度 — `demos/` 说明

当前目录内**已提供** 4 个 PostgreSQL 相关脚本；理论稿中若还提到更多主题，可后续按同样风格补 `05_*.py` 等。

## 前置依赖

### 1. 启动 PostgreSQL（Docker Compose）

在本目录下运行：

```bash
docker compose up -d
```

默认映射见 `docker-compose.yml`（常见为 `localhost:5433`，避免与系统 PG 冲突）。

### 2. Python 依赖

以各 demo 文件头部注释为准，常见包括：

```bash
pip install psycopg2-binary
```

### 3. 连接信息

以 `_common.py` 与各脚本内常量为准；与 compose 里用户名/库名一致。

## Demo 清单（当前仓库）

| 文件 | 要点 |
|------|------|
| `01_pg_datatypes.py` | PG 数据类型实操 |
| `02_pg_indexes.py` | 索引与查询 |
| `03_pg_explain.py` | `EXPLAIN` / 执行计划 |
| `04_pg_transactions.py` | 事务与隔离级别 |

## 学习建议

- 先读上级 `理论讲解.md` 再跑脚本，对照注释改参数看结果。
- Redis / SQLAlchemy / pgvector 等扩展 demo 若你本地已写，可放入本目录并在此表追加一行，保持编号连续。
