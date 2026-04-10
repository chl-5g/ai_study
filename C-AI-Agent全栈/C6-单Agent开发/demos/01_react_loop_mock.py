#!/usr/bin/env python3
"""
01_react_loop_mock.py — 最小 ReAct：多步直到「最终答复」或达上限（无真实 LLM）

依赖：无
运行：python3 01_react_loop_mock.py
"""

from __future__ import annotations

import json
from typing import Any


def tool_search_kb(query: str) -> str:
    kb = {"退款": "7 天内可退", "运费": "满 99 包邮"}
    for k, v in kb.items():
        if k in query:
            return v
    return "未找到相关条目"


TOOLS = {
    "search_kb": tool_search_kb,
}


def fake_llm_think_step(messages: list[dict[str, Any]], step: int) -> dict[str, Any]:
    """极简规则：首轮若用户问业务则调 search_kb，否则直接答。"""
    last_user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
    if step == 0 and ("退" in last_user or "运费" in last_user):
        q = "退款" if "退" in last_user else "运费"
        return {
            "type": "tool_call",
            "name": "search_kb",
            "arguments": {"query": q},
        }
    if step == 1 and messages[-1]["role"] == "tool":
        return {"type": "final", "content": f"根据知识库：{messages[-1]['content']}"}
    return {"type": "final", "content": "你好，我是演示 Agent（mock LLM）。"}


def main() -> None:
    messages: list[dict[str, Any]] = [{"role": "user", "content": "你们退款政策怎样？"}]
    max_steps = 6
    for step in range(max_steps):
        decision = fake_llm_think_step(messages, step)
        print(f"\n[step {step}] 决策:", decision)
        if decision["type"] == "final":
            print(">>> 最终:", decision["content"])
            break
        if decision["type"] == "tool_call":
            name = decision["name"]
            args = decision["arguments"]
            fn = TOOLS.get(name)
            if not fn:
                raise RuntimeError(name)
            obs = fn(**args)
            messages.append(
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": f"t{step}",
                            "function": {"name": name, "arguments": json.dumps(args)},
                        }
                    ],
                }
            )
            messages.append({"role": "tool", "content": obs, "tool_call_id": f"t{step}"})
    else:
        print("达到 max_steps，强制结束")


if __name__ == "__main__":
    main()
