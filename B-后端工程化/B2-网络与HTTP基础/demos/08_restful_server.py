#!/usr/bin/env python3
"""
用 Flask 实现最小 RESTful API（Todo CRUD）
演示 RESTful 设计规范的完整实现

安装：pip3 install flask

运行后访问: http://localhost:5000/api/todos
"""

# ============================================================
# RESTful API 设计规范速查
# ============================================================
#
# HTTP 方法    URL              操作         状态码
# GET         /api/todos        列出全部      200
# GET         /api/todos/1      获取单个      200 / 404
# POST        /api/todos        创建         201
# PUT         /api/todos/1      全量更新      200 / 404
# PATCH       /api/todos/1      部分更新      200 / 404
# DELETE      /api/todos/1      删除         204 / 404
#
# 统一响应格式：
# 成功: {"code": 200, "data": {...}, "message": "ok"}
# 失败: {"code": 404, "data": null, "message": "Not found"}

try:
    from flask import Flask, request, jsonify
except ImportError:
    print("请先安装 Flask: pip3 install flask")
    exit(1)

app = Flask(__name__)

# 用内存模拟数据库
todos = [
    {"id": 1, "title": "学习 Python OOP", "done": False},
    {"id": 2, "title": "完成 HTTP Demo", "done": False},
    {"id": 3, "title": "理解 RESTful 设计", "done": True},
]
next_id = 4  # 自增 ID


# ============================================================
# 统一响应格式
# ============================================================

def success_response(data=None, message="ok", status=200):
    """成功响应"""
    return jsonify({"code": status, "data": data, "message": message}), status


def error_response(message="error", status=400):
    """失败响应"""
    return jsonify({"code": status, "data": None, "message": message}), status


# ============================================================
# RESTful 路由
# ============================================================

@app.route("/api/todos", methods=["GET"])
def list_todos():
    """
    GET /api/todos — 列出所有待办事项
    支持分页: ?page=1&per_page=10
    支持过滤: ?done=true
    """
    # 过滤参数
    done_filter = request.args.get("done")
    result = todos

    if done_filter is not None:
        is_done = done_filter.lower() in ("true", "1", "yes")
        result = [t for t in todos if t["done"] == is_done]

    # 分页参数
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))
    start = (page - 1) * per_page
    end = start + per_page

    return success_response({
        "items": result[start:end],
        "total": len(result),
        "page": page,
        "per_page": per_page,
    })


@app.route("/api/todos/<int:todo_id>", methods=["GET"])
def get_todo(todo_id):
    """GET /api/todos/:id — 获取单个待办事项"""
    todo = next((t for t in todos if t["id"] == todo_id), None)
    if not todo:
        return error_response("Todo not found", 404)
    return success_response(todo)


@app.route("/api/todos", methods=["POST"])
def create_todo():
    """
    POST /api/todos — 创建待办事项
    请求体: {"title": "新任务"}
    """
    global next_id

    # 校验请求体
    if not request.is_json:
        return error_response("Content-Type must be application/json", 400)

    data = request.get_json()
    title = data.get("title", "").strip()

    if not title:
        return error_response("title is required", 400)

    # 创建新 Todo
    new_todo = {
        "id": next_id,
        "title": title,
        "done": False,
    }
    next_id += 1
    todos.append(new_todo)

    # 201 Created
    return success_response(new_todo, "Created", 201)


@app.route("/api/todos/<int:todo_id>", methods=["PUT"])
def update_todo(todo_id):
    """
    PUT /api/todos/:id — 全量更新
    请求体: {"title": "更新后标题", "done": true}
    """
    todo = next((t for t in todos if t["id"] == todo_id), None)
    if not todo:
        return error_response("Todo not found", 404)

    if not request.is_json:
        return error_response("Content-Type must be application/json", 400)

    data = request.get_json()

    # PUT 是全量替换，所有字段都必须提供
    if "title" not in data:
        return error_response("title is required for PUT", 400)

    todo["title"] = data["title"]
    todo["done"] = data.get("done", False)

    return success_response(todo)


@app.route("/api/todos/<int:todo_id>", methods=["PATCH"])
def patch_todo(todo_id):
    """
    PATCH /api/todos/:id — 部分更新
    请求体: {"done": true}  (只传要改的字段)
    """
    todo = next((t for t in todos if t["id"] == todo_id), None)
    if not todo:
        return error_response("Todo not found", 404)

    if not request.is_json:
        return error_response("Content-Type must be application/json", 400)

    data = request.get_json()

    # PATCH 只更新传入的字段
    if "title" in data:
        todo["title"] = data["title"]
    if "done" in data:
        todo["done"] = data["done"]

    return success_response(todo)


@app.route("/api/todos/<int:todo_id>", methods=["DELETE"])
def delete_todo(todo_id):
    """DELETE /api/todos/:id — 删除待办事项"""
    global todos
    before = len(todos)
    todos = [t for t in todos if t["id"] != todo_id]

    if len(todos) == before:
        return error_response("Todo not found", 404)

    # 204 No Content（删除成功，无返回体）
    return "", 204


# ============================================================
# 错误处理
# ============================================================

@app.errorhandler(404)
def not_found(e):
    return error_response("Endpoint not found", 404)


@app.errorhandler(405)
def method_not_allowed(e):
    return error_response("Method not allowed", 405)


# ============================================================
# 主程序
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("RESTful API 服务器 (Flask)")
    print("=" * 60)
    print(f"  启动: http://localhost:5000")
    print(f"  按 Ctrl+C 停止\n")
    print(f"  测试命令:")
    print(f"    # 列出所有")
    print(f"    curl http://localhost:5000/api/todos")
    print(f"")
    print(f"    # 获取单个")
    print(f"    curl http://localhost:5000/api/todos/1")
    print(f"")
    print(f"    # 创建")
    print(f'    curl -X POST http://localhost:5000/api/todos \\')
    print(f'      -H "Content-Type: application/json" \\')
    print(f'      -d \'{{"title": "新任务"}}\'')
    print(f"")
    print(f"    # 部分更新")
    print(f'    curl -X PATCH http://localhost:5000/api/todos/1 \\')
    print(f'      -H "Content-Type: application/json" \\')
    print(f'      -d \'{{"done": true}}\'')
    print(f"")
    print(f"    # 删除")
    print(f"    curl -X DELETE http://localhost:5000/api/todos/1")
    print(f"")
    print(f"    # 过滤（只看未完成的）")
    print(f"    curl http://localhost:5000/api/todos?done=false")
    print()

    app.run(debug=True, port=5000)
