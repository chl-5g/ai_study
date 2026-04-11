#!/usr/bin/env python3
"""
用 requests 库演示 HTTP 方法：GET / POST / PUT / DELETE
requests 是 Python 最流行的 HTTP 客户端库

安装：pip3 install requests
"""

# ============================================================
# requests 库核心用法
# ============================================================
# requests.get(url)      → GET 请求（获取资源）
# requests.post(url)     → POST 请求（创建资源）
# requests.put(url)      → PUT 请求（更新资源，全量替换）
# requests.patch(url)    → PATCH 请求（更新资源，部分修改）
# requests.delete(url)   → DELETE 请求（删除资源）

import requests
import json


# 使用 httpbin.org 作为测试 API（它会回显你的请求内容）
BASE_URL = "https://httpbin.org"


def demo_get():
    """GET 请求：获取数据"""
    print("=" * 60)
    print("1. GET 请求")
    print("=" * 60)

    # 最简单的 GET
    resp = requests.get(f"{BASE_URL}/get", timeout=10)

    # 响应对象的常用属性
    print(f"  状态码: {resp.status_code}")          # 200
    print(f"  状态文本: {resp.reason}")              # OK
    print(f"  Content-Type: {resp.headers.get('Content-Type')}")
    print(f"  编码: {resp.encoding}")

    # 带查询参数的 GET（等价于 /get?name=Allen&age=30）
    params = {"name": "Allen", "age": 30}
    resp = requests.get(f"{BASE_URL}/get", params=params, timeout=10)
    data = resp.json()  # 自动解析 JSON 响应
    print(f"  查询参数: {data['args']}")
    print(f"  完整 URL: {resp.url}")

    # 自定义请求头
    headers = {
        "User-Agent": "MyApp/1.0",
        "Accept-Language": "zh-CN",
    }
    resp = requests.get(f"{BASE_URL}/get", headers=headers, timeout=10)
    print(f"  自定义 UA: {resp.json()['headers'].get('User-Agent')}")


def demo_post():
    """POST 请求：提交数据"""
    print()
    print("=" * 60)
    print("2. POST 请求")
    print("=" * 60)

    # POST JSON 数据（最常用）
    payload = {"username": "allen", "email": "allen@example.com"}
    resp = requests.post(
        f"{BASE_URL}/post",
        json=payload,  # 自动序列化为 JSON，自动设置 Content-Type
        timeout=10
    )
    data = resp.json()
    print(f"  发送的 JSON: {data['json']}")
    print(f"  Content-Type: {data['headers'].get('Content-Type')}")

    # POST 表单数据（传统表单提交）
    form_data = {"username": "allen", "password": "123456"}
    resp = requests.post(
        f"{BASE_URL}/post",
        data=form_data,  # 用 data= 发送表单
        timeout=10
    )
    data = resp.json()
    print(f"  发送的表单: {data['form']}")


def demo_put_delete():
    """PUT 和 DELETE 请求"""
    print()
    print("=" * 60)
    print("3. PUT / DELETE 请求")
    print("=" * 60)

    # PUT：更新资源（全量替换）
    resp = requests.put(
        f"{BASE_URL}/put",
        json={"name": "Allen Tsai", "role": "AI Engineer"},
        timeout=10
    )
    print(f"  PUT 响应: {resp.json()['json']}")

    # DELETE：删除资源
    resp = requests.delete(f"{BASE_URL}/delete", timeout=10)
    print(f"  DELETE 状态码: {resp.status_code}")


def demo_error_handling():
    """错误处理"""
    print()
    print("=" * 60)
    print("4. 错误处理")
    print("=" * 60)

    # HTTP 错误状态码
    resp = requests.get(f"{BASE_URL}/status/404", timeout=10)
    print(f"  404 状态码: {resp.status_code}")
    print(f"  是否成功: {resp.ok}")  # False（状态码 >= 400）

    # raise_for_status() 在非 2xx 时抛出异常
    try:
        resp = requests.get(f"{BASE_URL}/status/500", timeout=10)
        resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"  HTTP 错误: {e}")

    # 超时处理
    try:
        resp = requests.get(f"{BASE_URL}/delay/5", timeout=2)
    except requests.exceptions.Timeout:
        print(f"  请求超时（2秒限制）")

    # 连接错误
    try:
        resp = requests.get("http://不存在的域名.com", timeout=2)
    except requests.exceptions.ConnectionError:
        print(f"  连接错误（域名不存在）")


def demo_session():
    """Session：复用连接和 Cookie"""
    print()
    print("=" * 60)
    print("5. Session（会话管理）")
    print("=" * 60)

    # Session 可以跨请求保持 Cookie 和连接
    session = requests.Session()

    # 设置 Cookie
    session.get(f"{BASE_URL}/cookies/set/token/abc123", timeout=10)

    # 后续请求自动携带 Cookie
    resp = session.get(f"{BASE_URL}/cookies", timeout=10)
    print(f"  Session Cookie: {resp.json()}")

    # Session 还可以设置默认请求头
    session.headers.update({"Authorization": "Bearer my_token"})
    resp = session.get(f"{BASE_URL}/get", timeout=10)
    print(f"  Authorization: {resp.json()['headers'].get('Authorization')}")

    session.close()


if __name__ == "__main__":
    print("注意：本 Demo 需要网络连接，调用 httpbin.org 测试 API\n")

    try:
        demo_get()
        demo_post()
        demo_put_delete()
        demo_error_handling()
        demo_session()
    except requests.exceptions.ConnectionError:
        print("\n  [错误] 无法连接到 httpbin.org，请检查网络")
        print("  如果需要代理: export HTTPS_PROXY=http://127.0.0.1:7890")

    print()
    print("=" * 60)
    print("6. HTTP 状态码速查")
    print("=" * 60)
    status_codes = {
        "1xx": "信息性（100 Continue）",
        "2xx": "成功（200 OK, 201 Created, 204 No Content）",
        "3xx": "重定向（301 永久, 302 临时, 304 未修改）",
        "4xx": "客户端错误（400 Bad Request, 401 未授权, 403 禁止, 404 未找到）",
        "5xx": "服务端错误（500 内部错误, 502 Bad Gateway, 503 服务不可用）",
    }
    for code, desc in status_codes.items():
        print(f"  {code}: {desc}")
