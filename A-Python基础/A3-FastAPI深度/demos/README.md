# A3 FastAPI 深度 — `demos/` 说明

在目录内执行（需 `pip install fastapi uvicorn pydantic` 等，见各文件头部注释）：

```bash
python3 01_fastapi_basics.py    # 自带 uvicorn 启动，或按文件内说明访问 /docs
```

| 文件 | 要点 |
|------|------|
| `01_fastapi_basics.py` | 路由、路径/查询参数、请求体 |
| `02_pydantic_deep.py` | 校验、Field、嵌套模型 |
| `03_dependency_injection.py` | Depends、子依赖 |
| `04_middleware.py` | 中间件顺序与请求 ID |
| `05_async_routes.py` | async 路由与阻塞注意 |
| `06_error_handling.py` | HTTPException、自定义 handler |
| `07_complete_api.py` | 综合小 API |

详细脉络见上级目录 `理论讲解.md`。
