"""
03_dependency_injection.py — 依赖注入实战
演示：数据库 session 注入、认证、权限检查、嵌套依赖、依赖覆盖（测试）

运行：python3 03_dependency_injection.py
访问：http://localhost:8000/docs

安装：pip3 install fastapi uvicorn pydantic
"""

from fastapi import FastAPI, Depends, HTTPException, Header, Query
from pydantic import BaseModel
from datetime import datetime
from typing import Annotated

app = FastAPI(title="依赖注入实战", version="1.0.0")


# ============================================================
# 1. 基础依赖 — 函数作为依赖
# ============================================================

def common_pagination(
    skip: int = Query(default=0, ge=0, description="跳过条数"),
    limit: int = Query(default=10, ge=1, le=100, description="每页数量"),
) -> dict:
    """
    公共分页参数 — 多个端点复用同一套分页逻辑
    FastAPI 会自动从查询参数中提取 skip 和 limit
    """
    return {"skip": skip, "limit": limit}


# 使用 Annotated 简化类型标注（推荐写法）
PaginationDep = Annotated[dict, Depends(common_pagination)]


@app.get("/items")
async def list_items(pagination: PaginationDep):
    """使用公共分页依赖"""
    fake_items = [f"item_{i}" for i in range(50)]
    start = pagination["skip"]
    end = start + pagination["limit"]
    return {"data": fake_items[start:end], "pagination": pagination}


@app.get("/users")
async def list_users(pagination: PaginationDep):
    """同一个分页依赖，另一个端点复用"""
    fake_users = [f"user_{i}" for i in range(30)]
    start = pagination["skip"]
    end = start + pagination["limit"]
    return {"data": fake_users[start:end], "pagination": pagination}


# ============================================================
# 2. yield 依赖 — 模拟数据库 session 生命周期管理
# ============================================================

class FakeDatabase:
    """模拟数据库连接"""

    def __init__(self):
        self.connected = True
        self.data = {
            1: {"id": 1, "name": "Alice", "role": "admin"},
            2: {"id": 2, "name": "Bob", "role": "user"},
            3: {"id": 3, "name": "Charlie", "role": "user"},
        }
        print(f"  [DB] 连接已建立 (id={id(self)})")

    def query_user(self, user_id: int) -> dict | None:
        return self.data.get(user_id)

    def query_all_users(self) -> list[dict]:
        return list(self.data.values())

    def close(self):
        self.connected = False
        print(f"  [DB] 连接已关闭 (id={id(self)})")


def get_db():
    """
    yield 依赖 — 管理数据库连接的生命周期

    yield 之前：创建资源（在请求处理前执行）
    yield 值：注入给端点函数
    yield 之后：清理资源（在响应发送后执行，即使发生异常也会执行）
    """
    db = FakeDatabase()
    try:
        yield db          # 将 db 注入给使用者
    finally:
        db.close()        # 请求结束后清理（类似 try/finally）


# 使用 Annotated 定义类型别名
DbDep = Annotated[FakeDatabase, Depends(get_db)]


@app.get("/db/users")
async def db_list_users(db: DbDep):
    """使用注入的数据库连接查询所有用户"""
    return {"users": db.query_all_users()}


@app.get("/db/users/{user_id}")
async def db_get_user(user_id: int, db: DbDep):
    """使用注入的数据库连接查询单个用户"""
    user = db.query_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"用户 {user_id} 不存在")
    return user


# ============================================================
# 3. 认证依赖 — 模拟 Token 认证
# ============================================================

# 模拟 token 数据库
FAKE_TOKENS = {
    "token-admin-001": {"user_id": 1, "username": "Alice", "role": "admin"},
    "token-user-002": {"user_id": 2, "username": "Bob", "role": "user"},
    "token-user-003": {"user_id": 3, "username": "Charlie", "role": "user"},
}


class CurrentUser(BaseModel):
    """当前登录用户"""
    user_id: int
    username: str
    role: str


