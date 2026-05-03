#!/usr/bin/env python3
"""
B6 微服务——API 网关概念演示 + 健康检查端点

理论对应：B6-微服务与系统设计/理论讲解.md §7（API 网关）、§10（可观测性）

运行方式：python3 05_api_gateway_proxy.py
依赖：pip install fastapi uvicorn httpx
然后：uvicorn 05_api_gateway_proxy:gateway_app --port 9000
"""

from dataclasses import dataclass
import time


# ============================================================
# 1. API 网关的路由表概念
# ============================================================
print("=" * 60)
print("1. API 网关——路由表与转发逻辑")
print("=" * 60)


@dataclass
class Route:
    """网关中的一条路由规则"""
    path_prefix: str         # 路径前缀，如 "/users"
    target_service: str      # 目标服务名，如 "user-service"
    target_url: str          # 目标 URL，如 "http://user-service:8000"
    timeout_seconds: float = 10.0   # 该路由的默认超时


class SimpleGatewayRouter:
    """
    极简网关路由器的核心逻辑。

    真正的 API 网关（Nginx、Kong、Traefik、Envoy）做的事情：
    1. 看请求的 URL 路径 → 匹配路由规则
    2. 找到目标服务的地址 → 转发请求
    3. 把响应原样返回给客户端
    4. 如果目标服务挂了 → 返回 502 Bad Gateway

    这不是可运行的网关，只是帮助理解网关在做什么。
    """

    def __init__(self):
        self.routes: list[Route] = [
            Route("/users", "user-service", "http://user-service:8000"),
            Route("/orders", "order-service", "http://order-service:8001"),
            Route("/products", "product-service", "http://product-service:8002"),
            Route("/chat", "agent-service", "http://agent-service:8003", timeout_seconds=30.0),
            # agent-service 的超时设得比较长，因为 LLM 调用可能很久
        ]

    def find_route(self, path: str) -> Route | None:
        """根据请求路径找到对应的路由"""
        for route in self.routes:
            if path.startswith(route.path_prefix):
                return route
        return None

    def explain_routing(self):
        """演示路由匹配过程"""
        test_paths = [
            "/users/123",
            "/orders/456/items",
            "/products?category=electronics",
            "/chat/completions",
            "/health",
        ]

        for path in test_paths:
            route = self.find_route(path)
            if route:
                print(f"  {path} → [{route.target_service}] {route.target_url}{path}"
                      f" (超时={route.timeout_seconds}s)")
            else:
                print(f"  {path} → 404 Not Found (无匹配路由)")


router = SimpleGatewayRouter()
router.explain_routing()


# ============================================================
# 2. 结构化日志 + trace_id 概念
# ============================================================
print("\n" + "=" * 60)
print("2. 结构化日志（JSON） + trace_id")
print("=" * 60)


import json
import uuid
from datetime import datetime, timezone


def structured_log(level: str, message: str, trace_id: str,
                   extra: dict | None = None) -> str:
    """
    生产级的结构化日志格式。

    为什么用 JSON？
    - 能被日志收集系统（ELK、Loki）自动解析
    - 支持按字段搜索：trace_id="abc123" AND level="ERROR"
    - 不会被换行符搞乱

    为什么每条日志都要带 trace_id？
    - 一个请求可能经过 5 个微服务
    - 每个服务都会写日志
    - 用 trace_id 把分散在 5 个服务里的日志串起来
    """
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "message": message,
        "trace_id": trace_id,
    }
    if extra:
        log_entry.update(extra)
    return json.dumps(log_entry, ensure_ascii=False)


def demo_structured_logging():
    """演示 trace_id 如何贯穿多个服务的日志"""
    trace_id = str(uuid.uuid4())[:8]  # 简化版 trace_id

    print(f"  trace_id: {trace_id}")
    print()

    # 网关的日志
    print("  " + structured_log("INFO", "收到请求 POST /orders", trace_id,
                                {"method": "POST", "path": "/orders"}))

    # 订单服务的日志
    print("  " + structured_log("INFO", "开始处理订单", trace_id,
                                {"order_id": "ord-123", "user_id": "user-456"}))

    # 订单服务调用用户服务
    print("  " + structured_log("DEBUG", "调用用户服务获取用户信息", trace_id,
                                {"target": "user-service", "user_id": "user-456"}))

    # 用户服务的日志（同一个 trace_id!）
    print("  " + structured_log("INFO", "查询用户", trace_id,
                                {"user_id": "user-456", "cache": "hit"}))

    # 回到订单服务，写入数据库
    print("  " + structured_log("INFO", "订单创建成功", trace_id,
                                {"order_id": "ord-123", "duration_ms": 45}))

    print()
    print("  上面所有日志都有同一个 trace_id，可以用 grep trace_id 串起来")
    print(f"  grep {trace_id} *.log → 得到完整的请求链路")


demo_structured_logging()


# ============================================================
# 3. 健康检查端点
# ============================================================
print("\n" + "=" * 60)
print("3. 健康检查端点——K8s 怎么知道你的服务还活着")
print("=" * 60)


def demo_health_checks():
    """
    K8s 用两种探针判断容器状态：

    Liveness Probe（存活探针）：
      "服务还活着吗？"
      失败了 → K8s 杀掉容器并重启
      用来检测死锁、无限循环等进程还"活着但傻了"的情况

    Readiness Probe（就绪探针）：
      "服务能接受流量吗？"
      失败了 → K8s 把 Pod 从 Service 的负载均衡里摘掉
      用来检测依赖还没准备好（数据库还没连上、缓存还在预热）

    常见实现：
    - /health → Liveness（简单：只要进程在就返回 200）
    - /ready → Readiness（复杂：检查所有依赖是否就绪）
    """

    print("""
    FastAPI 健康检查端点示例：

    @app.get("/health")
    def liveness_check():
        # Liveness：最简单，进程活着就返回 200
        return {"status": "ok"}

    @app.get("/ready")
    def readiness_check():
        # Readiness：检查关键依赖
        problems = []
        try:
            db.execute("SELECT 1")   # 数据库通不通？
        except Exception:
            problems.append("db")

        try:
            redis.ping()             # Redis 通不通？
        except Exception:
            problems.append("redis")

        if problems:
            raise HTTPException(
                status_code=503,
                detail=f"not ready: {', '.join(problems)}"
            )
        return {"status": "ready"}

    K8s 配置（简化）：
    livenessProbe:
      httpGet:
        path: /health
        port: 8000
      initialDelaySeconds: 10   # 启动后等 10 秒再开始探
      periodSeconds: 15         # 每 15 秒探一次

    readinessProbe:
      httpGet:
        path: /ready
        port: 8000
      periodSeconds: 5          # 每 5 秒探一次
    """)


demo_health_checks()


print("\n✅ B6 网关、日志与健康检查概念演示完成")
print("理论对应：B6-微服务与系统设计/理论讲解.md §7、§10")
