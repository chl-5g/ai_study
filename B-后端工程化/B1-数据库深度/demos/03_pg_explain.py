"""
03_pg_explain.py — EXPLAIN ANALYZE 读懂执行计划

对应理论：1.3 EXPLAIN 查询分析

核心知识点：
  - EXPLAIN vs EXPLAIN ANALYZE 的区别
  - 读懂 Seq Scan / Index Scan / Bitmap Heap Scan / Nested Loop / Hash Join
  - 关注 cost / rows / actual time / loops
  - 如何发现慢查询的根因

运行：python 03_pg_explain.py
"""

import psycopg2
from _common import PG_DSN, banner


def explain_analyze(cur, sql: str) -> None:
    """运行 EXPLAIN (ANALYZE, BUFFERS) 并打印结果。

    ANALYZE：真实执行一遍查询，拿到实际耗时和实际行数
    BUFFERS：显示 shared buffer 的命中/读取情况（缓存效果）
    """
    cur.execute("EXPLAIN (ANALYZE, BUFFERS, VERBOSE) " + sql)
    for row in cur.fetchall():
        print("  " + row[0])


def main() -> None:
    conn = psycopg2.connect(PG_DSN)
    conn.autocommit = True
    cur = conn.cursor()

    # ---------- 准备数据 ----------
    banner("建表：users + orders")
    cur.execute("DROP TABLE IF EXISTS orders CASCADE; DROP TABLE IF EXISTS users CASCADE;")
    cur.execute("""
        CREATE TABLE users (
            id       SERIAL PRIMARY KEY,
            name     TEXT NOT NULL,
            country  TEXT NOT NULL
        );
        CREATE TABLE orders (
            id       SERIAL PRIMARY KEY,
            user_id  INTEGER NOT NULL REFERENCES users(id),
            amount   NUMERIC(10, 2),
            status   TEXT
        );
        INSERT INTO users (name, country)
        SELECT 'u_' || g, (ARRAY['CN','US','JP','DE'])[1 + g % 4]
        FROM generate_series(1, 5000) g;
        INSERT INTO orders (user_id, amount, status)
        SELECT 1 + g % 5000, g * 1.3, (ARRAY['paid','pending','refunded'])[1 + g % 3]
        FROM generate_series(1, 50000) g;
        ANALYZE users; ANALYZE orders;
    """)

    # ---------- 1. Seq Scan：无索引的代价 ----------
    banner("1. Seq Scan（全表扫描）")
    # 5000 行的小表全扫本身很快，重点看计划结构
    explain_analyze(cur, "SELECT * FROM users WHERE country = 'CN';")
    # 观察点：
    #   - 'Seq Scan on users' 表示全表扫描
    #   - rows=1250 是规划器的估算值，actual time 后的 rows 是实际值
    #   - 估算 vs 实际差距过大 → 需要 VACUUM ANALYZE 更新统计信息

    # ---------- 2. Index Scan：加索引 ----------
    banner("2. Index Scan（走索引）")
    cur.execute("CREATE INDEX idx_users_country ON users(country);")
    explain_analyze(cur, "SELECT * FROM users WHERE country = 'CN';")
    # 现在变成 'Index Scan using idx_users_country'
    # Buffers 里 shared hit 表示命中缓存，read 表示从磁盘读

    # ---------- 3. Bitmap Heap Scan：中等选择性 ----------
    banner("3. Bitmap Heap Scan（中等选择性）")
    # 当匹配行数较多但又不至于全扫时，PG 用 Bitmap Scan：
    #   1) 遍历索引收集所有匹配的 TID（tuple id）到 bitmap
    #   2) 按物理顺序一次性读取 heap page，减少随机 IO
    explain_analyze(cur, "SELECT * FROM orders WHERE status IN ('paid','refunded');")

    # ---------- 4. Nested Loop vs Hash Join ----------
    banner("4a. Nested Loop Join（一侧很小）")
    # 小结果集驱动大结果集时，Nested Loop 最优：对每行小表在大表索引里查一次
    explain_analyze(cur, """
        SELECT u.name, o.amount
        FROM users u JOIN orders o ON o.user_id = u.id
        WHERE u.id = 42;
    """)

    banner("4b. Hash Join（两侧都大）")
    # 两侧数据量都大时，Hash Join 更优：
    #   1) 在较小的一侧建哈希表
    #   2) 遍历另一侧逐行查哈希表
    # 特征：计划里出现 'Hash' 节点，上面是 'Hash Join'
    explain_analyze(cur, """
        SELECT u.country, SUM(o.amount)
        FROM users u JOIN orders o ON o.user_id = u.id
        GROUP BY u.country;
    """)

    # ---------- 5. 识别"规划 vs 实际"偏差 ----------
    banner("5. 规划器误判 —— rows 估算与实际不符")
    # 插入一批极度倾斜的数据
    cur.execute("INSERT INTO orders (user_id, amount, status) SELECT 1, 0.01, 'paid' FROM generate_series(1, 10000);")
    # 没 ANALYZE 前，规划器仍以为 user_id=1 只有少量行
    explain_analyze(cur, "SELECT * FROM orders WHERE user_id = 1;")
    print("\n  ↑ 注意：estimated rows 和 actual rows 差距很大吗？")
    print("    这是典型的'统计信息过期'，生产环境定期 VACUUM ANALYZE 解决。")

    cur.execute("ANALYZE orders;")
    print("\n  运行 ANALYZE 后重新规划：")
    explain_analyze(cur, "SELECT * FROM orders WHERE user_id = 1;")

    cur.close()
    conn.close()
    print("\n完成 ✓")


if __name__ == "__main__":
    main()
