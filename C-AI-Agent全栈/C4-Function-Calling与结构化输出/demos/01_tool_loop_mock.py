#!/usr/bin/env python3
"""
01_tool_loop_mock.py — 无模型：模拟「模型提议 tool → 宿主执行 → 写回观察」一轮闭环

依赖：无
运行：python3 01_tool_loop_mock.py
"""

from __future__ import annotations

import ast
import json
from typing import Any, Callable


def safe_calc(expr: str) -> str:
    """仅允许常数与 + - * / 的二元表达式（演示用）。"""
    expr = expr.replace(" ", "")
    tree = ast.parse(expr, mode="eval")

    def ev(n: ast.AST) -> float:
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return float(n.value)
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub):
            return -ev(n.operand)
        if isinstance(n, ast.BinOp):
            a, b = ev(n.left), ev(n.right)
            if isinstance(n.op, ast.Add):
                return a + b
            if isinstance(n.op, ast.Sub):
                return a - b
            if isinstance(n.op, ast.Mult):
                return a * b
            if isinstance(n.op, ast.Div):
                return a / b
        raise ValueError("不支持的表达式")

    return str(ev(tree))


TOOLS: dict[str, tuple[str, Callable[..., str]]] = {
    "get_weather": ("查询城市天气（演示）", lambda city: f"{city} 今日晴，18°C"),
    "calc": ("计算四则表达式（演示级校验）", lambda expr: safe_calc(expr)),
}


def list_tool_specs_for_api() -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": TOOLS["get_weather"][0],
                "parameters": {
                    "type": "object",
                    "properties": {"city": {"type": "string", "description": "城市名"}},
                    "required": ["city"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "calc",
                "description": TOOLS["calc"][0],
                "parameters": {
                    "type": "object",
                    "properties": {"expr": {"type": "string"}},
                    "required": ["expr"],
                },
            },
        },
    ]


def fake_model_decide(user_text: str) -> dict[str, Any]:
    """假装模型：根据关键词返回 assistant 消息或 tool_calls。"""
    if "天气" in user_text:
        city = user_text.replace("天气", "").strip() or "北京"
        return {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {
                        "name": "get_weather",
                        "arguments": json.dumps({"city": city}, ensure_ascii=False),
                    },
                }
            ],
        }
    if "计算" in user_text:
        return {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call_2",
                    "type": "function",
                    "function": {
                        "name": "calc",
                        "arguments": json.dumps({"expr": "19+23"}),
                    },
                }
            ],
        }
    return {"role": "assistant", "content": "你好，我可以查天气或做简单计算（说「天气上海」「计算」）。"}


def run_tool(name: str, arguments_json: str) -> str:
    if name not in TOOLS:
        raise ValueError(f"未知工具: {name}")
    args = json.loads(arguments_json)
    _, fn = TOOLS[name]
    if name == "get_weather":
        return fn(args["city"])
    if name == "calc":
        return fn(args["expr"])
    return fn(**args)


def main() -> None:
    print("已注册 tools（OpenAI 风格 schema 预览）：")
    print(json.dumps(list_tool_specs_for_api(), ensure_ascii=False, indent=2)[:800], "...\n")

    for user in ["天气福州", "计算"]:
        print(f"\n=== 用户: {user} ===")
        msg = fake_model_decide(user)
        print("模型消息:", json.dumps(msg, ensure_ascii=False))
        if msg.get("tool_calls"):
            for tc in msg["tool_calls"]:
                fname = tc["function"]["name"]
                fargs = tc["function"]["arguments"]
                print(f"  执行 {fname}({fargs})")
                result = run_tool(fname, fargs)
                print(f"  观察: {result}")
        else:
            print("  最终:", msg.get("content"))


if __name__ == "__main__":
    main()
