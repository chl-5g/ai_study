"""
07_complete_api.py — 完整 CRUD API 项目（Todo + 用户认证）
整合前面所有概念：路由、Pydantic、依赖注入、中间件、异步、后台任务、错误处理

运行：python3 07_complete_api.py
访问：http://localhost:8000/docs

安装：pip3 install fastapi uvicorn pydantic

认证流程：
    1. POST /auth/register  — 注册用户
    2. POST /auth/login     — 登录，获取 token
    3. 后续请求带上 Header:  Authorization: Bearer <token>
"""

import hashlib
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from enum import Enum

from fastapi import (
    FastAPI, Depends, HTTPException, Request, Header, Query, BackgroundTasks, APIRouter,
)
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Annotated


# ================================================================
# 数据存储（内存模拟，生产环境用数据库）
# ================================================================

class InMemoryDB:
    """内存数据库 — 模拟真实数据库操作"""

    def __init__(self):
        self.users: dict[int, dict] = {}
        self.todos: dict[int, dict] = {}
        self.tokens: dict[str, int] = {}  # token → user_id
        self._user_id_seq = 0
        self._todo_id_seq = 0

    def next_user_id(self) -> int:
        self._user_id_seq += 1
        return self._user_id_seq

    def next_todo_id(self) -> int:
        self._todo_id_seq += 1
        return self._todo_id_seq


# 全局数据库实例
db = InMemoryDB()


# ================================================================
# Lifespan — 应用启动/关闭
# ================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期钩子"""
    print("[启动] 初始化资源...")
    # 预置一个管理员账户
    admin_id = db.next_user_id()
    db.users[admin_id] = {
        "id": admin_id,
        "username": "admin",
        "email": "admin@example.com",
        "password_hash": _hash_password("admin123"),
        "role": "admin",
        "is_active": True,
        "created_at": datetime.now().isoformat(),
    }
    admin_token = "admin-token-001"
    db.tokens[admin_token] = admin_id
    print(f"[启动] 预置管理员: admin / admin123")
    print(f"[启动] 管理员 token: {admin_token}")
    yield
    print("[关闭] 清理资源...")


# ================================================================
# FastAPI App
# ================================================================

app = FastAPI(
    title="Todo API",
    description="完整的 Todo CRUD API，包含用户认证",
    version="2.0.0",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "认证", "description": "注册、登录"},
        {"name": "Todo", "description": "Todo CRUD 操作"},
        {"name": "用户", "description": "用户管理（需要管理员权限）"},
    ],
)


# ================================================================
# 中间件
# ================================================================

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 请求日志 + 计时
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    print(f"  {request.method} {request.url.path} → {response.status_code} ({duration_ms}ms)")
    response.headers["X-Process-Time"] = f"{duration_ms}ms"
    return response


# ================================================================
# 统一错误响应
# ================================================================

class ErrorResponse(BaseModel):
    success: bool = False
    error_code: str
    message: str
    detail: list | dict | None = None


class BusinessError(Exception):
    def __init__(self, error_code: str, message: str, status_code: int = 400):
        self.error_code = error_code
        self.message = message
        self.status_code = status_code


@app.exception_handler(BusinessError)
async def business_error_handler(request: Request, exc: BusinessError):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(error_code=exc.error_code, message=exc.message).model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        field = " → ".join(str(loc) for loc in err["loc"])
        errors.append({"field": field, "message": err["msg"]})
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error_code="VALIDATION_ERROR",
            message=f"参数校验失败，共 {len(errors)} 个错误",
            detail=errors,
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def global_error_handler(request: Request, exc: Exception):
    print(f"[ERROR] {type(exc).__name__}: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(error_code="INTERNAL_ERROR", message="服务器内部错误").model_dump(),
    )


# ================================================================
# 工具函数
# ================================================================

def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _generate_token() -> str:
    return str(uuid.uuid4())


# ================================================================
# Pydantic Schema（请求/响应模型）
# ================================================================

# --- 用户 ---

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=30, description="用户名")
    email: str = Field(..., pattern=r"^[\w.-]+@[\w.-]+\.\w+$", description="邮箱")
    password: str = Field(..., min_length=6, description="密码，至少6位")

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        if not v.replace("_", "").isalnum():
            raise ValueError("用户名只能包含字母、数字和下划线")
        return v.lower()


class LoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: UserRole
    is_active: bool
    created_at: str


class LoginResponse(BaseModel):
    token: str
    user: UserResponse


# --- Todo ---

class TodoPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TodoCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="标题")
    description: str = Field(default="", max_length=2000, description="详细描述")
    priority: TodoPriority = Field(default=TodoPriority.MEDIUM, description="优先级")
    tags: list[str] = Field(default_factory=list, description="标签")
    due_date: str | None = Field(default=None, description="截止日期，格式 YYYY-MM-DD")

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        if len(v) > 10:
            raise ValueError("标签最多10个")
        return [tag.strip().lower() for tag in v if tag.strip()]

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "title": "学习 FastAPI",
                "description": "完成 B2-FastAPI深度 的所有 demo",
                "priority": "high",
                "tags": ["python", "学习"],
                "due_date": "2026-04-15",
            }]
        }
    }


class TodoUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    priority: TodoPriority | None = None
    is_completed: bool | None = None
    tags: list[str] | None = None
    due_date: str | None = None


class TodoResponse(BaseModel):
    id: int
    title: str
    description: str
    priority: TodoPriority
    is_completed: bool
    tags: list[str]
    due_date: str | None
    owner_id: int
    created_at: str
    updated_at: str


class PaginatedTodos(BaseModel):
    total: int
    page: int
    page_size: int
    data: list[TodoResponse]


# ================================================================
# 依赖注入
# ================================================================

async def get_current_user(
    authorization: str | None = Header(default=None),
) -> dict:
    """认证依赖 — 从 token 获取当前用户"""
    if not authorization:
        raise BusinessError("UNAUTHORIZED", "缺少 Authorization header", 401)

    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise BusinessError("UNAUTHORIZED", "Authorization 格式错误", 401)

    token = parts[1]
    user_id = db.tokens.get(token)
    if not user_id:
        raise BusinessError("UNAUTHORIZED", "无效的 token", 401)

    user = db.users.get(user_id)
    if not user:
        raise BusinessError("UNAUTHORIZED", "用户不存在", 401)
    if not user["is_active"]:
        raise BusinessError("FORBIDDEN", "账户已被禁用", 403)

    return user


async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """管理员权限依赖"""
    if user["role"] != "admin":
        raise BusinessError("FORBIDDEN", "需要管理员权限", 403)
    return user


# 类型别名
CurrentUser = Annotated[dict, Depends(get_current_user)]
AdminUser = Annotated[dict, Depends(require_admin)]


# ================================================================
# 后台任务
# ================================================================

activity_log: list[dict] = []


def log_activity(user_id: int, action: str, detail: str):
    """记录用户活动（后台执行）"""
    entry = {
        "user_id": user_id,
        "action": action,
        "detail": detail,
        "timestamp": datetime.now().isoformat(),
    }
    activity_log.append(entry)
    print(f"  [活动日志] 用户{user_id}: {action} - {detail}")


# ================================================================
# 路由：认证
# ================================================================

auth_router = APIRouter(prefix="/auth", tags=["认证"])


@auth_router.post("/register", response_model=UserResponse, status_code=201)
async def register(req: RegisterRequest, bg: BackgroundTasks):
    """注册新用户"""
    # 检查用户名是否已存在
    for user in db.users.values():
        if user["username"] == req.username:
            raise BusinessError("CONFLICT", f"用户名 {req.username} 已被注册", 409)
        if user["email"] == req.email:
            raise BusinessError("CONFLICT", f"邮箱 {req.email} 已被注册", 409)

    user_id = db.next_user_id()
    user = {
        "id": user_id,
        "username": req.username,
        "email": req.email,
        "password_hash": _hash_password(req.password),
        "role": "user",
        "is_active": True,
        "created_at": datetime.now().isoformat(),
    }
    db.users[user_id] = user

    bg.add_task(log_activity, user_id, "REGISTER", f"新用户注册: {req.username}")
    return user


