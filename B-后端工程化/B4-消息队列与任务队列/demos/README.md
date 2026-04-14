# B4 消息队列与任务队列 — `demos/` 说明

| 文件 | 要点 |
|------|------|
| `01_thread_queue.py` | 标准库 `queue.Queue`：生产者 / 消费者（进程内） |
| `02_asyncio_task_queue.py` | FastAPI 风格：请求里 `background_tasks` 异步投递（无外部 MQ） |
| `03_redis_list_optional.py` | Redis `LPUSH/BRPOP`（本机无 Redis 则跳过并提示） |

完整 **Celery + Redis/RabbitMQ** 建议用单独 `docker-compose` 起 broker 后再写 worker；本章理论稿第 10–12 节有架构说明。以下为 Redis 演示可选安装：

```bash
brew install redis   # 或 Docker: docker run -d -p 6379:6379 redis:7-alpine
pip install redis
python3 03_redis_list_optional.py
```
