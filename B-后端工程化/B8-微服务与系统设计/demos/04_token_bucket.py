"""
04_token_bucket.py — 令牌桶：平均速率 + 允许突发。

运行：python3 04_token_bucket.py
"""

from __future__ import annotations

import time


class TokenBucket:
    def __init__(self, rate: float, capacity: float) -> None:
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last = time.monotonic()

    def allow(self) -> bool:
        now = time.monotonic()
        elapsed = now - self.last
        self.last = now
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False


def main() -> None:
    # 每秒补充 2 个令牌，桶容量 3（允许突发 3 次连点）
    b = TokenBucket(rate=2.0, capacity=3.0)
    for i in range(10):
        ok = b.allow()
        print(f"req {i}: {'通过' if ok else '拒绝'}")
        time.sleep(0.15)


if __name__ == "__main__":
    main()
