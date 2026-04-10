#!/usr/bin/env python3
"""
03_normalize_text.py — 全角标点、零宽字符、重复空格

依赖：无
运行：python3 03_normalize_text.py
"""

from __future__ import annotations

import re
import unicodedata

FULLWIDTH_MAP = str.maketrans(
    "，。！？：（）【】「」",
    ",.!?:()[]\"\"",
)


def remove_zero_width(s: str) -> str:
    for ch in ("\u200b", "\u200c", "\u200d", "\ufeff"):
        s = s.replace(ch, "")
    return s


def normalize(s: str) -> str:
    s = unicodedata.normalize("NFKC", s)
    s = s.translate(FULLWIDTH_MAP)
    s = remove_zero_width(s)
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()


def main() -> None:
    raw = "　你好，世界！\u200b  人工智能　"
    print("原文 repr:", repr(raw))
    print("归一化:", normalize(raw))


if __name__ == "__main__":
    main()
