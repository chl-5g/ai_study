#!/usr/bin/env python3
"""
06_token_counter.py — Token 计算与成本估算工具

演示内容：
1. 使用 tiktoken 计算 Token 数量
2. 不同编码器（cl100k_base / o200k_base）对比
3. 中英文 Token 消耗差异
4. API 调用成本估算
5. 实用的 Token 统计工具函数

安装依赖：pip3 install tiktoken

运行：python3 06_token_counter.py
"""

import sys

# ============================================================
# 检查 tiktoken 是否安装
# ============================================================
try:
    import tiktoken
    TIKTOKEN_OK = True
except ImportError:
    TIKTOKEN_OK = False
    print("tiktoken 未安装。安装命令：pip3 install tiktoken")
    print("将使用估算方法代替精确计算\n")


# ============================================================
# 模型定价表（2025 年参考，单位：$/1M tokens）
# ============================================================
PRICING = {
    "gpt-4o": {"input": 2.50, "output": 10.00, "encoding": "o200k_base"},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60, "encoding": "o200k_base"},
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50, "encoding": "cl100k_base"},
    "claude-sonnet-4": {"input": 3.00, "output": 15.00, "encoding": "cl100k_base"},
    "claude-haiku-3.5": {"input": 0.80, "output": 4.00, "encoding": "cl100k_base"},
    "deepseek-v3": {"input": 0.27, "output": 1.10, "encoding": "cl100k_base"},
}


def count_tokens(text, encoding_name="cl100k_base"):
    """
    计算文本的 Token 数量

    参数：
        text: 输入文本
        encoding_name: 编码器名称
            - cl100k_base: GPT-3.5/4、Claude（近似）
            - o200k_base: GPT-4o 系列

    返回：Token 数量
    """
    if TIKTOKEN_OK:
        enc = tiktoken.get_encoding(encoding_name)
        tokens = enc.encode(text)
        return len(tokens)
    else:
        # 粗略估算：英文约 4 字符/token，中文约 2 字符/token
        cn_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        en_chars = len(text) - cn_chars
        return int(cn_chars / 1.5 + en_chars / 4)


def show_tokens(text, encoding_name="cl100k_base"):
    """
    展示文本的 Token 分词细节

    这个函数帮助理解 Tokenizer 如何切分文本
    """
    if not TIKTOKEN_OK:
        print("  (需要 tiktoken 库查看分词细节)")
        return

    enc = tiktoken.get_encoding(encoding_name)
    token_ids = enc.encode(text)
    # 解码每个 Token，查看对应的文本片段
    token_texts = [enc.decode([tid]) for tid in token_ids]

    print(f"  文本: {repr(text)}")
    print(f"  编码器: {encoding_name}")
    print(f"  Token 数: {len(token_ids)}")
    print(f"  Token IDs: {token_ids[:20]}{'...' if len(token_ids) > 20 else ''}")
    print(f"  Token 分词: {token_texts[:20]}{'...' if len(token_texts) > 20 else ''}")


def estimate_cost(input_tokens, output_tokens, model="gpt-4o"):
    """
    估算 API 调用成本

    参数：
        input_tokens: 输入 Token 数
        output_tokens: 输出 Token 数
        model: 模型名称

    返回：(成本美元, 成本人民币)
    """
    pricing = PRICING.get(model, PRICING["gpt-4o"])
    cost_usd = (
        (input_tokens / 1_000_000) * pricing["input"]
        + (output_tokens / 1_000_000) * pricing["output"]
    )
    cost_cny = cost_usd * 7.2  # 汇率估算
    return cost_usd, cost_cny


