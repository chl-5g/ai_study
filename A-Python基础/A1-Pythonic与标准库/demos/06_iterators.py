#!/usr/bin/env python3
"""
迭代器协议（Iterator Protocol）
理解 for 循环背后到底发生了什么
"""


# ============================================================
# 1. 迭代器协议：__iter__ 和 __next__
# ============================================================

class CountDown:
    """
    自定义迭代器：倒计时

    迭代器协议要求实现两个方法：
    - __iter__(): 返回迭代器对象本身（通常返回 self）
    - __next__(): 返回下一个值，没有更多值时抛出 StopIteration

    for 循环的本质：
        for x in obj:   等价于

        it = iter(obj)          # 调用 __iter__()
        while True:
            try:
                x = next(it)    # 调用 __next__()
            except StopIteration:
                break
    """

    def __init__(self, start: int):
        self.current = start

    def __iter__(self):
        """返回自身作为迭代器"""
        return self

    def __next__(self) -> int:
        """返回下一个值"""
        if self.current <= 0:
            raise StopIteration  # 告诉 for 循环"没了"
        value = self.current
        self.current -= 1
        return value


# ============================================================
# 2. 可迭代对象 vs 迭代器
# ============================================================

class NumberRange:
    """
    可迭代对象（Iterable）：实现 __iter__ 返回一个新的迭代器

    与迭代器的区别：
    - 可迭代对象可以多次遍历（每次创建新的迭代器）
    - 迭代器只能遍历一次（遍历完就耗尽了）

    类比：
    - 可迭代对象 = 一本书（可以反复翻阅）
    - 迭代器 = 书签（读到哪算哪，读完就没了）
    """

    def __init__(self, start: int, end: int):
        self.start = start
        self.end = end

    def __iter__(self):
        """每次调用都返回一个新的迭代器"""
        return NumberRangeIterator(self.start, self.end)


class NumberRangeIterator:
    """NumberRange 的迭代器"""

    def __init__(self, start: int, end: int):
        self.current = start
        self.end = end

    def __iter__(self):
        return self

    def __next__(self) -> int:
        if self.current >= self.end:
            raise StopIteration
        value = self.current
        self.current += 1
        return value


# ============================================================
# 3. 实用迭代器：循环迭代器
# ============================================================

class CycleIterator:
    """
    无限循环迭代器：到末尾后自动回到开头
    类似 itertools.cycle()
    """

    def __init__(self, items):
        self.items = list(items)
        self.index = 0
        if not self.items:
            raise ValueError("不能创建空的循环迭代器")

    def __iter__(self):
        return self

    def __next__(self):
        value = self.items[self.index]
        self.index = (self.index + 1) % len(self.items)
        return value


# ============================================================
# 主程序
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("1. 自定义迭代器：CountDown")
    print("=" * 60)

    print("  for 循环遍历:")
    for num in CountDown(5):
        print(f"    {num}", end=" ")
    print()

    # 手动调用 next() 来理解底层原理
    print("\n  手动调用 next():")
    cd = CountDown(3)
    print(f"    next() → {next(cd)}")
    print(f"    next() → {next(cd)}")
    print(f"    next() → {next(cd)}")
    try:
        next(cd)
    except StopIteration:
        print("    next() → StopIteration（已耗尽）")

    print()
    print("=" * 60)
    print("2. 可迭代对象 vs 迭代器")
    print("=" * 60)

    # 迭代器：只能遍历一次
    print("  迭代器（CountDown）只能遍历一次:")
    cd = CountDown(3)
    print(f"    第1次: {list(cd)}")
    print(f"    第2次: {list(cd)}")  # 空！已耗尽

    # 可迭代对象：可以多次遍历
    print("\n  可迭代对象（NumberRange）可以多次遍历:")
    nr = NumberRange(1, 4)
    print(f"    第1次: {list(nr)}")
    print(f"    第2次: {list(nr)}")  # 正常！每次创建新迭代器

    print()
    print("=" * 60)
    print("3. Python 内置可迭代对象")
    print("=" * 60)

    # 这些都是可迭代的
    print("  列表:", list(iter([1, 2, 3])))
    print("  字符串:", list(iter("abc")))
    print("  字典:", list(iter({"a": 1, "b": 2})))  # 迭代的是 key
    print("  range:", list(iter(range(5))))

    print()
    print("=" * 60)
    print("4. 循环迭代器")
    print("=" * 60)

    colors = CycleIterator(["红", "黄", "蓝"])
    first_9 = [next(colors) for _ in range(9)]
    print(f"  循环取 9 个: {first_9}")

    print()
    print("=" * 60)
    print("5. 内置迭代工具")
    print("=" * 60)

    # enumerate：带索引的迭代
    fruits = ["苹果", "香蕉", "橙子"]
    print("  enumerate:")
    for i, fruit in enumerate(fruits, start=1):
        print(f"    {i}. {fruit}")

    # zip：并行迭代多个序列
    names = ["Alice", "Bob", "Charlie"]
    scores = [85, 92, 78]
    print("  zip:")
    for name, score in zip(names, scores):
        print(f"    {name}: {score}")

    # map + filter（函数式风格）
    nums = [1, 2, 3, 4, 5, 6]
    evens_doubled = list(map(lambda x: x * 2, filter(lambda x: x % 2 == 0, nums)))
    print(f"  filter+map 偶数*2: {evens_doubled}")
