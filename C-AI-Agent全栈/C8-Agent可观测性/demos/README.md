# C8 Agent 可观测性 — `demos/` 说明

与 [`../理论讲解.md`](../理论讲解.md) 配套：**零第三方**的 trace_id 贯穿日志；嵌套阶段耗时模拟 span。

```bash
cd demos
python3 01_trace_contextvars.py
python3 02_span_timings.py
```

| 文件 | 要点 | 依赖 |
|------|------|------|
| `01_trace_contextvars.py` | `contextvars` + 自定义 `LogRecordFactory`，日志带 `trace_id` | 无 |
| `02_span_timings.py` | `contextmanager` 打印 START/END 与毫秒耗时 | 无 |

接入 OpenTelemetry、结构化日志（如 `structlog`）时，可把本 demo 的「一次请求一条 trace」直觉迁移到标准 SDK。
