"""
_common.py - 所有 demo 共用的连接信息和工具函数

为什么单独抽出：避免每个 demo 都重复写连接字符串和 reset_table，
学习时应把注意力放在每个 demo 独有的知识点上，而不是样板代码。
"""

import os

# PostgreSQL DSN（Data Source Name）
# 格式：postgresql://<user>:<password>@<host>:<port>/<database>
# 5433 是 docker-compose.yml 里映射到本机的端口
PG_DSN = os.environ.get("B1_PG_DSN", "postgresql://demo:demo@localhost:5433/demo")

# asyncpg 的 DSN 风格略有不同（scheme 也叫 postgresql 也行）
PG_ASYNC_DSN = PG_DSN

# SQLAlchemy 需要 driver 前缀：postgresql+psycopg2://...
SA_DSN = PG_DSN.replace("postgresql://", "postgresql+psycopg2://")
SA_ASYNC_DSN = PG_DSN.replace("postgresql://", "postgresql+asyncpg://")

# Redis URL
REDIS_URL = os.environ.get("B1_REDIS_URL", "redis://localhost:6380/0")


def banner(title: str) -> None:
    """打印漂亮的章节标题，方便运行时区分每一步的输出。"""
    line = "=" * 60
    print(f"\n{line}\n  {title}\n{line}")
