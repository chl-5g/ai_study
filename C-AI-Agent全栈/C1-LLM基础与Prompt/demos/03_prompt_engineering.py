#!/usr/bin/env python3
"""
03_prompt_engineering.py — Prompt Engineering 实战

演示内容：
1. 角色设定（Role Prompting）
2. Few-shot 学习
3. Chain-of-Thought (CoT)
4. 结构化输出（JSON）
5. Prompt 反模式 vs 最佳实践对比

每种技巧展示 prompt 模板，有模型可用时实际调用对比效果。

依赖：requests
运行：python3 03_prompt_engineering.py
"""

import json
import requests
import sys

# ============================================================
# 配置
# ============================================================
OLLAMA_URL = "http://localhost:11434"
MODEL = "qwen2.5:7b"


def call_llm(messages, temperature=0.7, max_tokens=500):
    """
    统一的 LLM 调用函数
    返回 (content, success)
    """
    try:
        resp = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": MODEL,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                }
            },
            timeout=60
        )
        if resp.status_code == 200:
            data = resp.json()
            return data.get("message", {}).get("content", ""), True
        return "", False
    except (requests.ConnectionError, requests.Timeout):
        return "", False


def check_model_available():
    """检查模型是否可用"""
    try:
        resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        return resp.status_code == 200
    except (requests.ConnectionError, requests.Timeout):
        return False


# ============================================================
# 技巧 1：角色设定（Role Prompting）
# ============================================================
def demo_role_prompting(has_model):
    print(f"\n{'='*60}")
    print("技巧 1：角色设定（Role Prompting）")
    print(f"{'='*60}")
    print()
    print("原理：给模型一个明确的角色身份，使输出更专业、更有针对性。")
    print("角色设定通常放在 system message 中。\n")

    # 没有角色设定的 prompt
    prompt_without_role = [
        {"role": "user", "content": "审查这段代码：\ndef add(a, b):\n    return a + b"}
    ]

    # 有角色设定的 prompt
    prompt_with_role = [
        {
            "role": "system",
            "content": (
                "你是一位拥有 10 年经验的 Python 高级工程师和代码审查专家。\n"
                "你在审查代码时关注以下方面：\n"
                "1. 类型安全与类型提示\n"
                "2. 文档字符串与注释\n"
                "3. 错误处理\n"
                "4. 性能优化\n"
                "5. 命名规范\n"
                "请以结构化格式输出审查结果。"
            )
        },
        {"role": "user", "content": "审查这段代码：\ndef add(a, b):\n    return a + b"}
    ]

    print("--- 无角色设定 ---")
    print(f"Prompt: {prompt_without_role[0]['content']}")
    if has_model:
        content, _ = call_llm(prompt_without_role)
        print(f"回答: {content[:300]}...")
    else:
        print("(模型不可用，跳过调用)")

    print("\n--- 有角色设定 ---")
    print(f"System: {prompt_with_role[0]['content'][:100]}...")
    print(f"User: {prompt_with_role[1]['content']}")
    if has_model:
        content, _ = call_llm(prompt_with_role)
        print(f"回答: {content[:500]}...")
    else:
        print("(模型不可用，跳过调用)")

    print("\n关键差异：有角色设定后，模型会从专家视角给出更结构化、更专业的审查意见。")


# ============================================================
# 技巧 2：Few-shot 学习
# ============================================================
def demo_few_shot(has_model):
    print(f"\n{'='*60}")
    print("技巧 2：Few-shot 学习")
    print(f"{'='*60}")
    print()
    print("原理：通过提供示例，让模型理解期望的输入/输出格式和任务要求。\n")

    # Zero-shot：不给例子
    zero_shot_prompt = """将以下产品评论分类为"正面"、"负面"或"中性"：

评论：这个耳机音质还行，但是佩戴不太舒服"""

    # Few-shot：给几个例子
    few_shot_prompt = """将以下产品评论分类为"正面"、"负面"或"中性"。

示例：
评论：这款手机拍照效果非常好，电池续航也很给力！ → 正面
评论：快递太慢了，而且包装破损严重 → 负面
评论：产品一般般，没有特别好也没有特别差 → 中性
评论：质量不错但价格偏高 → 中性

现在分类：
评论：这个耳机音质还行，但是佩戴不太舒服 →"""

    print("--- Zero-shot（无示例） ---")
    print(f"Prompt:\n{zero_shot_prompt}\n")
    if has_model:
        content, _ = call_llm([{"role": "user", "content": zero_shot_prompt}], temperature=0)
        print(f"回答: {content[:200]}")
    else:
        print("(模型不可用，跳过调用)")

    print("\n--- Few-shot（有示例） ---")
    print(f"Prompt:\n{few_shot_prompt}\n")
    if has_model:
        content, _ = call_llm([{"role": "user", "content": few_shot_prompt}], temperature=0)
        print(f"回答: {content[:200]}")
    else:
        print("(模型不可用，跳过调用)")

    print("\n关键差异：Few-shot 示例让模型输出格式统一，分类更准确。")


