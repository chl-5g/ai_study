#!/usr/bin/env python3
"""
上下文管理器（Context Manager）与 with 语句
核心思想：确保资源的获取和释放成对出现，即使出错也不会泄漏
"""

import os
import time
from contextlib import contextmanager


# ============================================================
# 1. with 语句解决了什么问题？
# ============================================================

def demo_without_with():
    """没有 with 的写法（容易忘记关闭文件）"""
    f = open("/tmp/test_ctx.txt", "w")
    try:
        f.write("hello")
    finally:
        f.close()  # 必须手动关闭，容易忘记


def demo_with_with():
    """有 with 的写法（自动关闭，安全简洁）"""
    with open("/tmp/test_ctx.txt", "w") as f:
        f.write("hello")
    # 离开 with 块后，f 自动关闭，即使发生异常也会关闭


# ============================================================
# 2. 用类实现上下文管理器
# ============================================================

class Timer:
    """
    计时器上下文管理器

    需要实现两个魔术方法：
    - __enter__(): 进入 with 块时调用，返回值赋给 as 后面的变量
    - __exit__():  离开 with 块时调用（无论是否发生异常）
    """

    def __enter__(self):
        """进入 with 块"""
        self.start = time.perf_counter()
        print("  [Timer] 开始计时...")
        return self  # 这个值会赋给 as 后面的变量

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        离开 with 块

        参数说明（用于异常处理）：
        - exc_type: 异常类型（没有异常则为 None）
        - exc_val:  异常值
        - exc_tb:   异常追踪信息

        返回值：
        - True:  吞掉异常，程序继续运行
        - False: 不处理异常，继续向上抛出（默认）
        """
        self.elapsed = time.perf_counter() - self.start
        print(f"  [Timer] 耗时: {self.elapsed:.6f} 秒")
        return False  # 不吞掉异常

    @property
    def duration(self):
        return self.elapsed


class FileManager:
    """文件管理器：演示异常处理"""

    def __init__(self, filename: str, mode: str = "w"):
        self.filename = filename
        self.mode = mode
        self.file = None

    def __enter__(self):
        print(f"  [FileManager] 打开文件: {self.filename}")
        self.file = open(self.filename, self.mode)
        return self.file

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.file:
            self.file.close()
            print(f"  [FileManager] 文件已关闭: {self.filename}")
        if exc_type:
            print(f"  [FileManager] 捕获异常: {exc_type.__name__}: {exc_val}")
        return False  # 不吞掉异常


# ============================================================
# 3. 用 @contextmanager 装饰器（更简洁的写法）
# ============================================================

@contextmanager
def timer_simple(label: str = "代码块"):
    """
    用 @contextmanager 实现计时器

    yield 之前的代码 = __enter__
    yield 的值 = as 后面的变量
    yield 之后的代码 = __exit__
    """
    start = time.perf_counter()
    print(f"  [{label}] 开始...")
    yield  # 在这里暂停，执行 with 块中的代码
    elapsed = time.perf_counter() - start
    print(f"  [{label}] 完成，耗时: {elapsed:.6f} 秒")


@contextmanager
def temp_directory(path: str):
    """临时目录管理器：进入时创建，退出时清理"""
    os.makedirs(path, exist_ok=True)
    print(f"  创建临时目录: {path}")
    try:
        yield path
    finally:
        # finally 确保清理代码一定执行
        if os.path.exists(path):
            os.rmdir(path)
            print(f"  清理临时目录: {path}")


@contextmanager
def suppress_errors(*exception_types):
    """
    抑制指定类型的异常（类似 contextlib.suppress）
    演示 try/except 与 yield 的配合
    """
    try:
        yield
    except exception_types as e:
        print(f"  [已抑制] {type(e).__name__}: {e}")


# ============================================================
# 主程序
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("1. 基本 with 用法：文件操作")
    print("=" * 60)

    test_file = "/tmp/test_context_manager.txt"
    with open(test_file, "w") as f:
        f.write("Hello, Context Manager!\n")
        print(f"  写入文件: {test_file}")
    # f 已自动关闭
    print(f"  文件已关闭? {f.closed}")

    with open(test_file, "r") as f:
        content = f.read()
        print(f"  读取内容: {content.strip()}")

    print()
    print("=" * 60)
    print("2. 类实现的上下文管理器：Timer")
    print("=" * 60)

    with Timer() as t:
        total = sum(range(1_000_000))
    print(f"  计算结果: {total:,}")

    print()
    print("=" * 60)
    print("3. @contextmanager 装饰器写法")
    print("=" * 60)

    with timer_simple("求和计算"):
        total = sum(i ** 2 for i in range(100_000))

    print()
    print("=" * 60)
    print("4. 临时资源管理")
    print("=" * 60)

    with temp_directory("/tmp/my_temp_dir"):
        print(f"  目录存在? {os.path.exists('/tmp/my_temp_dir')}")
    print(f"  退出后存在? {os.path.exists('/tmp/my_temp_dir')}")

    print()
    print("=" * 60)
    print("5. 异常抑制")
    print("=" * 60)

    with suppress_errors(ZeroDivisionError, ValueError):
        result = 1 / 0  # 异常被抑制，不会崩溃
    print("  程序继续运行！")

    print()
    print("=" * 60)
    print("6. 多个上下文管理器同时使用")
    print("=" * 60)

    # 同时管理多个资源
    file1 = "/tmp/ctx_a.txt"
    file2 = "/tmp/ctx_b.txt"
    with open(file1, "w") as f1, open(file2, "w") as f2:
        f1.write("文件A")
        f2.write("文件B")
        print(f"  同时打开了 {file1} 和 {file2}")
    print(f"  两个文件都已关闭: {f1.closed}, {f2.closed}")

    # 清理临时文件
    for f in [test_file, file1, file2]:
        os.remove(f) if os.path.exists(f) else None
