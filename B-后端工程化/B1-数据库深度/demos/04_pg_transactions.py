"""
04_pg_transactions.py — 事务与隔离级别实操

对应理论：1.4 事务与隔离级别

核心知识点：
  - Read Committed（PG 默认）：可能出现不可重复读
  - Repeatable Read（PG 中使用 Snapshot 实现）：天然阻止不可重复读和幻读
  - Serializable：最严格，靠可串行化快照隔离（SSI）检测冲突后 rollback
  - PG 在 Repeatable Read 下已经能阻止幻读，与 MySQL 不同

验证方式：开两个连接模拟并发事务。

运行：python 04_pg_transactions.py
"""

import psycopg2
from _common import PG_DSN, banner


def main() -> None:
    # 用两个独立连接模拟"事务 A"和"事务 B"
    conn_a = psycopg2.connect(PG_DSN)
    conn_b = psycopg2.connect(PG_DSN)
    # 关闭 autocommit 才能手动控制事务边界
    conn_a.autocommit = False
    conn_b.autocommit = False

    # 管理员连接，用于初始化
    admin = psycopg2.connect(PG_DSN)
    admin.autocommit = True
    acur = admin.cursor()

    acur.execute("DROP TABLE IF EXISTS accounts;")
    acur.execute("""
        CREATE TABLE accounts (
            id      SERIAL PRIMARY KEY,
            owner   TEXT NOT NULL,
            balance NUMERIC(10, 2) NOT NULL
        );
        INSERT INTO accounts (owner, balance) VALUES ('alice', 1000), ('bob', 500);
    """)

    # ========== 场景 1：Read Committed 下的不可重复读 ==========
    banner("场景 1：READ COMMITTED（默认）—— 不可重复读")

    cur_a = conn_a.cursor()
    cur_b = conn_b.cursor()

    # 事务 A 开启
    cur_a.execute("BEGIN;")
    cur_a.execute("SELECT balance FROM accounts WHERE owner = 'alice';")
    print(f"  [A] 第一次读 alice = {cur_a.fetchone()[0]}")

    # 事务 B 并发修改并提交
    cur_b.execute("BEGIN;")
    cur_b.execute("UPDATE accounts SET balance = 9999 WHERE owner = 'alice';")
    conn_b.commit()
    print("  [B] 已修改 alice = 9999 并提交")

    # 事务 A 再读一次 —— 在 READ COMMITTED 下会读到 B 提交的新值
    cur_a.execute("SELECT balance FROM accounts WHERE owner = 'alice';")
    print(f"  [A] 第二次读 alice = {cur_a.fetchone()[0]}  ← 值变了，这就是不可重复读")
    conn_a.commit()

    # 恢复数据
    acur.execute("UPDATE accounts SET balance = 1000 WHERE owner = 'alice';")

    # ========== 场景 2：Repeatable Read 阻止不可重复读 ==========
    banner("场景 2：REPEATABLE READ —— 快照隔离，阻止不可重复读")

    # PG 的 REPEATABLE READ 基于 MVCC 快照：事务开始时拍一个快照，
    # 之后所有读都从这个快照读，完全看不见其他事务的新提交
    cur_a.execute("BEGIN ISOLATION LEVEL REPEATABLE READ;")
    cur_a.execute("SELECT balance FROM accounts WHERE owner = 'alice';")
    print(f"  [A] 第一次读 alice = {cur_a.fetchone()[0]}")

    cur_b.execute("BEGIN;")
    cur_b.execute("UPDATE accounts SET balance = 8888 WHERE owner = 'alice';")
    conn_b.commit()
    print("  [B] 已修改 alice = 8888 并提交")

    cur_a.execute("SELECT balance FROM accounts WHERE owner = 'alice';")
    print(f"  [A] 第二次读 alice = {cur_a.fetchone()[0]}  ← 依然是旧值！快照隔离")
    conn_a.commit()

    acur.execute("UPDATE accounts SET balance = 1000 WHERE owner = 'alice';")

    # ========== 场景 3：Serializable 检测写偏斜 ==========
    banner("场景 3：SERIALIZABLE —— 检测写偏斜并回滚")

    # 经典"写偏斜"场景：
    # 规则：两个账户余额之和必须 >= 0
    # A 事务：看到 alice+bob = 1500，决定从 alice 扣 800
    # B 事务：看到 alice+bob = 1500，决定从 bob 扣 800
    # 两者单独看都合法，但同时提交后总和变 -100，违反约束
    # SERIALIZABLE 会检测到这种"串行化异常"，强制回滚一个

    cur_a.execute("BEGIN ISOLATION LEVEL SERIALIZABLE;")
    cur_b.execute("BEGIN ISOLATION LEVEL SERIALIZABLE;")

    cur_a.execute("SELECT SUM(balance) FROM accounts;")
    total_a = cur_a.fetchone()[0]
    print(f"  [A] 看到总额 = {total_a}")

    cur_b.execute("SELECT SUM(balance) FROM accounts;")
    total_b = cur_b.fetchone()[0]
    print(f"  [B] 看到总额 = {total_b}")

    cur_a.execute("UPDATE accounts SET balance = balance - 800 WHERE owner = 'alice';")
    cur_b.execute("UPDATE accounts SET balance = balance - 800 WHERE owner = 'bob';")

    conn_a.commit()
    print("  [A] 提交成功")
    try:
        conn_b.commit()
        print("  [B] 提交成功（？这不应该发生）")
    except psycopg2.errors.SerializationFailure as e:
        conn_b.rollback()
        print(f"  [B] 提交失败：{type(e).__name__}")
        print("       ↑ SERIALIZABLE 检测到串行化异常，强制回滚")
        print("       应用层应捕获后 retry")

    # ========== 清理 ==========
    cur_a.close()
    cur_b.close()
    conn_a.close()
    conn_b.close()
    acur.close()
    admin.close()
    print("\n完成 ✓")


if __name__ == "__main__":
    main()
