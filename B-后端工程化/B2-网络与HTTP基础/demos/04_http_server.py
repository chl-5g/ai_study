#!/usr/bin/env python3
"""
用 Python 标准库实现简单 HTTP 服务器
理解 HTTP 请求/响应的底层结构

运行后访问: http://localhost:8080
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from urllib.parse import urlparse, parse_qs
from datetime import datetime


class SimpleHandler(BaseHTTPRequestHandler):
    """
    自定义 HTTP 请求处理器

    BaseHTTPRequestHandler 的工作流程：
    1. 接收客户端连接
    2. 解析 HTTP 请求行（方法 + 路径 + 版本）
    3. 解析请求头
    4. 根据请求方法调用对应的 do_XXX 方法
    """

    def do_GET(self):
        """
        处理 GET 请求

        self.path: 请求路径（如 /api/hello?name=Allen）
        self.headers: 请求头字典
        """
        # 解析 URL
        parsed = urlparse(self.path)
        path = parsed.path            # /api/hello
        query = parse_qs(parsed.query)  # {'name': ['Allen']}

        # 路由分发
        if path == "/":
            self._send_html("<h1>欢迎！</h1><p>这是一个用 Python 标准库写的 HTTP 服务器</p>"
                           "<p>试试访问:</p>"
                           "<ul>"
                           "<li><a href='/api/hello?name=Allen'>/api/hello?name=Allen</a></li>"
                           "<li><a href='/api/time'>/api/time</a></li>"
                           "<li><a href='/api/headers'>/api/headers</a></li>"
                           "</ul>")
        elif path == "/api/hello":
            name = query.get("name", ["World"])[0]
            self._send_json({"message": f"Hello, {name}!", "method": "GET"})
        elif path == "/api/time":
            self._send_json({"time": datetime.now().isoformat()})
        elif path == "/api/headers":
            # 回显客户端的请求头
            headers_dict = {k: v for k, v in self.headers.items()}
            self._send_json({"your_headers": headers_dict})
        else:
            self._send_json({"error": "Not Found"}, status=404)

    def do_POST(self):
        """处理 POST 请求"""
        # 读取请求体
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")

        # 尝试解析 JSON
        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            data = {"raw": body}

        # 回显收到的数据
        self._send_json({
            "message": "POST 请求已收到",
            "received_data": data,
            "content_type": self.headers.get("Content-Type"),
        }, status=201)

    def _send_json(self, data: dict, status: int = 200):
        """
        发送 JSON 响应

        HTTP 响应结构：
        1. 状态行：HTTP/1.1 200 OK
        2. 响应头：Content-Type, Content-Length 等
        3. 空行
        4. 响应体：JSON 数据
        """
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)                          # 状态行
        self.send_header("Content-Type", "application/json; charset=utf-8")  # 响应头
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()                                  # 空行
        self.wfile.write(body)                              # 响应体

    def _send_html(self, html: str, status: int = 200):
        """发送 HTML 响应"""
        body = f"<!DOCTYPE html><html><head><meta charset='utf-8'></head><body>{html}</body></html>"
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"  [{datetime.now().strftime('%H:%M:%S')}] {args[0]}")


def main():
    host = "localhost"
    port = 8080
    server = HTTPServer((host, port), SimpleHandler)

    print("=" * 60)
    print("简易 HTTP 服务器")
    print("=" * 60)
    print(f"  服务器启动: http://{host}:{port}")
    print(f"  按 Ctrl+C 停止\n")
    print(f"  测试命令:")
    print(f"    curl http://localhost:{port}/")
    print(f"    curl http://localhost:{port}/api/hello?name=Allen")
    print(f"    curl http://localhost:{port}/api/time")
    print(f'    curl -X POST http://localhost:{port}/api/hello -H "Content-Type: application/json" -d \'{{"name":"Allen"}}\'')
    print()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  服务器已停止")
        server.server_close()


if __name__ == "__main__":
    main()