# ============================================================
# 演示 1：基本 Token 计数
# ============================================================
def demo_basic_counting():
    print(f"\n{'='*60}")
    print("演示 1：基本 Token 计数")
    print(f"{'='*60}")

    examples = [
        ("Hello, World!", "简单英文"),
        ("你好，世界！", "简单中文"),
        ("Artificial Intelligence is transforming the world.", "英文长句"),
        ("人工智能正在深刻地改变着我们的世界。", "中文长句"),
        ("def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)", "Python 代码"),
        ("SELECT * FROM users WHERE age > 18 ORDER BY name;", "SQL 代码"),
    ]

    encoding_name = "cl100k_base"
    print(f"\n  编码器: {encoding_name}")
    print(f"  {'文本':<50s} {'类型':<12s} {'Token数':>8s} {'字符数':>8s}")
    print(f"  {'-'*80}")

    for text, desc in examples:
        token_count = count_tokens(text, encoding_name)
        display_text = text[:45] + "..." if len(text) > 45 else text
        print(f"  {display_text:<50s} {desc:<12s} {token_count:>8d} {len(text):>8d}")


# ============================================================
# 演示 2：Token 分词可视化
# ============================================================
def demo_tokenization():
    print(f"\n{'='*60}")
    print("演示 2：Token 分词可视化")
    print(f"{'='*60}")

    texts = [
        "Hello World",
        "你好世界",
        "unbelievable",
        "人工智能",
        "def hello():\n    print('Hello')",
    ]

    for text in texts:
        print()
        show_tokens(text)


# ============================================================
# 演示 3：中英文 Token 消耗对比
# ============================================================
def demo_cn_en_comparison():
    print(f"\n{'='*60}")
    print("演示 3：中英文 Token 消耗对比")
    print(f"{'='*60}")

    # 相同语义的中英文文本
    pairs = [
        ("Hello", "你好"),
        ("Artificial Intelligence", "人工智能"),
        ("Machine learning is a subset of artificial intelligence.",
         "机器学习是人工智能的一个子集。"),
        ("Python is a popular programming language known for its simplicity.",
         "Python 是一种以简洁著称的流行编程语言。"),
    ]

    print(f"\n  {'英文':<55s} {'en_tokens':>10s} | {'中文':<30s} {'cn_tokens':>10s} {'比率':>8s}")
    print(f"  {'-'*120}")

    for en, cn in pairs:
        en_tokens = count_tokens(en)
        cn_tokens = count_tokens(cn)
        ratio = cn_tokens / en_tokens if en_tokens > 0 else 0
        en_display = en[:50] + "..." if len(en) > 50 else en
        cn_display = cn[:25] + "..." if len(cn) > 25 else cn
        print(f"  {en_display:<55s} {en_tokens:>10d} | {cn_display:<30s} {cn_tokens:>10d} {ratio:>7.1f}x")

    print(f"\n  结论：相同语义下，中文通常比英文消耗更多 Token（约 1.2-1.8 倍）")
    print(f"  原因：大部分 Tokenizer 以英文语料为主训练，中文字符编码效率较低")


# ============================================================
# 演示 4：成本估算
# ============================================================
def demo_cost_estimation():
    print(f"\n{'='*60}")
    print("演示 4：API 成本估算")
    print(f"{'='*60}")

    # 模拟不同场景
    scenarios = [
        {
            "name": "简单问答（一轮）",
            "input_text": "请用一句话解释什么是 RESTful API",
            "output_tokens": 50,
        },
        {
            "name": "代码生成（中等）",
            "input_text": "请用 Python 实现一个带分页的 REST API，使用 FastAPI 框架，包含 CRUD 操作、输入验证、错误处理。数据模型为用户（User），字段包括 id, name, email, age。",
            "output_tokens": 500,
        },
        {
            "name": "长文档分析",
            "input_text": "x" * 10000,  # 模拟长文档输入
            "output_tokens": 2000,
        },
    ]

    for scenario in scenarios:
        input_tokens = count_tokens(scenario["input_text"])
        output_tokens = scenario["output_tokens"]

        print(f"\n  场景: {scenario['name']}")
        print(f"  输入 Token: {input_tokens}, 输出 Token: {output_tokens}")
        print(f"  {'模型':<20s} {'输入单价':>12s} {'输出单价':>12s} {'总成本(USD)':>14s} {'总成本(CNY)':>14s}")
        print(f"  {'-'*75}")

        for model_name, pricing in PRICING.items():
            cost_usd, cost_cny = estimate_cost(input_tokens, output_tokens, model_name)
            print(f"  {model_name:<20s} "
                  f"${pricing['input']:>9.2f}/M "
                  f"${pricing['output']:>9.2f}/M "
                  f"${cost_usd:>12.6f} "
                  f"¥{cost_cny:>12.6f}")


