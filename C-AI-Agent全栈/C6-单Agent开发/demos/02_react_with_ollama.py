#!/usr/bin/env python3
"""
02_react_with_ollama.py — 真实 LLM + 一轮工具调用（Ollama OpenAI 兼容）

需：Ollama 运行中、模型支持 tools（如 qwen2.5）
依赖：requests

运行：python3 02_react_with_ollama.py
环境变量：同 C4 的 02（OPENAI_BASE_URL / OPENAI_API_KEY / OPENAI_MODEL）
"""

from __future__ import annotations

import json
import os

import requests

BASE = os.environ.get("OPENAI_BASE_URL", "http://localhost:11434/v1")
KEY = os.environ.get("OPENAI_API_KEY", "ollama")
MODEL = os.environ.get("OPENAI_MODEL", "qwen2.5:7b")


def kb_lookup(topic: str) -> str:
    data = {"退款": "7 天无理由", "发票": "联系财务邮箱"}
    return data.get(topic, "暂无")


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "kb_lookup",
            "description": "按主题查询内部知识库关键词",
            "parameters": {
                "type": "object",
                "properties": {"topic": {"type": "string", "enum": ["退款", "发票"]}},
                "required": ["topic"],
            },
        },
    }
]


def main() -> None:
    url = f"{BASE.rstrip('/')}/chat/completions"
    h = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
    messages = [
        {
            "role": "system",
            "content": "你是客服助手，有工具 kb_lookup 时必须先调用再回答。",
        },
        {"role": "user", "content": "我想了解退款政策"},
    ]
    r = requests.post(
        url,
        headers=h,
        json={"model": MODEL, "messages": messages, "tools": TOOLS, "temperature": 0.2},
        timeout=120,
    )
    if r.status_code != 200:
        print("错误", r.status_code, r.text[:400])
        return
    msg = r.json()["choices"][0]["message"]
    print("第一轮:", json.dumps(msg, ensure_ascii=False, indent=2)[:1200])
    calls = msg.get("tool_calls") or []
    if not calls:
        print("未产生 tool_calls，结束。")
        return
    messages.append(msg)
    for tc in calls:
        name = tc["function"]["name"]
        args = json.loads(tc["function"].get("arguments") or "{}")
        out = kb_lookup(args.get("topic", "")) if name == "kb_lookup" else "?"
        messages.append({"role": "tool", "tool_call_id": tc["id"], "content": out})
    r2 = requests.post(
        url,
        headers=h,
        json={"model": MODEL, "messages": messages, "tools": TOOLS, "temperature": 0.2},
        timeout=120,
    )
    if r2.status_code != 200:
        print("第二轮错误", r2.text[:400])
        return
    final = r2.json()["choices"][0]["message"].get("content")
    print("\n最终:\n", final)


if __name__ == "__main__":
    main()
