#!/usr/bin/env python3
"""
CORS（跨域资源共享）问题演示与解决
前后端分离开发中最常遇到的问题之一

安装：pip3 install flask flask-cors
"""

# ============================================================
# CORS 原理
# ============================================================
#
# 什么是跨域？
#   当前页面 URL 和请求的 API URL 的 协议/域名/端口 任何一个不同，就是跨域
#
#   http://localhost:3000  →  http://localhost:5000/api   ← 端口不同，跨域！
#   http://example.com     →  https://api.example.com    ← 协议和子域不同，跨域！
#
# 为什么浏览器要限制跨域？
#   安全！防止恶意网站偷取你在其他网站的数据（CSRF 攻击）
#
# 注意：只有浏览器会限制！curl、Python requests 不受此限制
#
# CORS 解决方案：
#   服务端在响应头中声明"允许哪些源访问"
#
# 关键响应头:
#   Access-Control-Allow-Origin: https://myapp.com   (允许的源)
#   Access-Control-Allow-Methods: GET, POST, PUT      (允许的方法)
#   Access-Control-Allow-Headers: Content-Type, Authorization  (允许的请求头)
#   Access-Control-Allow-Credentials: true             (允许携带 Cookie)
#   Access-Control-Max-Age: 3600                       (预检缓存时间)
#
# 预检请求（Preflight）:
#   对于"复杂请求"（如 POST JSON），浏览器先发 OPTIONS 请求问服务端
#   "我可以发 POST + JSON 吗？" → 服务端回答 CORS 头 → 浏览器再发真正的请求

import json
import sys

try:
    from flask import Flask, jsonify, request
except ImportError:
    print("请先安装: pip3 install flask flask-cors")
    sys.exit(1)


# ============================================================
# 方法 1：手动处理 CORS（理解原理）
# ============================================================

app_manual = Flask("manual_cors")

@app_manual.after_request
def add_cors_headers(response):
    """
    手动添加 CORS 响应头
    after_request 钩子在每个响应返回前执行
    """
    # 允许的源（生产环境应该指定具体域名，不要用 *）
    response.headers["Access-Control-Allow-Origin"] = "*"
    # 允许的 HTTP 方法
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    # 允许的请求头
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    # 预检请求缓存时间（秒）
    response.headers["Access-Control-Max-Age"] = "3600"
    return response

@app_manual.route("/api/data", methods=["GET", "OPTIONS"])
def get_data():
    """带 CORS 的 API 端点"""
    if request.method == "OPTIONS":
        # 预检请求直接返回 200
        return "", 200
    return jsonify({"message": "这个响应包含 CORS 头", "cors": "manual"})


# ============================================================
# 方法 2：用 flask-cors 扩展（生产推荐）
# ============================================================

try:
    from flask_cors import CORS

    app_ext = Flask("ext_cors")

    # 全局启用 CORS
    CORS(app_ext, resources={
        r"/api/*": {
            "origins": ["http://localhost:3000", "https://myapp.com"],
            "methods": ["GET", "POST", "PUT", "DELETE"],
            "allow_headers": ["Content-Type", "Authorization"],
        }
    })

    @app_ext.route("/api/data")
    def get_data_ext():
        return jsonify({"message": "flask-cors 自动处理", "cors": "extension"})

    HAS_FLASK_CORS = True
except ImportError:
    HAS_FLASK_CORS = False


# ============================================================
# 演示页面（模拟前端跨域请求）
# ============================================================

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>CORS Demo</title></head>
<body>
<h2>CORS 跨域演示</h2>
<p>打开浏览器开发者工具 (F12) → Network 标签，观察请求</p>
<button onclick="fetchData()">发送跨域请求</button>
<pre id="result">点击按钮发送请求...</pre>
<script>
async function fetchData() {
    const result = document.getElementById('result');
    try {
        // 这个请求从 :8081 发到 :8080，是跨域的
        const resp = await fetch('http://localhost:8080/api/data', {
            headers: {'Content-Type': 'application/json'}
        });
        const data = await resp.json();
        result.textContent = JSON.stringify(data, null, 2);
    } catch (e) {
        result.textContent = '跨域请求被阻止！\\n错误: ' + e.message +
            '\\n\\n解决方法: 服务端需要添加 CORS 响应头';
    }
}
</script>
</body>
</html>
"""


# ============================================================
# 主程序（非交互式演示）
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("CORS 跨域演示")
    print("=" * 60)

    print("""
  CORS 核心概念:

  1. 同源策略（Same-Origin Policy）
     浏览器安全机制：只允许向同源（协议+域名+端口相同）发请求

  2. 跨域场景
     前端 http://localhost:3000 → 后端 http://localhost:5000  ← 端口不同 = 跨域

  3. 解决方案
     服务端添加 CORS 响应头，告诉浏览器"我允许这个源访问"

  4. 预检请求（Preflight）
     浏览器对"复杂请求"先发 OPTIONS 探路
     复杂请求 = POST JSON / 自定义头 / PUT/DELETE 等

  5. 关键响应头
     Access-Control-Allow-Origin:  允许的源（* 或具体域名）
     Access-Control-Allow-Methods: 允许的 HTTP 方法
     Access-Control-Allow-Headers: 允许的自定义请求头

  6. 安全注意
     - 生产环境不要用 Access-Control-Allow-Origin: *
     - 应该明确列出允许的域名
     - 携带 Cookie 时 Origin 不能是 *
    """)

    print("  FastAPI 中配置 CORS:")
    print("""
    from fastapi.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    """)

    print("  Flask 中配置 CORS:")
    print("""
    from flask_cors import CORS
    CORS(app, origins=["http://localhost:3000"])
    """)

    print("  要运行交互式演示，请取消注释下面两行：")
    print("  # 启动两个服务器：:8080 (API) 和 :8081 (前端页面)")
    print("  # 然后浏览器打开 http://localhost:8081 观察跨域行为")

    # 如果要交互式演示，取消注释：
    # import threading
    # app_manual.run(port=8080)
