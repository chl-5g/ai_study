#!/usr/bin/env python3
"""
01_supervisor_router.py — 监督者路由：按规则把查询分给不同「子 Agent」（函数模拟）

依赖：无
运行：python3 01_supervisor_router.py
"""

from __future__ import annotations


def agent_refund(query: str) -> str:
    return f"[退款专员] 已记录工单：{query[:40]}"


def agent_search(query: str) -> str:
    return f"[搜索专员] 找到 3 条与「{query[:20]}」相关的帮助文档"


def agent_general(query: str) -> str:
    return f"[通用客服] 感谢您的提问：{query[:50]}"


def route(query: str) -> str:
    if "退" in query or "款" in query:
        return "refund"
    if "查" in query or "怎么" in query:
        return "search"
    return "general"


def main() -> None:
    agents = {
        "refund": agent_refund,
        "search": agent_search,
        "general": agent_general,
    }
    samples = ["我要退款", "怎么修改密码", "你好"]
    for q in samples:
        tag = route(q)
        out = agents[tag](q)
        print(f"Q: {q}\n  路由={tag}\n  {out}\n")


if __name__ == "__main__":
    main()
