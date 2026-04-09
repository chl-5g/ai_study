#!/usr/bin/env python3
"""
魔术方法（Magic Methods / Dunder Methods）
以 __ 开头和结尾的特殊方法，让你的类支持 Python 内置操作
"""


class Vector:
    """
    二维向量类 —— 用来演示各种魔术方法
    让自定义对象也能像内置类型一样使用 +、==、len() 等操作
    """

    def __init__(self, x: float, y: float):
        """构造方法：最常用的魔术方法"""
        self.x = x
        self.y = y

    # ---- 字符串表示 ----

    def __str__(self) -> str:
        """print() 时调用，给用户看的"""
        return f"Vector({self.x}, {self.y})"

    def __repr__(self) -> str:
        """交互式环境/调试时调用，给开发者看的，应该能用来重建对象"""
        return f"Vector({self.x!r}, {self.y!r})"

    # ---- 算术运算 ----

    def __add__(self, other):
        """支持 v1 + v2"""
        if isinstance(other, Vector):
            return Vector(self.x + other.x, self.y + other.y)
        return NotImplemented  # 告诉 Python "我不知道怎么处理这个类型"

    def __sub__(self, other):
        """支持 v1 - v2"""
        if isinstance(other, Vector):
            return Vector(self.x - other.x, self.y - other.y)
        return NotImplemented

    def __mul__(self, scalar):
        """支持 v * 3（向量数乘）"""
        if isinstance(scalar, (int, float)):
            return Vector(self.x * scalar, self.y * scalar)
        return NotImplemented

    def __rmul__(self, scalar):
        """支持 3 * v（反向乘法）"""
        return self.__mul__(scalar)

    # ---- 比较运算 ----

    def __eq__(self, other) -> bool:
        """支持 v1 == v2"""
        if isinstance(other, Vector):
            return self.x == other.x and self.y == other.y
        return NotImplemented

    def __lt__(self, other) -> bool:
        """支持 v1 < v2（按向量长度比较）"""
        if isinstance(other, Vector):
            return abs(self) < abs(other)
        return NotImplemented

    # ---- 内置函数支持 ----

    def __abs__(self) -> float:
        """支持 abs(v)，返回向量长度"""
        return (self.x ** 2 + self.y ** 2) ** 0.5

    def __len__(self) -> int:
        """支持 len(v)，返回维度数"""
        return 2

    def __bool__(self) -> bool:
        """
        支持 if v: ...
        零向量为 False，非零向量为 True
        """
        return self.x != 0 or self.y != 0

    # ---- 容器行为 ----

    def __getitem__(self, index):
        """
        支持 v[0], v[1] 下标访问
        让 Vector 可以像列表一样用索引
        """
        if index == 0:
            return self.x
        elif index == 1:
            return self.y
        else:
            raise IndexError(f"Vector 只有 2 个分量，索引 {index} 越界")

    def __iter__(self):
        """
        支持 for x in v: ...
        让 Vector 可以被迭代、解包
        """
        yield self.x
        yield self.y

    # ---- 哈希（让对象能放入 set 和用作 dict 的 key）----

    def __hash__(self) -> int:
        return hash((self.x, self.y))


# ============================================================
# 另一个例子：温度类（演示 __format__ 和 __del__）
# ============================================================

class Temperature:
    """温度类：演示 __format__ 自定义格式化"""

    def __init__(self, celsius: float):
        self.celsius = celsius

    def __str__(self) -> str:
        return f"{self.celsius}°C"

    def __format__(self, format_spec: str) -> str:
        """
        支持 f"{temp:f}" 华氏度，f"{temp:c}" 摄氏度
        format_spec 就是冒号后面的内容
        """
        if format_spec == "f":
            fahrenheit = self.celsius * 9 / 5 + 32
            return f"{fahrenheit:.1f}°F"
        elif format_spec == "c":
            return f"{self.celsius:.1f}°C"
        elif format_spec == "k":
            kelvin = self.celsius + 273.15
            return f"{kelvin:.1f}K"
        else:
            return str(self)


# ============================================================
# 主程序
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("1. 字符串表示：__str__ 和 __repr__")
    print("=" * 60)
    v1 = Vector(3, 4)
    print(f"  str:  {v1}")        # 调用 __str__
    print(f"  repr: {v1!r}")      # 调用 __repr__

    print()
    print("=" * 60)
    print("2. 算术运算：__add__, __sub__, __mul__")
    print("=" * 60)
    v2 = Vector(1, 2)
    print(f"  {v1} + {v2} = {v1 + v2}")      # __add__
    print(f"  {v1} - {v2} = {v1 - v2}")      # __sub__
    print(f"  {v1} * 3 = {v1 * 3}")          # __mul__
    print(f"  3 * {v1} = {3 * v1}")          # __rmul__

    print()
    print("=" * 60)
    print("3. 比较运算：__eq__, __lt__")
    print("=" * 60)
    v3 = Vector(3, 4)
    print(f"  {v1} == {v3}? {v1 == v3}")     # __eq__
    print(f"  {v1} == {v2}? {v1 == v2}")
    print(f"  {v2} < {v1}?  {v2 < v1}")     # __lt__

    print()
    print("=" * 60)
    print("4. 内置函数：abs(), len(), bool()")
    print("=" * 60)
    print(f"  abs({v1}) = {abs(v1):.2f}")   # __abs__ → 向量长度 5.0
    print(f"  len({v1}) = {len(v1)}")        # __len__ → 维度 2
    print(f"  bool({v1}) = {bool(v1)}")      # __bool__
    zero = Vector(0, 0)
    print(f"  bool({zero}) = {bool(zero)}")  # 零向量 → False

    print()
    print("=" * 60)
    print("5. 容器行为：__getitem__, __iter__")
    print("=" * 60)
    print(f"  {v1}[0] = {v1[0]}")           # __getitem__
    print(f"  {v1}[1] = {v1[1]}")
    x, y = v1  # 解包，依赖 __iter__
    print(f"  解包: x={x}, y={y}")
    print(f"  遍历:", end=" ")
    for component in v1:  # __iter__
        print(component, end=" ")
    print()

    print()
    print("=" * 60)
    print("6. 哈希：__hash__（可以放入 set / 做 dict 的 key）")
    print("=" * 60)
    vectors = {Vector(1, 2), Vector(3, 4), Vector(1, 2)}  # 去重
    print(f"  集合（自动去重）: {vectors}")
    d = {Vector(1, 0): "右", Vector(0, 1): "上"}
    print(f"  字典: {d}")

    print()
    print("=" * 60)
    print("7. 自定义格式化：__format__")
    print("=" * 60)
    temp = Temperature(100)
    print(f"  摄氏: {temp:c}")
    print(f"  华氏: {temp:f}")
    print(f"  开尔文: {temp:k}")
