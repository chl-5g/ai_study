#!/usr/bin/env python3
"""
05_langchain_basics.py — LangChain 入门

演示内容：
1. PromptTemplate — 提示词模板
2. ChatPromptTemplate — 对话模板
3. OutputParser — 输出解析
4. LCEL Chain — 管道式组合
5. Memory — 对话记忆（概念展示）

安装依赖：
  pip3 install langchain langchain-community langchain-core

运行：python3 05_langchain_basics.py
"""

import sys
import json

# ============================================================
# 检查依赖
# ============================================================
try:
    import langchain
    from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
    from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
    LANGCHAIN_OK = True
    print(f"LangChain 版本: {langchain.__version__}")
except ImportError:
    LANGCHAIN_OK = False
    print("LangChain 未安装。安装命令：")
    print("  pip3 install langchain langchain-community langchain-core")
    print("\n以下将展示代码结构和概念（不实际执行）\n")

# 检查 Ollama 是否可用（用于实际调用）
OLLAMA_OK = False
if LANGCHAIN_OK:
    try:
        from langchain_community.llms import Ollama
        from langchain_community.chat_models import ChatOllama
        import requests
        resp = requests.get("http://localhost:11434/api/tags", timeout=3)
        OLLAMA_OK = resp.status_code == 200
    except Exception:
        pass

MODEL = "qwen2.5:7b"


# ============================================================
# 演示 1：PromptTemplate（提示词模板）
# ============================================================
def demo_prompt_template():
    print(f"\n{'='*60}")
    print("演示 1：PromptTemplate（提示词模板）")
    print(f"{'='*60}")

    if not LANGCHAIN_OK:
        print("""
  概念：PromptTemplate 是带变量的字符串模板，类似 Python 的 f-string。

  代码示例：
  ```python
  from langchain_core.prompts import PromptTemplate

  # 方式 1：from_template（自动检测变量）
  prompt = PromptTemplate.from_template(
      "请将以下文本翻译成{language}：\\n{text}"
  )
  result = prompt.format(language="英文", text="你好世界")
  # 输出: "请将以下文本翻译成英文：\\n你好世界"

  # 方式 2：显式指定变量
  prompt = PromptTemplate(
      input_variables=["topic", "level"],
      template="用{level}的方式解释{topic}"
  )
  ```

  核心价值：将 prompt 的「结构」和「数据」分离，便于复用和管理。
""")
        return

    # 实际创建和使用 PromptTemplate
    # 方式 1：from_template
    prompt = PromptTemplate.from_template(
        "请将以下文本翻译成{language}：\n{text}"
    )

    # 查看模板信息
    print(f"\n  模板: {prompt.template}")
    print(f"  变量: {prompt.input_variables}")

    # 填充变量
    result = prompt.format(language="英文", text="人工智能正在改变世界")
    print(f"\n  填充后:\n  {result}")

    # 方式 2：更复杂的模板
    code_review_prompt = PromptTemplate.from_template(
        "你是一位{language}专家。\n"
        "请审查以下代码，关注{focus}：\n"
        "```\n{code}\n```\n"
        "输出格式：问题列表 + 改进建议"
    )

    print(f"\n  代码审查模板变量: {code_review_prompt.input_variables}")
    filled = code_review_prompt.format(
        language="Python",
        focus="类型安全和错误处理",
        code="def divide(a, b):\n    return a / b"
    )
    print(f"  填充后:\n{filled}")


