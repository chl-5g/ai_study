#!/usr/bin/env python3
"""
调用公开 API 并解析 JSON 响应
演示实际开发中最常见的 HTTP 交互模式

安装：pip3 install requests
"""

import requests
import json


def demo_github_api():
    """
    调用 GitHub API（无需认证）
    演示：GET 请求 + JSON 解析 + 数据提取
    """
    print("=" * 60)
    print("1. GitHub API —— 查询用户信息")
    print("=" * 60)

    # GitHub API 是 RESTful 的典型代表
    username = "octocat"
    url = f"https://api.github.com/users/{username}"

    resp = requests.get(url, timeout=10, headers={
        "Accept": "application/vnd.github.v3+json",  # 指定 API 版本
    })

    if resp.status_code == 200:
        user = resp.json()
        print(f"  用户名: {user['login']}")
        print(f"  公开仓库数: {user['public_repos']}")
        print(f"  创建时间: {user['created_at']}")
        print(f"  主页: {user['html_url']}")
    else:
        print(f"  请求失败: {resp.status_code}")

    # 查询用户的仓库列表
    print(f"\n  {username} 的公开仓库:")
    repos_url = f"https://api.github.com/users/{username}/repos"
    resp = requests.get(repos_url, params={"sort": "updated", "per_page": 5}, timeout=10)

    if resp.status_code == 200:
        repos = resp.json()
        for repo in repos:
            stars = repo['stargazers_count']
            lang = repo['language'] or '未知'
            print(f"    ⭐{stars} [{lang:>10}] {repo['name']}")
    else:
        print(f"  请求失败: {resp.status_code}")


def demo_weather_api():
    """
    调用天气 API（wttr.in，无需 API Key）
    演示：带参数的 GET 请求
    """
    print()
    print("=" * 60)
    print("2. 天气 API —— wttr.in")
    print("=" * 60)

    # wttr.in 支持 JSON 格式返回
    city = "Hangzhou"
    url = f"https://wttr.in/{city}"
    params = {"format": "j1"}  # JSON 格式

    try:
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            current = data["current_condition"][0]
            print(f"  城市: {city}")
            print(f"  温度: {current['temp_C']}°C")
            print(f"  体感: {current['FeelsLikeC']}°C")
            print(f"  湿度: {current['humidity']}%")
            print(f"  天气: {current['weatherDesc'][0]['value']}")
        else:
            print(f"  请求失败: {resp.status_code}")
    except Exception as e:
        print(f"  天气 API 暂不可用: {e}")


def demo_ip_api():
    """
    IP 信息查询 API
    演示：简单 API 调用
    """
    print()
    print("=" * 60)
    print("3. IP 信息查询")
    print("=" * 60)

    try:
        resp = requests.get("https://httpbin.org/ip", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            print(f"  你的公网 IP: {data['origin']}")
    except Exception as e:
        print(f"  查询失败: {e}")


def demo_pagination():
    """
    分页请求演示
    很多 API 数据量大时会分页返回
    """
    print()
    print("=" * 60)
    print("4. 分页请求 —— GitHub API")
    print("=" * 60)

    # GitHub API 通过 per_page 和 page 参数分页
    url = "https://api.github.com/repos/python/cpython/commits"
    all_commits = []

    for page in range(1, 4):  # 获取前3页
        resp = requests.get(url, params={
            "per_page": 3,
            "page": page,
        }, timeout=10)

        if resp.status_code != 200:
            break

        commits = resp.json()
        if not commits:
            break

        all_commits.extend(commits)
        print(f"  第 {page} 页: 获取 {len(commits)} 条提交")

    print(f"  总计获取: {len(all_commits)} 条")
    if all_commits:
        print(f"\n  最近3条提交:")
        for c in all_commits[:3]:
            msg = c['commit']['message'].split('\n')[0][:50]
            date = c['commit']['author']['date'][:10]
            print(f"    [{date}] {msg}")


def demo_error_codes():
    """
    HTTP 状态码实际演示
    """
    print()
    print("=" * 60)
    print("5. 常见 HTTP 状态码实战")
    print("=" * 60)

    test_cases = [
        ("https://httpbin.org/status/200", "200 OK（成功）"),
        ("https://httpbin.org/status/201", "201 Created（资源已创建）"),
        ("https://httpbin.org/status/301", "301 Moved Permanently（永久重定向）"),
        ("https://httpbin.org/status/400", "400 Bad Request（请求错误）"),
        ("https://httpbin.org/status/401", "401 Unauthorized（未认证）"),
        ("https://httpbin.org/status/403", "403 Forbidden（禁止访问）"),
        ("https://httpbin.org/status/404", "404 Not Found（资源不存在）"),
        ("https://httpbin.org/status/500", "500 Internal Server Error（服务端错误）"),
    ]

    for url, desc in test_cases:
        try:
            resp = requests.get(url, timeout=5, allow_redirects=False)
            print(f"  {resp.status_code} ← {desc}")
        except Exception:
            print(f"  失败 ← {desc}")


if __name__ == "__main__":
    print("注意：本 Demo 需要网络连接\n")

    try:
        demo_github_api()
        demo_weather_api()
        demo_ip_api()
        demo_pagination()
        demo_error_codes()
    except requests.exceptions.ConnectionError:
        print("\n  [错误] 网络连接失败，请检查网络或代理设置")