@auth_router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest, bg: BackgroundTasks):
    """
    登录获取 token

    预置账户: admin / admin123（或注册新用户）
    """
    target_user = None
    for user in db.users.values():
        if user["username"] == req.username:
            target_user = user
            break

    if not target_user or target_user["password_hash"] != _hash_password(req.password):
        raise BusinessError("UNAUTHORIZED", "用户名或密码错误", 401)

    if not target_user["is_active"]:
        raise BusinessError("FORBIDDEN", "账户已被禁用", 403)

    token = _generate_token()
    db.tokens[token] = target_user["id"]

    bg.add_task(log_activity, target_user["id"], "LOGIN", f"用户登录: {req.username}")

    return {"token": token, "user": target_user}


app.include_router(auth_router)


# ================================================================
# 路由：Todo CRUD
# ================================================================

todo_router = APIRouter(prefix="/todos", tags=["Todo"])


@todo_router.post("", response_model=TodoResponse, status_code=201)
async def create_todo(
    todo: TodoCreate,
    current_user: CurrentUser,
    bg: BackgroundTasks,
):
    """创建新的 Todo"""
    todo_id = db.next_todo_id()
    now = datetime.now().isoformat()

    todo_data = {
        "id": todo_id,
        **todo.model_dump(),
        "is_completed": False,
        "owner_id": current_user["id"],
        "created_at": now,
        "updated_at": now,
    }
    db.todos[todo_id] = todo_data

    bg.add_task(log_activity, current_user["id"], "CREATE_TODO", f"创建 Todo: {todo.title}")
    return todo_data


@todo_router.get("", response_model=PaginatedTodos)
async def list_todos(
    current_user: CurrentUser,
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=10, ge=1, le=50, description="每页数量"),
    priority: TodoPriority | None = Query(default=None, description="按优先级筛选"),
    is_completed: bool | None = Query(default=None, description="按完成状态筛选"),
    q: str | None = Query(default=None, min_length=1, description="搜索标题"),
    tag: str | None = Query(default=None, description="按标签筛选"),
):
    """
    获取当前用户的 Todo 列表（支持分页、筛选、搜索）
    """
    # 筛选当前用户的 Todo
    user_todos = [
        t for t in db.todos.values()
        if t["owner_id"] == current_user["id"]
    ]

    # 应用筛选条件
    if priority:
        user_todos = [t for t in user_todos if t["priority"] == priority.value]
    if is_completed is not None:
        user_todos = [t for t in user_todos if t["is_completed"] == is_completed]
    if q:
        user_todos = [t for t in user_todos if q.lower() in t["title"].lower()]
    if tag:
        user_todos = [t for t in user_todos if tag.lower() in t["tags"]]

    # 按创建时间倒序
    user_todos.sort(key=lambda t: t["created_at"], reverse=True)

    # 分页
    total = len(user_todos)
    start = (page - 1) * page_size
    end = start + page_size
    page_data = user_todos[start:end]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "data": page_data,
    }


@todo_router.get("/{todo_id}", response_model=TodoResponse)
async def get_todo(todo_id: int, current_user: CurrentUser):
    """获取单个 Todo 详情"""
    todo = db.todos.get(todo_id)
    if not todo:
        raise BusinessError("NOT_FOUND", f"Todo {todo_id} 不存在", 404)
    if todo["owner_id"] != current_user["id"]:
        raise BusinessError("FORBIDDEN", "无权访问此 Todo", 403)
    return todo


@todo_router.put("/{todo_id}", response_model=TodoResponse)
async def update_todo(
    todo_id: int,
    update: TodoUpdate,
    current_user: CurrentUser,
    bg: BackgroundTasks,
):
    """更新 Todo"""
    todo = db.todos.get(todo_id)
    if not todo:
        raise BusinessError("NOT_FOUND", f"Todo {todo_id} 不存在", 404)
    if todo["owner_id"] != current_user["id"]:
        raise BusinessError("FORBIDDEN", "无权修改此 Todo", 403)

    # 只更新传入的字段
    update_data = update.model_dump(exclude_unset=True)
    todo.update(update_data)
    todo["updated_at"] = datetime.now().isoformat()

    bg.add_task(log_activity, current_user["id"], "UPDATE_TODO", f"更新 Todo #{todo_id}")
    return todo


