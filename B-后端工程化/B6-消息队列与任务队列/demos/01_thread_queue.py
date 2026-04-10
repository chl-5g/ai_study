"""
01_thread_queue.py — 进程内队列：多个线程共享 queue.Queue。

运行：python3 01_thread_queue.py
"""

from __future__ import annotations

import queue
import threading
import time


def worker(q: queue.Queue[str], name: str) -> None:
    while True:
        item = q.get()
        if item is None:
            q.task_done()
            break
        print(f"  [{name}] 处理: {item}")
        time.sleep(0.05)
        q.task_done()


def main() -> None:
    q: queue.Queue[str] = queue.Queue()
    t = threading.Thread(target=worker, args=(q, "W1"))
    t.start()

    for i in range(5):
        q.put(f"job-{i}")
    q.put(None)
    t.join()
    print("完成")


if __name__ == "__main__":
    main()
