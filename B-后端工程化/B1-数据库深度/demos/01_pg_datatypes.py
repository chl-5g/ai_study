"""
01_pg_datatypes.py — PostgreSQL 数据类型实战

对应理论：1.1 数据类型

本 demo 演示 PG 最常用、也最能体现 PG 优势的几个类型：
  - NUMERIC         精确小数，金融场景必用
  - TIMESTAMPTZ     带时区时间戳（best practice）
  - JSONB           二进制 JSON，支持索引
  - UUID            分布式主键首选
  - TEXT[] (数组)    PG 原生支持的数组列
  - INET            网络地址专用类型

运行前：
  1. 确保已 `docker compose up -d` 启动 PG
  2. pip install psycopg2-binary

运行方式：
  python 01_pg_datatypes.py

预期输出：依次插入 3 条 AI Agent 对话记录，然后按不同类型查询验证。
"""

import uuid
from datetime import datetime, timezone

import psycopg2
import psycopg2.extras

from _common import PG_DSN, banner


def main() -> None:
    # psycopg2 默认返回 tuple，注册 dict_cursor 后返回 dict，打印更清楚
    # 注意这是 cursor 级别的选项，不是连接级别的
    conn = psycopg2.connect(PG_DSN)
    conn.autocommit = True  # demo 里简化处理，不手动 commit；生产代码应该显式事务管理
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # ---------- Step 1: 建表，覆盖 6 种类型 ----------
    banner("Step 1: 建表 agent_messages（演示6种PG类型）")

    # DROP + CREATE 方便反复运行 demo
    cur.execute("DROP TABLE IF EXISTS agent_messages;")
    cur.execute("""
        CREATE TABLE agent_messages (
            -- UUID 作为主键：分布式系统无需中心化发号，客户端可先生成再上送
            id           UUID PRIMARY KEY,

            -- TEXT 而不是 VARCHAR(n)：PG 中两者性能一样，TEXT 更灵活
            role         TEXT NOT NULL,
            content      TEXT NOT NULL,

            -- TIMESTAMPTZ 存 UTC，读出时按客户端时区自动换算
            -- 对比 TIMESTAMP：后者不带时区，跨时区部署会踩坑
            created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),

            -- JSONB 比 JSON 更强：解析后二进制存储，支持 GIN 索引和操作符
            -- 用途：存 tool_call 参数、metadata、自定义扩展字段
            metadata     JSONB NOT NULL DEFAULT '{}'::jsonb,

            -- NUMERIC(10,4) 精确小数：4 位小数，总共 10 位数字
            -- 金额/Token 成本这类场景，绝不能用 FLOAT（精度损失）
            token_cost   NUMERIC(10, 4) NOT NULL DEFAULT 0,

            -- 数组类型：一条消息可以带多个标签，不需要再建关联表
            -- 代价是破坏了 1NF（第一范式），需要权衡
            tags         TEXT[] NOT NULL DEFAULT '{}',

            -- INET 专用网络地址类型，支持 CIDR 判断
            client_ip    INET
        );
    """)
    print("  表已创建")

    # ---------- Step 2: 插入示例数据 ----------
    banner("Step 2: 插入 3 条消息")

    rows = [
        (
            uuid.uuid4(),           # 客户端生成 UUID
            "user",
            "帮我查询北京今天的天气",
            datetime.now(timezone.utc),  # 永远用 UTC 时间，到展示层再转时区
            # JSONB 可以直接传 dict，psycopg2 会自动序列化
            psycopg2.extras.Json({"source": "web", "session": "s-001"}),
            0.0023,
            ["weather", "query"],
            "192.168.1.100",
        ),
        (
            uuid.uuid4(),
            "assistant",
            "北京今天晴，25°C",
            datetime.now(timezone.utc),
            psycopg2.extras.Json({
                "tool_call": "get_weather",
                "arguments": {"city": "Beijing"},
                "latency_ms": 420,
            }),
            0.0156,
            ["weather", "response", "tool-use"],
            None,  # assistant 没有 IP
        ),
        (
            uuid.uuid4(),
            "user",
            "谢谢",
            datetime.now(timezone.utc),
            psycopg2.extras.Json({}),
            0.0004,
            ["chitchat"],
            "192.168.1.100",
        ),
    ]

    # executemany 批量插入，比 for 循环 execute 快很多
    cur.executemany("""
        INSERT INTO agent_messages
            (id, role, content, created_at, metadata, token_cost, tags, client_ip)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
    """, rows)
    print(f"  已插入 {len(rows)} 条")

    # ---------- Step 3: JSONB 查询 ----------
    banner("Step 3: JSONB 字段查询（tool_call = get_weather）")

    # @> 是 "包含" 操作符：左边的 jsonb 是否包含右边的 jsonb
    # 这是 JSONB 最常用的查询方式，配合 GIN 索引非常快
    cur.execute("""
        SELECT id, content, metadata->'tool_call' AS tool
        FROM agent_messages
        WHERE metadata @> '{"tool_call": "get_weather"}'::jsonb;
    """)
    for row in cur.fetchall():
        print(f"  {row['content'][:20]} -> tool={row['tool']}")

    # ---------- Step 4: 数组查询 ----------
    banner("Step 4: 数组字段查询（tags 包含 'tool-use'）")

    # && 是 "有交集" 操作符：两个数组是否有公共元素
    # @> 是 "包含" 操作符：左数组是否完全包含右数组
    cur.execute("""
        SELECT content, tags
        FROM agent_messages
        WHERE tags @> ARRAY['tool-use'];
    """)
    for row in cur.fetchall():
        print(f"  tags={row['tags']} content={row['content'][:20]}")

    # ---------- Step 5: TIMESTAMPTZ 查询 + 时区展示 ----------
    banner("Step 5: 时间查询，并按不同时区显示")

    cur.execute("""
        SELECT content,
               created_at AT TIME ZONE 'UTC'              AS utc_time,
               created_at AT TIME ZONE 'Asia/Shanghai'    AS sh_time,
               created_at AT TIME ZONE 'America/New_York' AS ny_time
        FROM agent_messages
        ORDER BY created_at DESC
        LIMIT 1;
    """)
    row = cur.fetchone()
    print(f"  UTC:      {row['utc_time']}")
    print(f"  Shanghai: {row['sh_time']}")
    print(f"  New York: {row['ny_time']}")

    # ---------- Step 6: INET 网段判断 ----------
    banner("Step 6: INET 查询（哪些客户端来自 192.168.1.0/24 网段）")

    # <<= 是 "被包含于" 操作符，PG 原生支持 CIDR 判断
    # 用 TEXT + LIKE 实现同样功能既慢又容易出错
    cur.execute("""
        SELECT DISTINCT client_ip
        FROM agent_messages
        WHERE client_ip <<= inet '192.168.1.0/24';
    """)
    for row in cur.fetchall():
        print(f"  ip={row['client_ip']}")

    # ---------- Step 7: NUMERIC 聚合 ----------
    banner("Step 7: NUMERIC 精确求和（总 token 成本）")

    # SUM 精确小数不会有浮点误差，金融/计费场景必须这样
    cur.execute("SELECT SUM(token_cost) AS total FROM agent_messages;")
    row = cur.fetchone()
    # 注意：NUMERIC 在 Python 侧会被转成 decimal.Decimal，而不是 float
    print(f"  total = {row['total']} (type: {type(row['total']).__name__})")

    cur.close()
    conn.close()

    print("\n完成 ✓")


if __name__ == "__main__":
    main()