async def get_current_user(
    authorization: str | None = Header(default=None, description="Bearer token"),
) -> CurrentUser:
    """
    认证依赖 — 从 Authorization header 中提取并验证 token

    请求时需要带上 Header:
        Authorization: Bearer token-admin-001
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="缺少 Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 解析 "Bearer <token>" 格式
    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Authorization 格式错误，应为 'Bearer <token>'")

    token = parts[1]
    user_data = FAKE_TOKENS.get(token)
    if not user_data:
        raise HTTPException(status_code=401, detail="无效的 token")

    return CurrentUser(**user_data)


# 类型别名
AuthUserDep = Annotated[CurrentUser, Depends(get_current_user)]


@app.get("/me")
async def get_me(current_user: AuthUserDep):
    """
    获取当前用户信息 — 需要认证

    测试：在 Swagger 文档中添加 Header
        Authorization: Bearer token-admin-001
    """
    return {"user": current_user, "authenticated_at": datetime.now().isoformat()}


# ============================================================
# 4. 权限检查 — 嵌套依赖
# ============================================================

def require_role(*allowed_roles: str):
    """
    权限依赖工厂 — 返回一个依赖函数

    这是一个"依赖工厂"模式：用函数生成依赖，可以参数化
    """
    async def role_checker(current_user: AuthUserDep) -> CurrentUser:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"权限不足，需要角色: {allowed_roles}，当前角色: {current_user.role}"
            )
        return current_user
    return role_checker


# 不同的权限依赖
AdminDep = Annotated[CurrentUser, Depends(require_role("admin"))]
UserOrAdminDep = Annotated[CurrentUser, Depends(require_role("user", "admin"))]


@app.get("/admin/dashboard")
async def admin_dashboard(admin: AdminDep):
    """
    管理员仪表板 — 只有 admin 角色可访问

    依赖链：get_current_user → require_role("admin") → admin_dashboard

    测试：
        ✅ Authorization: Bearer token-admin-001  (Alice, admin)
        ❌ Authorization: Bearer token-user-002   (Bob, user) → 403
    """
    return {"message": f"欢迎管理员 {admin.username}", "secret_data": "机密信息"}


@app.delete("/admin/users/{user_id}")
async def delete_user(user_id: int, admin: AdminDep, db: DbDep):
    """
    删除用户 — 需要 admin 权限 + 数据库访问
    同时注入认证依赖和数据库依赖
    """
    user = db.query_user(user_id)
    if not user:
        raise HTTPException(404, f"用户 {user_id} 不存在")
    return {"message": f"用户 {user['name']} 已被管理员 {admin.username} 删除"}


@app.get("/profile")
async def get_profile(user: UserOrAdminDep):
    """普通用户和管理员都可访问"""
    return {"message": f"你好 {user.username}，你的角色是 {user.role}"}


# ============================================================
# 5. 类作为依赖 — 使用 __call__
# ============================================================

class RateLimiter:
    """
    限流器 — 类作为依赖
    类的好处是可以保持状态（如请求计数）
    """

    def __init__(self, max_requests: int = 5):
        self.max_requests = max_requests
        self.requests: dict[str, list[float]] = {}  # IP → 时间戳列表

    async def __call__(self, authorization: str | None = Header(default=None)) -> None:
        """
        FastAPI 会调用 __call__，就像调用普通函数一样
        """
        # 用 token 模拟 IP（简化示例）
        client_id = authorization or "anonymous"
        now = datetime.now().timestamp()

        if client_id not in self.requests:
            self.requests[client_id] = []

        # 清理 60 秒前的记录
        self.requests[client_id] = [
            t for t in self.requests[client_id]
            if now - t < 60
        ]

        if len(self.requests[client_id]) >= self.max_requests:
            raise HTTPException(
                status_code=429,
                detail=f"请求过于频繁，每分钟最多 {self.max_requests} 次"
            )

        self.requests[client_id].append(now)


# 创建限流器实例（每分钟最多 3 次请求）
rate_limiter = RateLimiter(max_requests=3)


@app.get("/limited", dependencies=[Depends(rate_limiter)])
async def limited_endpoint():
    """
    限流端点 — 每分钟最多 3 次请求

    注意：这里用 dependencies=[...] 而不是参数注入
    因为我们不需要限流器的返回值，只需要它的副作用（限流检查）
    """
    return {"message": "你成功访问了限流端点", "time": datetime.now().isoformat()}


# ============================================================
# 6. 路由级别的依赖 — 整个 Router 共享
# ============================================================

from fastapi import APIRouter

# 这个 Router 下的所有端点都需要认证
authenticated_router = APIRouter(
    prefix="/api/v1",
    tags=["需认证的 API"],
    dependencies=[Depends(get_current_user)],  # Router 级别的依赖
)


@authenticated_router.get("/data")
async def get_data():
    """这个端点自动要求认证（Router 级别依赖）"""
    return {"data": "some protected data"}


@authenticated_router.get("/stats")
async def get_stats():
    """这个端点也自动要求认证"""
    return {"stats": {"total_users": 100, "active_today": 42}}


app.include_router(authenticated_router)


# ============================================================
# 启动入口
# ============================================================

if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("依赖注入实战")
    print("Swagger 文档: http://localhost:8000/docs")
    print()
    print("测试认证：在请求 Header 中添加")
    print("  Authorization: Bearer token-admin-001  (管理员)")
    print("  Authorization: Bearer token-user-002   (普通用户)")
    print("=" * 60)

    uvicorn.run(app, host="0.0.0.0", port=8000)
