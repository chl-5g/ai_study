#!/usr/bin/env python3
"""
02_span_timings.py — 嵌套阶段耗时（演示 trace 中 span 的直觉）

依赖：无
运行：python3 02_span_timings.py
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Iterator


@contextmanager
def span(name: str, trace_id: str) -> Iterator[None]:
    t0 = time.perf_counter()
    print(f"{trace_id} START {name}")
    try:
        yield
    finally:
        ms = (time.perf_counter() - t0) * 1000
        print(f"{trace_id} END   {name}  {ms:.1f}ms")


def fake_agent_turn(trace_id: str) -> None:
    with span("retrieve", trace_id):
        time.sleep(0.05)
    with span("llm_first", trace_id):
        time.sleep(0.08)
    with span("tool_http", trace_id):
        time.sleep(0.04)
    with span("llm_final", trace_id):
        time.sleep(0.06)


def main() -> None:
    fake_agent_turn("t-abc123")


if __name__ == "__main__":
    main()
