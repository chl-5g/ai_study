#!/usr/bin/env python3
"""
01_clean_markdown.py — Markdown 清洗：front matter、多余空行、行尾空白

依赖：无（标准库）
运行：python3 01_clean_markdown.py
"""

from __future__ import annotations

import re


def strip_front_matter(text: str) -> str:
    """移除 YAML front matter（--- ... ---）。"""
    if not text.startswith("---"):
        return text
    parts = text.split("---", 2)
    if len(parts) >= 3:
        return parts[2].lstrip("\n")
    return text


def normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def collapse_blank_lines(text: str, max_blank: int = 2) -> str:
    """连续空行压缩为最多 max_blank 个换行。"""
    pattern = r"\n{3,}"
    repl = "\n" * max_blank
    return re.sub(pattern, repl, text)


def strip_trailing_spaces(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.split("\n"))


def main() -> None:
    sample = """---
title: Demo
tags: [rag]
---

# 标题  


段落一。



段落二。  
"""
    cleaned = strip_front_matter(normalize_newlines(sample))
    cleaned = strip_trailing_spaces(collapse_blank_lines(cleaned))
    print("--- 清洗后 ---")
    print(cleaned)
    print("--- 结束 ---")


if __name__ == "__main__":
    main()
