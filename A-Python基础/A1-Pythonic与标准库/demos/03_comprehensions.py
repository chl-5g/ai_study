#!/usr/bin/env python3
"""
推导式（Comprehensions）
Python 最具特色的语法糖之一，用一行代码替代多行循环
"""


if __name__ == "__main__":

    # ============================================================
    # 1. 列表推导式（List Comprehension）
    # ============================================================
    print("=" * 60)
    print("1. 列表推导式")
    print("=" * 60)

    # 传统写法：创建平方数列表
    squares_old = []
    for i in range(10):
        squares_old.append(i ** 2)

    # 推导式写法：[表达式 for 变量 in 可迭代对象]
    squares = [i ** 2 for i in range(10)]
    print(f"  平方数: {squares}")

    # 带条件过滤：[表达式 for 变量 in 可迭代对象 if 条件]
    even_squares = [i ** 2 for i in range(10) if i % 2 == 0]
    print(f"  偶数的平方: {even_squares}")

    # 带 if-else（注意位置不同！）
    # if 在 for 前面时是三元表达式的一部分
    labels = ["偶" if i % 2 == 0 else "奇" for i in range(6)]
    print(f"  奇偶标签: {labels}")

    # 嵌套循环
    pairs = [(x, y) for x in range(3) for y in range(3) if x != y]
    print(f"  不相等的坐标对: {pairs}")

    # 字符串处理
    words = ["Hello", "World", "Python"]
    lower_words = [w.lower() for w in words]
    print(f"  转小写: {lower_words}")

    # ============================================================
    # 2. 字典推导式（Dict Comprehension）
    # ============================================================
    print()
    print("=" * 60)
    print("2. 字典推导式")
    print("=" * 60)

    # {key表达式: value表达式 for 变量 in 可迭代对象}
    square_dict = {i: i ** 2 for i in range(6)}
    print(f"  数字→平方: {square_dict}")

    # 反转字典的 key 和 value
    original = {"a": 1, "b": 2, "c": 3}
    reversed_dict = {v: k for k, v in original.items()}
    print(f"  反转字典: {reversed_dict}")

    # 过滤
    scores = {"张三": 85, "李四": 62, "王五": 91, "赵六": 45}
    passed = {name: score for name, score in scores.items() if score >= 60}
    print(f"  及格的同学: {passed}")

    # ============================================================
    # 3. 集合推导式（Set Comprehension）
    # ============================================================
    print()
    print("=" * 60)
    print("3. 集合推导式")
    print("=" * 60)

    # 集合自动去重
    text = "hello world"
    unique_chars = {c for c in text if c != " "}
    print(f"  '{text}' 的不重复字符: {unique_chars}")

    # 提取文件扩展名
    files = ["main.py", "utils.py", "readme.md", "test.py", "config.json"]
    extensions = {f.split(".")[-1] for f in files}
    print(f"  文件扩展名: {extensions}")

    # ============================================================
    # 4. 生成器表达式（Generator Expression）
    # ============================================================
    print()
    print("=" * 60)
    print("4. 生成器表达式（用圆括号）")
    print("=" * 60)

    # 和列表推导式的区别：用 () 而不是 []
    # 生成器是惰性的，不会一次性生成所有元素，节省内存
    gen = (i ** 2 for i in range(10))
    print(f"  生成器对象: {gen}")
    print(f"  转为列表: {list(gen)}")

    # 实际应用：sum/max/min 直接接受生成器
    total = sum(i ** 2 for i in range(10))  # 不需要额外的括号
    print(f"  平方和: {total}")

    # 大数据场景的内存优势
    # 列表推导式：[i for i in range(10_000_000)]  → 占用大量内存
    # 生成器表达式：(i for i in range(10_000_000)) → 几乎不占内存

    # ============================================================
    # 5. 实战：数据清洗
    # ============================================================
    print()
    print("=" * 60)
    print("5. 实战：数据清洗")
    print("=" * 60)

    raw_data = ["  Alice  ", "bob", "  CHARLIE", "", "  ", "David  "]

    # 一步到位：去空白、统一格式、过滤空值
    cleaned = [name.strip().title() for name in raw_data if name.strip()]
    print(f"  原始数据: {raw_data}")
    print(f"  清洗结果: {cleaned}")

    # 嵌套列表展平（flatten）
    matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    flat = [num for row in matrix for num in row]
    print(f"  矩阵: {matrix}")
    print(f"  展平: {flat}")
