#!/usr/bin/env python3
"""
Session 与 Cookie 机制演示
理解 HTTP 无状态问题和解决方案

安装：pip3 install requests flask（Flask 仅用于本地服务器演示）
"""

import requests
import threading
import time
import json


# ============================================================
# 理论部分（代码中穿插讲解）
# ============================================================
#
# HTTP 是无状态协议：每次请求独立，服务端不记得"你是谁"
#
# 问题：如何实现"登录状态保持"？
#
# 方案 1: Cookie + Session（传统方案）
#   1. 用户登录 → 服务端创建 Session，生成 Session ID
#   2. 服务端通过 Set-Cookie 响应头把 Session ID 发给浏览器
#   3. 浏览器后续请求自动携带 Cookie（包含 Session ID）
#   4. 服务端通过 Session ID 查找用户信息
#
# 方案 2: Token（现代方案，见 07_jwt_demo.py）
#   用户登录 → 服务端返回 Token → 客户端存储并在请求头中携带


def demo_cookie_basics():
    """Cookie 基础操作"""
    print("=" * 60)
    print("1. Cookie 基础")
    print("=" * 60)

    # httpbin.org 提供 Cookie 设置和读取的测试接口
    session = requests.Session()

    # 服务端设置 Cookie（通过 Set-Cookie 响应头）
    resp = session.get("https://httpbin.org/cookies/set/user_id/12345", timeout=10,
                       allow_redirects=False)
    print(f"  Set-Cookie 响应头: {resp.headers.get('Set-Cookie', '(重定向中)')}")

    # 跟随重定向后，Cookie 已经保存在 Session 中
    session.get("https://httpbin.org/cookies/set/user_id/12345", timeout=10)

    # 查看当前所有 Cookie
    resp = session.get("https://httpbin.org/cookies", timeout=10)
    print(f"  当前 Cookie: {resp.json()}")

    # 再设置一个 Cookie
    session.get("https://httpbin.org/cookies/set/theme/dark", timeout=10)
    resp = session.get("https://httpbin.org/cookies", timeout=10)
    print(f"  添加后: {resp.json()}")

    # 手动设置 Cookie
    session.cookies.set("language", "zh-CN")
    resp = session.get("https://httpbin.org/cookies", timeout=10)
    print(f"  手动添加后: {resp.json()}")

    session.close()


def demo_session_persistence():
    """Session 持久化演示"""
    print()
    print("=" * 60)
    print("2. Session 保持（登录态模拟）")
    print("=" * 60)

    # 用 httpbin 的 Basic Auth 模拟登录
    session = requests.Session()

    # 设置认证信息（Session 会保持）
    session.auth = ("admin", "password123")
    session.headers.update({"X-Custom-Header": "my-app"})

    # 第一次请求（带认证）
    resp = session.get("https://httpbin.org/basic-auth/admin/password123", timeout=10)
    print(f"  登录结果: {resp.json()}")

    # 后续请求自动携带认证头
    resp = session.get("https://httpbin.org/get", timeout=10)
    auth_header = resp.json()["headers"].get("Authorization", "")
    print(f"  后续请求自动携带 Auth: {auth_header[:30]}...")
    print(f"  自定义头也保持: {resp.json()['headers'].get('X-Custom-Header')}")

    session.close()


def demo_cookie_vs_no_cookie():
    """对比有无 Session 的区别"""
    print()
    print("=" * 60)
    print("3. 有无 Session 对比")
    print("=" * 60)

    # 不用 Session：每次请求独立，Cookie 不保持
    print("  不用 Session:")
    requests.get("https://httpbin.org/cookies/set/token/abc", timeout=10)
    resp = requests.get("https://httpbin.org/cookies", timeout=10)
    print(f"    Cookie: {resp.json()}")  # 空的！Cookie 丢失了

    # 用 Session：Cookie 自动保持
    print("  用 Session:")
    s = requests.Session()
    s.get("https://httpbin.org/cookies/set/token/abc", timeout=10)
    resp = s.get("https://httpbin.org/cookies", timeout=10)
    print(f"    Cookie: {resp.json()}")  # token=abc 被保持了
    s.close()


def demo_cookie_attributes():
    """Cookie 属性讲解"""
    print()
    print("=" * 60)
    print("4. Cookie 属性速查")
    print("=" * 60)

    attributes = {
        "Name=Value":   "Cookie 的名称和值（必须）",
        "Domain":       "Cookie 生效的域名（如 .example.com）",
        "Path":         "Cookie 生效的路径（如 /api）",
        "Expires":      "过期时间（绝对时间）",
        "Max-Age":      "存活秒数（相对时间，优先于 Expires）",
        "Secure":       "仅 HTTPS 传输",
        "HttpOnly":     "JS 无法访问（防 XSS 攻击）",
        "SameSite":     "跨站策略（Strict/Lax/None，防 CSRF）",
    }

    for attr, desc in attributes.items():
        print(f"  {attr:15s} → {desc}")

    print("\n  示例 Set-Cookie 响应头:")
    print("  Set-Cookie: session_id=abc123; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=3600")


if __name__ == "__main__":
    print("注意：本 Demo 需要网络连接（httpbin.org）\n")

    try:
        demo_cookie_basics()
        demo_session_persistence()
        demo_cookie_vs_no_cookie()
        demo_cookie_attributes()
    except requests.exceptions.ConnectionError:
        print("\n  [错误] 网络连接失败")

    print()
    print("=" * 60)
    print("5. Session vs Token 对比")
    print("=" * 60)
    print("""
  Session/Cookie 方案:
    - 状态存在服务端（内存/Redis）
    - 服务端有状态，水平扩展需要共享 Session
    - 浏览器自动管理 Cookie
    - 适合：传统 Web 应用

  Token（JWT）方案:
    - 状态编码在 Token 中（客户端保存）
    - 服务端无状态，天然支持水平扩展
    - 需要手动在请求头中携带
    - 适合：API 服务、移动端、微服务
    - 详见 07_jwt_demo.py
    """)
