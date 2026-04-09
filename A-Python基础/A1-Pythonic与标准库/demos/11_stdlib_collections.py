#!/usr/bin/env python3
"""
标准库：collections 模块
提供比内置 dict/list/tuple 更强大的数据结构
"""

from collections import Counter, defaultdict, OrderedDict, namedtuple, deque


if __name__ == "__main__":
    # ============================================================
    # 1. Counter —— 计数器（统计频次神器）
    # ============================================================
    print("=" * 60)
    print("1. Counter —— 计数器")
    print("=" * 60)

    # 统计字符频率
    text = "abracadabra"
    char_count = Counter(text)
    print(f"  '{text}' 的字符频率: {char_count}")
    print(f"  最常见的3个: {char_count.most_common(3)}")

    # 统计单词
    words = "the cat sat on the mat the cat".split()
    word_count = Counter(words)
    print(f"  单词统计: {word_count}")

    # Counter 的运算
    c1 = Counter(a=3, b=1)
    c2 = Counter(a=1, b=2)
    print(f"  c1 + c2 = {c1 + c2}")  # 合并
    print(f"  c1 - c2 = {c1 - c2}")  # 差集（只保留正数）

    # ============================================================
    # 2. defaultdict —— 带默认值的字典
    # ============================================================
    print()
    print("=" * 60)
    print("2. defaultdict —— 自动初始化值")
    print("=" * 60)

    # 普通 dict 的痛点：key 不存在时会 KeyError
    # defaultdict：key 不存在时自动创建默认值

    # 按分类分组
    students = [
        ("数学", "张三"), ("语文", "李四"), ("数学", "王五"),
        ("语文", "赵六"), ("英语", "张三"), ("英语", "李四"),
    ]

    # 用 defaultdict(list) 自动初始化为空列表
    groups = defaultdict(list)
    for subject, name in students:
        groups[subject].append(name)  # 不用先检查 key 是否存在
    print(f"  按科目分组: {dict(groups)}")

    # defaultdict(int) 自动初始化为 0
    char_freq = defaultdict(int)
    for c in "hello world":
        char_freq[c] += 1  # 不用先判断 key 是否存在
    print(f"  字符频率: {dict(char_freq)}")

    # defaultdict(set)
    tag_users = defaultdict(set)
    tags = [("python", "Alice"), ("ai", "Bob"), ("python", "Bob"), ("ai", "Alice")]
    for tag, user in tags:
        tag_users[tag].add(user)
    print(f"  标签用户: {dict(tag_users)}")

    # ============================================================
    # 3. namedtuple —— 具名元组
    # ============================================================
    print()
    print("=" * 60)
    print("3. namedtuple —— 给元组的元素起名字")
    print("=" * 60)

    # 普通元组：只能用索引访问，可读性差
    point_tuple = (3, 4)
    # point_tuple[0] 是 x 还是 y？看不出来

    # namedtuple：既有元组的不可变性，又能用名字访问
    Point = namedtuple("Point", ["x", "y"])
    p = Point(3, 4)
    print(f"  点: {p}")
    print(f"  x={p.x}, y={p.y}")  # 用名字访问
    print(f"  x={p[0]}, y={p[1]}")  # 也能用索引
    print(f"  是元组? {isinstance(p, tuple)}")

    # 实际应用：数据库行、CSV 行、API 响应
    User = namedtuple("User", "name age email")
    user = User("Allen", 30, "allen@example.com")
    print(f"  用户: {user.name}, {user.age}岁")

    # _asdict() 转为字典
    print(f"  转字典: {user._asdict()}")

    # ============================================================
    # 4. deque —— 双端队列（高效的头尾操作）
    # ============================================================
    print()
    print("=" * 60)
    print("4. deque —— 双端队列")
    print("=" * 60)

    # list 在头部插入/删除是 O(n)，deque 是 O(1)
    d = deque([1, 2, 3])
    print(f"  初始: {d}")

    d.append(4)        # 右端添加
    d.appendleft(0)    # 左端添加
    print(f"  两端添加后: {d}")

    d.pop()            # 右端弹出
    d.popleft()        # 左端弹出
    print(f"  两端弹出后: {d}")

    # rotate：旋转
    d = deque([1, 2, 3, 4, 5])
    d.rotate(2)   # 右旋2步
    print(f"  右旋2步: {d}")
    d.rotate(-2)  # 左旋2步
    print(f"  左旋2步: {d}")

    # maxlen：固定长度的滑动窗口
    recent = deque(maxlen=3)
    for i in range(5):
        recent.append(i)
        print(f"    添加 {i}: {list(recent)}")
    print(f"  最近3个: {list(recent)}")

    # ============================================================
    # 5. OrderedDict（Python 3.7+ dict 已保序，但仍有场景）
    # ============================================================
    print()
    print("=" * 60)
    print("5. OrderedDict —— 有序字典")
    print("=" * 60)

    # Python 3.7+ 普通 dict 已经保持插入顺序
    # OrderedDict 的额外功能：move_to_end()
    od = OrderedDict([("a", 1), ("b", 2), ("c", 3)])
    print(f"  初始: {od}")
    od.move_to_end("a")  # 移到末尾
    print(f"  'a' 移到末尾: {od}")
    od.move_to_end("c", last=False)  # 移到开头
    print(f"  'c' 移到开头: {od}")

    # 实际应用：LRU 缓存的基础
    print()
    print("=" * 60)
    print("6. 综合实战：日志分析")
    print("=" * 60)

    logs = [
        "2026-04-09 ERROR 数据库连接失败",
        "2026-04-09 INFO 用户登录成功",
        "2026-04-09 ERROR 文件不存在",
        "2026-04-09 WARN 内存使用率高",
        "2026-04-09 ERROR 数据库连接失败",
        "2026-04-09 INFO 用户退出",
        "2026-04-09 ERROR 权限不足",
    ]

    # 统计日志级别
    levels = Counter(log.split()[1] for log in logs)
    print(f"  日志级别统计: {levels}")
    print(f"  最多的级别: {levels.most_common(1)[0]}")

    # 按级别分组
    log_groups = defaultdict(list)
    for log in logs:
        parts = log.split(maxsplit=2)
        log_groups[parts[1]].append(parts[2])
    print(f"  ERROR 日志:")
    for msg in log_groups["ERROR"]:
        print(f"    - {msg}")

    # 统计错误类型
    error_counts = Counter(log_groups["ERROR"])
    print(f"  错误频率: {error_counts}")
