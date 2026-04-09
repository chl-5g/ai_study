#!/usr/bin/env python3
"""
装饰器（Decorator）
从闭包讲起，理解 @ 语法糖的本质
"""

import time
import functools


# ============================================================
# 1. 前置知识：闭包（Closure）
# ============================================================

def make_multiplier(factor: int):
    """
    闭包示例：内部函数"记住"了外部函数的变量
    即使外部函数已经返回，内部函数仍然可以访问 factor
    """
    def multiplier(x):
        return x * factor  # factor 来自外层函数，被"闭包"住了
    return multiplier  # 返回函数本身（不是调用结果）


# ============================================================
# 2. 最简单的装饰器
# ============================================================

def simple_logger(func):
    """
    装饰器的本质：
    1. 接收一个函数作为参数
    2. 返回一个新函数（通常是 wrapper）
    3. 新函数在调用原函数前后添加额外行为

    @simple_logger 等价于 func = simple_logger(func)
    """
    @functools.wraps(func)  # 保留原函数的名称和文档字符串
    def wrapper(*args, **kwargs):
        print(f"    [LOG] 调用 {func.__name__}(args={args}, kwargs={kwargs})")
        result = func(*args, **kwargs)  # 调用原函数
        print(f"    [LOG] {func.__name__} 返回 {result}")
        return result
    return wrapper


@simple_logger  # 等价于 add = simple_logger(add)
def add(a, b):
    """两数相加"""
    return a + b


# ============================================================
# 3. 实用装饰器：计时器
# ============================================================

def timer(func):
    """测量函数执行时间的装饰器"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"    {func.__name__} 耗时: {elapsed:.6f} 秒")
        return result
    return wrapper


@timer
def slow_sum(n: int) -> int:
    """计算 1+2+...+n（故意用循环来演示耗时）"""
    total = 0
    for i in range(n + 1):
        total += i
    return total


# ============================================================
# 4. 带参数的装饰器（三层嵌套）
# ============================================================

def retry(max_attempts: int = 3, delay: float = 0.1):
    """
    带参数的装饰器：需要三层函数
    第一层：接收装饰器的参数
    第二层：接收被装饰的函数
    第三层：实际的 wrapper

    用法：@retry(max_attempts=5)
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    print(f"    [重试] {func.__name__} 第 {attempt} 次失败: {e}")
                    if attempt < max_attempts:
                        time.sleep(delay)
            raise last_exception
        return wrapper
    return decorator


# 模拟一个不稳定的函数
call_count = 0

@retry(max_attempts=3, delay=0.1)
def unstable_function():
    """模拟不稳定的网络请求"""
    global call_count
    call_count += 1
    if call_count < 3:
        raise ConnectionError(f"连接失败（第 {call_count} 次）")
    return "成功！"


# ============================================================
# 5. 类作为装饰器
# ============================================================

class CountCalls:
    """
    用类实现装饰器：通过 __call__ 魔术方法
    好处：可以保存状态（比如调用次数）
    """

    def __init__(self, func):
        self.func = func
        self.count = 0
        functools.update_wrapper(self, func)

    def __call__(self, *args, **kwargs):
        self.count += 1
        print(f"    [{self.func.__name__}] 第 {self.count} 次调用")
        return self.func(*args, **kwargs)


@CountCalls
def greet(name: str) -> str:
    return f"你好，{name}！"


# ============================================================
# 6. 多个装饰器叠加
# ============================================================

def bold(func):
    """加粗装饰器"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return f"**{func(*args, **kwargs)}**"
    return wrapper


def italic(func):
    """斜体装饰器"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return f"_{func(*args, **kwargs)}_"
    return wrapper


@bold       # 第二步：bold(italic(hello))
@italic     # 第一步：italic(hello)
def hello(name: str) -> str:
    return f"Hello, {name}"


# ============================================================
# 主程序
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("1. 闭包：函数记住外部变量")
    print("=" * 60)
    double = make_multiplier(2)
    triple = make_multiplier(3)
    print(f"  double(5) = {double(5)}")  # 10
    print(f"  triple(5) = {triple(5)}")  # 15

    print()
    print("=" * 60)
    print("2. 简单装饰器：@simple_logger")
    print("=" * 60)
    result = add(3, 5)
    print(f"  函数名保留: {add.__name__}")  # functools.wraps 的作用
    print(f"  文档保留: {add.__doc__}")

    print()
    print("=" * 60)
    print("3. 计时装饰器：@timer")
    print("=" * 60)
    result = slow_sum(1_000_000)
    print(f"  结果: {result:,}")

    print()
    print("=" * 60)
    print("4. 带参数装饰器：@retry")
    print("=" * 60)
    call_count = 0  # 重置
    result = unstable_function()
    print(f"  最终结果: {result}")

    print()
    print("=" * 60)
    print("5. 类装饰器：@CountCalls")
    print("=" * 60)
    greet("Alice")
    greet("Bob")
    greet("Charlie")
    print(f"  总调用次数: {greet.count}")

    print()
    print("=" * 60)
    print("6. 装饰器叠加顺序")
    print("=" * 60)
    print(f"  @bold @italic hello('World') = {hello('World')}")
    print(f"  执行顺序：先 italic 再 bold → **_Hello, World_**")
