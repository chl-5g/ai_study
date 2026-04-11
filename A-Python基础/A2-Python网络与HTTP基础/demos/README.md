# A2 网络与 HTTP — `demos/` 说明

在目录内运行：`python3 01_tcp_server_client.py` 等。第三方依赖见各文件注释（如 `requests`、`PyJWT`）。

| 文件 | 内容 |
|------|------|
| `01_tcp_server_client.py` | TCP：`socket` 服务端/客户端 |
| `02_udp_server_client.py` | UDP：`sendto` / `recvfrom` |
| `03_http_requests.py` | `requests`：GET/POST 等（需网络访问 httpbin） |
| `04_http_server.py` | 标准库裸 HTTP 响应 |
| `05_json_api.py` | 小 JSON API 示例 |
| `06_session_cookie.py` | Cookie / Session |
| `07_jwt_demo.py` | JWT 签发与校验思路 |
| `08_restful_server.py` | REST 风格路由 |
| `09_cors_demo.py` | CORS 响应头 |

更完整的协议脉络见上级 `理论讲解.md`（含 §3–§21 与文末对照表）。
