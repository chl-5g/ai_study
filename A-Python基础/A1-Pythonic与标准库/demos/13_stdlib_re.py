#!/usr/bin/env python3
"""
标准库：re 模块（正则表达式）
文本匹配、搜索、替换的强大工具
"""

import re


if __name__ == "__main__":
    # ============================================================
    # 1. 基础匹配
    # ============================================================
    print("=" * 60)
    print("1. 基础匹配方法")
    print("=" * 60)

    text = "我的手机号是 15094315696，邮箱是 allen@example.com"

    # re.search: 在字符串中搜索第一个匹配
    match = re.search(r"\d{11}", text)
    if match:
        print(f"  search 找到手机号: {match.group()}")
        print(f"    位置: {match.start()}-{match.end()}")

    # re.match: 只匹配字符串开头
    match = re.match(r"我的", text)
    print(f"  match 开头匹配: {match.group() if match else '未匹配'}")

    # re.findall: 找到所有匹配（返回列表）
    numbers = re.findall(r"\d+", text)
    print(f"  findall 所有数字: {numbers}")

    # re.finditer: 找到所有匹配（返回迭代器，包含位置信息）
    print(f"  finditer 详细匹配:")
    for m in re.finditer(r"\d+", text):
        print(f"    '{m.group()}' 在位置 {m.start()}-{m.end()}")

    # ============================================================
    # 2. 常用正则语法
    # ============================================================
    print()
    print("=" * 60)
    print("2. 常用正则语法速查")
    print("=" * 60)

    patterns = {
        r"\d":   ("数字", "abc123def", "匹配所有数字"),
        r"\w":   ("字母/数字/下划线", "hello_world!", "匹配单词字符"),
        r"\s":   ("空白字符", "a b\tc", "匹配空格和Tab"),
        r"[aeiou]": ("元音字母", "hello world", "匹配集合中的任意一个"),
        r"\b\w+\b": ("完整单词", "hello world python", "单词边界"),
    }

    for pattern, (desc, test_str, explanation) in patterns.items():
        matches = re.findall(pattern, test_str)
        print(f"  {pattern:15s} ({desc}): '{test_str}' → {matches}")

    # 量词
    print("\n  量词演示:")
    test = "aaa ab a aabb"
    for pattern in [r"a+", r"a*b", r"a{2}", r"a{1,3}"]:
        result = re.findall(pattern, test)
        print(f"    {pattern:10s} → {result}")

    # ============================================================
    # 3. 分组与捕获
    # ============================================================
    print()
    print("=" * 60)
    print("3. 分组与捕获 ()")
    print("=" * 60)

    # 用 () 创建捕获组
    date_text = "今天是 2026-04-09，明天是 2026-04-10"
    pattern = r"(\d{4})-(\d{2})-(\d{2})"

    for match in re.finditer(pattern, date_text):
        print(f"  完整匹配: {match.group(0)}")
        print(f"    年: {match.group(1)}, 月: {match.group(2)}, 日: {match.group(3)}")

    # 命名分组 (?P<name>...)
    pattern = r"(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})"
    match = re.search(pattern, date_text)
    if match:
        print(f"  命名分组: {match.groupdict()}")

    # findall 有分组时返回分组内容
    dates = re.findall(pattern, date_text)
    print(f"  findall 带分组: {dates}")

    # ============================================================
    # 4. 替换
    # ============================================================
    print()
    print("=" * 60)
    print("4. 替换 re.sub()")
    print("=" * 60)

    # 基础替换
    text = "我的电话是 15094315696，另一个是 13800138000"
    masked = re.sub(r"(\d{3})\d{4}(\d{4})", r"\1****\2", text)
    print(f"  手机号脱敏: {masked}")

    # 函数替换（更灵活）
    def double_number(match):
        """把匹配到的数字翻倍"""
        num = int(match.group())
        return str(num * 2)

    text = "价格: 100元 和 250元"
    doubled = re.sub(r"\d+", double_number, text)
    print(f"  数字翻倍: {doubled}")

    # 清除多余空白
    messy = "  hello   world   python  "
    clean = re.sub(r"\s+", " ", messy).strip()
    print(f"  清除空白: '{messy}' → '{clean}'")

    # ============================================================
    # 5. 编译正则（提升性能）
    # ============================================================
    print()
    print("=" * 60)
    print("5. 编译正则 re.compile()")
    print("=" * 60)

    # 如果一个正则要用很多次，先编译可以提升性能
    email_pattern = re.compile(
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        re.IGNORECASE  # 忽略大小写
    )

    texts = [
        "联系我: Allen@Example.COM",
        "无邮箱的文本",
        "两个邮箱: a@b.com 和 c@d.org",
    ]

    for t in texts:
        emails = email_pattern.findall(t)
        print(f"  '{t[:30]}...' → {emails}")

    # ============================================================
    # 6. 实战：日志解析
    # ============================================================
    print()
    print("=" * 60)
    print("6. 实战：解析日志")
    print("=" * 60)

    logs = [
        "2026-04-09 14:23:01 [ERROR] 数据库连接超时 (host=192.168.0.15, port=5432)",
        "2026-04-09 14:23:05 [INFO] 重试连接成功",
        "2026-04-09 14:23:10 [WARN] 响应时间过长: 3500ms",
    ]

    log_pattern = re.compile(
        r"(?P<date>\d{4}-\d{2}-\d{2}) "
        r"(?P<time>\d{2}:\d{2}:\d{2}) "
        r"\[(?P<level>\w+)\] "
        r"(?P<message>.*)"
    )

    print("  解析结果:")
    for log in logs:
        match = log_pattern.match(log)
        if match:
            d = match.groupdict()
            print(f"    [{d['level']:5s}] {d['time']} - {d['message']}")

    # 提取 IP 和端口
    ip_port = re.findall(r"(\d+\.\d+\.\d+\.\d+).*?port=(\d+)", logs[0])
    print(f"\n  提取的IP和端口: {ip_port}")

    # 提取毫秒数
    ms = re.search(r"(\d+)ms", logs[2])
    if ms:
        print(f"  响应时间: {ms.group(1)}ms")
