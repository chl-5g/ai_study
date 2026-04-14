"""
01_fastapi_basics.py — 最小 FastAPI 应用
演示：路由、路径参数、查询参数、请求体

运行：python3 01_fastapi_basics.py
访问：http://localhost:8000/docs 查看 Swagger 文档

安装：pip3 install fastapi uvicorn pydantic
"""

from fastapi import FastAPI, Query, Path, Body
from pydantic import BaseModel, Field
from enum import Enum

# ========== 创建 FastAPI 应用 ==========

app = FastAPI(
    title="FastAPI 基础示例",
    description="演示路由、路径参数、查询参数、请求体",
    version="1.0.0",
)


# ========== 1. 最简单的路由 ==========

@app.get("/")
async def root():
    """根路由，返回欢迎信息"""
    return {"message": "Hello, FastAPI!"}


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "ok"}


# ========== 2. 路径参数 ==========

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    """
    路径参数：user_id 会自动转为 int
    如果传入非整数（如 /users/abc），FastAPI 自动返回 422 错误
    """
    return {"user_id": user_id, "name": f"用户_{user_id}"}


# 枚举类型的路径参数 — 限制可选值
class ModelName(str, Enum):
    ALEXNET = "alexnet"
    RESNET = "resnet"
    LENET = "lenet"


@app.get("/models/{model_name}")
async def get_model(model_name: ModelName):
    """
    枚举路径参数：只接受 alexnet/resnet/lenet
    其他值会返回 422 错误
    """
    messages = {
        ModelName.ALEXNET: "Deep Learning FTW!",
        ModelName.RESNET: "LeCun would be proud",
        ModelName.LENET: "Have some residuals",
    }
    return {"model_name": model_name.value, "message": messages[model_name]}


# Path() 参数校验
@app.get("/items/{item_id}")
async def get_item(
    item_id: int = Path(
        ...,                    # 必填（路径参数本来就是必填的）
        title="物品ID",
        description="数据库中的物品唯一标识",
        ge=1,                   # >= 1
        le=10000,               # <= 10000
    )
):
    """使用 Path() 对路径参数进行校验和文档增强"""
    return {"item_id": item_id}


# ========== 3. 查询参数 ==========

# 模拟数据库
fake_items_db = [
    {"name": f"Item_{i}", "price": i * 10.5}
    for i in range(1, 51)
]


@app.get("/items")
async def list_items(
    skip: int = Query(default=0, ge=0, description="跳过前N条"),
    limit: int = Query(default=10, ge=1, le=100, description="每页数量"),
    q: str | None = Query(default=None, min_length=1, max_length=50, description="搜索关键词"),
):
    """
    查询参数演示：
    - skip/limit 用于分页
    - q 是可选的搜索参数

    示例：/items?skip=0&limit=5&q=Item_1
    """
    results = fake_items_db[skip: skip + limit]
    if q:
        results = [item for item in results if q.lower() in item["name"].lower()]
    return {
        "total": len(fake_items_db),
        "skip": skip,
        "limit": limit,
        "query": q,
        "data": results,
    }


# 多值查询参数
@app.get("/search")
async def search(
    tags: list[str] = Query(default=[], description="标签列表，可传多个"),
):
    """
    多值查询参数：/search?tags=python&tags=fastapi
    """
    return {"tags": tags, "count": len(tags)}


# ========== 4. 请求体 ==========

class ItemCreate(BaseModel):
    """创建物品的请求体模型"""
    name: str = Field(..., min_length=1, max_length=100, description="物品名称")
    price: float = Field(..., gt=0, description="价格，必须大于0")
    description: str | None = Field(default=None, max_length=500, description="物品描述")
    tags: list[str] = Field(default_factory=list, description="标签列表")
    is_published: bool = Field(default=False, description="是否发布")

    # 提供请求体示例，会显示在 Swagger 文档中
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "MacBook Pro",
                    "price": 14999.0,
                    "description": "Apple 笔记本电脑",
                    "tags": ["电子产品", "苹果"],
                    "is_published": True,
                }
            ]
        }
    }


class ItemResponse(BaseModel):
    """物品响应模型"""
    id: int
    name: str
    price: float
    description: str | None
    tags: list[str]
    is_published: bool


# 内存存储
items_store: dict[int, dict] = {}
next_id = 1


@app.post("/items", response_model=ItemResponse, status_code=201)
async def create_item(item: ItemCreate):
    """
    创建物品 — 请求体会根据 ItemCreate 模型自动校验
    校验失败返回 422，成功返回 201 + 创建的物品
    """
    global next_id
    item_data = {"id": next_id, **item.model_dump()}
    items_store[next_id] = item_data
    next_id += 1
    return item_data


# ========== 5. 混合参数：路径 + 查询 + 请求体 ==========

class ItemUpdate(BaseModel):
    """更新物品的请求体（所有字段可选）"""
    name: str | None = None
    price: float | None = Field(default=None, gt=0)
    description: str | None = None
    tags: list[str] | None = None
    is_published: bool | None = None


@app.put("/items/{item_id}")
async def update_item(
    item_id: int = Path(..., ge=1, description="物品ID"),          # 路径参数
    dry_run: bool = Query(default=False, description="试运行，不实际更新"),  # 查询参数
    item: ItemUpdate = Body(..., description="更新内容"),            # 请求体
):
    """
    同时使用路径参数、查询参数、请求体
    FastAPI 自动区分三种参数来源
    """
    if item_id not in items_store:
        return {"error": f"物品 {item_id} 不存在"}

    update_data = item.model_dump(exclude_unset=True)  # 只取用户实际传入的字段

    if dry_run:
        return {"dry_run": True, "would_update": update_data}

    items_store[item_id].update(update_data)
    return items_store[item_id]


# ========== 6. 多种 HTTP 方法 ==========

@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    """删除物品"""
    if item_id in items_store:
        deleted = items_store.pop(item_id)
        return {"deleted": deleted}
    return {"error": f"物品 {item_id} 不存在"}


@app.patch("/items/{item_id}/publish")
async def publish_item(item_id: int):
    """发布物品（PATCH 用于部分更新）"""
    if item_id not in items_store:
        return {"error": f"物品 {item_id} 不存在"}
    items_store[item_id]["is_published"] = True
    return items_store[item_id]


# ========== 启动入口 ==========

if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("FastAPI 基础示例")
    print("Swagger 文档: http://localhost:8000/docs")
    print("ReDoc 文档:   http://localhost:8000/redoc")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8000)
