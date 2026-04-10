# B5 Docker 与部署 — `demos/` 说明

## 仅构建并运行 Web 镜像

```bash
cd demos
docker build -t b5-demo:local .
docker run --rm -p 8000:8000 b5-demo:local
# 浏览器访问 http://127.0.0.1:8000/health
```

## docker-compose（Web + Postgres）

```bash
cd demos
docker compose up --build
```

- API：<http://127.0.0.1:8000/health>
- Postgres：主机端口 `5433` → 容器 `5432`（与 B1 本地 PG 错开）

停止：`docker compose down`。
