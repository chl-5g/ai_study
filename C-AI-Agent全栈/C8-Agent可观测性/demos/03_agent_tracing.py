#!/usr/bin/env python3
"""
C8 Agent 可观测性——Agent 请求的完整追踪

一个 Agent 请求可能经过多个步骤，每一步都可能出错。
可观测性让你在出问题时，一眼看到"是哪一跳坏了"。

运行方式：python3 03_agent_tracing.py
"""

import time
import uuid
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone


# ============================================================
# 1. Span——追踪的基本单位
# ============================================================
print("=" * 60)
print("1. Span：一次操作的完整记录")
print("=" * 60)

SPAN_CONCEPT = """
一次 Agent 请求可能包含这些 span（一个 span = 一个有名字、有开始/结束时间的操作）：

  trace_id: abc-123（整个请求的 ID）
  │
  ├─ Span: agent.run (总耗时: 3.2s)
  │   ├─ Span: llm.call (第 1 次，耗时: 1.5s)
  │   │   └─ Span: openai.chat.completions.create (耗时: 1.4s)  ← HTTP 调用
  │   ├─ Span: tool.execute (tool=get_weather, 耗时: 0.3s)
  │   │   └─ Span: http.get (url=weather-api.com, 耗时: 0.28s)
  │   └─ Span: llm.call (第 2 次，耗时: 0.8s)

每个 span 记录：
  - name: 操作名（llm.call / tool.execute / http.get）
  - start_time / end_time: 什么时间开始和结束
  - attributes: 附加上下文（model=gpt-4, tool=get_weather, url=xxx）
  - status: OK / ERROR
  - parent_span: 父操作是哪个
"""

print(SPAN_CONCEPT)


# ============================================================
# 2. 极简 Tracing 实现
# ============================================================
print("=" * 60)
print("2. 自己实现一个极简 Agent Tracer")
print("=" * 60)


@dataclass
class Span:
    """追踪的基本单位"""
    name: str
    trace_id: str
    span_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    parent_id: str | None = None
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None
    status: str = "OK"
    attributes: dict = field(default_factory=dict)
    events: list[dict] = field(default_factory=list)

    def finish(self, status: str = "OK"):
        """标记 span 结束"""
        self.end_time = time.time()
        self.status = status

    def add_event(self, name: str, attributes: dict | None = None):
        """在 span 内记录一个事件"""
        self.events.append({
            "name": name,
            "timestamp": time.time(),
            "attributes": attributes or {},
        })

    @property
    def duration_ms(self) -> float:
        """span 的耗时（毫秒）"""
        if self.end_time:
            return (self.end_time - self.start_time) * 1000
        return 0


class AgentTracer:
    """
    Agent 请求追踪器。

    用法：
        tracer = AgentTracer()
        trace_id = tracer.start_trace("user_query", {"query": "xxx"})

        with tracer.span("llm.call", attributes={"model": "gpt-4"}):
            result = call_llm(messages)

        with tracer.span("tool.execute", attributes={"tool": "search"}):
            result = execute_tool(params)

        tracer.finish_trace()
    """

    def __init__(self):
        self.traces: dict[str, list[Span]] = {}
        self._span_stack: list[Span] = []

    def start_trace(self, name: str, attributes: dict | None = None) -> str:
        """开始一个 trace"""
        trace_id = str(uuid.uuid4())[:8]
        span = Span(name=name, trace_id=trace_id)
        if attributes:
            span.attributes.update(attributes)
        self.traces[trace_id] = [span]
        self._span_stack = [span]
        return trace_id

    def start_span(self, name: str, attributes: dict | None = None) -> Span:
        """在当前的 trace 里新建一个 span"""
        parent = self._span_stack[-1] if self._span_stack else None
        trace_id = parent.trace_id if parent else str(uuid.uuid4())[:8]
        span = Span(
            name=name,
            trace_id=trace_id,
            parent_id=parent.span_id if parent else None,
        )
        if attributes:
            span.attributes.update(attributes)

        if trace_id not in self.traces:
            self.traces[trace_id] = []
        self.traces[trace_id].append(span)
        self._span_stack.append(span)
        return span

    def end_span(self, span: Span, status: str = "OK"):
        """结束一个 span"""
        span.finish(status)
        if self._span_stack and self._span_stack[-1] is span:
            self._span_stack.pop()

    def finish_trace(self):
        """结束当前 trace 中的所有未结束 span"""
        while self._span_stack:
            span = self._span_stack.pop()
            if span.end_time is None:
                span.finish()

    def print_trace(self, trace_id: str):
        """以树形结构打印一个 trace"""
        spans = self.traces.get(trace_id, [])
        if not spans:
            return

        print(f"\n  trace_id: {trace_id}")
        print(f"  ─────────────────────────────")

        # 找到根 span
        roots = [s for s in spans if s.parent_id is None]
        for root in roots:
            self._print_span_tree(spans, root, indent="  ")

    def _print_span_tree(self, all_spans: list[Span], span: Span,
                         indent: str = ""):
        """递归打印 span 树"""
        status_icon = "✅" if span.status == "OK" else "❌"
        print(f"{indent}{status_icon} {span.name} "
              f"({span.duration_ms:.0f}ms)")
        if span.attributes:
            for k, v in span.attributes.items():
                print(f"{indent}    {k}: {v}")

        # 找到所有子 span
        children = [s for s in all_spans if s.parent_id == span.span_id]
        for child in children:
            self._print_span_tree(all_spans, child, indent + "  ")