# ============================================================
# 演示 5：批量估算工具
# ============================================================
def demo_batch_estimation():
    print(f"\n{'='*60}")
    print("演示 5：月度成本估算工具")
    print(f"{'='*60}")

    print(f"\n  假设场景：客服机器人，每天 1000 次对话")
    print(f"  每次对话：平均输入 200 tokens，输出 300 tokens\n")

    daily_calls = 1000
    avg_input = 200
    avg_output = 300
    days_per_month = 30

    monthly_input = daily_calls * avg_input * days_per_month
    monthly_output = daily_calls * avg_output * days_per_month

    print(f"  月度 Token 用量:")
    print(f"    输入: {monthly_input:>12,} tokens ({monthly_input/1_000_000:.1f}M)")
    print(f"    输出: {monthly_output:>12,} tokens ({monthly_output/1_000_000:.1f}M)")
    print()

    print(f"  {'模型':<20s} {'月成本(USD)':>14s} {'月成本(CNY)':>14s}")
    print(f"  {'-'*50}")

    for model_name in PRICING:
        cost_usd, cost_cny = estimate_cost(monthly_input, monthly_output, model_name)
        print(f"  {model_name:<20s} ${cost_usd:>12.2f} ¥{cost_cny:>12.2f}")

    print(f"\n  本地部署（Ollama）：硬件成本固定，边际调用成本为零")
    print(f"  当月度 API 成本 > $100 时，可考虑本地部署是否更经济")


# ============================================================
# 实用工具函数
# ============================================================
def token_budget_check(text, max_tokens=4096, encoding="cl100k_base"):
    """
    检查文本是否超出 Token 预算

    在实际应用中，需要确保输入不超过模型的上下文限制。
    """
    tokens = count_tokens(text, encoding)
    within_budget = tokens <= max_tokens
    return {
        "token_count": tokens,
        "max_tokens": max_tokens,
        "within_budget": within_budget,
        "remaining": max_tokens - tokens,
        "utilization": f"{tokens/max_tokens*100:.1f}%"
    }


def demo_budget_check():
    print(f"\n{'='*60}")
    print("附录：Token 预算检查工具")
    print(f"{'='*60}")

    texts = [
        ("短文本", "Hello World", 4096),
        ("中等文本", "Python 是一种高级编程语言 " * 100, 4096),
        ("超长文本", "这是一段很长的文本 " * 2000, 4096),
    ]

    for name, text, budget in texts:
        result = token_budget_check(text, budget)
        status = "OK" if result["within_budget"] else "OVER"
        print(f"\n  [{name}] {status}")
        print(f"    Token 数: {result['token_count']}, "
              f"预算: {result['max_tokens']}, "
              f"剩余: {result['remaining']}, "
              f"使用率: {result['utilization']}")


# ============================================================
# 主程序
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("Token 计算与成本估算工具")
    print("=" * 60)
    print(f"\n  tiktoken: {'已安装' if TIKTOKEN_OK else '未安装（使用估算方法）'}")

    demo_basic_counting()
    demo_tokenization()
    demo_cn_en_comparison()
    demo_cost_estimation()
    demo_batch_estimation()
    demo_budget_check()

    print(f"\n{'='*60}")
    print("演示完成！")
    print("=" * 60)
