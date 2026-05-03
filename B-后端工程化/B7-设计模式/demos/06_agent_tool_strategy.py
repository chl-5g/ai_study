#!/usr/bin/env python3
"""
B7 设计模式——AI Agent 中的策略模式：工具调用系统

理论对应：B7-设计模式/理论讲解.md §3（策略）、§15（AI Agent 关联）

每个工具 = 一个策略。Agent 选择工具的过程 = 策略选择。
不用 if-elif 选工具，用策略字典（O(1) 查找）。

运行方式：python3 06_agent_tool_strategy.py
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


# ============================================================
# 1. 问题：不用策略模式的样子
# ============================================================
print("=" * 60)
print("1. 反模式：用 if-elif 选工具")
print("=" * 60)

BAD_CODE = """
def execute_tool(tool_name: str, params: dict) -> str:
    if tool_name == "search":
        return google_search(params["query"])
    elif tool_name == "calculator":
        return str(eval(params["expression"]))
    elif tool_name == "weather":
        return get_weather(params["city"])
    elif tool_name == "translator":
        return translate(params["text"], params["target_lang"])
    # 加新工具？再加一个 elif
    # 10 个工具？10 个 elif
    # 工具逻辑改了？在几百行的 if-else 里找对应的分支
"""

print(BAD_CODE)


# ============================================================
# 2. 用策略模式改造：统一接口 → 策略字典
# ============================================================
print("=" * 60)
print("2. 策略模式解法：每个工具一个类 → 策略字典")
print("=" * 60)


# —— Step 1：定义统一接口 ——
class Tool(ABC):
    """
    所有工具的抽象接口。

    这是策略模式的"策略接口"——每个具体工具都要实现这三个方法。
    对 Agent 来说，它只需要知道 Tool 接口，不关心具体是什么工具。
    """
    @abstractmethod
    def name(self) -> str:
        """工具名——Agent 通过这个名字选择工具"""
        ...

    @abstractmethod
    def description(self) -> str:
        """工具描述——告诉 LLM 这个工具是干什么的"""
        ...

    @abstractmethod
    def parameters_schema(self) -> dict:
        """参数 schema——告诉 LLM 该传什么参数"""
        ...

    @abstractmethod
    def execute(self, params: dict) -> str:
        """执行工具——每个工具自己的逻辑"""
        ...


# —— Step 2：每个工具 = 一个策略类 ——
class SearchTool(Tool):
    """搜索互联网"""
    def name(self) -> str:
        return "search"

    def description(self) -> str:
        return "搜索互联网获取最新信息。参数：query（搜索关键词）"

    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索关键词"}
            },
            "required": ["query"]
        }

    def execute(self, params: dict) -> str:
        query = params.get("query", "")
        # 真实实现：调用 Google/Bing API 或 SerpAPI
        return f"关于'{query}'的搜索结果：(模拟) 找到 3 条相关信息..."


class CalculatorTool(Tool):
    """数学计算"""
    def name(self) -> str:
        return "calculator"

    def description(self) -> str:
        return "执行数学计算。参数：expression（数学表达式，如 '2+3*4'）"

    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "数学表达式"}
            },
            "required": ["expression"]
        }

    def execute(self, params: dict) -> str:
        expression = params.get("expression", "0")
        try:
            # 注意：生产环境不要用 eval，用 pyparsing 或 numexpr
            # 这里仅作演示
            result = eval(expression, {"__builtins__": {}}, {})
            return f"计算结果：{expression} = {result}"
        except Exception as e:
            return f"计算错误：{e}"


class WeatherTool(Tool):
    """查询天气"""
    def name(self) -> str:
        return "weather"

    def description(self) -> str:
        return "查询城市天气。参数：city（城市名）"

    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名称"}
            },
            "required": ["city"]
        }

    def execute(self, params: dict) -> str:
        city = params.get("city", "")
        return f"{city}天气：晴，25°C，湿度 60%（模拟数据）"


# —— Step 3：Agent 持有工具字典（策略字典） ——
class AgentWithTools:
    """
    Agent 不需要知道有哪些具体工具。
    它只知道 Tool 接口和 tools 字典。

    加新工具 → 新建 Tool 子类 → 注册到 Agent。Agent 代码不变。
    这就是"开闭原则"：对扩展开放（加新工具），对修改关闭（不改 Agent）。
    """

    def __init__(self):
        # 策略字典：工具名 → 工具实例
        # O(1) 查找，不是 O(n) 的 if-elif！
        self.tools: dict[str, Tool] = {}

    def register_tool(self, tool: Tool):
        """注册一个工具。永远不会改 Agent 的核心逻辑！"""
        self.tools[tool.name()] = tool
        print(f"  📦 注册工具: {tool.name()} - {tool.description()}")

    def get_tool_schemas(self) -> list[dict]:
        """获取所有工具的 schema（给 LLM 做 function calling）"""
        return [
            {
                "name": tool.name(),
                "description": tool.description(),
                "parameters": tool.parameters_schema(),
            }
            for tool in self.tools.values()
        ]

    def execute_tool(self, tool_name: str, params: dict) -> str:
        """执行工具——O(1) 字典查找，不是 if-elif"""
        tool = self.tools.get(tool_name)
        if tool is None:
            return f"未知工具：{tool_name}"
        return tool.execute(params)


# —— Step 4：使用 ——
agent = AgentWithTools()
agent.register_tool(SearchTool())
agent.register_tool(CalculatorTool())
agent.register_tool(WeatherTool())

print("\n工具列表（给 LLM 的 function calling schema）：")
for schema in agent.get_tool_schemas():
    print(f"  - {schema['name']}: {schema['description']}")

print("\n模拟 Agent 调用工具：")

# LLM 返回 function call: {"name": "calculator", "parameters": {"expression": "15 * 3 + 7"}}
result = agent.execute_tool("calculator", {"expression": "15 * 3 + 7"})
print(f"  calculator → {result}")

result = agent.execute_tool("search", {"query": "Python 3.13 新特性"})
print(f"  search → {result}")

result = agent.execute_tool("weather", {"city": "福州"})
print(f"  weather → {result}")


# ============================================================
# 3. 扩展：加新工具不需要改 Agent 代码
# ============================================================
print("\n" + "=" * 60)
print("3. 开闭原则：加新工具 = 加新类，不改 Agent")
print("=" * 60)


class TranslatorTool(Tool):
    """翻译工具——新增的，对 Agent 零侵入"""
    def name(self) -> str:
        return "translator"

    def description(self) -> str:
        return "翻译文本。参数：text（待翻译文本），target_lang（目标语言）"

    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "target_lang": {"type": "string", "description": "目标语言（en/zh/ja）"}
            },
            "required": ["text", "target_lang"]
        }

    def execute(self, params: dict) -> str:
        text = params.get("text", "")
        target = params.get("target_lang", "en")
        return f"翻译结果（{target}）：{text[::-1]}"  # 模拟翻译


# 注册新工具——不改 Agent 代码！
agent.register_tool(TranslatorTool())
result = agent.execute_tool("translator", {"text": "Hello World", "target_lang": "zh"})
print(f"  translator → {result}")

print(f"\n  Agent 现在有 {len(agent.tools)} 个工具，Agent 类代码从未改动。")
print("  这就是策略模式在 Agent 工程中的核心价值。")


print("\n✅ B7 AI Agent 工具策略模式演示完成")
print("理论对应：B7-设计模式/理论讲解.md §3（策略模式）、§15（AI Agent 关联）")
