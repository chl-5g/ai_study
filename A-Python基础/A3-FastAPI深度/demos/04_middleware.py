"""
04_middleware.py — 中间件实战
演示：CORS、日志、计时、限流、自定义中间件

运行：python3 04_middleware.py
访问：http://localhost:8000/docs

安装：pip3 install fastapi uvicorn pydantic
"""

import time
import uuid
from collections import defaultdict
from datetime import datetime

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

app = FastAPI(title="中间件实战", version="1.0.0")


# ============================================================
# 1. CORS 中间件 — 处理跨域请求
# ============================================================

app.add_middleware(
    CORSMiddleware,
    # 允许的前端域名列表（生产环境不要用 "*"）
    allow_origins=[
        "http://localhost:3000",     # React 开发服务器
        "http://localhost:5173",     # Vite 开发服务器
        "https://your-frontend.com", # 生产环境前端
    ],
    allow_credentials=True,          # 允许携带 Cookie
    allow_methods=["*"],             # 允许所有 HTTP 方法
    allow_headers=["*"],             # 允许所有 Header
    expose_headers=["X-Request-ID"], # 允许前端读取的自定义 Header
    max_age=3600,                    # 预检请求缓存时间（秒）
)
# 注意：CORS 中间件应该在其他中间件之前添加（实际执行时最后进入）


# ============================================================
# 2. 请求计时中间件 — 装饰器写法（简单场景）
# ============================================================

@app.middleware("http")
async def timing_middleware(request: Request, call_next):
    """
    计时中间件 — 记录每个请求的处理耗时

    洋葱模型：
        call_next 之前 = 请求进入时执行
        call_next(request) = 调用下一层（最终到达路由）
        call_next 之后 = 响应返回时执行
    """
    start_time = time.perf_counter()

    # 调用下一层中间件/路由
    response = await call_next(request)

    # 计算耗时
    duration = time.perf_counter() - start_time
    duration_ms = round(duration * 1000, 2)

    # 在响应 Header 中添加耗时信息
    response.headers["X-Process-Time"] = f"{duration_ms}ms"

    return response


# ============================================================
# 3. 请求 ID 中间件 — 追踪每个请求
# ============================================================

@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """
    请求 ID 中间件 — 为每个请求分配唯一 ID，便于日志追踪

    前端可以通过 X-Request-ID header 获取，排查问题时提供给后端
    """
    # 如果客户端传了 X-Request-ID 就用客户端的，否则生成新的
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])

    # 将 request_id 存到 request.state 中，后续中间件和路由都可以访问
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    return response


# ============================================================
# 4. 日志中间件 — 类写法（复杂场景，推荐）
# ============================================================

class LoggingMiddleware(BaseHTTPMiddleware):
    """
    日志中间件 — 记录请求和响应信息

    类写法的优势：
    - 可以在 __init__ 中接收配置参数
    - 可以保持状态
    - 代码组织更清晰
    """

    def __init__(self, app, log_request_body: bool = False):
        super().__init__(app)
        self.log_request_body = log_request_body

    async def dispatch(self, request: Request, call_next):
        # 获取请求信息
        request_id = getattr(request.state, "request_id", "unknown")
        method = request.method
        path = request.url.path
        client_ip = request.client.host if request.client else "unknown"
        query = str(request.query_params) if request.query_params else ""

        # 可选：记录请求体（注意：读取 body 后需要重新设置）
        body_info = ""
        if self.log_request_body and method in ("POST", "PUT", "PATCH"):
            body = await request.body()
            body_info = f" | body={body[:200].decode('utf-8', errors='replace')}"

        print(
            f"[{datetime.now().strftime('%H:%M:%S')}] "
            f"→ {method} {path}"
            f"{f'?{query}' if query else ''}"
            f" | ip={client_ip}"
            f" | rid={request_id}"
            f"{body_info}"
        )

        # 调用下一层
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        print(
            f"[{datetime.now().strftime('%H:%M:%S')}] "
            f"← {method} {path}"
            f" | status={response.status_code}"
            f" | {duration_ms}ms"
            f" | rid={request_id}"
        )

        return response


# 添加日志中间件
app.add_middleware(LoggingMiddleware, log_request_body=True)


