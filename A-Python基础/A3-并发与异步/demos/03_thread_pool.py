"""
03_thread_pool.py — ThreadPoolExecutor 并发多个短 HTTP GET（IO 密集）。

运行：python3 03_thread_pool.py
依赖：pip install requests
无网络或 httpbin 不可达时会打印跳过说明。
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import requests
except ImportError:
    requests = None  # type: ignore


URLS = [
    "https://httpbin.org/delay/1",
    "https://httpbin.org/delay/1",
    "https://httpbin.org/delay/1",
]


def fetch(url: str) -> tuple[str, int]:
    r = requests.get(url, timeout=15)
    return url, r.status_code


def main() -> None:
    if requests is None:
        print("请先安装: pip install requests")
        return

    print("串行请求（约 9s+）...")
    t0 = time.perf_counter()
    try:
        for u in URLS:
            fetch(u)
    except Exception as e:
        print(f"串行失败（可忽略本 demo）: {e}")
        return
    serial = time.perf_counter() - t0
    print(f"串行耗时: {serial:.2f}s\n")

    print("线程池并发（约 1s+）...")
    t0 = time.perf_counter()
    try:
        with ThreadPoolExecutor(max_workers=3) as ex:
            futs = [ex.submit(fetch, u) for u in URLS]
            for fut in as_completed(futs):
                print("  ", fut.result())
    except Exception as e:
        print(f"并发失败: {e}")
        return
    parallel = time.perf_counter() - t0
    print(f"并发耗时: {parallel:.2f}s")


if __name__ == "__main__":
    main()
