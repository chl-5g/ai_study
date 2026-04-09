#!/usr/bin/env python3
"""
Type Hints（类型提示）
Python 3.5+ 引入，不影响运行，但让代码更易读、IDE 更智能
"""

from typing import Optional, Union, Any
from typing import Dict, List, Tuple, Set  # Python 3.9+ 可直接用 dict, list 等
from dataclasses import dataclass


# ============================================================
# 1. 基础类型提示
# ============================================================

def greet(name: str) -> str:
    """参数类型: str，返回值类型: str"""
    return f"你好，{name}！"


def add(a: int, b: int) -> int:
    return a + b


def is_adult(age: int) -> bool:
    return age >= 18


# 变量也可以加类型提示
count: int = 0
name: str = "Allen"
pi: float = 3.14
is_active: bool = True


# ============================================================
# 2. 容器类型
# ============================================================

def average(numbers: list[float]) -> float:
    """Python 3.9+ 可以直接用 list[float]"""
    return sum(numbers) / len(numbers)


def count_words(text: str) -> dict[str, int]:
    """返回每个单词出现的次数"""
    words = text.lower().split()
    result: dict[str, int] = {}
    for word in words:
        result[word] = result.get(word, 0) + 1
    return result


def get_coordinates() -> tuple[float, float]:
    """元组类型提示：指定每个位置的类型"""
    return (39.9, 116.4)


def unique_tags(articles: list[list[str]]) -> set[str]:
    """嵌套容器类型"""
    tags: set[str] = set()
    for article_tags in articles:
        tags.update(article_tags)
    return tags


# ============================================================
# 3. Optional 和 Union
# ============================================================

def find_user(user_id: int) -> Optional[str]:
    """
    Optional[str] 等价于 Union[str, None] 等价于 str | None (3.10+)
    表示可能返回 str，也可能返回 None
    """
    users = {1: "Alice", 2: "Bob"}
    return users.get(user_id)


def process_input(value: Union[str, int]) -> str:
    """
    Union[str, int] 等价于 str | int (3.10+)
    接受多种类型
    """
    if isinstance(value, int):
        return f"数字: {value}"
    return f"字符串: {value}"


# ============================================================
# 4. 函数类型提示
# ============================================================

from typing import Callable

def apply_func(func: Callable[[int, int], int], a: int, b: int) -> int:
    """
    Callable[[参数类型列表], 返回类型]
    func 是一个接受两个 int 参数、返回 int 的函数
    """
    return func(a, b)


# ============================================================
# 5. dataclass（类型提示的最佳搭档）
# ============================================================

@dataclass
class User:
    """
    @dataclass 自动生成 __init__、__repr__、__eq__ 等方法
    结合 Type Hints 使用，代码极其简洁
    """
    name: str
    age: int
    email: str
    is_active: bool = True  # 有默认值的字段放后面
    tags: list[str] = None  # 注意：可变默认值需要特殊处理

    def __post_init__(self):
        """__init__ 之后自动调用，用于额外初始化"""
        if self.tags is None:
            self.tags = []


@dataclass
class Point:
    x: float
    y: float

    def distance_to(self, other: 'Point') -> float:
        """前向引用：用字符串 'Point' 引用尚未定义完的类"""
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5


# ============================================================
# 主程序
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("1. 基础类型提示")
    print("=" * 60)
    print(f"  {greet('Allen')}")
    print(f"  add(3, 5) = {add(3, 5)}")
    print(f"  is_adult(20) = {is_adult(20)}")

    # 类型提示不强制！传错类型也能运行（但 IDE 会警告）
    print(f"  add('hello', ' world') = {add('hello', ' world')}")  # 能运行，但不推荐

    print()
    print("=" * 60)
    print("2. 容器类型")
    print("=" * 60)
    print(f"  average([1, 2, 3, 4, 5]) = {average([1, 2, 3, 4, 5])}")
    print(f"  count_words('hello world hello') = {count_words('hello world hello')}")
    print(f"  get_coordinates() = {get_coordinates()}")

    articles = [["python", "ai"], ["python", "web"], ["ai", "ml"]]
    print(f"  unique_tags = {unique_tags(articles)}")

    print()
    print("=" * 60)
    print("3. Optional 和 Union")
    print("=" * 60)
    print(f"  find_user(1) = {find_user(1)}")
    print(f"  find_user(99) = {find_user(99)}")
    print(f"  process_input(42) = {process_input(42)}")
    print(f"  process_input('hi') = {process_input('hi')}")

    print()
    print("=" * 60)
    print("4. 函数类型")
    print("=" * 60)
    print(f"  apply_func(add, 3, 5) = {apply_func(add, 3, 5)}")
    print(f"  apply_func(lambda a,b: a*b, 3, 5) = {apply_func(lambda a, b: a * b, 3, 5)}")

    print()
    print("=" * 60)
    print("5. dataclass")
    print("=" * 60)
    user = User("Allen", 30, "allen@example.com", tags=["ai", "python"])
    print(f"  {user}")
    print(f"  user.name = {user.name}")

    p1 = Point(0, 0)
    p2 = Point(3, 4)
    print(f"  {p1} 到 {p2} 的距离 = {p1.distance_to(p2)}")

    # dataclass 自动生成 __eq__
    p3 = Point(0, 0)
    print(f"  Point(0,0) == Point(0,0)? {p1 == p3}")
