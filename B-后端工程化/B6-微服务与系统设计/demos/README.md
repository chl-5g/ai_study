# B6 微服务与系统设计 — `demos/` 说明

教学用**极简内存实现**，便于改参数观察行为；生产请用成熟库（如 `tenacity`、Resilience4j、Envoy、istio 等）。

```bash
cd demos
python3 01_circuit_breaker.py
python3 02_retry_backoff.py
python3 03_idempotency_memory.py
python3 04_token_bucket.py
```

| 文件 | 要点 |
|------|------|
| `01_circuit_breaker.py` | closed → open → half-open |
| `02_retry_backoff.py` | 指数退避 + 随机抖动 |
| `03_idempotency_memory.py` | 同一 key 重复提交只执行一次 |
| `04_token_bucket.py` | 平滑限流直觉 |
