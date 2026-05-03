#!/usr/bin/env python3
"""
C6 单 Agent 开发——ReAct 循环的完整实现

ReAct = Reasoning（推理） + Acting（行动）
Agent 的决策循环：思考 → 行动 → 观察 → 思考 → 行动 → ... → 最终回答

运行方式：python3 03_react_loop_complete.py
"""

import json
from dataclasses import dataclass, field
from enum import Enum


# ============================================================
# 1. ReAct 循环的概念
# ============================================================
print("=" * 60)
print("1. ReAct 循环（Reasoning + Acting）")
print("=" * 60)

REACT_FLOW = """
ReAct 循环流程（一张图看懂）：

  用户输入："福州加上海的人口是多少？"
       │
       ▼
  ┌──────────────────────────────┐
  │  Step 1: Thought（推理）      │
  │  "我需要查福州人口和上海人口， │
  │   然后加起来。"               │
  └──────────┬───────────────────┘
             │
             ▼
  ┌──────────────────────────────┐
  │  Step 2: Action（行动）       │
  │  get_population(city="福州")  │
  │  → "8,290,000"              │
  └──────────┬───────────────────┘
             │
             ▼
  ┌──────────────────────────────┐
  │  Step 3: Observation（观察）  │
  │  "福州人口 829 万"            │
  └──────────┬───────────────────┘
             │
             ▼
  ┌──────────────────────────────┐
  │  Step 4: Thought（再推理）     │
  │  "还需要上海人口，继续调工具"   │
  └──────────┬───────────────────┘
             │
             ▼
  ┌──────────────────────────────┐
  │  Step 5: Action（行动）       │
  │  get_population(city="上海")  │
  │  → "24,870,000"             │
  └──────────┬───────────────────┘
             │
             ▼
  ┌──────────────────────────────┐
  │  Step 6: Thought（最终推理）   │
  │  "829万 + 2487万 = 3316万"   │
  │  输出最终答案                 │
  └──────────────────────────────┘

关键设计决策：
- 什么时候停止？→ 达到 max_iterations 或 LLM 输出 Final Answer
- 重复调同一个工具怎么办？→ 记录历史，检测循环
- 工具调用失败了怎么办？→ 把错误信息作为 Observation，让 LLM 决定下一步
"""

print(REACT_FLOW)


# ============================================================
# 2. ReAct 循环的代码实现
# ============================================================
print("=" * 60)
print("2. ReAct 循环——完整代码实现")
print("=" * 60)


class StopReason(Enum):
    """ReAct 循环的停止原因"""
    FINAL_ANSWER = "final_answer"      # LLM 给出了最终答案
    MAX_ITERATIONS = "max_iterations"  # 达到最大迭代步数
    TOOL_ERROR_LOOP = "tool_error_loop"  # 工具连续失败
    NO_TOOL = "no_tool"               # LLM 没调工具也没给答案


@dataclass
class ReActStep:
    """ReAct 循环中每一步的记录"""
    step_number: int
    thought: str = ""
    action: str = ""          # 工具名
    action_input: str = ""    # 工具参数
    observation: str = ""     # 工具返回的结果


