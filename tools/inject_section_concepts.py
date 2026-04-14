# -*- coding: utf-8 -*-
"""
在 Markdown 的 ### 小节下插入 **本节概念**（与 A1、B2 等教材体例对齐）。

用法（仓库根目录执行）：
  python tools/inject_section_concepts.py "B-后端工程化/B2-网络与HTTP基础/理论讲解.md"
  python tools/inject_section_concepts.py "A-Python基础/A1-Pythonic与标准库/理论讲解.md" --dry-run
  python tools/inject_section_concepts.py "A-Python基础/A2-FastAPI深度/理论讲解.md"

说明：
  - 默认跳过：Checkpoint、本节小结、三张卡片、动手实验、面试考点速查 等标题。
  - 若小节首行已是 **本节概念**，不会重复插入。
  - 标题含 Why：/What：/How： 时，从标题抽取；否则首行若以列表项开头，用「要点见下文」式概括，避免把 bullet 误当概念句。
  - 文首「写作原则 / 阅读提示」的修改请手写或通过 --header-snippet 注入（见下方可选参数）。
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

DEFAULT_SKIP = (
    "Checkpoint",
    "本节小结",
    "三张卡片",
    "动手：",
    "10 分钟对照实验",
    "面试考点速查",
)


def next_nonempty(lines: list[str], start: int) -> tuple[int, str]:
    j = start
    while j < len(lines):
        t = lines[j].strip()
        if t:
            return j, t
        j += 1
    return len(lines), ""


def concept_line(title: str, body_first: str) -> str:
    title = title.strip()
    bf = body_first.strip()

    for sep in ("Why：", "Why:", "What：", "What:", "How：", "How:"):
        if sep in title:
            tail = title.split(sep, 1)[1].strip()
            label = "Why" if sep.startswith("Why") else "What" if sep.startswith("What") else "How"
            return f"**本节概念**：{label} —— {tail}"
    if "深度补充：" in title:
        tail = title.split("深度补充：", 1)[1].strip()
        return f"**本节概念**：深度补充 —— {tail}"
    if "补充：" in title[:32]:
        tail = title.split("补充：", 1)[1].strip() if "补充：" in title else title
        return f"**本节概念**：补充 —— {tail}"
    if "常见误区" in title:
        return "**本节概念**：常见误区 —— 汇总易混点与纠偏口径。"

    if bf.startswith("-") or re.match(r"^\d+\.\s", bf):
        return f"**本节概念**：「{title}」——要点见下文列表。"

    if bf.startswith("```"):
        return "**本节概念**：见下正文与示例（先扫结构再逐段读）。"

    if len(bf) > 160:
        bf = bf[:157].rstrip() + "..."
    return f"**本节概念**：{bf}"


def process_file(path: Path, skip_substr: tuple[str, ...], dry_run: bool) -> int:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    inserted = 0
    i = 0
    while i < len(lines):
        line = lines[i]
        out.append(line)
        if line.startswith("### "):
            title = line[4:].strip()
            if not any(s in title for s in skip_substr):
                _, nxt = next_nonempty(lines, i + 1)
                if nxt and not nxt.startswith("**本节概念**"):
                    out.append("\n")
                    out.append(concept_line(title, nxt) + "\n")
                    inserted += 1
        i += 1
    new_text = "".join(out)
    if dry_run:
        print(f"[dry-run] {path}: would insert ~{inserted} blocks (file not written)")
        return inserted
    path.write_text(new_text, encoding="utf-8")
    print(f"OK {path}: inserted {inserted} **本节概念** blocks")
    return inserted


def main() -> None:
    p = argparse.ArgumentParser(description="Inject **本节概念** under ### headings in theory Markdown.")
    p.add_argument(
        "markdown_files",
        nargs="+",
        type=Path,
        help="Target .md paths (relative to cwd or absolute)",
    )
    p.add_argument("--dry-run", action="store_true", help="Do not write files")
    p.add_argument(
        "--extra-skip",
        action="append",
        default=[],
        help="Additional substring; if present in ### title, skip that section (repeatable)",
    )
    args = p.parse_args()
    skip = tuple(DEFAULT_SKIP) + tuple(args.extra_skip)

    total = 0
    for f in args.markdown_files:
        if not f.exists():
            print("Missing:", f, file=sys.stderr)
            sys.exit(1)
        total += process_file(f, skip, args.dry_run)
    if args.dry_run:
        print(f"Total insertions (estimate): {total}")


if __name__ == "__main__":
    main()
