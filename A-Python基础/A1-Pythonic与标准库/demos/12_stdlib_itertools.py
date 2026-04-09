#!/usr/bin/env python3
"""
标准库：itertools 模块
高效的迭代工具，处理排列组合、无限序列、分组等
"""

import itertools


if __name__ == "__main__":
    # ============================================================
    # 1. 无限迭代器
    # ============================================================
    print("=" * 60)
    print("1. 无限迭代器")
    print("=" * 60)

    # count: 从 n 开始无限计数
    counter = itertools.count(start=1, step=2)  # 1, 3, 5, 7, ...
    first_5 = [next(counter) for _ in range(5)]
    print(f"  count(1, step=2) 前5个: {first_5}")

    # cycle: 无限循环一个序列
    cycler = itertools.cycle(["红", "黄", "绿"])
    first_7 = [next(cycler) for _ in range(7)]
    print(f"  cycle(['红','黄','绿']) 前7个: {first_7}")

    # repeat: 重复一个值
    repeated = list(itertools.repeat("hello", 3))
    print(f"  repeat('hello', 3): {repeated}")

    # ============================================================
    # 2. 组合工具
    # ============================================================
    print()
    print("=" * 60)
    print("2. 排列组合")
    print("=" * 60)

    # permutations: 排列（顺序有关）
    perms = list(itertools.permutations("ABC", 2))
    print(f"  permutations('ABC', 2): {perms}")
    print(f"    → 共 {len(perms)} 种")

    # combinations: 组合（顺序无关）
    combs = list(itertools.combinations("ABCD", 2))
    print(f"  combinations('ABCD', 2): {combs}")
    print(f"    → 共 {len(combs)} 种")

    # combinations_with_replacement: 可重复组合
    combs_r = list(itertools.combinations_with_replacement("AB", 3))
    print(f"  combinations_with_replacement('AB', 3): {combs_r}")

    # product: 笛卡尔积
    prod = list(itertools.product("AB", "12"))
    print(f"  product('AB', '12'): {prod}")

    # 实用：生成密码组合
    digits = "0123456789"
    three_digit = list(itertools.product(digits, repeat=3))
    print(f"  3位数字密码总数: {len(three_digit)}")

    # ============================================================
    # 3. 链接与分片
    # ============================================================
    print()
    print("=" * 60)
    print("3. 链接与分片")
    print("=" * 60)

    # chain: 链接多个可迭代对象
    combined = list(itertools.chain([1, 2], [3, 4], [5, 6]))
    print(f"  chain([1,2], [3,4], [5,6]): {combined}")

    # chain.from_iterable: 展平嵌套列表
    nested = [[1, 2], [3, 4], [5, 6]]
    flat = list(itertools.chain.from_iterable(nested))
    print(f"  展平 {nested}: {flat}")

    # islice: 切片（适用于迭代器，不会一次加载全部）
    sliced = list(itertools.islice(range(100), 5, 15, 2))
    print(f"  islice(range(100), 5, 15, 2): {sliced}")

    # ============================================================
    # 4. 过滤
    # ============================================================
    print()
    print("=" * 60)
    print("4. 过滤工具")
    print("=" * 60)

    data = [1, 0, 2, 0, 3, 0, 4]

    # takewhile: 取到条件为 False 时停止
    taken = list(itertools.takewhile(lambda x: x < 3, [1, 2, 5, 1, 0]))
    print(f"  takewhile(x<3, [1,2,5,1,0]): {taken}")  # [1, 2]

    # dropwhile: 丢弃直到条件为 False，然后取剩余全部
    dropped = list(itertools.dropwhile(lambda x: x < 3, [1, 2, 5, 1, 0]))
    print(f"  dropwhile(x<3, [1,2,5,1,0]): {dropped}")  # [5, 1, 0]

    # filterfalse: filter 的反向版本
    falsy = list(itertools.filterfalse(lambda x: x % 2, range(10)))
    print(f"  filterfalse(奇数, range(10)): {falsy}")  # 偶数

    # compress: 用选择器过滤
    data = ["A", "B", "C", "D", "E"]
    selectors = [1, 0, 1, 0, 1]
    selected = list(itertools.compress(data, selectors))
    print(f"  compress({data}, {selectors}): {selected}")

    # ============================================================
    # 5. 分组
    # ============================================================
    print()
    print("=" * 60)
    print("5. groupby —— 分组（数据必须先排序！）")
    print("=" * 60)

    # groupby 只对连续相同的元素分组，所以必须先排序
    students = [
        {"name": "张三", "grade": "A"},
        {"name": "李四", "grade": "B"},
        {"name": "王五", "grade": "A"},
        {"name": "赵六", "grade": "B"},
        {"name": "钱七", "grade": "A"},
    ]

    # 先按 grade 排序
    sorted_students = sorted(students, key=lambda s: s["grade"])

    # 再分组
    print("  按成绩分组:")
    for grade, group in itertools.groupby(sorted_students, key=lambda s: s["grade"]):
        names = [s["name"] for s in group]
        print(f"    {grade}: {names}")

    # ============================================================
    # 6. 累积
    # ============================================================
    print()
    print("=" * 60)
    print("6. accumulate —— 累积计算")
    print("=" * 60)

    nums = [1, 2, 3, 4, 5]

    # 默认累加
    acc_sum = list(itertools.accumulate(nums))
    print(f"  累加 {nums}: {acc_sum}")

    # 自定义函数：累乘
    import operator
    acc_mul = list(itertools.accumulate(nums, operator.mul))
    print(f"  累乘 {nums}: {acc_mul}")

    # 实用：求运行最大值
    data = [3, 1, 4, 1, 5, 9, 2, 6]
    running_max = list(itertools.accumulate(data, max))
    print(f"  运行最大值 {data}: {running_max}")

    # ============================================================
    # 7. 实战：批量数据处理
    # ============================================================
    print()
    print("=" * 60)
    print("7. 实战应用")
    print("=" * 60)

    # 分批处理（batch）—— Python 3.12+ 有 itertools.batched
    def batched(iterable, n):
        it = iter(iterable)
        while True:
            batch = list(itertools.islice(it, n))
            if not batch:
                break
            yield batch

    data = list(range(1, 11))
    print(f"  分批处理 {data} (每批3个):")
    for i, batch in enumerate(batched(data, 3), 1):
        print(f"    第{i}批: {batch}")

    # 生成时间序列的标签
    months = itertools.cycle(["Q1", "Q2", "Q3", "Q4"])
    years = itertools.chain.from_iterable(
        itertools.repeat(y, 4) for y in range(2024, 2027)
    )
    labels = [f"{y}-{q}" for y, q in itertools.islice(zip(years, months), 12)]
    print(f"\n  季度标签: {labels}")
