"""
07_run_in_executor.py — 用默认线程池跑阻塞函数，避免阻塞事件循环。

运行：python3 07_run_in_executor.py
"""

from __future__ import annotations

import asyncio
import time


def blocking_add(a: int, b: int) -> int:
    time.sleep(0.5)
    return a + b


async def wrong_way() -> None:
    """直接在协程里 sleep/阻塞会卡住整个循环。"""
    t0 = time.perf_counter()
    # 故意用同步 sleep 模拟阻塞 IO —— 不要在生产协程里这么写
    time.sleep(0.3)
    time.sleep(0.3)
    print(f"wrong_way（串行阻塞）: {time.perf_counter() - t0:.2f}s")


async def right_way() -> None:
    loop = asyncio.get_running_loop()
    t0 = time.perf_counter()
    r1 = await loop.run_in_executor(None, blocking_add, 1, 2)
    r2 = await loop.run_in_executor(None, blocking_add, 3, 4)
    print(f"right_way（线程池执行阻塞函数）: {r1}, {r2} in {time.perf_counter() - t0:.2f}s")
    print("若希望两个 blocking_add 重叠，应再用 gather 包两层 run_in_executor。")


async def main_async() -> None:
    await wrong_way()
    await right_way()


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
