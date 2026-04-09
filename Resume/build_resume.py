#!/usr/bin/env python3
"""
简历编译脚本：调用 xelatex 编译 resume.tex，支持 --watch 自动监控。
"""

import argparse
import glob
import os
import subprocess
import sys
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEX_FILE = os.path.join(SCRIPT_DIR, "resume.tex")
AUX_EXTENSIONS = [".aux", ".log", ".out", ".fls", ".fdb_latexmk", ".synctex.gz", ".toc"]


def clean_aux_files():
    """清理编译产生的辅助文件。"""
    base = os.path.splitext(TEX_FILE)[0]
    for ext in AUX_EXTENSIONS:
        path = base + ext
        if os.path.exists(path):
            os.remove(path)
            print(f"  已清理: {os.path.basename(path)}")


def compile_tex():
    """调用 xelatex 编译 .tex 文件，返回是否成功。"""
    print(f"\n{'='*50}")
    print(f"开始编译 {os.path.basename(TEX_FILE)} ...")
    print(f"{'='*50}")

    cmd = [
        "xelatex",
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-output-directory", SCRIPT_DIR,
        TEX_FILE,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=SCRIPT_DIR, timeout=180)
    except FileNotFoundError:
        print("错误: 未找到 xelatex，请先安装 MacTeX 或 TeX Live。")
        print("  macOS:  brew install --cask mactex")
        print("  Linux:  sudo apt install texlive-xetex texlive-lang-chinese")
        return False
    except subprocess.TimeoutExpired:
        print("错误: 编译超时（180秒）。")
        return False

    if result.returncode == 0:
        pdf_path = os.path.splitext(TEX_FILE)[0] + ".pdf"
        print(f"编译成功! -> {os.path.basename(pdf_path)}")
        clean_aux_files()
        return True
    else:
        print("编译失败! xelatex 输出:")
        # 只打印最后 30 行，通常包含错误信息
        lines = result.stdout.strip().split("\n")
        for line in lines[-30:]:
            print(f"  {line}")
        clean_aux_files()
        return False


def watch_mode():
    """监控 .tex 文件变化，保存后自动重新编译。"""
    print(f"监控模式已启动，正在监控: {os.path.basename(TEX_FILE)}")
    print("按 Ctrl+C 退出。\n")

    # 先编译一次
    compile_tex()

    last_mtime = os.path.getmtime(TEX_FILE)

    try:
        while True:
            time.sleep(1)
            try:
                current_mtime = os.path.getmtime(TEX_FILE)
            except OSError:
                continue

            if current_mtime != last_mtime:
                last_mtime = current_mtime
                compile_tex()
    except KeyboardInterrupt:
        print("\n\n监控已停止。")


def main():
    parser = argparse.ArgumentParser(description="编译简历 LaTeX 文件")
    parser.add_argument("--watch", action="store_true", help="监控 .tex 文件变化并自动编译")
    args = parser.parse_args()

    if not os.path.exists(TEX_FILE):
        print(f"错误: 未找到 {TEX_FILE}")
        sys.exit(1)

    if args.watch:
        watch_mode()
    else:
        success = compile_tex()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
