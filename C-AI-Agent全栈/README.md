# C — AI Agent 全栈

个人学习用 **LLM → RAG → 工具 → Agent → 多 Agent → 观测** 主线笔记，与仓库根目录 [学习流程-5步循环.md](../学习流程-5步循环.md) 配合。

## 教材体例（与 [A1 — Pythonic 与标准库](../A-Python基础/A1-Pythonic与标准库/理论讲解.md) 对齐）

- **叙述顺序**：重要概念默认 **Why（为何痛苦）→ What（术语与边界）→ How（落地做法与 demo）**；避免「只给结论表」的跳步写法。
- **小节标记**：在第一个长表格、长代码块或长场景前，用一两句 **本节概念** 固定术语含义。
- **收尾方式**：大节末尾尽量有 **本节小结（三张卡片）**：一句话定义、典型场景、**和 A1 的类比**（把新知识挂到已熟悉的装饰器、生成器、`logging`、类型标注等上）。
- **实操闭环**：每章文末保留 **与 `demos/` 脚本对照** 表；读完一节就改参数跑脚本，与 A1 的「跑 demo + 改参数看输出」节奏一致。

| 章 | 理论 | demos |
|----|------|--------|
| [C1 — LLM 基础与 Prompt](C1-LLM基础与Prompt/理论讲解.md) | 有 | [说明](C1-LLM基础与Prompt/demos/README.md) · 7 个 `.py` |
| [C2 — 数据处理](C2-数据处理/理论讲解.md) | 有 | [说明](C2-数据处理/demos/README.md) · 4 个 `.py` |
| [C3 — RAG 与知识库](C3-RAG与知识库/理论讲解.md) | 有 | [说明](C3-RAG与知识库/demos/README.md) · 7 个 `.py` |
| [C4 — Function Calling](C4-Function-Calling与结构化输出/理论讲解.md) | 有 | [说明](C4-Function-Calling与结构化输出/demos/README.md) · 3 个 `.py`（`pip install -r demos/requirements.txt`） |
| [C5 — 工具链与 MCP](C5-工具链与MCP/理论讲解.md) | 有 | [说明](C5-工具链与MCP/demos/README.md) · 2 个 `.py` |
| [C6 — 单 Agent](C6-单Agent开发/理论讲解.md) | 有 | [说明](C6-单Agent开发/demos/README.md) · 2 个 `.py` |
| [C7 — 多 Agent](C7-多Agent协作/理论讲解.md) | 有 | [说明](C7-多Agent协作/demos/README.md) · 2 个 `.py` |
| [C8 — 可观测性](C8-Agent可观测性/理论讲解.md) | 有 | [说明](C8-Agent可观测性/demos/README.md) · 2 个 `.py` |

**建议顺序**：C1 → C2/C3（可与 C2 并行）→ C4 → C5 → C6 → C7 → C8。

**完备性约定**：每章 `理论讲解.md` 文末均有 **与 `demos/` 脚本对照**，表内文件名与该章 `demos/README.md` 一致；C4 另需 [`demos/requirements.txt`](C4-Function-Calling与结构化输出/demos/requirements.txt)。