# ============================================================
# 技巧 3：Chain-of-Thought (CoT)
# ============================================================
def demo_cot(has_model):
    print(f"\n{'='*60}")
    print("技巧 3：Chain-of-Thought (CoT)")
    print(f"{'='*60}")
    print()
    print("原理：引导模型逐步推理，而非直接给答案，显著提升推理类任务准确率。\n")

    question = "一个书架有 3 层，第一层有 12 本书，第二层比第一层多 5 本，第三层是第二层的 2 倍。书架总共有多少本书？"

    # 直接回答
    direct_prompt = f"回答以下问题：\n{question}"

    # CoT 提示
    cot_prompt = f"""回答以下问题，请逐步推理：

{question}

让我们一步一步来思考："""

    # Zero-shot CoT（最简单的 CoT 技巧）
    zero_shot_cot = f"""{question}

Let's think step by step."""

    print("--- 直接回答 ---")
    print(f"Prompt: {direct_prompt}\n")
    if has_model:
        content, _ = call_llm([{"role": "user", "content": direct_prompt}], temperature=0)
        print(f"回答: {content[:300]}")
    else:
        print("(跳过)")

    print("\n--- Chain-of-Thought ---")
    print(f"Prompt: {cot_prompt}\n")
    if has_model:
        content, _ = call_llm([{"role": "user", "content": cot_prompt}], temperature=0)
        print(f"回答: {content[:500]}")
    else:
        print("(跳过)")

    print("\n--- Zero-shot CoT（加一句 'Let's think step by step'） ---")
    print(f"Prompt: {zero_shot_cot}\n")
    if has_model:
        content, _ = call_llm([{"role": "user", "content": zero_shot_cot}], temperature=0)
        print(f"回答: {content[:500]}")
    else:
        print("(跳过)")

    print("\n正确答案：12 + 17 + 34 = 63 本")
    print("CoT 通过显式推理过程，减少了计算跳步带来的错误。")


# ============================================================
# 技巧 4：结构化输出（JSON）
# ============================================================
def demo_structured_output(has_model):
    print(f"\n{'='*60}")
    print("技巧 4：结构化输出（JSON）")
    print(f"{'='*60}")
    print()
    print("原理：明确要求模型输出 JSON 等结构化格式，方便程序解析。\n")

    prompt = """从以下文本中提取信息，以 JSON 格式输出。

文本：
"张三，男，28岁，就职于杭州某互联网公司，担任高级工程师，月薪3万元。"

请输出以下 JSON 格式（不要输出其他内容）：
{
    "name": "姓名",
    "gender": "性别",
    "age": 年龄(数字),
    "city": "城市",
    "company_type": "公司类型",
    "position": "职位",
    "salary": 月薪(数字，单位元)
}"""

    print(f"Prompt:\n{prompt}\n")

    if has_model:
        content, _ = call_llm(
            [{"role": "user", "content": prompt}],
            temperature=0  # 结构化输出建议温度为 0
        )
        print(f"模型输出:\n{content}\n")

        # 尝试解析 JSON
        try:
            # 提取 JSON 部分（模型可能会加 markdown 标记）
            json_str = content
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]
            result = json.loads(json_str.strip())
            print(f"解析成功: {json.dumps(result, ensure_ascii=False, indent=2)}")
        except (json.JSONDecodeError, IndexError) as e:
            print(f"JSON 解析失败: {e}")
            print("提示：可以通过更明确的格式要求和 Few-shot 示例来提高 JSON 输出的可靠性")
    else:
        print("(模型不可用)")
        print("预期输出示例：")
        expected = {
            "name": "张三",
            "gender": "男",
            "age": 28,
            "city": "杭州",
            "company_type": "互联网",
            "position": "高级工程师",
            "salary": 30000
        }
        print(json.dumps(expected, ensure_ascii=False, indent=2))


