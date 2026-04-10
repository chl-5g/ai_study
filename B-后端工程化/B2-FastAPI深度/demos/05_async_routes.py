"""
05_async_routes.py — 异步路由 + 后台任务 + 异步文件操作
演示：async def vs def、并发请求、BackgroundTasks、异步文件 I/O

运行：python3 05_async_routes.py
访问：http://localhost:8000/docs

安装：pip3 install fastapi uvicorn pydantic aiofiles
（aiofiles 可选，没有也能运行，会跳过异步文件操作的部分演示）
"""

import asyncio
import time
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel, Field

app = FastAPI(title="异步路由与后台任务", version="1.0.0")


# ============================================================
# 1. async def vs def — 核心区别
# ============================================================

@app.get("/async-endpoint")
async def async_endpoint():
    """
    异步路由 — 使用 async def

    适用场景：
    - 内部使用 await（网络请求、异步数据库、异步文件操作）
    - 纯计算（无 I/O）

    ⚠️ 注意：千万不要在 async def 中调用阻塞操作（如 time.sleep、同步数据库）
    这会阻塞整个事件循环，导致所有请求都卡住！
    """
    # 正确：使用 asyncio.sleep（非阻塞）
    await asyncio.sleep(0.1)
    return {"type": "async", "message": "使用 await 的异步路由"}


@app.get("/sync-endpoint")
def sync_endpoint():
    """
    同步路由 — 使用 def（注意：没有 async）

    FastAPI 会自动把 def 路由放到 **线程池** 中执行
    所以即使内部有阻塞操作，也不会阻塞事件循环

    适用场景：
    - 使用同步库（如 requests、同步数据库驱动）
    - 需要调用阻塞的第三方库
    """
    # 这里可以安全地使用阻塞操作，因为 FastAPI 会放到线程池
    time.sleep(0.1)
    return {"type": "sync", "message": "同步路由（自动在线程池中执行）"}


# ============================================================
# 2. 并发演示 — async 的威力
# ============================================================

async def fetch_from_service(service_name: str, delay: float) -> dict:
    """模拟异步调用外部服务"""
    await asyncio.sleep(delay)  # 模拟网络延迟
    return {
        "service": service_name,
        "data": f"{service_name} 的响应数据",
        "latency_ms": int(delay * 1000),
    }


@app.get("/sequential")
async def sequential_calls():
    """
    串行调用 — 依次等待每个服务
    总耗时 = 所有服务延迟之和 = 0.5 + 0.3 + 0.2 = 1.0 秒
    """
    start = time.perf_counter()

    result1 = await fetch_from_service("用户服务", 0.5)
    result2 = await fetch_from_service("订单服务", 0.3)
    result3 = await fetch_from_service("推荐服务", 0.2)

    total_ms = round((time.perf_counter() - start) * 1000, 2)
    return {
        "mode": "串行",
        "total_ms": total_ms,
        "results": [result1, result2, result3],
    }


@app.get("/concurrent")
async def concurrent_calls():
    """
    并发调用 — 同时等待所有服务（使用 asyncio.gather）
    总耗时 ≈ 最慢服务的延迟 = 0.5 秒

    这就是异步的威力：I/O 等待时间可以重叠！
    """
    start = time.perf_counter()

    # asyncio.gather 并发执行多个协程
    result1, result2, result3 = await asyncio.gather(
        fetch_from_service("用户服务", 0.5),
        fetch_from_service("订单服务", 0.3),
        fetch_from_service("推荐服务", 0.2),
    )

    total_ms = round((time.perf_counter() - start) * 1000, 2)
    return {
        "mode": "并发",
        "total_ms": total_ms,
        "说明": "总耗时 ≈ 最慢服务的延迟（约500ms），而非三者之和",
        "results": [result1, result2, result3],
    }


# ============================================================
# 3. 后台任务 — BackgroundTasks
# ============================================================

# 模拟日志存储
task_log: list[str] = []


def write_log(message: str):
    """同步后台任务 — 模拟写日志（可以是阻塞操作）"""
    time.sleep(0.5)  # 模拟耗时写入
    task_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
    print(f"  [后台任务] 日志已写入: {message}")


async def send_notification(user_id: int, event: str):
    """异步后台任务 — 模拟发送通知"""
    await asyncio.sleep(1)  # 模拟网络请求
    task_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 通知: 用户{user_id} - {event}")
    print(f"  [后台任务] 通知已发送: 用户{user_id} - {event}")


class OrderCreate(BaseModel):
    product: str = Field(description="商品名称")
    quantity: int = Field(ge=1, description="数量")


