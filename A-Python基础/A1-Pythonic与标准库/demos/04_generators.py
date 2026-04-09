#!/usr/bin/env python3
"""
生成器（Generator）与 yield
核心思想：惰性计算 —— 需要一个值时才生成一个，不预先生成全部
"""

import sys


# ============================================================
# 1. 生成器函数 vs 普通函数
# ============================================================

def get_squares_list(n: int) -> list:
    """普通函数：一次性生成所有结果，占内存"""
    result = []
    for i in range(n):
        result.append(i ** 2)
    return result


def get_squares_gen(n: int):
    """
    生成器函数：用 yield 代替 return
    - 遇到 yield 时"暂停"，返回一个值
    - 下次迭代时从暂停处继续执行
    - 不会一次性把所有值放进内存
    """
    for i in range(n):
        yield i ** 2  # 每次暂停，返回一个平方数


# ============================================================
# 2. 理解 yield 的执行流程
# ============================================================

def countdown(n: int):
    """倒计时生成器：观察 yield 的暂停与恢复"""
    print(f"    [生成器] 开始倒计时，从 {n}")
    while n > 0:
        print(f"    [生成器] 即将 yield {n}")
        yield n  # 暂停，把 n 交给调用者
        print(f"    [生成器] 从 yield 恢复，继续执行")
        n -= 1
    print(f"    [生成器] 倒计时结束")


# ============================================================
# 3. 实用生成器示例
# ============================================================

def fibonacci():
    """
    无限斐波那契数列生成器
    生成器的强大之处：可以表示无限序列！
    列表做不到这一点（内存会爆）
    """
    a, b = 0, 1
    while True:  # 无限循环没关系，因为是惰性的
        yield a
        a, b = b, a + b


def read_large_file(filepath: str, chunk_size: int = 1024):
    """
    分块读取大文件（实际项目中非常常用）
    避免一次性把整个文件加载到内存
    """
    with open(filepath, "r") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            yield chunk


def batched(iterable, batch_size: int):
    """
    将数据分批处理（常用于数据库批量插入、API 批量请求）
    """
    batch = []
    for item in iterable:
        batch.append(item)
        if len(batch) == batch_size:
            yield batch
            batch = []
    if batch:  # 最后一批（可能不满 batch_size）
        yield batch


# ============================================================
# 4. yield from（委托生成器）
# ============================================================

def chain(*iterables):
    """
    yield from：把一个可迭代对象的所有值"委托"出去
    等价于 for item in iterable: yield item
    但更简洁、更高效
    """
    for it in iterables:
        yield from it  # 把 it 中的每个元素依次 yield 出去


# ============================================================
# 主程序
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("1. 生成器 vs 列表：内存对比")
    print("=" * 60)

    n = 100_000
    lst = get_squares_list(n)
    gen = get_squares_gen(n)

    print(f"  列表占用内存: {sys.getsizeof(lst):,} 字节")
    print(f"  生成器占用内存: {sys.getsizeof(gen):,} 字节")
    print(f"  差距: {sys.getsizeof(lst) / sys.getsizeof(gen):.0f} 倍")

    print()
    print("=" * 60)
    print("2. yield 的执行流程（观察暂停与恢复）")
    print("=" * 60)

    print("  开始迭代 countdown(3):")
    for num in countdown(3):
        print(f"    [调用者] 收到值: {num}")
        print()

    print()
    print("=" * 60)
    print("3. 无限序列：斐波那契数列前 15 个")
    print("=" * 60)

    fib = fibonacci()
    fib_list = [next(fib) for _ in range(15)]
    print(f"  {fib_list}")

    print()
    print("=" * 60)
    print("4. 数据分批处理")
    print("=" * 60)

    data = list(range(1, 12))
    print(f"  原始数据: {data}")
    print(f"  分批（每批 3 个）:")
    for i, batch in enumerate(batched(data, 3)):
        print(f"    第 {i+1} 批: {batch}")

    print()
    print("=" * 60)
    print("5. yield from：链接多个可迭代对象")
    print("=" * 60)

    result = list(chain([1, 2, 3], "abc", (10, 20)))
    print(f"  chain([1,2,3], 'abc', (10,20)) = {result}")

    print()
    print("=" * 60)
    print("6. 生成器表达式（一行写法）")
    print("=" * 60)

    # 生成器表达式：用圆括号
    gen_expr = (x ** 2 for x in range(10) if x % 2 == 0)
    print(f"  偶数平方和: {sum(gen_expr)}")

    # 生成器只能遍历一次！
    gen = (x for x in range(5))
    print(f"  第一次: {list(gen)}")
    print(f"  第二次: {list(gen)}")  # 空的！生成器已耗尽
