"""
01_gil_bench.py — 验证 CPython GIL：CPU 密集下多线程几乎不加速，多进程可加速。

运行：python3 01_gil_bench.py
环境变量 GIL_BENCH_N：循环次数（默认 5_000_000，可按机器调小）
"""

from __future__ import annotations

import os
import time
from multiprocessing import Process
from threading import Thread


def cpu_spin(n: int) -> None:
    while n > 0:
        n -= 1


def main() -> None:
    n = int(os.environ.get("GIL_BENCH_N", "5000000"))
    print(f"每段任务循环次数 N = {n}（可用环境变量 GIL_BENCH_N 调整）\n")

    t0 = time.perf_counter()
    cpu_spin(n)
    cpu_spin(n)
    serial = time.perf_counter() - t0
    print(f"1) 串行两次 count:     {serial:.3f}s")

    t0 = time.perf_counter()
    t1 = Thread(target=cpu_spin, args=(n,))
    t2 = Thread(target=cpu_spin, args=(n,))
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    threaded = time.perf_counter() - t0
    print(f"2) 两个线程并行:       {threaded:.3f}s  （通常 ≈ 串行，因 GIL）")

    t0 = time.perf_counter()
    p1 = Process(target=cpu_spin, args=(n,))
    p2 = Process(target=cpu_spin, args=(n,))
    p1.start()
    p2.start()
    p1.join()
    p2.join()
    mp = time.perf_counter() - t0
    print(f"3) 两个进程并行:       {mp:.3f}s  （双核机器上通常明显短于串行）")

    print("\n结论：CPU 密集用多进程；IO 密集再考虑线程或 asyncio。")


if __name__ == "__main__":
    main()
