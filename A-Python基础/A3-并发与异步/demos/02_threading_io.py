"""
02_threading_io.py — IO 等待重叠：多线程对 sleep 类等待有效。

运行：python3 02_threading_io.py
"""

from __future__ import annotations

import time
from threading import Thread


def io_wait(seconds: float, name: str) -> None:
    time.sleep(seconds)
    print(f"  [{name}] 完成")


def main() -> None:
    delay = 0.4

    t0 = time.perf_counter()
    io_wait(delay, "A")
    io_wait(delay, "B")
    io_wait(delay, "C")
    serial = time.perf_counter() - t0
    print(f"串行 3 x sleep({delay}): {serial:.2f}s\n")

    print("并行（3 线程）:")
    t0 = time.perf_counter()
    threads = [Thread(target=io_wait, args=(delay, f"T{i}")) for i in range(3)]
    for th in threads:
        th.start()
    for th in threads:
        th.join()
    parallel = time.perf_counter() - t0
    print(f"总耗时: {parallel:.2f}s（应接近 {delay}s，而非 {3 * delay}s）")


if __name__ == "__main__":
    main()
