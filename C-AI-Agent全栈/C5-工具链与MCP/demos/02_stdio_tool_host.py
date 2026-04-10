#!/usr/bin/env python3
"""
02_stdio_tool_host.py — 极简 stdio JSON-RPC 风格宿主：模拟「另一进程通过管道调工具」

子进程模式（另一终端或 IDE）：
  python3 02_stdio_tool_host.py --server
  然后 stdin 每行一个 JSON：
    {"cmd":"list_tools"}
    {"cmd":"call","name":"echo","arguments":{"text":"hi"}}

一次性演示（默认）：
  python3 02_stdio_tool_host.py

依赖：无
"""

from __future__ import annotations

import json
import sys
from typing import Any


def build_registry() -> dict[str, Any]:
    tools = {
        "echo": {
            "description": "原样返回 text",
            "parameters": {
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
            "fn": lambda text: text,
        },
    }
    return tools


def list_tools_payload(tools: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for name, meta in tools.items():
        out.append(
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": meta["description"],
                    "parameters": meta["parameters"],
                },
            }
        )
    return out


def server_loop() -> None:
    tools = build_registry()
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        req = json.loads(line)
        cmd = req.get("cmd")
        if cmd == "list_tools":
            print(json.dumps({"tools": list_tools_payload(tools)}, ensure_ascii=False))
        elif cmd == "call":
            name = req["name"]
            args = req.get("arguments") or {}
            result = tools[name]["fn"](**args)
            print(json.dumps({"result": result}, ensure_ascii=False))
        else:
            print(json.dumps({"error": "unknown cmd"}, ensure_ascii=False))
        sys.stdout.flush()


def demo_once() -> None:
    tools = build_registry()
    print("list_tools =>", json.dumps(list_tools_payload(tools), ensure_ascii=False))
    print('call echo =>', tools["echo"]["fn"](text="hello"))


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "--server":
        server_loop()
    else:
        demo_once()
        print("\n提示: 另一终端运行  python3 02_stdio_tool_host.py --server")
        print('  然后输入: {"cmd":"list_tools"}')


if __name__ == "__main__":
    main()
