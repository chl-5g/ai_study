"""
05_asyncio_gather.py — asyncio.gather 并发 sleep（协程重叠等待）。

运行：python3 05_asyncio_gather.py
"""

from __future__ import annotations

import asyncio
import time


async def slow(name: str, seconds: float) -> str:
    await asyncio.sleep(seconds)
    return f"{name} done"


async def main_async() -> None:
    t0 = time.perf_counter()
    a = await slow("A", 0.3)
    b = await slow("B", 0.3)
    c = await slow("C", 0.3)
    serial = time.perf_counter() - t0
    print("串行 await:", a, b, c)
    print(f"耗时 ~0.9s: {serial:.2f}s\n")

    t0 = time.perf_counter()
    results = await asyncio.gather(
        slow("A", 0.3),
        slow("B", 0.3),
        slow("C", 0.3),
    )
    parallel = time.perf_counter() - t0
    print("gather:", results)
    print(f"耗时 ~0.3s: {parallel:.2f}s")


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
