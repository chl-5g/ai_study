"""
02_asyncio_task_queue.py — 用 asyncio.Queue 在协程间传递“后台任务”描述（无 Celery）。

运行：python3 02_asyncio_task_queue.py
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass


@dataclass
class Job:
    job_id: int
    payload: str


async def worker_loop(q: asyncio.Queue[Job | None]) -> None:
    while True:
        job = await q.get()
        if job is None:
            q.task_done()
            break
        print(f"  worker: 模拟耗时处理 job {job.job_id} {job.payload!r}")
        await asyncio.sleep(0.1)
        q.task_done()


async def main_async() -> None:
    q: asyncio.Queue[Job | None] = asyncio.Queue()
    worker = asyncio.create_task(worker_loop(q))

    for i in range(4):
        await q.put(Job(i, f"payload-{i}"))
    await q.put(None)
    await worker


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
