"""
03_idempotency_memory.py — 进程内幂等键：同一 key 只执行一次副作用。

运行：python3 03_idempotency_memory.py
生产应把结果存 Redis/DB 并设 TTL。
"""

from __future__ import annotations


def main() -> None:
    seen: dict[str, str] = {}

    def pay(order_id: str, idem_key: str) -> str:
        if idem_key in seen:
            print(f"  重复请求，返回缓存结果: {seen[idem_key]}")
            return seen[idem_key]
        print(f"  首次执行扣款逻辑 order={order_id}")
        result = f"txn-{order_id}-ok"
        seen[idem_key] = result
        return result

    k = "client-uuid-001"
    print(pay("A1", k))
    print(pay("A1", k))
    print(pay("B2", "other-key"))


if __name__ == "__main__":
    main()