# ============================================================
# 演示 2：ChatPromptTemplate（对话模板）
# ============================================================
def demo_chat_prompt_template():
    print(f"\n{'='*60}")
    print("演示 2：ChatPromptTemplate（对话模板）")
    print(f"{'='*60}")

    if not LANGCHAIN_OK:
        print("""
  概念：ChatPromptTemplate 用于构建多角色对话消息。

  代码示例：
  ```python
  from langchain_core.prompts import ChatPromptTemplate

  # 定义对话模板
  chat_prompt = ChatPromptTemplate.from_messages([
      ("system", "你是一位{role}，擅长{skill}"),
      ("human", "{question}")
  ])

  # 填充变量
  messages = chat_prompt.format_messages(
      role="Python 教师",
      skill="深入浅出地讲解概念",
      question="什么是装饰器？"
  )
  # messages = [SystemMessage(...), HumanMessage(...)]
  ```

  与 PromptTemplate 的区别：
  - PromptTemplate → 单个字符串
  - ChatPromptTemplate → 消息列表（system/human/ai）
""")
        return

    # 创建对话模板
    chat_prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一位{role}，用{style}风格回答问题"),
        ("human", "{question}")
    ])

    print(f"\n  模板消息数: {len(chat_prompt.messages)}")
    print(f"  变量: {chat_prompt.input_variables}")

    # 填充变量，生成消息列表
    messages = chat_prompt.format_messages(
        role="数据科学家",
        style="通俗易懂",
        question="什么是过拟合？"
    )

    for msg in messages:
        print(f"\n  {msg.__class__.__name__}: {msg.content}")

    # 实际调用（如果 Ollama 可用）
    if OLLAMA_OK:
        print(f"\n  --- 实际调用 ---")
        chat = ChatOllama(model=MODEL)
        response = chat.invoke(messages)
        print(f"  AIMessage: {response.content[:200]}...")


# ============================================================
# 演示 3：OutputParser（输出解析）
# ============================================================
def demo_output_parser():
    print(f"\n{'='*60}")
    print("演示 3：OutputParser（输出解析）")
    print(f"{'='*60}")

    if not LANGCHAIN_OK:
        print("""
  概念：OutputParser 将模型的文本输出解析为结构化数据。

  常用 Parser：
  - StrOutputParser: 直接返回字符串
  - JsonOutputParser: 解析 JSON
  - PydanticOutputParser: 解析为 Pydantic 模型
  - CommaSeparatedListOutputParser: 解析逗号分隔列表

  代码示例：
  ```python
  from langchain_core.output_parsers import JsonOutputParser

  parser = JsonOutputParser()

  # 获取格式说明（拼入 prompt）
  format_instructions = parser.get_format_instructions()

  prompt = f"提取以下文本中的人名和地点，{format_instructions}\\n文本：..."

  # 解析模型输出
  result = parser.parse('{"names": ["张三"], "places": ["北京"]}')
  ```
""")
        return

    # StrOutputParser —— 最简单的解析器
    str_parser = StrOutputParser()
    print(f"\n  StrOutputParser:")
    print(f"    输入: AIMessage(content='Hello World')")
    # StrOutputParser 从 AIMessage 中提取 content 字符串
    from langchain_core.messages import AIMessage
    result = str_parser.invoke(AIMessage(content="Hello World"))
    print(f"    输出: {repr(result)}")

    # JsonOutputParser —— 解析 JSON
    json_parser = JsonOutputParser()
    print(f"\n  JsonOutputParser:")
    format_inst = json_parser.get_format_instructions()
    print(f"    格式说明（拼入 prompt）:\n    {format_inst[:200]}...")

    # 模拟解析
    json_text = '{"name": "张三", "age": 28, "city": "杭州"}'
    parsed = json_parser.parse(json_text)
    print(f"    输入: {json_text}")
    print(f"    输出: {parsed} (type: {type(parsed).__name__})")

    # PydanticOutputParser（需要定义 Pydantic 模型）
    print(f"\n  PydanticOutputParser 示例代码:")
    print("""    from pydantic import BaseModel, Field
    from langchain.output_parsers import PydanticOutputParser

    class Person(BaseModel):
        name: str = Field(description="姓名")
        age: int = Field(description="年龄")
        skills: list[str] = Field(description="技能列表")

    parser = PydanticOutputParser(pydantic_object=Person)
    # parser.get_format_instructions() 返回 JSON Schema 说明
    # parser.parse(text) 返回 Person 实例""")


