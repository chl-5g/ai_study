"""
06_asyncio_event_order.py — 单线程事件循环：协程交替让出执行权。

运行：python3 06_asyncio_event_order.py
"""

from __future__ import annotations

import asyncio


async def ticker(name: str, n: int) -> None:
    for i in range(n):
        print(f"  {name} step {i}")
        await asyncio.sleep(0)


async def main_async() -> None:
    print("两个协程交错打印（await asyncio.sleep(0) 主动让出）:")
    await asyncio.gather(ticker("X", 3), ticker("Y", 3))


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
