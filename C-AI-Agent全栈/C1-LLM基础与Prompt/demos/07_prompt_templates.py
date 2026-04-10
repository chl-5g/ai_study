#!/usr/bin/env python3
"""
07_prompt_templates.py — 实用 Prompt 模板库

包含多种实战场景的 Prompt 模板，可直接使用或作为参考：
1. 代码审查
2. 文档生成
3. 数据提取（结构化）
4. 翻译与本地化
5. SQL 生成
6. 单元测试生成
7. 文本摘要
8. 需求分析

每个模板包含：模板定义、变量说明、使用示例、调用演示（可选）

依赖：requests（可选，用于调用 Ollama）
运行：python3 07_prompt_templates.py
"""

import json
import requests
import sys
from string import Template

# ============================================================
# 配置
# ============================================================
OLLAMA_URL = "http://localhost:11434"
MODEL = "qwen2.5:7b"


def check_ollama():
    """检查 Ollama 是否可用"""
    try:
        resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        return resp.status_code == 200
    except (requests.ConnectionError, requests.Timeout):
        return False


def call_llm(system_msg, user_msg, temperature=0.7):
    """调用 Ollama，返回 (content, success)"""
    try:
        resp = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg},
                ],
                "stream": False,
                "options": {"temperature": temperature, "num_predict": 800},
            },
            timeout=60,
        )
        if resp.status_code == 200:
            return resp.json().get("message", {}).get("content", ""), True
        return "", False
    except (requests.ConnectionError, requests.Timeout):
        return "", False


# ============================================================
# 模板 1：代码审查
# ============================================================
CODE_REVIEW_TEMPLATE = {
    "name": "代码审查",
    "system": """你是一位资深的 {language} 工程师和代码审查专家。
你在审查代码时关注以下维度：
1. **正确性** — 逻辑是否正确，是否有 Bug
2. **安全性** — 是否有注入、泄漏等安全风险
3. **性能** — 是否有性能瓶颈或优化空间
4. **可读性** — 命名、注释、代码结构
5. **最佳实践** — 是否遵循 {language} 的惯用写法""",
    "user": """请审查以下代码：

```{language}
{code}
```

请按以下格式输出：

## 审查结果

### 问题列表
| 序号 | 严重程度 | 问题描述 | 所在行 | 修复建议 |
|------|---------|---------|--------|---------|
| ... | 高/中/低 | ... | ... | ... |

### 改进后的代码
```{language}
（改进后的完整代码）
```

### 总结
（一句话总结代码质量和关键改进点）""",
    "variables": ["language", "code"],
}


# ============================================================
# 模板 2：文档生成
# ============================================================
DOC_GENERATION_TEMPLATE = {
    "name": "API 文档生成",
    "system": "你是一位技术文档专家，擅长编写清晰、规范的 API 文档。",
    "user": """根据以下代码自动生成 API 文档：

```{language}
{code}
```

请生成以下内容：

## API 文档

### 概述
（功能简述）

### 接口列表
对每个公开接口/函数：

#### `函数名(参数)`
- **描述**：功能说明
- **参数**：
  | 参数名 | 类型 | 必填 | 说明 | 默认值 |
  |--------|------|------|------|--------|
- **返回值**：类型和说明
- **异常**：可能抛出的异常
- **示例**：
  ```{language}
  （调用示例）
  ```""",
    "variables": ["language", "code"],
}


# ============================================================
# 模板 3：数据提取（结构化输出）
# ============================================================
DATA_EXTRACTION_TEMPLATE = {
    "name": "数据提取",
    "system": """你是一个精确的数据提取工具。
从给定文本中提取结构化信息，严格按照指定的 JSON 格式输出。
只输出 JSON，不要添加任何其他文字说明。""",
    "user": """从以下文本中提取信息：

文本：
{text}

请提取以下字段，以 JSON 格式输出：
{schema}

注意：
- 如果某字段信息不存在，填 null
- 数字类型不要加引号
- 日期格式统一为 YYYY-MM-DD""",
    "variables": ["text", "schema"],
}


# ============================================================
# 模板 4：翻译与本地化
# ============================================================
TRANSLATION_TEMPLATE = {
    "name": "翻译与本地化",
    "system": """你是一位专业的 {source_lang}-{target_lang} 翻译专家。

翻译原则：
1. 信达雅 — 准确传达原意，表达流畅，文采得当
2. 技术术语保留原文或使用业界通用译法
3. 根据目标语言的习惯调整语序和表达
4. 代码、变量名、命令不翻译""",
    "user": """请将以下{content_type}翻译成{target_lang}：

{text}

输出格式：
1. 翻译结果
2. 术语表（原文 → 译文，仅列出专业术语）""",
    "variables": ["source_lang", "target_lang", "content_type", "text"],
}