# ============================================================
# 演示 4：LCEL Chain（管道式组合）
# ============================================================
def demo_lcel_chain():
    print(f"\n{'='*60}")
    print("演示 4：LCEL Chain（管道式组合）")
    print(f"{'='*60}")

    if not LANGCHAIN_OK:
        print("""
  概念：LCEL (LangChain Expression Language) 用 | 管道符组合组件。

  ```python
  # 基础 Chain
  chain = prompt | model | parser

  # 等价于：
  # 1. prompt.format(input)    → 生成完整 prompt
  # 2. model.invoke(prompt)    → 调用模型
  # 3. parser.parse(output)    → 解析输出

  # 调用
  result = chain.invoke({"topic": "量子计算"})
  ```

  LCEL 的优势：
  - 声明式：清晰表达数据流
  - 可组合：灵活拼接组件
  - 支持流式：chain.stream(input)
  - 支持异步：chain.ainvoke(input)
  - 支持批量：chain.batch([input1, input2])
""")
        return

    # 构建一个简单的 Chain
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个简洁的技术助手，用一句话回答。"),
        ("human", "用一句话解释{concept}")
    ])

    str_parser = StrOutputParser()

    print(f"\n  Chain 结构: prompt | model | parser")

    if OLLAMA_OK:
        # 实际执行 Chain
        model = ChatOllama(model=MODEL)
        chain = prompt | model | str_parser

        print(f"\n  --- 执行 chain.invoke() ---")
        result = chain.invoke({"concept": "微服务架构"})
        print(f"  输入: concept='微服务架构'")
        print(f"  输出: {result}")

        # 批量调用
        print(f"\n  --- 执行 chain.batch() ---")
        results = chain.batch([
            {"concept": "Docker"},
            {"concept": "Kubernetes"},
        ])
        for concept, result in zip(["Docker", "Kubernetes"], results):
            print(f"  {concept}: {result[:100]}")
    else:
        print(f"\n  Ollama 不可用，展示 Chain 组件:")
        print(f"    prompt 变量: {prompt.input_variables}")
        print(f"    parser 类型: {str_parser.__class__.__name__}")

        # 展示 prompt 模板的输出
        messages = prompt.format_messages(concept="微服务架构")
        print(f"\n  prompt 格式化后:")
        for msg in messages:
            print(f"    {msg.__class__.__name__}: {msg.content}")

        print(f"\n  （接下来 model 会处理这些消息，parser 提取文本）")


# ============================================================
# 演示 5：对话记忆（Memory）概念
# ============================================================
def demo_memory_concept():
    print(f"\n{'='*60}")
    print("演示 5：对话记忆（Memory）概念")
    print(f"{'='*60}")

    print("""
  LLM 本身无状态 — 每次调用都是独立的。对话记忆需要客户端维护。

  LangChain 提供的 Memory 类型：

  1. ConversationBufferMemory
     - 完整保存所有历史消息
     - 简单但 Token 消耗随对话增长

  2. ConversationBufferWindowMemory
     - 只保留最近 k 轮对话
     - 控制 Token 消耗，但会丢失早期信息

  3. ConversationSummaryMemory
     - 用 LLM 总结历史对话
     - Token 消耗可控，保留关键信息

  4. ConversationSummaryBufferMemory
     - 近期对话完整保留 + 早期对话总结
     - 平衡信息保留和 Token 消耗

  代码示例（ConversationBufferMemory）：
  ```python
  from langchain.memory import ConversationBufferMemory

  memory = ConversationBufferMemory(return_messages=True)

  # 保存对话
  memory.save_context(
      {"input": "你好"},
      {"output": "你好！有什么可以帮你？"}
  )

  # 读取历史
  history = memory.load_memory_variables({})
  # {'history': [HumanMessage(...), AIMessage(...)]}
  ```

  实际应用中的记忆管理策略：
  - 短对话（< 10 轮）：BufferMemory 足够
  - 长对话（> 10 轮）：SummaryBufferMemory
  - 多用户：每个用户独立 Memory 实例 + 持久化存储
""")


# ============================================================
# 主程序
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("LangChain 入门演示")
    print("=" * 60)

    if LANGCHAIN_OK:
        print(f"\n  LangChain 已安装")
        print(f"  Ollama: {'可用' if OLLAMA_OK else '不可用（将跳过实际调用）'}")
    else:
        print(f"\n  LangChain 未安装，将展示代码结构和概念")

    demo_prompt_template()
    demo_chat_prompt_template()
    demo_output_parser()
    demo_lcel_chain()
    demo_memory_concept()

    print(f"\n{'='*60}")
    print("演示完成！")
    print(f"\n后续学习路径:")
    print("  1. langchain → 基础组件")
    print("  2. langchain-community → 第三方集成（Ollama/OpenAI/...）")
    print("  3. langgraph → Agent 和工作流")
    print("  4. langsmith → 可观测性和调试")
    print("=" * 60)
