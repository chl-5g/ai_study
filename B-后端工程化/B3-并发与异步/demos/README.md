# B3 并发与异步 — `demos/` 说明

在目录内执行：`python3 01_gil_bench.py`（依此类推）。

| 文件 | 要点 |
|------|------|
| `01_gil_bench.py` | CPU 密集：多线程 vs 多进程 vs 串行（验证 GIL） |
| `02_threading_io.py` | IO 密集：`time.sleep` 模拟，多线程重叠等待 |
| `03_thread_pool.py` | `ThreadPoolExecutor` 并发 HTTP（需网络，失败则跳过） |
| `04_process_pool.py` | `ProcessPoolExecutor` 并行 CPU 小任务 |
| `05_asyncio_gather.py` | `asyncio.gather` 并发多个 `asyncio.sleep` |
| `06_asyncio_event_order.py` | 单线程协程调度顺序（打印顺序可预测） |
| `07_run_in_executor.py` | 在线程池里跑阻塞函数，避免卡住事件循环 |
| `08_asyncio_queue.py` | `asyncio.Queue` 生产者 / 消费者 |

可选环境变量：`GIL_BENCH_N`（默认 5000000）控制 `01` 的计算量。
