#!/usr/bin/env python3
"""
综合项目：批量文件重命名脚本
综合运用 os + re + 命令行参数 + 异常处理

功能：
- 按规则批量重命名文件
- 支持前缀/后缀添加、序号重命名、正则替换
- 预览模式（dry-run）：先看效果再执行
"""

import os
import re
import sys


def add_prefix(directory: str, prefix: str, dry_run: bool = True) -> list[tuple[str, str]]:
    """
    给目录下所有文件添加前缀

    参数:
        directory: 目标目录
        prefix: 要添加的前缀
        dry_run: True 只预览不执行

    返回: [(旧名, 新名), ...] 的列表
    """
    renames = []
    for filename in sorted(os.listdir(directory)):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath) and not filename.startswith("."):
            new_name = prefix + filename
            renames.append((filename, new_name))
            if not dry_run:
                os.rename(filepath, os.path.join(directory, new_name))
    return renames


def sequential_rename(directory: str, pattern: str = "{:03d}_{name}",
                      start: int = 1, dry_run: bool = True) -> list[tuple[str, str]]:
    """
    按序号重命名文件

    参数:
        directory: 目标目录
        pattern: 命名模板，{:03d} 是序号，{name} 是原文件名
        start: 起始序号
        dry_run: 预览模式
    """
    renames = []
    files = sorted(f for f in os.listdir(directory)
                   if os.path.isfile(os.path.join(directory, f)) and not f.startswith("."))

    for i, filename in enumerate(files, start=start):
        name, ext = os.path.splitext(filename)
        # 支持两种占位符
        new_name = pattern.format(i, name=name) + ext
        renames.append((filename, new_name))
        if not dry_run:
            old_path = os.path.join(directory, filename)
            new_path = os.path.join(directory, new_name)
            os.rename(old_path, new_path)
    return renames


def regex_rename(directory: str, search: str, replace: str,
                 dry_run: bool = True) -> list[tuple[str, str]]:
    """
    用正则表达式批量替换文件名

    参数:
        directory: 目标目录
        search: 正则搜索模式
        replace: 替换字符串（支持 \\1 反向引用）
        dry_run: 预览模式
    """
    renames = []
    pattern = re.compile(search)

    for filename in sorted(os.listdir(directory)):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            new_name = pattern.sub(replace, filename)
            if new_name != filename:
                renames.append((filename, new_name))
                if not dry_run:
                    os.rename(filepath, os.path.join(directory, new_name))
    return renames


def print_renames(renames: list[tuple[str, str]], dry_run: bool = True):
    """打印重命名结果"""
    if not renames:
        print("  没有需要重命名的文件")
        return

    label = "[预览]" if dry_run else "[已执行]"
    print(f"\n  {label} 共 {len(renames)} 个文件:")
    for old, new in renames:
        print(f"    {old}")
        print(f"      → {new}")


def demo():
    """
    演示模式：创建临时文件，展示重命名效果，然后清理
    """
    # 创建临时目录和测试文件
    demo_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_rename_demo")
    os.makedirs(demo_dir, exist_ok=True)

    # 创建测试文件
    test_files = [
        "photo 2026-01-15.jpg",
        "photo 2026-02-20.jpg",
        "photo 2026-03-10.jpg",
        "document_draft.pdf",
        "document_final.pdf",
        "notes.txt",
    ]
    for f in test_files:
        open(os.path.join(demo_dir, f), "w").close()

    print("=" * 60)
    print("批量重命名脚本演示")
    print("=" * 60)

    print(f"\n  测试目录: {demo_dir}")
    print(f"  原始文件:")
    for f in sorted(os.listdir(demo_dir)):
        print(f"    {f}")

    # 演示1：正则替换（空格→下划线）
    print("\n" + "-" * 60)
    print("演示1：正则替换（空格→下划线）")
    print("-" * 60)
    renames = regex_rename(demo_dir, r"\s+", "_", dry_run=True)
    print_renames(renames, dry_run=True)

    # 实际执行
    regex_rename(demo_dir, r"\s+", "_", dry_run=False)

    # 演示2：添加前缀
    print("\n" + "-" * 60)
    print("演示2：添加前缀 'project_'")
    print("-" * 60)
    renames = add_prefix(demo_dir, "project_", dry_run=True)
    print_renames(renames, dry_run=True)

    # 演示3：序号重命名
    print("\n" + "-" * 60)
    print("演示3：序号重命名")
    print("-" * 60)
    renames = sequential_rename(demo_dir, "{:03d}_{name}", dry_run=True)
    print_renames(renames, dry_run=True)

    # 演示4：提取日期重命名
    print("\n" + "-" * 60)
    print("演示4：正则提取日期重组文件名")
    print("-" * 60)
    renames = regex_rename(demo_dir, r"photo_(\d{4})-(\d{2})-(\d{2})", r"\1\2\3_photo", dry_run=True)
    print_renames(renames, dry_run=True)

    # 清理
    import shutil
    shutil.rmtree(demo_dir)
    print(f"\n  (临时目录已清理)")
    print(f"\n  实际使用:")
    print(f"    1. 修改 demo() 中的目录和规则")
    print(f"    2. 先用 dry_run=True 预览")
    print(f"    3. 确认后改为 dry_run=False 执行")


if __name__ == "__main__":
    demo()