@dataclass
class ReActLoop:
    """
    ReAct 循环的实现。

    这不是调真 LLM 的代码，而是把 ReAct 的决策逻辑"抽出骨架"。
    理解了这个骨架，换成真 LLM + 真工具就是工程细节。
    """

    max_iterations: int = 10  # 最多循环多少次（防止无限循环）
    verbose: bool = True      # 是否打印每一步

    def run(self, user_input: str) -> str:
        """执行 ReAct 循环"""
        steps: list[ReActStep] = []
        context: list[str] = [f"用户问题: {user_input}"]
        stop_reason = StopReason.NO_TOOL

        for i in range(self.max_iterations):
            step = ReActStep(step_number=i + 1)

            # Phase 1: THOUGHT（推理）
            # 真实现实：LLM 看上下文 → 判断下一步该思考什么
            thought = self._simulate_though(context, i)
            step.thought = thought
            context.append(f"Thought: {thought}")

            if self.verbose:
                print(f"\n  ┌─ Step {i+1} ─────────────────────")
                print(f"  │ Thought: {thought}")

            # Phase 2: DECISION——调工具还是给答案？
            action_decision = self._simulate_decision(context, i)

            if action_decision == "STOP":
                # LLM 判断：信息够了，可以出最终答案
                final_answer = self._simulate_final_answer(context)
                stop_reason = StopReason.FINAL_ANSWER
                if self.verbose:
                    print(f"  │ Action: Final Answer")
                    print(f"  │ → {final_answer}")
                return final_answer

            # Phase 3: ACTION（调工具）
            tool_name, tool_input = action_decision
            step.action = tool_name
            step.action_input = json.dumps(tool_input, ensure_ascii=False)
            context.append(f"Action: {tool_name}({tool_input})")

            if self.verbose:
                print(f"  │ Action: {tool_name}({json.dumps(tool_input, ensure_ascii=False)})")

            # Phase 4: OBSERVATION（观察结果）
            observation = self._execute_tool(tool_name, tool_input)
            step.observation = observation
            context.append(f"Observation: {observation}")

            if self.verbose:
                print(f"  │ Observation: {observation}")
                print(f"  └──────────────────────────")

            steps.append(step)

            # 检查工具是否返回了错误
            if observation.startswith("Error"):
                recent_errors = sum(
                    1 for s in steps[-3:]
                    if s.observation.startswith("Error")
                )
                if recent_errors >= 3:
                    stop_reason = StopReason.TOOL_ERROR_LOOP
                    return "抱歉，工具多次失败，无法完成此任务"

        # 超过最大迭代次数
        stop_reason = StopReason.MAX_ITERATIONS
        return f"达到最大迭代次数 {self.max_iterations}，任务未完成"

    def _simulate_though(self, context: list[str], step_idx: int) -> str:
        """
        模拟 LLM 的"思考"过程。

        真实实现：发送 context 给 GPT-4/Claude，让它用 ReAct 格式输出。
        这里用硬编码模拟不同步骤的推理逻辑。
        """
        if step_idx == 0:
            return "我需要查询福州和上海的人口数据，然后把两个数字相加。先查福州。"
        elif step_idx == 1:
            return "福州人口是 8,290,000。还需要上海人口，继续查询。"
        elif step_idx == 2:
            return "上海人口是 24,870,000。现在可以计算总和了。"
        else:
            return "我已经有足够信息来回答问题。"

    def _simulate_decision(self, context: list[str], step_idx: int):
        """
        模拟 LLM 的"决策"：调工具还是给最终答案？

        真实实现：解析 LLM 返回的 ReAct 格式文本，
        找到 "Action:" 或 "Final Answer:"。
        """
        if step_idx == 0:
            return ("get_population", {"city": "福州"})
        elif step_idx == 1:
            return ("get_population", {"city": "上海"})
        elif step_idx == 2:
            return "STOP"

    def _simulate_final_answer(self, context: list[str]) -> str:
        """模拟 LLM 生成最终答案"""
        return ("福州人口约 829 万，上海人口约 2487 万。"
                "两个城市人口总和约为 3316 万。")

    def _execute_tool(self, tool_name: str, params: dict) -> str:
        """执行工具（模拟）"""
        populations = {
            "福州": 8290000,
            "上海": 24870000,
            "北京": 21880000,
        }
        if tool_name == "get_population":
            city = params.get("city", "")
            pop = populations.get(city)
            if pop:
                return f"{city}人口: {pop:,}"
            return f"Error: 未找到{city}的人口数据"
        return f"Error: 未知工具 '{tool_name}'"


# 运行
agent = ReActLoop(max_iterations=10)
result = agent.run("福州加上海的人口是多少？")
print(f"\n  📋 最终答案: {result}")


# ============================================================
# 3. ReAct 的关键设计问题
# ============================================================
print("\n" + "=" * 60)
print("3. ReAct 循环的关键设计问题")
print("=" * 60)

DESIGN_QUESTIONS = """
Q1: 什么时候停止？
   A1: 三个条件任一个触发：
       - LLM 输出 "Final Answer:"（信息足够了）
       - 达到 max_iterations（防止无限循环烧 token）
       - 工具连续失败（继续下去没意义）

Q2: 怎么防止"死循环"（Agent 反复调同一个工具同一个参数）？
   A2: 记录最近的 action 历史，检测重复。
       如果连续 3 次同样的 action + input → 停止并提示。

Q3: 上下文（context）怎么管理？
   A3: 所有 Thought/Action/Observation 都追加到 messages 数组。
       但要注意 token 预算——消息太长超出模型 context window 要截断。

Q4: 工具执行超时怎么办？
   A4: 设 max_tool_timeout（如 30 秒）。
       超时 → observation = "Error: 工具执行超时"
       让 LLM 决定是重试、换工具还是放弃。

Q5: 和 LangChain AgentExecutor 的关系？
   A5: LangChain 的 AgentExecutor 就是这个循环的封装。
       核心逻辑完全一样：推理→选择工具→执行→观察→推理→...
"""

print(DESIGN_QUESTIONS)

print("\n✅ C6 ReAct 循环完整演示完成")