@app.post("/orders")
async def create_order(order: OrderCreate, background_tasks: BackgroundTasks):
    """
    创建订单 — 响应立即返回，后台异步处理日志和通知

    BackgroundTasks 的特点：
    1. 响应先返回给客户端，后台任务之后执行
    2. 多个后台任务按添加顺序串行执行
    3. 支持同步和异步函数
    4. 适合轻量任务（发邮件、写日志）
    5. 重量任务应使用 Celery/arq 等任务队列
    """
    order_id = int(time.time() * 1000) % 100000

    # 添加后台任务（不会阻塞响应）
    background_tasks.add_task(write_log, f"订单创建: #{order_id} - {order.product} x{order.quantity}")
    background_tasks.add_task(send_notification, 1, f"您的订单 #{order_id} 已创建")

    # 立即返回（后台任务还没执行完）
    return {
        "order_id": order_id,
        "product": order.product,
        "quantity": order.quantity,
        "status": "已创建",
        "message": "订单已创建，正在后台发送通知...",
    }


@app.get("/task-log")
async def get_task_log():
    """查看后台任务的执行记录"""
    return {"log": task_log, "count": len(task_log)}


# ============================================================
# 4. 后台任务 + 依赖注入
# ============================================================

class EmailRequest(BaseModel):
    to: str = Field(description="收件人邮箱")
    subject: str = Field(description="邮件主题")
    body: str = Field(description="邮件内容")


async def send_email_task(to: str, subject: str, body: str):
    """模拟异步发送邮件"""
    await asyncio.sleep(2)  # 模拟 SMTP 发送
    task_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 邮件已发送: {to} - {subject}")
    print(f"  [后台任务] 邮件已发送给 {to}: {subject}")


@app.post("/send-email")
async def send_email(email: EmailRequest, background_tasks: BackgroundTasks):
    """
    发送邮件 — 典型的后台任务场景

    客户端不需要等待邮件实际发送完成
    """
    background_tasks.add_task(send_email_task, email.to, email.subject, email.body)
    return {"message": f"邮件将发送给 {email.to}", "status": "queued"}


# ============================================================
# 5. 异步文件操作
# ============================================================

# 临时文件目录
TEMP_DIR = Path("/tmp/fastapi_demo")
TEMP_DIR.mkdir(exist_ok=True)


@app.post("/files/write")
async def write_file(filename: str, content: str):
    """
    异步写文件

    方式1：使用 aiofiles（推荐，真正的异步 I/O）
    方式2：使用 asyncio.to_thread（将同步操作放到线程池）
    """
    filepath = TEMP_DIR / filename

    try:
        # 尝试使用 aiofiles（如果已安装）
        import aiofiles
        async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
            await f.write(content)
        method = "aiofiles（异步I/O）"
    except ImportError:
        # 回退：使用 asyncio.to_thread（Python 3.9+）
        def _write():
            filepath.write_text(content, encoding="utf-8")
        await asyncio.to_thread(_write)
        method = "asyncio.to_thread（线程池）"

    return {
        "filepath": str(filepath),
        "size": len(content),
        "method": method,
    }


@app.get("/files/read")
async def read_file(filename: str):
    """异步读文件"""
    filepath = TEMP_DIR / filename

    if not filepath.exists():
        return {"error": f"文件 {filename} 不存在"}

    try:
        import aiofiles
        async with aiofiles.open(filepath, "r", encoding="utf-8") as f:
            content = await f.read()
    except ImportError:
        content = await asyncio.to_thread(filepath.read_text, "utf-8")

    return {"filename": filename, "content": content, "size": len(content)}


@app.get("/files/list")
async def list_files():
    """列出临时目录中的文件"""
    files = []
    for f in TEMP_DIR.iterdir():
        if f.is_file():
            stat = f.stat()
            files.append({
                "name": f.name,
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })
    return {"directory": str(TEMP_DIR), "files": files}


# ============================================================
# 6. 异步上下文管理 — Lifespan（应用启动/关闭）
# ============================================================

# 注意：这个例子使用了 lifespan，如果要看效果需要用这个 app
# 这里作为知识点展示，实际的 app 使用上面定义的

from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan — 应用级别的启动和关闭钩子

    替代了旧版的 @app.on_event("startup") 和 @app.on_event("shutdown")

    典型用途：
    - 启动时：初始化数据库连接池、加载 ML 模型、连接 Redis
    - 关闭时：释放连接、保存状态、清理临时文件
    """
    # === 启动时执行 ===
    print("[Lifespan] 应用启动：初始化资源...")
    # 例如：初始化数据库连接池
    # app.state.db_pool = await create_pool(...)

    yield  # 应用运行期间

    # === 关闭时执行 ===
    print("[Lifespan] 应用关闭：清理资源...")
    # 例如：关闭数据库连接池
    # await app.state.db_pool.close()


# 如果要使用 lifespan，创建 app 时传入：
# app = FastAPI(lifespan=lifespan)


# ============================================================
# 启动入口
# ============================================================

if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("异步路由与后台任务")
    print("Swagger 文档: http://localhost:8000/docs")
    print()
    print("重点测试：")
    print("  GET /sequential  — 串行调用（约1秒）")
    print("  GET /concurrent  — 并发调用（约0.5秒）")
    print("  POST /orders     — 后台任务（立即返回）")
    print("  GET /task-log    — 查看后台任务日志")
    print("=" * 60)

    uvicorn.run(app, host="0.0.0.0", port=8000)
