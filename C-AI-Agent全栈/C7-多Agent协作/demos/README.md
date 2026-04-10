# C7 多 Agent 协作 — `demos/` 说明

与 [`../理论讲解.md`](../理论讲解.md) 配套：监督者路由多个「子 Agent」（函数模拟）；Fan-out / Fan-in 并行合并。

```bash
cd demos
python3 01_supervisor_router.py
python3 02_fanout_merge_mock.py
```

| 文件 | 要点 | 依赖 |
|------|------|------|
| `01_supervisor_router.py` | 按关键词规则路由到退款 / 搜索 / 通用客服 | 无 |
| `02_fanout_merge_mock.py` | `ThreadPoolExecutor` 并行子任务、`as_completed` 合并输出 | 无（标准库） |
