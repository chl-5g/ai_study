"""
06_error_handling.py — 自定义异常处理器 + 统一错误响应格式
演示：HTTPException、自定义异常、覆盖默认 422、全局异常捕获

运行：python3 06_error_handling.py
访问：http://localhost:8000/docs

安装：pip3 install fastapi uvicorn pydantic
"""

import traceback
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

app = FastAPI(title="错误处理实战", version="1.0.0")


# ============================================================
# 1. 统一错误响应格式
# ============================================================

class ErrorResponse(BaseModel):
    """统一的错误响应格式 — 所有异常都返回这个结构"""
    success: bool = False
    error_code: str = Field(description="错误码，如 NOT_FOUND, VALIDATION_ERROR")
    message: str = Field(description="人类可读的错误信息")
    detail: dict | list | None = Field(default=None, description="详细错误信息（可选）")
    timestamp: str = Field(description="错误发生时间")
    path: str = Field(description="请求路径")


def make_error_response(
    status_code: int,
    error_code: str,
    message: str,
    path: str,
    detail: dict | list | None = None,
) -> JSONResponse:
    """构造统一格式的错误响应"""
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(
            error_code=error_code,
            message=message,
            detail=detail,
            timestamp=datetime.now().isoformat(),
            path=path,
        ).model_dump(),
    )


# ============================================================
# 2. 自定义业务异常
# ============================================================

class BusinessError(Exception):
    """业务逻辑错误基类"""
    def __init__(self, error_code: str, message: str, status_code: int = 400):
        self.error_code = error_code
        self.message = message
        self.status_code = status_code


class NotFoundError(BusinessError):
    """资源不存在"""
    def __init__(self, resource: str, resource_id: int | str):
        super().__init__(
            error_code="NOT_FOUND",
            message=f"{resource} {resource_id} 不存在",
            status_code=404,
        )


class PermissionDeniedError(BusinessError):
    """权限不足"""
    def __init__(self, action: str):
        super().__init__(
            error_code="PERMISSION_DENIED",
            message=f"没有权限执行操作: {action}",
            status_code=403,
        )


class ConflictError(BusinessError):
    """资源冲突（如重复创建）"""
    def __init__(self, message: str):
        super().__init__(
            error_code="CONFLICT",
            message=message,
            status_code=409,
        )


class RateLimitError(BusinessError):
    """请求限流"""
    def __init__(self, retry_after: int = 60):
        super().__init__(
            error_code="RATE_LIMITED",
            message=f"请求过于频繁，请 {retry_after} 秒后重试",
            status_code=429,
        )
        self.retry_after = retry_after


# ============================================================
# 3. 注册异常处理器
# ============================================================