# ============================================================
# 技巧 5：Prompt 反模式 vs 最佳实践
# ============================================================
def demo_antipatterns():
    print(f"\n{'='*60}")
    print("技巧 5：Prompt 反模式 vs 最佳实践对比")
    print(f"{'='*60}")

    comparisons = [
        {
            "name": "指令模糊 → 具体明确",
            "bad": "帮我写个接口",
            "good": (
                "用 Python FastAPI 写一个用户注册接口，\n"
                "接收 JSON Body（username, email, password），\n"
                "返回 201 状态码和用户 ID，\n"
                "包含输入验证和错误处理。"
            ),
        },
        {
            "name": "否定指令 → 正向指令",
            "bad": "不要用循环，不要用全局变量，不要写太长",
            "good": (
                "请使用列表推导式替代显式循环，\n"
                "所有变量定义在函数作用域内，\n"
                "每个函数不超过 20 行。"
            ),
        },
        {
            "name": "格式缺失 → 明确格式",
            "bad": "分析一下这段代码的问题",
            "good": (
                "分析以下代码的问题，按如下格式输出：\n"
                "## 问题列表\n"
                "1. **问题描述** — 严重程度(高/中/低) — 修复建议\n"
                "## 改进后的代码\n"
                "```python\n...\n```"
            ),
        },
        {
            "name": "多任务混合 → 单任务分拆",
            "bad": "帮我写代码，顺便写测试，再写文档，最后部署到服务器上",
            "good": (
                "任务 1（本次）：实现 UserService 类，包含 CRUD 方法\n"
                "（测试、文档、部署将分别在后续请求中处理）"
            ),
        },
        {
            "name": "缺乏约束 → 设定边界",
            "bad": "介绍一下机器学习",
            "good": (
                "用 3 个要点介绍机器学习的核心概念，\n"
                "每个要点不超过 50 字，\n"
                "面向零基础读者，避免数学公式。"
            ),
        },
    ]

    for comp in comparisons:
        print(f"\n  [{comp['name']}]")
        print(f"  反模式: {comp['bad']}")
        print(f"  最佳:   {comp['good']}")


# ============================================================
# Prompt 模板汇总
# ============================================================
def demo_prompt_templates():
    print(f"\n{'='*60}")
    print("附录：常用 Prompt 模式速查")
    print(f"{'='*60}")

    templates = {
        "角色设定": 'system: "你是{角色}，擅长{技能}..."',
        "Few-shot": '提供 2-5 个 输入→输出 示例',
        "CoT": '加入 "让我们一步一步思考" 或分步指引',
        "结构化输出": '明确指定 JSON/Markdown 格式 + 字段说明',
        "约束设定": '字数限制 / 语言 / 风格 / 格式要求',
        "ReAct": 'Thought→Action→Observation 循环',
        "ToT": '生成多条推理路径→评估→选择最优',
        "Self-Consistency": '多次采样(高温度)→多数投票',
    }

    for name, desc in templates.items():
        print(f"  {name:20s} → {desc}")


# ============================================================
# 主程序
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("Prompt Engineering 实战演示")
    print("=" * 60)

    has_model = check_model_available()
    if has_model:
        print(f"\n  Ollama 可用，将使用 {MODEL} 进行实际调用")
    else:
        print(f"\n  Ollama 不可用，将展示 Prompt 模板（跳过实际调用）")
        print("  启动 Ollama 后重新运行可看到实际效果")

    demo_role_prompting(has_model)
    demo_few_shot(has_model)
    demo_cot(has_model)
    demo_structured_output(has_model)
    demo_antipatterns()
    demo_prompt_templates()

    print(f"\n{'='*60}")
    print("演示完成！")
    print("=" * 60)