# ============================================================
# 模板 5：SQL 生成
# ============================================================
SQL_GENERATION_TEMPLATE = {
    "name": "SQL 生成",
    "system": """你是一位数据库专家，擅长将自然语言需求转换为 SQL 查询。

数据库方言：{dialect}
请遵循以下规则：
1. 使用标准 SQL 语法
2. 添加注释说明每个部分的作用
3. 考虑性能优化（合适的 JOIN、索引提示）
4. 防止 SQL 注入（使用参数化写法）""",
    "user": """数据库表结构：
{schema}

需求：{requirement}

请生成 SQL 查询，并说明：
1. SQL 语句（带注释）
2. 查询逻辑说明
3. 性能注意事项（如果有）""",
    "variables": ["dialect", "schema", "requirement"],
}


# ============================================================
# 模板 6：单元测试生成
# ============================================================
UNIT_TEST_TEMPLATE = {
    "name": "单元测试生成",
    "system": """你是一位测试工程师，擅长编写全面的单元测试。

测试框架：{test_framework}
测试原则：
1. 覆盖正常路径和边界条件
2. 包含异常/错误情况测试
3. 测试命名清晰（test_功能_条件_期望结果）
4. 每个测试只验证一个行为
5. 使用 AAA 模式（Arrange-Act-Assert）""",
    "user": """请为以下代码生成单元测试：

```{language}
{code}
```

要求：
- 测试覆盖率尽可能高
- 包含边界值测试
- 包含异常情况测试
- 使用 {test_framework} 框架""",
    "variables": ["language", "code", "test_framework"],
}


# ============================================================
# 模板 7：文本摘要
# ============================================================
SUMMARIZE_TEMPLATE = {
    "name": "文本摘要",
    "system": """你是一个文本分析专家。请按要求对文本进行摘要。""",
    "user": """请对以下文本进行摘要：

文本：
{text}

摘要要求：
- 类型：{summary_type}（extractive=提取关键句 / abstractive=重新组织语言）
- 长度：{max_length}
- 要点数量：{num_points} 个
- 语言：{language}

输出格式：
## 摘要
（摘要内容）

## 关键词
（3-5 个关键词）""",
    "variables": ["text", "summary_type", "max_length", "num_points", "language"],
}


# ============================================================
# 模板 8：需求分析
# ============================================================
REQUIREMENT_ANALYSIS_TEMPLATE = {
    "name": "需求分析",
    "system": """你是一位资深产品经理和系统架构师。
请对给定的需求描述进行专业分析。""",
    "user": """需求描述：
{requirement}

请进行以下分析：

## 1. 需求拆解
将需求拆分为可执行的子任务，估算每个任务的复杂度（简单/中等/复杂）

## 2. 技术选型建议
推荐的技术栈和工具，说明理由

## 3. 数据模型
涉及的核心数据实体和关系

## 4. API 设计
主要接口列表（RESTful 风格）

## 5. 风险评估
潜在风险和应对方案

## 6. 工时估算
总体工时估算（人天）""",
    "variables": ["requirement"],
}


# ============================================================
# 所有模板集合
# ============================================================
ALL_TEMPLATES = [
    CODE_REVIEW_TEMPLATE,
    DOC_GENERATION_TEMPLATE,
    DATA_EXTRACTION_TEMPLATE,
    TRANSLATION_TEMPLATE,
    SQL_GENERATION_TEMPLATE,
    UNIT_TEST_TEMPLATE,
    SUMMARIZE_TEMPLATE,
    REQUIREMENT_ANALYSIS_TEMPLATE,
]


def fill_template(template, **kwargs):
    """
    填充模板变量

    返回 (system_message, user_message)
    """
    system = template["system"]
    user = template["user"]

    for key, value in kwargs.items():
        system = system.replace(f"{{{key}}}", str(value))
        user = user.replace(f"{{{key}}}", str(value))

    return system, user


# ============================================================
# 展示所有模板
# ============================================================
def show_all_templates():
    """展示所有模板的概要"""
    print(f"\n{'='*60}")
    print("模板库概览")
    print(f"{'='*60}")

    for i, tmpl in enumerate(ALL_TEMPLATES, 1):
        print(f"\n  {i}. {tmpl['name']}")
        print(f"     变量: {', '.join(tmpl['variables'])}")
        # 显示 system 的第一行
        first_line = tmpl["system"].split("\n")[0]
        print(f"     角色: {first_line[:60]}...")


# ============================================================
# 实战演示
# ============================================================
def demo_code_review(has_ollama):
    """演示代码审查模板"""
    print(f"\n{'='*60}")
    print("演示：代码审查模板")
    print(f"{'='*60}")

    code = """def get_user(user_id):
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    result = cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
    user = result.fetchone()
    return {"id": user[0], "name": user[1], "email": user[2]}"""

    system, user = fill_template(
        CODE_REVIEW_TEMPLATE,
        language="Python",
        code=code
    )

    print(f"\n  输入代码:\n{code}\n")

    if has_ollama:
        print("  调用模型审查中...\n")
        content, ok = call_llm(system, user, temperature=0.3)
        if ok:
            print(content[:800])
        else:
            print("  调用失败")
    else:
        print("  (Ollama 不可用，展示模板填充结果)")
        print(f"\n  System:\n{system[:200]}...")
        print(f"\n  User:\n{user[:300]}...")


