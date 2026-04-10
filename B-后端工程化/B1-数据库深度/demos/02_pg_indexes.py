"""
02_pg_indexes.py — B-tree / GIN / GiST 三种索引对比

对应理论：1.2 索引

核心知识点：
  - 不同索引类型适合不同查询模式
  - 索引未命中的典型原因（函数包裹、左模糊、类型不匹配）
  - 复合索引的左前缀原则

运行前：docker compose up -d
运行方式：python 02_pg_indexes.py
"""

import psycopg2
import psycopg2.extras
from _common import PG_DSN, banner


def explain(cur, sql: str) -> str:
    """返回 EXPLAIN 的第一行（Seq Scan / Index Scan / Bitmap Heap Scan...）。"""
    cur.execute("EXPLAIN " + sql)
    return cur.fetchone()[0]


def main() -> None:
    conn = psycopg2.connect(PG_DSN)
    conn.autocommit = True
    cur = conn.cursor()

    # ---------- 建表 + 造数据 ----------
    banner("准备数据：10000 条文章")
    cur.execute("DROP TABLE IF EXISTS articles;")
    cur.execute("""
        CREATE TABLE articles (
            id      SERIAL PRIMARY KEY,
            title   TEXT NOT NULL,
            content TEXT NOT NULL,
            tags    TEXT[] NOT NULL DEFAULT '{}',
            meta    JSONB NOT NULL DEFAULT '{}'::jsonb
        );
    """)
    # generate_series 是 PG 生成序列的神器，不用在应用层 for 循环
    cur.execute("""
        INSERT INTO articles (title, content, tags, meta)
        SELECT
            'title_' || g,
            'content body ' || g || ' python backend agent',
            ARRAY['tag_' || (g % 100), 'lang_python'],
            jsonb_build_object('views', g, 'author', 'user_' || (g % 50))
        FROM generate_series(1, 10000) g;
    """)
    # ANALYZE 更新统计信息，查询规划器才会做出正确选择
    # 没有 ANALYZE 的新表，规划器可能误判为"小表"而不走索引
    cur.execute("ANALYZE articles;")

    # ---------- B-tree：等值 / 范围 ----------
    banner("B-tree 索引：等值查询")
    cur.execute("CREATE INDEX idx_articles_title ON articles(title);")

    # 无索引时是 Seq Scan，有索引后变成 Index Scan
    plan = explain(cur, "SELECT * FROM articles WHERE title = 'title_5000';")
    print(f"  title 等值 -> {plan}")

    # 左模糊 LIKE '%xxx' 无法使用 B-tree 索引（前缀不确定）
    # 只有右模糊 LIKE 'xxx%' 才能走 B-tree
    plan = explain(cur, "SELECT * FROM articles WHERE title LIKE '%5000';")
    print(f"  title 左模糊 -> {plan}  ← 索引失效！")

    plan = explain(cur, "SELECT * FROM articles WHERE title LIKE 'title_500%';")
    print(f"  title 右模糊 -> {plan}")

    # ---------- 函数包裹导致索引失效 ----------
    banner("陷阱：函数包裹列 → 索引失效")

    # 对列做了 lower() 后，B-tree 索引不再匹配
    plan = explain(cur, "SELECT * FROM articles WHERE lower(title) = 'title_5000';")
    print(f"  lower(title) -> {plan}  ← 失效")

    # 解决方案：建函数索引（表达式索引）
    cur.execute("CREATE INDEX idx_articles_title_lower ON articles(lower(title));")
    plan = explain(cur, "SELECT * FROM articles WHERE lower(title) = 'title_5000';")
    print(f"  建函数索引后 -> {plan}")

    # ---------- GIN：数组包含 / JSONB ----------
    banner("GIN 索引：数组 / JSONB")
    cur.execute("CREATE INDEX idx_articles_tags_gin ON articles USING GIN(tags);")
    cur.execute("CREATE INDEX idx_articles_meta_gin ON articles USING GIN(meta);")

    plan = explain(cur, "SELECT * FROM articles WHERE tags @> ARRAY['tag_42'];")
    print(f"  tags 包含 -> {plan}")

    plan = explain(cur, "SELECT * FROM articles WHERE meta @> '{\"author\": \"user_10\"}'::jsonb;")
    print(f"  JSONB 包含 -> {plan}")

    # ---------- 复合索引 + 左前缀原则 ----------
    banner("复合索引的左前缀原则")
    cur.execute("DROP TABLE IF EXISTS orders;")
    cur.execute("""
        CREATE TABLE orders (
            user_id    INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            amount     NUMERIC(10, 2)
        );
        INSERT INTO orders SELECT g % 100, g % 500, g * 1.5
        FROM generate_series(1, 50000) g;
        CREATE INDEX idx_orders_user_product ON orders(user_id, product_id);
        ANALYZE orders;
    """)

    # 匹配最左列 user_id → 走索引
    plan = explain(cur, "SELECT * FROM orders WHERE user_id = 42;")
    print(f"  user_id = ? -> {plan}")

    # 同时匹配 user_id 和 product_id → 走索引
    plan = explain(cur, "SELECT * FROM orders WHERE user_id = 42 AND product_id = 100;")
    print(f"  user_id + product_id -> {plan}")

    # 只匹配 product_id（跳过最左列）→ 索引失效（走 Seq Scan）
    # 原理：复合索引 B-tree 按 (user_id, product_id) 排序，
    # 没有 user_id 就没法定位 product_id 所在的子树
    plan = explain(cur, "SELECT * FROM orders WHERE product_id = 100;")
    print(f"  只用 product_id -> {plan}  ← 失效")

    cur.close()
    conn.close()
    print("\n完成 ✓")


if __name__ == "__main__":
    main()
