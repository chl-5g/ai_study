"""
08_asyncio_queue.py — asyncio.Queue 生产者 / 消费者。

运行：python3 08_asyncio_queue.py
"""

from __future__ import annotations

import asyncio
import random


async def producer(q: asyncio.Queue[int | None], n: int) -> None:
    for i in range(n):
        await asyncio.sleep(random.uniform(0.01, 0.05))
        await q.put(i)
        print(f"  produce {i}")
    await q.put(None)


async def consumer(q: asyncio.Queue[int | None], name: str) -> None:
    while True:
        item = await q.get()
        if item is None:
            q.task_done()
            break
        print(f"  {name} consumed {item}")
        q.task_done()


async def main_async() -> None:
    q: asyncio.Queue[int | None] = asyncio.Queue()
    await asyncio.gather(
        producer(q, 6),
        consumer(q, "C1"),
    )


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