def demo_data_extraction(has_ollama):
    """演示数据提取模板"""
    print(f"\n{'='*60}")
    print("演示：数据提取模板")
    print(f"{'='*60}")

    text = "2024年3月15日，苹果公司在加州库比蒂诺发布了 M4 芯片，售价999美元起。CEO Tim Cook 表示新芯片性能提升了50%。"

    schema = """{
    "date": "发布日期(YYYY-MM-DD)",
    "company": "公司名称",
    "location": "发布地点",
    "product": "产品名称",
    "price": 起售价(数字),
    "currency": "货币单位",
    "spokesperson": "发言人",
    "key_metric": "关键性能指标"
}"""

    system, user = fill_template(
        DATA_EXTRACTION_TEMPLATE,
        text=text,
        schema=schema
    )

    print(f"\n  输入文本: {text}")
    print(f"\n  目标 Schema: {schema}")

    if has_ollama:
        print("\n  提取中...\n")
        content, ok = call_llm(system, user, temperature=0)
        if ok:
            print(f"  模型输出:\n{content}")
    else:
        print("\n  (Ollama 不可用)")
        print("  预期输出:")
        expected = {
            "date": "2024-03-15",
            "company": "苹果公司",
            "location": "加州库比蒂诺",
            "product": "M4 芯片",
            "price": 999,
            "currency": "USD",
            "spokesperson": "Tim Cook",
            "key_metric": "性能提升50%"
        }
        print(f"  {json.dumps(expected, ensure_ascii=False, indent=2)}")


def demo_sql_generation(has_ollama):
    """演示 SQL 生成模板"""
    print(f"\n{'='*60}")
    print("演示：SQL 生成模板")
    print(f"{'='*60}")

    schema = """
- users (id, name, email, created_at, department_id)
- departments (id, name, manager_id)
- orders (id, user_id, amount, status, created_at)"""

    requirement = "查询每个部门的订单总金额，按金额降序排列，只显示总金额超过10000的部门"

    system, user = fill_template(
        SQL_GENERATION_TEMPLATE,
        dialect="PostgreSQL",
        schema=schema,
        requirement=requirement
    )

    print(f"\n  表结构: {schema}")
    print(f"\n  需求: {requirement}")

    if has_ollama:
        print("\n  生成中...\n")
        content, ok = call_llm(system, user, temperature=0.2)
        if ok:
            print(content[:600])
    else:
        print("\n  (Ollama 不可用)")
        print("  预期 SQL:")
        print("""  SELECT
      d.name AS department_name,
      SUM(o.amount) AS total_amount
  FROM departments d
  JOIN users u ON u.department_id = d.id
  JOIN orders o ON o.user_id = u.id
  GROUP BY d.id, d.name
  HAVING SUM(o.amount) > 10000
  ORDER BY total_amount DESC;""")


def demo_template_usage():
    """展示如何在代码中使用模板"""
    print(f"\n{'='*60}")
    print("附录：在代码中使用模板的方式")
    print(f"{'='*60}")

    print("""
  方式 1：直接使用 fill_template 函数

    from prompt_templates import CODE_REVIEW_TEMPLATE, fill_template

    system, user = fill_template(
        CODE_REVIEW_TEMPLATE,
        language="Python",
        code="def hello(): print('hi')"
    )
    # 然后调用 LLM API

  方式 2：导入模板字典自行处理

    template = CODE_REVIEW_TEMPLATE
    system = template["system"].format(language="Python")
    user = template["user"].format(language="Python", code="...")

  方式 3：结合 LangChain PromptTemplate

    from langchain_core.prompts import ChatPromptTemplate

    chat_prompt = ChatPromptTemplate.from_messages([
        ("system", CODE_REVIEW_TEMPLATE["system"]),
        ("human", CODE_REVIEW_TEMPLATE["user"]),
    ])
    messages = chat_prompt.format_messages(language="Python", code="...")

  最佳实践：
  - 将模板存储在独立文件或数据库中
  - 版本化管理模板（模板变更可追溯）
  - A/B 测试不同模板的效果
  - 记录每个模板的适用场景和限制
""")


# ============================================================
# 主程序
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("实用 Prompt 模板库")
    print("=" * 60)

    has_ollama = check_ollama()
    if has_ollama:
        print(f"\n  Ollama 可用，将进行实际调用演示")
    else:
        print(f"\n  Ollama 不可用，将展示模板内容和预期输出")

    show_all_templates()
    demo_code_review(has_ollama)
    demo_data_extraction(has_ollama)
    demo_sql_generation(has_ollama)
    demo_template_usage()

    print(f"\n{'='*60}")
    print(f"本文件包含 {len(ALL_TEMPLATES)} 个实用模板，可直接导入使用：")
    print(f"  from prompt_templates_07 import ALL_TEMPLATES, fill_template")
    print("=" * 60)
