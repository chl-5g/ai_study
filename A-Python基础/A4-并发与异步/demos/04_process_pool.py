"""
04_process_pool.py — ProcessPoolExecutor：小粒度 CPU 任务并行。

运行：python3 04_process_pool.py
"""

from __future__ import annotations

import math
import time
from concurrent.futures import ProcessPoolExecutor


def heavy_sqrt(i: int) -> float:
    # 故意做一点纯 CPU 计算
    x = float(i)
    for _ in range(2000):
        x = math.sqrt(x + 1.0)
    return x


def main() -> None:
    items = list(range(16))

    t0 = time.perf_counter()
    serial = [heavy_sqrt(i) for i in items]
    t_serial = time.perf_counter() - t0
    print(f"串行: {t_serial:.3f}s, 末项 ~ {serial[-1]:.4f}")

    t0 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=4) as ex:
        parallel = list(ex.map(heavy_sqrt, items))
    t_par = time.perf_counter() - t0
    print(f"4 进程: {t_par:.3f}s, 末项 ~ {parallel[-1]:.4f}")


if __name__ == "__main__":
    main()
