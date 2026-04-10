#!/usr/bin/env python3
"""
02_fanout_merge_mock.py — Fan-out / Fan-in：并行「子任务」再合并（线程池模拟）

依赖：无（标准库 concurrent.futures）
运行：python3 02_fanout_merge_mock.py
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed


def slow_fetch(name: str, delay: float) -> tuple[str, str]:
    time.sleep(delay)
    return name, f"{name} 结果 delay={delay}"


def main() -> None:
    tasks = [("源A", 0.2), ("源B", 0.15), ("源C", 0.25)]
    merged: list[str] = []
    with ThreadPoolExecutor(max_workers=3) as ex:
        futs = [ex.submit(slow_fetch, n, d) for n, d in tasks]
        for fut in as_completed(futs):
            name, text = fut.result()
            merged.append(f"[{name}] {text}")
    print("合并输出:\n", "\n".join(sorted(merged)))


if __name__ == "__main__":
    main()