@app.exception_handler(BusinessError)
async def business_error_handler(request: Request, exc: BusinessError):
    """
    处理所有 BusinessError 及其子类
    将业务异常转换为统一格式的 JSON 响应
    """
    return make_error_response(
        status_code=exc.status_code,
        error_code=exc.error_code,
        message=exc.message,
        path=str(request.url.path),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    覆盖 FastAPI 默认的 HTTPException 处理器
    将标准 HTTPException 也转换为统一格式
    """
    # 状态码到错误码的映射
    code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        429: "RATE_LIMITED",
        500: "INTERNAL_ERROR",
    }
    error_code = code_map.get(exc.status_code, f"HTTP_{exc.status_code}")

    return make_error_response(
        status_code=exc.status_code,
        error_code=error_code,
        message=str(exc.detail),
        path=str(request.url.path),
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    """
    覆盖默认的 422 验证错误处理器

    默认的 422 响应格式对前端不太友好，这里转换为统一格式
    并将 Pydantic 的错误详情放在 detail 字段中
    """
    # 提取简化的错误信息
    errors = []
    for error in exc.errors():
        field = " → ".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"],
        })

    return make_error_response(
        status_code=422,
        error_code="VALIDATION_ERROR",
        message=f"请求参数校验失败，共 {len(errors)} 个错误",
        path=str(request.url.path),
        detail=errors,
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    全局异常捕获 — 兜底处理所有未预料的异常

    ⚠️ 生产环境注意：
    - 不要把异常堆栈暴露给客户端（安全风险）
    - 应该记录到日志系统（如 Sentry、ELK）
    - 返回通用的 500 错误
    """
    # 打印到控制台（生产环境应写入日志系统）
    print(f"[UNHANDLED ERROR] {request.method} {request.url.path}")
    print(f"  Exception: {type(exc).__name__}: {exc}")
    traceback.print_exc()

    return make_error_response(
        status_code=500,
        error_code="INTERNAL_ERROR",
        message="服务器内部错误，请稍后重试",
        path=str(request.url.path),
        # 生产环境不要返回具体错误信息！
        # detail={"exception": str(exc)},  # 仅开发环境使用
    )


# ============================================================
# 4. 测试路由 — 触发各种异常
# ============================================================

# 模拟数据库
fake_users = {
    1: {"id": 1, "name": "Alice", "email": "alice@example.com"},
    2: {"id": 2, "name": "Bob", "email": "bob@example.com"},
}
registered_emails = {"alice@example.com", "bob@example.com"}


class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    email: str = Field(..., pattern=r"^[\w.-]+@[\w.-]+\.\w+$")
    age: int = Field(..., ge=0, le=150)


@app.get("/users/{user_id}")
async def get_user(user_id: int):
    """
    获取用户 — 演示 NotFoundError

    测试：
        GET /users/1    → 200 成功
        GET /users/999  → 404 NotFoundError
    """
    user = fake_users.get(user_id)
    if not user:
        raise NotFoundError("用户", user_id)
    return {"success": True, "data": user}


@app.post("/users")
async def create_user(user: UserCreate):
    """
    创建用户 — 演示多种异常

    测试：
        1. 正常创建：{"name": "Charlie", "email": "charlie@test.com", "age": 25}
        2. 邮箱重复：{"name": "Test", "email": "alice@example.com", "age": 25}
        3. 校验失败：{"name": "A", "email": "invalid", "age": -1}
    """
    # 业务校验：邮箱是否已注册
    if user.email in registered_emails:
        raise ConflictError(f"邮箱 {user.email} 已被注册")

    new_id = max(fake_users.keys()) + 1
    new_user = {"id": new_id, "name": user.name, "email": user.email}
    fake_users[new_id] = new_user
    registered_emails.add(user.email)

    return {"success": True, "data": new_user}


@app.delete("/users/{user_id}")
async def delete_user(user_id: int):
    """
    删除用户 — 演示 PermissionDeniedError

    测试：
        DELETE /users/1 → 403 PermissionDeniedError（模拟权限不足）
    """
    if user_id not in fake_users:
        raise NotFoundError("用户", user_id)

    # 模拟权限检查
    raise PermissionDeniedError("删除用户")


@app.get("/http-error")
async def trigger_http_error():
    """
    触发标准 HTTPException — 测试覆盖后的处理器
    """
    raise HTTPException(
        status_code=401,
        detail="Token 已过期，请重新登录",
    )


@app.get("/rate-limited")
async def trigger_rate_limit():
    """触发限流异常"""
    raise RateLimitError(retry_after=30)


@app.get("/server-error")
async def trigger_server_error():
    """
    触发未处理的异常 — 测试全局异常捕获

    生产环境中这类错误应该被监控系统捕获（如 Sentry）
    """
    # 故意触发一个未处理的异常
    result = 1 / 0  # ZeroDivisionError
    return result


@app.get("/validation-demo")
async def validation_demo(
    page: int = 1,
    size: int = 10,
    email: str = "test@example.com",
):
    """
    参数校验演示

    测试：
        /validation-demo?page=abc          → 422（page 不是整数）
        /validation-demo?page=1&size=10    → 200（正常）
    """
    return {"page": page, "size": size, "email": email}


# ============================================================
# 5. 健康检查（不会触发异常）
# ============================================================

@app.get("/")
async def root():
    """根路由 — 返回可用的测试端点"""
    return {
        "message": "错误处理实战",
        "test_endpoints": {
            "GET /users/1": "正常请求",
            "GET /users/999": "404 资源不存在",
            "POST /users": "创建用户（支持 409 冲突、422 校验失败）",
            "DELETE /users/1": "403 权限不足",
            "GET /http-error": "401 HTTP 异常",
            "GET /rate-limited": "429 限流",
            "GET /server-error": "500 服务器错误",
            "GET /validation-demo?page=abc": "422 参数校验失败",
        }
    }


# ============================================================
# 启动入口
# ============================================================

if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("错误处理实战")
    print("Swagger 文档: http://localhost:8000/docs")
    print()
    print("所有错误都返回统一格式：")
    print('  {"success": false, "error_code": "...", "message": "...", ...}')
    print()
    print("访问 GET / 查看所有测试端点")
    print("=" * 60)

    uvicorn.run(app, host="0.0.0.0", port=8000)
