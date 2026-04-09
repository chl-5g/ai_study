#!/usr/bin/env python3
"""
标准库：os 和 sys 模块
os —— 操作系统交互（文件/目录/环境变量）
sys —— Python 解释器相关（参数/路径/退出）
"""

import os
import sys


if __name__ == "__main__":
    print("=" * 60)
    print("1. os.path —— 路径操作（最常用）")
    print("=" * 60)

    # 获取当前文件的目录
    current_file = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_file)

    print(f"  当前文件: {current_file}")
    print(f"  当前目录: {current_dir}")
    print(f"  文件名: {os.path.basename(current_file)}")
    print(f"  分离扩展名: {os.path.splitext('demo.py')}")  # ('demo', '.py')

    # 路径拼接（永远不要用字符串拼接路径！）
    new_path = os.path.join(current_dir, "data", "file.txt")
    print(f"  路径拼接: {new_path}")

    # 路径判断
    print(f"  文件存在? {os.path.exists(current_file)}")
    print(f"  是文件?   {os.path.isfile(current_file)}")
    print(f"  是目录?   {os.path.isdir(current_dir)}")

    # 用户目录
    print(f"  Home 目录: {os.path.expanduser('~')}")

    print()
    print("=" * 60)
    print("2. os —— 目录操作")
    print("=" * 60)

    # 列出目录内容
    print(f"  当前目录内容:")
    for item in os.listdir(current_dir):
        full_path = os.path.join(current_dir, item)
        kind = "[DIR]" if os.path.isdir(full_path) else "[FILE]"
        print(f"    {kind} {item}")

    # 创建和删除目录
    test_dir = os.path.join(current_dir, "_temp_test")
    os.makedirs(test_dir, exist_ok=True)  # exist_ok=True 不报错如果已存在
    print(f"\n  创建目录: {test_dir}")
    print(f"  存在? {os.path.exists(test_dir)}")
    os.rmdir(test_dir)
    print(f"  删除后存在? {os.path.exists(test_dir)}")

    # os.walk：递归遍历目录树
    print(f"\n  os.walk 遍历 (只显示前3个):")
    for i, (dirpath, dirnames, filenames) in enumerate(os.walk(current_dir)):
        if i >= 3:
            print(f"    ...")
            break
        level = dirpath.replace(current_dir, "").count(os.sep)
        indent = "    " + "  " * level
        print(f"{indent}{os.path.basename(dirpath)}/")
        for f in filenames[:3]:
            print(f"{indent}  {f}")

    print()
    print("=" * 60)
    print("3. os —— 环境变量")
    print("=" * 60)

    print(f"  PATH 前 100 字符: {os.environ.get('PATH', '')[:100]}...")
    print(f"  HOME: {os.environ.get('HOME', '未设置')}")
    print(f"  获取不存在的变量: {os.environ.get('MY_VAR', '默认值')}")

    # 设置环境变量（只在当前进程有效）
    os.environ["MY_DEMO_VAR"] = "hello"
    print(f"  设置后: MY_DEMO_VAR = {os.environ['MY_DEMO_VAR']}")

    print()
    print("=" * 60)
    print("4. os —— 其他常用功能")
    print("=" * 60)

    print(f"  当前工作目录: {os.getcwd()}")
    print(f"  CPU 核心数: {os.cpu_count()}")
    print(f"  进程 ID: {os.getpid()}")
    print(f"  系统名称: {os.name}")  # posix / nt / java
    print(f"  路径分隔符: {os.sep}")
    print(f"  换行符: {repr(os.linesep)}")

    print()
    print("=" * 60)
    print("5. sys —— 解释器信息")
    print("=" * 60)

    print(f"  Python 版本: {sys.version}")
    print(f"  版本元组: {sys.version_info}")
    print(f"  平台: {sys.platform}")
    print(f"  默认编码: {sys.getdefaultencoding()}")
    print(f"  最大整数: {sys.maxsize}")
    print(f"  递归深度限制: {sys.getrecursionlimit()}")

    print()
    print("=" * 60)
    print("6. sys —— 命令行参数")
    print("=" * 60)

    # sys.argv 包含命令行参数列表
    # 第一个元素是脚本名称
    print(f"  sys.argv = {sys.argv}")
    print(f"  脚本名: {sys.argv[0]}")
    if len(sys.argv) > 1:
        print(f"  额外参数: {sys.argv[1:]}")
    else:
        print(f"  （没有额外参数，试试: python3 {os.path.basename(__file__)} arg1 arg2）")

    print()
    print("=" * 60)
    print("7. sys —— 模块搜索路径")
    print("=" * 60)

    print(f"  sys.path (前5项):")
    for p in sys.path[:5]:
        print(f"    {p}")

    # sys.exit(0) —— 正常退出
    # sys.exit(1) —— 异常退出
    # 这里不调用，否则程序会终止
