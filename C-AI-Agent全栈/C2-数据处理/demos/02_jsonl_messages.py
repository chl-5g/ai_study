#!/usr/bin/env python3
"""
02_jsonl_messages.py — 对话 JSONL：读写、校验 role、合并为 API messages

依赖：无
运行：python3 02_jsonl_messages.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

VALID_ROLES = frozenset({"system", "user", "assistant", "tool"})


def write_sample_jsonl(path: Path) -> None:
    rows = [
        {"role": "system", "content": "你是助手。"},
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好，有什么可以帮你？"},
    ]
    path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")


def load_messages(path: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)
        if "role" not in obj or "content" not in obj:
            raise ValueError(f"行 {i}: 缺少 role 或 content")
        if obj["role"] not in VALID_ROLES:
            raise ValueError(f"行 {i}: 非法 role {obj['role']!r}")
        out.append(obj)
    return out


def main() -> None:
    p = Path(__file__).with_name("_sample_messages.jsonl")
    write_sample_jsonl(p)
    msgs = load_messages(p)
    print("共", len(msgs), "条消息")
    print("可原样作为 Chat Completions 的 messages：")
    print(json.dumps(msgs, ensure_ascii=False, indent=2))
    p.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
