#!/usr/bin/env python3
"""
01_trace_contextvars.py — 用 contextvars 在日志中贯穿 trace_id（无第三方）

依赖：无
运行：python3 01_trace_contextvars.py
"""

from __future__ import annotations

import contextvars
import logging
import uuid

trace_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("trace_id", default="-")

_old_factory = logging.getLogRecordFactory()


def record_factory(*args, **kwargs):
    record = _old_factory(*args, **kwargs)
    record.trace_id = trace_id_var.get()
    return record


logging.setLogRecordFactory(record_factory)

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s trace_id=%(trace_id)s %(message)s",
)


def handle_request(user_query: str) -> None:
    tid = str(uuid.uuid4())[:8]
    trace_id_var.set(tid)
    logging.info("收到请求")
    logging.info("调用 LLM（模拟）")
    logging.info("调用工具 search")
    logging.info("返回用户")


def main() -> None:
    handle_request("你好")
    handle_request("再见")


if __name__ == "__main__":
    main()
