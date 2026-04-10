#!/usr/bin/env python3
"""
01_tool_registry.py — 工具注册表：MCP 之前的最小抽象（名字 → schema + 可调用）

依赖：无
运行：python3 01_tool_registry.py
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any


class ToolRegistry:
    def __init__(self) -> None:
        self._fns: dict[str, Callable[..., Any]] = {}
        self._schemas: list[dict[str, Any]] = []

    def register(self, name: str, description: str, parameters: dict[str, Any], fn: Callable[..., Any]) -> None:
        self._fns[name] = fn
        self._schemas.append(
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": parameters,
                },
            }
        )

    def list_openai_tools(self) -> list[dict[str, Any]]:
        return list(self._schemas)

    def call(self, name: str, arguments: dict[str, Any]) -> Any:
        if name not in self._fns:
            raise KeyError(f"未注册工具: {name}")
        return self._fns[name](**arguments)


def main() -> None:
    reg = ToolRegistry()
    reg.register(
        "add",
        "两数相加",
        {
            "type": "object",
            "properties": {"a": {"type": "number"}, "b": {"type": "number"}},
            "required": ["a", "b"],
        },
        lambda a, b: a + b,
    )
    print("OpenAI 风格 tools 列表:")
    print(json.dumps(reg.list_openai_tools(), ensure_ascii=False, indent=2))
    print("\n调用 add(2,3) =>", reg.call("add", {"a": 2, "b": 3}))


if __name__ == "__main__":
    main()
