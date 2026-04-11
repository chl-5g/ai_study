#!/usr/bin/env python3
"""
标准库：datetime 和 json
datetime —— 日期时间处理
json —— JSON 数据的序列化与反序列化
"""

import json
from datetime import datetime, date, timedelta, timezone


if __name__ == "__main__":
    # ============================================================
    # datetime 模块
    # ============================================================
    print("=" * 60)
    print("1. datetime —— 获取当前时间")
    print("=" * 60)

    now = datetime.now()
    print(f"  当前时间: {now}")
    print(f"  年: {now.year}, 月: {now.month}, 日: {now.day}")
    print(f"  时: {now.hour}, 分: {now.minute}, 秒: {now.second}")
    print(f"  星期: {now.weekday()} (0=周一)")
    print(f"  今天的日期: {date.today()}")

    # UTC 时间
    utc_now = datetime.now(timezone.utc)
    print(f"  UTC 时间: {utc_now}")

    print()
    print("=" * 60)
    print("2. datetime —— 创建和格式化")
    print("=" * 60)

    # 创建指定日期
    birthday = datetime(1995, 4, 29, 8, 30)
    print(f"  生日: {birthday}")

    # strftime: datetime → 字符串
    formatted = now.strftime("%Y年%m月%d日 %H:%M:%S")
    print(f"  格式化: {formatted}")

    # 常用格式：
    print(f"  ISO格式: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  日期: {now.strftime('%Y-%m-%d')}")
    print(f"  时间: {now.strftime('%H:%M:%S')}")
    print(f"  中文: {now.strftime('%Y年%m月%d日')}")

    # strptime: 字符串 → datetime
    parsed = datetime.strptime("2026-04-09 15:30:00", "%Y-%m-%d %H:%M:%S")
    print(f"  解析字符串: {parsed}")

    print()
    print("=" * 60)
    print("3. datetime —— 时间运算 (timedelta)")
    print("=" * 60)

    # timedelta 表示时间差
    one_week = timedelta(weeks=1)
    three_days = timedelta(days=3, hours=5)

    future = now + one_week
    past = now - three_days

    print(f"  现在: {now.strftime('%Y-%m-%d %H:%M')}")
    print(f"  一周后: {future.strftime('%Y-%m-%d %H:%M')}")
    print(f"  三天前: {past.strftime('%Y-%m-%d %H:%M')}")

    # 两个时间的差
    diff = datetime(2026, 12, 31) - now
    print(f"  距离年底还有: {diff.days} 天")

    # 年龄计算
    age = (now - birthday).days // 365
    print(f"  年龄: {age} 岁")

    print()
    print("=" * 60)
    print("4. datetime —— 时间戳")
    print("=" * 60)

    # datetime ↔ 时间戳（Unix timestamp）
    timestamp = now.timestamp()
    print(f"  当前时间戳: {timestamp}")

    # 时间戳 → datetime
    from_ts = datetime.fromtimestamp(timestamp)
    print(f"  从时间戳恢复: {from_ts}")

    # ISO 格式（API 交互最常用）
    iso_str = now.isoformat()
    print(f"  ISO 格式: {iso_str}")
    from_iso = datetime.fromisoformat(iso_str)
    print(f"  从 ISO 恢复: {from_iso}")

    # ============================================================
    # json 模块
    # ============================================================
    print()
    print("=" * 60)
    print("5. json —— Python 对象 ↔ JSON 字符串")
    print("=" * 60)

    # Python dict → JSON 字符串 (序列化)
    data = {
        "name": "张三",
        "age": 30,
        "skills": ["Python", "Rust", "AI"],
        "is_active": True,
        "address": None,  # Python 的 None → JSON 的 null
    }

    # json.dumps: dict → str
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    print(f"  序列化:\n{json_str}")

    # json.loads: str → dict (反序列化)
    parsed_data = json.loads(json_str)
    print(f"\n  反序列化: {parsed_data}")
    print(f"  名字: {parsed_data['name']}")

    print()
    print("=" * 60)
    print("6. json —— 文件读写")
    print("=" * 60)

    filepath = "/tmp/demo_data.json"

    # 写入 JSON 文件
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  已写入: {filepath}")

    # 读取 JSON 文件
    with open(filepath, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    print(f"  已读取: {loaded}")

    import os
    os.remove(filepath)

    print()
    print("=" * 60)
    print("7. json —— 自定义序列化")
    print("=" * 60)

    # datetime 默认不能序列化，需要自定义
    complex_data = {
        "name": "Allen",
        "created_at": datetime.now(),
        "scores": [85, 92, 78],
    }

    # 方法1: default 参数
    def json_serializer(obj):
        """自定义序列化函数"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"无法序列化: {type(obj)}")

    json_str = json.dumps(complex_data, default=json_serializer, ensure_ascii=False, indent=2)
    print(f"  带 datetime 的 JSON:\n{json_str}")

    # 方法2: 自定义 Encoder
    class CustomEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            if isinstance(obj, set):
                return list(obj)
            return super().default(obj)

    data_with_set = {"tags": {"python", "ai", "ml"}, "time": datetime.now()}
    json_str = json.dumps(data_with_set, cls=CustomEncoder, ensure_ascii=False)
    print(f"\n  自定义 Encoder: {json_str}")
