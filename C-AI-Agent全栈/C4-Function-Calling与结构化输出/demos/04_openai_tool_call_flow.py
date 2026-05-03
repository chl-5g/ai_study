#!/usr/bin/env python3
"""
C4 Function Calling——一次完整的 LLM 工具调用往返

演示：用户问"北京今天天气怎么样？"
→ LLM 不知道天气（没有实时数据）→ 返回 function call
→ 程序执行 function（查天气）→ 把结果发回 LLM
→ LLM 生成最终回答

这个"用户→LLM→工具→LLM→回答"的循环，就是 ReAct Agent 的核心。

运行方式：python3 04_openai_tool_call_flow.py
依赖：pip install openai
"""

import json


# ============================================================
# 1. 工具调用流程图解
# ============================================================
print("=" * 60)
print("1. Function Calling 全流程")
print("=" * 60)

FLOW = """
用户问："北京今天天气怎么样？"

第 1 轮 ──────────────────────────────────────
  程序 → LLM API（带 tools 定义）
  {
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "北京今天天气怎么样？"}],
    "tools": [{
      "type": "function",
      "function": {
        "name": "get_weather",
        "description": "查询指定城市的天气",
        "parameters": {
          "type": "object",
          "properties": {
            "city": {"type": "string"}
          }
        }
      }
    }]
  }

  LLM 返回（不是文本，是 function call！）：
  {
    "choices": [{
      "message": {
        "role": "assistant",
        "tool_calls": [{
          "function": {
            "name": "get_weather",
            "arguments": "{\"city\": \"北京\"}"
          }
        }]
      }
    }]
  }
  ← LLM 不直接回答，而是说"我需要调 get_weather 工具，参数是 city=北京"

第 2 轮（工具执行）─────────────────────────
  程序执行 get_weather(city="北京")
  → 得到结果："北京今天晴，25°C"

第 3 轮（把结果发回 LLM）────────────────────
  程序 → LLM API
  {
    "messages": [
      {"role": "user", "content": "北京今天天气怎么样？"},
      {"role": "assistant", "tool_calls": [...]},           ← 第 1 轮返回的
      {"role": "tool", "tool_call_id": "xxx", "content": "北京今天晴，25°C"}  ← 工具结果
    ],
    "tools": [...]   ← 要带上工具定义
  }

  LLM 返回最终回答：
  "北京今天天气晴，气温 25°C，适合外出。"
"""

print(FLOW)


# ============================================================
# 2. 模拟 tools 定义和响应
# ============================================================
print("=" * 60)
print("2. 工具定义（OpenAI 格式）与 JSON Schema")
print("=" * 60)

# 工具定义的 JSON Schema
TOOLS_DEFINITION = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询指定城市当天天气",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，如'北京'、'上海'"
                    }
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "发送邮件",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "收件人邮箱"},
                    "subject": {"type": "string", "description": "邮件主题"},
                    "body": {"type": "string", "description": "邮件正文"}
                },
                "required": ["to", "subject", "body"]
            }
        }
    }
]

print("工具定义（发给 LLM 的）：")
print(json.dumps(TOOLS_DEFINITION, indent=2, ensure_ascii=False))


# ============================================================
# 3. 工具函数实现 + 分派
# ============================================================
print("\n" + "=" * 60)
print("3. 工具实现与分派")
print("=" * 60)


def get_weather(city: str) -> str:
    """真实实现会调用天气 API"""
    weather_data = {
        "北京": "晴，25°C，湿度 45%",
        "上海": "多云，28°C，湿度 70%",
        "福州": "小雨，22°C，湿度 85%",
    }
    return weather_data.get(city, f"未找到{city}的天气数据")


def send_email(to: str, subject: str, body: str) -> str:
    """真实实现会调用邮件服务"""
    return f"邮件已发送到 {to}，主题：{subject}"


# 工具分派字典（又是策略模式！）
TOOL_HANDLERS = {
    "get_weather": get_weather,
    "send_email": send_email,
}


def dispatch_tool_call(tool_name: str, arguments: str) -> str:
    """
    解析 LLM 返回的 function call，执行对应工具。
    这不是 if-elif 地狱，是策略字典。
    """
    handler = TOOL_HANDLERS.get(tool_name)
    if not handler:
        return json.dumps({"error": f"未知工具: {tool_name}"})

    try:
        params = json.loads(arguments)  # arguments 是 JSON 字符串
        result = handler(**params)  # 展开字典为关键字参数
        print(f"  执行工具: {tool_name}({params}) → {result}")
        return result
    except Exception as e:
        return json.dumps({"error": str(e)})


# 模拟 LLM 返回的 tool_calls
mock_tool_calls = [
    {"function": {"name": "get_weather", "arguments": '{"city": "福州"}'}},
    {"function": {"name": "send_email",
                   "arguments": '{"to": "boss@example.com", "subject": "天气报告", "body": "福州今天小雨"}'}},
]

print("模拟执行 LLM 返回的工具调用：")
for call in mock_tool_calls:
    name = call["function"]["name"]
    args = call["function"]["arguments"]
    result = dispatch_tool_call(name, args)
    print(f"    ← LLM 应该看到这个结果：{result}")


# ============================================================
# 4. 关键陷阱提示
# ============================================================
print("\n" + "=" * 60)
print("4. Function Calling 常见陷阱")
print("=" * 60)

TRAPS = """
陷阱 1：arguments 是 JSON 字符串，不是 dict！
  LLM 返回: {"arguments": "{\\"city\\": \\"北京\\"}"}
  注意 arguments 的值是一个字符串！需要 json.loads() 解析。
  直接用 arguments["city"] 会报错。

陷阱 2：LLM 可能编造工具参数
  LLM 可能返回 get_weather(city="不存在的城市123")
  你的工具实现要做好参数校验和错误处理。

陷阱 3：LLM 可能同时返回文本和 tool_calls
  有的模型可以同时返回一段文本 + 一个 function call。
  你的代码要能处理"message.content 和 message.tool_calls 都不为空"的情况。

陷阱 4：第 2 轮请求必须带上完整消息历史
  models 数组里必须包含之前所有的 user/assistant/tool 消息。
  丢了消息 → LLM 丢失上下文 → 混乱。

陷阱 5：stream=True（流式）时 tool_calls 的处理不同
  流式模式下，tool_calls 的参数是分 chunk 过来的。
  需要自己拼接，不能直接 json.loads 单个 chunk。
"""

print(TRAPS)

print("\n✅ C4 Function Calling 全流程演示完成")
