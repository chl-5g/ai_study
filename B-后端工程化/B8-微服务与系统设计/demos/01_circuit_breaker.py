"""
01_circuit_breaker.py — 极简熔断状态机（教学用）。

运行：python3 01_circuit_breaker.py
"""

from __future__ import annotations

import random
import time
from enum import Enum, auto


class State(Enum):
    CLOSED = auto()
    OPEN = auto()
    HALF_OPEN = auto()


class CircuitBreaker:
    def __init__(
        self,
        fail_threshold: int = 3,
        open_seconds: float = 2.0,
    ) -> None:
        self.fail_threshold = fail_threshold
        self.open_seconds = open_seconds
        self._state = State.CLOSED
        self._failures = 0
        self._opened_at = 0.0

    def state(self) -> State:
        if self._state == State.OPEN and (time.monotonic() - self._opened_at) >= self.open_seconds:
            self._state = State.HALF_OPEN
            self._failures = 0
            print("  [breaker] -> HALF_OPEN")
        return self._state

    def call(self, fn):
        st = self.state()
        if st == State.OPEN:
            print("  [breaker] OPEN: 快速失败，不调下游")
            raise RuntimeError("circuit open")

        try:
            result = fn()
        except Exception:
            self._failures += 1
            print(f"  [breaker] 失败计数={self._failures}")
            if self._failures >= self.fail_threshold:
                self._state = State.OPEN
                self._opened_at = time.monotonic()
                print("  [breaker] -> OPEN")
            raise

        # 成功
        if st == State.HALF_OPEN:
            print("  [breaker] HALF_OPEN 成功 -> CLOSED")
        self._state = State.CLOSED
        self._failures = 0
        return result


def flaky_downstream() -> str:
    if random.random() < 0.7:
        raise ConnectionError("timeout")
    return "ok"


def main() -> None:
    random.seed(0)
    cb = CircuitBreaker(fail_threshold=3, open_seconds=1.5)

    for i in range(12):
        print(f"\n--- 请求 {i} ---")
        try:
            r = cb.call(flaky_downstream)
            print("  结果:", r)
        except Exception as e:
            print("  捕获:", type(e).__name__, e)
        time.sleep(0.15)


if __name__ == "__main__":
    main()