@todo_router.delete("/{todo_id}", status_code=204)
async def delete_todo(
    todo_id: int,
    current_user: CurrentUser,
    bg: BackgroundTasks,
):
    """删除 Todo"""
    todo = db.todos.get(todo_id)
    if not todo:
        raise BusinessError("NOT_FOUND", f"Todo {todo_id} 不存在", 404)
    if todo["owner_id"] != current_user["id"]:
        raise BusinessError("FORBIDDEN", "无权删除此 Todo", 403)

    del db.todos[todo_id]
    bg.add_task(log_activity, current_user["id"], "DELETE_TODO", f"删除 Todo #{todo_id}")
    # 204 No Content — 不返回 body


@todo_router.patch("/{todo_id}/toggle", response_model=TodoResponse)
async def toggle_todo(todo_id: int, current_user: CurrentUser, bg: BackgroundTasks):
    """切换 Todo 完成状态"""
    todo = db.todos.get(todo_id)
    if not todo:
        raise BusinessError("NOT_FOUND", f"Todo {todo_id} 不存在", 404)
    if todo["owner_id"] != current_user["id"]:
        raise BusinessError("FORBIDDEN", "无权操作此 Todo", 403)

    todo["is_completed"] = not todo["is_completed"]
    todo["updated_at"] = datetime.now().isoformat()

    status = "完成" if todo["is_completed"] else "未完成"
    bg.add_task(log_activity, current_user["id"], "TOGGLE_TODO", f"Todo #{todo_id} → {status}")
    return todo


app.include_router(todo_router)


# ================================================================
# 路由：用户管理（管理员）
# ================================================================

admin_router = APIRouter(prefix="/admin/users", tags=["用户"])


@admin_router.get("", response_model=list[UserResponse])
async def admin_list_users(admin: AdminUser):
    """列出所有用户（管理员）"""
    return list(db.users.values())


@admin_router.patch("/{user_id}/toggle-active")
async def admin_toggle_user(user_id: int, admin: AdminUser, bg: BackgroundTasks):
    """启用/禁用用户（管理员）"""
    user = db.users.get(user_id)
    if not user:
        raise BusinessError("NOT_FOUND", f"用户 {user_id} 不存在", 404)
    if user["id"] == admin["id"]:
        raise BusinessError("BAD_REQUEST", "不能禁用自己", 400)

    user["is_active"] = not user["is_active"]
    status = "启用" if user["is_active"] else "禁用"
    bg.add_task(log_activity, admin["id"], "TOGGLE_USER", f"{status}用户 #{user_id}")
    return {"message": f"用户 {user['username']} 已{status}"}


app.include_router(admin_router)


# ================================================================
# 路由：活动日志
# ================================================================

@app.get("/activity-log", tags=["系统"])
async def get_activity_log(admin: AdminUser, limit: int = Query(default=50, ge=1, le=200)):
    """查看活动日志（管理员）"""
    return {"log": activity_log[-limit:], "total": len(activity_log)}


# ================================================================
# 根路由
# ================================================================

@app.get("/", tags=["系统"])
async def root():
    """API 入口 — 使用指南"""
    return {
        "title": "Todo API",
        "version": "2.0.0",
        "docs": "/docs",
        "使用步骤": [
            "1. POST /auth/register — 注册（或使用预置账户 admin/admin123）",
            "2. POST /auth/login — 登录获取 token",
            "3. 后续请求 Header 添加: Authorization: Bearer <token>",
            "4. 开始 CRUD Todo!",
        ],
        "预置账户": {
            "username": "admin",
            "password": "admin123",
            "预置token": "admin-token-001（可直接使用，无需登录）",
        },
    }


# ================================================================
# 启动入口
# ================================================================

if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("Todo API — 完整 CRUD 示例")
    print("Swagger 文档: http://localhost:8000/docs")
    print()
    print("预置账户: admin / admin123")
    print("预置 Token: admin-token-001")
    print()
    print("快速测试:")
    print("  curl -H 'Authorization: Bearer admin-token-001' http://localhost:8000/todos")
    print("=" * 60)

    uvicorn.run(app, host="0.0.0.0", port=8000)
