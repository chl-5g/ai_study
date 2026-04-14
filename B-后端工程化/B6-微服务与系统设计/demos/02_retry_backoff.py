"""
02_retry_backoff.py — 指数退避 + 抖动（教学用）。

运行：python3 02_retry_backoff.py
"""

from __future__ import annotations

import random
import time


def retry_with_backoff(
    fn,
    *,
    max_attempts: int = 5,
    base: float = 0.1,
    cap: float = 2.0,
) -> None:
    for attempt in range(1, max_attempts + 1):
        try:
            fn()
            print(f"第 {attempt} 次调用成功")
            return
        except Exception as e:
            print(f"第 {attempt} 次失败: {e}")
            if attempt == max_attempts:
                raise
            exp = min(cap, base * (2 ** (attempt - 1)))
            sleep = random.uniform(0, exp)
            print(f"  睡眠 {sleep:.3f}s 再试")
            time.sleep(sleep)


def main() -> None:
    n = {"v": 0}

    def flaky():
        n["v"] += 1
        if n["v"] < 4:
            raise ConnectionError("try again")
        print("  downstream ok")

    retry_with_backoff(flaky)


if __name__ == "__main__":
    main()
