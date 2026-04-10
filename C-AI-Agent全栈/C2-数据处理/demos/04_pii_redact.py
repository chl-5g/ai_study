#!/usr/bin/env python3
"""
04_pii_redact.py — 简单 PII 脱敏（手机、邮箱）再进日志/向量流水线

依赖：无
运行：python3 04_pii_redact.py
"""

from __future__ import annotations

import re


PHONE_RE = re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def redact(text: str) -> str:
    text = PHONE_RE.sub("[PHONE]", text)
    text = EMAIL_RE.sub("[EMAIL]", text)
    return text


def main() -> None:
    s = "联系我 13812345678 或 foo.bar@example.com，谢谢。"
    print(redact(s))


if __name__ == "__main__":
    main()