# ============================================================
# 5. 简易限流中间件 — 基于 IP 的滑动窗口
# ============================================================

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    限流中间件 — 基于客户端 IP 的滑动窗口限流

    注意：生产环境应使用 Redis 做分布式限流（如 slowapi 库）
    这里用内存字典做演示
    """

    def __init__(self, app, max_requests: int = 30, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # IP → 请求时间戳列表
        self.requests: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        # 某些路径不限流（如健康检查、文档）
        exempt_paths = {"/health", "/docs", "/redoc", "/openapi.json"}
        if request.url.path in exempt_paths:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        # 清理过期的时间戳
        self.requests[client_ip] = [
            t for t in self.requests[client_ip]
            if now - t < self.window_seconds
        ]

        # 检查是否超过限制
        if len(self.requests[client_ip]) >= self.max_requests:
            remaining_time = int(
                self.window_seconds - (now - self.requests[client_ip][0])
            )
            return JSONResponse(
                status_code=429,
                content={
                    "detail": f"请求过于频繁，请 {remaining_time} 秒后重试",
                    "retry_after": remaining_time,
                },
                headers={
                    "Retry-After": str(remaining_time),
                    "X-RateLimit-Limit": str(self.max_requests),
                    "X-RateLimit-Remaining": "0",
                }
            )

        # 记录本次请求
        self.requests[client_ip].append(now)
        remaining = self.max_requests - len(self.requests[client_ip])

        # 正常处理请求
        response = await call_next(request)

        # 添加限流信息到响应头
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response


# 添加限流中间件（每分钟最多 30 次请求）
app.add_middleware(RateLimitMiddleware, max_requests=30, window_seconds=60)


# ============================================================
# 6. 安全头中间件
# ============================================================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """添加安全相关的 HTTP 头"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # 防止 XSS
        response.headers["X-Content-Type-Options"] = "nosniff"
        # 防止点击劫持
        response.headers["X-Frame-Options"] = "DENY"
        # 启用 XSS 过滤
        response.headers["X-XSS-Protection"] = "1; mode=block"
        # 严格传输安全（仅 HTTPS）
        # response.headers["Strict-Transport-Security"] = "max-age=31536000"

        return response


app.add_middleware(SecurityHeadersMiddleware)


# ============================================================
# 中间件执行顺序说明
# ============================================================
#
# add_middleware 的添加顺序和执行顺序是 **相反** 的：
#
# 添加顺序（代码中从上到下）：
#   1. CORSMiddleware
#   2. timing_middleware (装饰器)
#   3. request_id_middleware (装饰器)
#   4. LoggingMiddleware
#   5. RateLimitMiddleware
#   6. SecurityHeadersMiddleware
#
# 请求执行顺序（最后添加的最先执行）：
#   SecurityHeaders → RateLimit → Logging → RequestID → Timing → CORS → 路由
#
# 响应返回顺序（反向）：
#   路由 → CORS → Timing → RequestID → Logging → RateLimit → SecurityHeaders → 客户端


# ============================================================
# 测试路由
# ============================================================

@app.get("/")
async def root():
    """根路由 — 用于测试中间件效果"""
    return {"message": "Hello, Middleware!"}


@app.get("/health")
async def health():
    """健康检查 — 不受限流中间件影响"""
    return {"status": "ok"}


@app.get("/slow")
async def slow_endpoint():
    """慢速端点 — 用于测试计时中间件"""
    import asyncio
    await asyncio.sleep(1)  # 模拟耗时操作
    return {"message": "这个请求处理了 1 秒"}


@app.get("/request-info")
async def request_info(request: Request):
    """
    查看请求信息 — 验证中间件添加的数据
    可以从 request.state 中读取中间件设置的值
    """
    return {
        "request_id": getattr(request.state, "request_id", "N/A"),
        "client_ip": request.client.host if request.client else "unknown",
        "headers": dict(request.headers),
    }


@app.post("/echo")
async def echo(request: Request):
    """回显请求体 — 用于测试日志中间件的 body 记录"""
    body = await request.json()
    return {"received": body}


# ============================================================
# 启动入口
# ============================================================

if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("中间件实战")
    print("Swagger 文档: http://localhost:8000/docs")
    print()
    print("观察控制台日志输出，可以看到中间件的执行过程")
    print("检查响应 Header，可以看到中间件添加的信息：")
    print("  X-Process-Time: 处理耗时")
    print("  X-Request-ID: 请求追踪ID")
    print("  X-RateLimit-*: 限流信息")
    print("=" * 60)

    uvicorn.run(app, host="0.0.0.0", port=8000)