# ============================================================
# 3. 模拟一个完整的 Agent 请求追踪
# ============================================================
print("=" * 60)
print("3. 模拟 Agent 请求：追踪每一步")
print("=" * 60)


def simulate_agent_request():
    """模拟一个 Agent 请求：用户问"北京天气怎么样，帮我记个备忘录" """
    tracer = AgentTracer()
    trace_id = tracer.start_trace(
        "agent.run",
        {"user_query": "北京天气怎么样？帮我记个备忘录"}
    )

    # —— 第 1 步：LLM 调用 ——
    span_llm1 = tracer.start_span("llm.call", {"model": "gpt-4", "attempt": 1})
    time.sleep(0.8)  # 模拟 LLM 耗时
    span_llm1.add_event("first_token", {"time_to_first_token_ms": 120})
    span_llm1.add_event("finish_reason", {"reason": "tool_calls"})
    # LLM 返回：需要调 get_weather 工具
    tracer.end_span(span_llm1, "OK")

    # —— 第 2 步：调天气工具 ——
    span_tool = tracer.start_span("tool.execute", {"tool": "get_weather", "city": "北京"})
    time.sleep(0.3)  # 模拟 API 调用
    tracer.end_span(span_tool, "OK")

    # —— 第 3 步：LLM 再次调用 ——
    span_llm2 = tracer.start_span("llm.call", {"model": "gpt-4", "attempt": 2})
    time.sleep(0.6)  # 模拟 LLM 耗时
    # LLM 返回：还需要调 memo 工具
    tracer.end_span(span_llm2, "OK")

    # —— 第 4 步：调备忘录工具 ——
    span_tool2 = tracer.start_span("tool.execute", {"tool": "create_memo"})
    time.sleep(0.2)
    # 模拟：备忘录工具失败！
    tracer.end_span(span_tool2, "ERROR")
    span_tool2.add_event("error", {"message": "备忘录服务超时"})

    # —— 第 5 步：LLM 最终调用（处理备忘录失败） ——
    span_llm3 = tracer.start_span("llm.call", {"model": "gpt-4", "attempt": 3})
    time.sleep(0.5)
    tracer.end_span(span_llm3, "OK")

    tracer.finish_trace()

    print("  Agent 请求完整追踪：")
    tracer.print_trace(trace_id)

    # 分析
    total_duration = sum(s.duration_ms for s in tracer.traces[trace_id]
                         if s.parent_id is None)
    error_spans = [s for s in tracer.traces[trace_id] if s.status == "ERROR"]
    print(f"\n  📊 总耗时: ~{total_duration:.0f}ms")
    print(f"  ❌ 失败操作: {len(error_spans)} 个 ", end="")
    if error_spans:
        print(f"({', '.join(s.name for s in error_spans)})")
    else:
        print()


simulate_agent_request()


# ============================================================
# 4. 生产级可观测性的核心要点
# ============================================================
print("\n" + "=" * 60)
print("4. 生产级可观测性：从 Demo 到生产")
print("=" * 60)

PRODUCTION_OBSERVABILITY = """
Demo 里的 AgentTracer 只能用于教学。生产环境需要：

1. 用 OpenTelemetry SDK
   - 业界标准，支持导出到 Jaeger/Zipkin/Datadog/Grafana
   - pip install opentelemetry-api opentelemetry-sdk
   - 自动追踪 HTTP/gRPC/DB 调用

2. 关键指标（不是只有追踪）
   - 延迟分位数：P50/P90/P99（不要看平均值！）
   - 首 token 时间：用户等多久看到第一个字
   - 端到端耗时：从用户发消息到完整回答的总时间
   - 工具调用成功率：每个工具的 error rate
   - LLM token 消耗：每次请求花了多少 token（= 花了多少钱）
   - 重试次数：每个请求平均重试几次（多了说明下游不稳）

3. 告警规则
   - LLM P99 延迟 > 10s → 通知
   - 工具错误率 > 5% → 通知
   - 首 token P95 > 3s → 通知
   - 重试率 > 10% → 通知

4. trace_id 的传播
   - 网关收到请求 → 提取或生成 trace_id → 放到 HTTP Header
   - 每个下游服务都要接收并传递该 trace_id
   - 通常放在 X-Trace-Id 或 W3C Trace Context 头里
"""

print(PRODUCTION_OBSERVABILITY)

print("\n✅ C8 Agent 可观测性演示完成")
print("理论对应：C8-Agent可观测性/理论讲解.md")
