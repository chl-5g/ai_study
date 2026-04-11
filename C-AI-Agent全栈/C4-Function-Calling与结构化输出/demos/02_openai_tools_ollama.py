#!/usr/bin/env python3
"""
02_openai_tools_ollama.py — OpenAI 兼容 Chat Completions + tools（Ollama / 其它兼容端）

依赖：requests
运行：python3 02_openai_tools_ollama.py

环境变量（与 C1 demos 一致即可）：
  OPENAI_BASE_URL  默认 http://localhost:11434/v1
  OPENAI_API_KEY     Ollama 可填 ollama
  OPENAI_MODEL       默认 qwen2.5:7b（需本地已 pull 且支持 tool calling）
"""

from __future__ import annotations

import json
import os

import requests

BASE = os.environ.get("OPENAI_BASE_URL", "http://localhost:11434/v1")
KEY = os.environ.get("OPENAI_API_KEY", "ollama")
MODEL = os.environ.get("OPENAI_MODEL", "qwen2.5:7b")

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_time_city",
            "description": "根据城市名返回演示用伪时间字符串（非真实 API）",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"],
            },
        },
    }
]


def run_tool(name: str, args: dict) -> str:
    if name == "get_time_city":
        return f"{args.get('city','?')} 本地演示时间 12:00"
    return "unknown tool"


def main() -> None:
    url = f"{BASE.rstrip('/')}/chat/completions"
    headers = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
    messages = [
        {"role": "system", "content": "你必须使用工具回答用户关于城市时间的问题。"},
        {"role": "user", "content": "杭州现在几点？（请调用工具）"},
    ]
    body = {
        "model": MODEL,
        "messages": messages,
        "tools": TOOLS,
        "tool_choice": "auto",
        "temperature": 0.2,
    }
    try:
        r = requests.post(url, headers=headers, json=body, timeout=120)
    except requests.RequestException as e:
        print("请求失败（是否已启动 Ollama？）:", e)
        return
    if r.status_code != 200:
        print("HTTP", r.status_code, r.text[:500])
        return
    data = r.json()
    choice = data["choices"][0]["message"]
    print("首轮 assistant:", json.dumps(choice, ensure_ascii=False, indent=2))
    tcalls = choice.get("tool_calls") or []
    if not tcalls:
        print("模型未返回 tool_calls，可能当前模型不支持 tools 或未按指令调用。")
        return
    messages.append(choice)
    for tc in tcalls:
        tid = tc["id"]
        name = tc["function"]["name"]
        raw_args = tc["function"].get("arguments") or "{}"
        args = json.loads(raw_args)
        out = run_tool(name, args)
        messages.append(
            {
                "role": "tool",
                "tool_call_id": tid,
                "content": out,
            }
        )
    body2 = {
        "model": MODEL,
        "messages": messages,
        "tools": TOOLS,
        "temperature": 0.2,
    }
    r2 = requests.post(url, headers=headers, json=body2, timeout=120)
    if r2.status_code != 200:
        print("第二轮 HTTP", r2.status_code, r2.text[:500])
        return
    final = r2.json()["choices"][0]["message"].get("content")
    print("\n最终回复:\n", final)


if __name__ == "__main__":
    main()
