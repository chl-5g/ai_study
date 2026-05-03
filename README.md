# ai_study AI工程化学习

个人 **AI 应用 / Agent / Python 后端工程化** 学习笔记与 Demo 仓库。内容按模块分目录存放，与根目录的进度文档配合使用。

在线仓库：<https://github.com/chl-5g/ai_study>

## 写作标准（全项目统一）

每章 `理论讲解.md` 遵循同一套标准——以 **A1** 为基准：

- **受众**：掌握高中毕业数学和逻辑基础即可读懂，不预设编程专业课背景
- **结构**：Why（为什么需要它 / 生活类比）→ What（术语与边界）→ How（代码 + 逐行解释）
- **小节标记**：每个 `###` 小节第一个代码块或长场景前，用 **本节概念** 钉住含义
- **收尾**：大节末尾设 **checkpoint**（自测题）；每章末尾设 **常见误区** + **面试考点**（含完整答案）
- **关联**：每章在合适的节点点明与 **AI Agent 后端** 的实际对应场景
- **示例**：每章 `demos/` 目录含可运行 `.py` 脚本，与理论节一一对照

## 强制学习顺序

章节之间存在前置依赖，**必须按序推进，禁止跳模块**：

```
A1 → A2 → A3 → A4 → B1 → B2 → B3 → B4 → B5 → B6 → B7 → C1 → C2 → C3 → C4 → C5 → C6 → C7 → C8 → D
```

每章的"下一章"与"前序建议"均遵循此顺序。无例外。

## 目录结构

| 目录 | 章 | 理论 | demos | 说明 |
|------|-----|------|-------|------|
| [A-Python基础](A-Python基础/) | A1  Pythonic与标准库 | 136KB | 17 | OOP/魔术方法/推导式/生成器/装饰器/迭代器/上下文管理器/Type Hints/标准库/Git |
| | A2  FastAPI深度 | 48KB | 7 | 路由/请求体/依赖注入/中间件/异常处理/后台任务 |
| | A3  并发与异步 | 81KB | 8 | 线程/进程/asyncio/协程/GIL/事件循环/异步上下文管理器 |
| | A4  测试与CI | 95KB | 1169 | pytest/覆盖率/fixture/mock/GitHub Actions/pre-commit |
| [B-后端工程化](B-后端工程化/) | B1  数据库深度 | 38KB | 5 | PG核心(索引/事务/EXPLAIN/JSONB)/pgvector/Redis/SQLAlchemy ORM/Alembic |
| | B2  网络与HTTP基础 | 144KB | 9 | TCP/IP/DNS/TLS/HTTP语义/REST/httpx/流式/WebSocket握手 |
| | B3  Docker与部署 | 61KB | 3 | 容器原理/Dockerfile多阶段/docker-compose/volumes/网络/K8s概念/Nginx |
| | B4  消息队列与任务队列 | 95KB | 4 | Redis Stream/Celery/生产者消费者/幂等/死信/发件箱 |
| | B5  SSE与WebSocket | 100KB | 3 | SSE协议/EventSource/大模型流式/WebSocket帧/心跳/广播/选型 |
| | B6  微服务与系统设计 | 54KB | 6 | 超时重试幂等/熔断降级/限流背压/API网关/CAP/Saga/链路追踪 |
| | B7  设计模式 | 41KB | 4 | GoF 23速览/策略/观察者/工厂/单例/装饰器/适配器/责任链/状态/DDD/集成/反模式 |
| [C-AI-Agent全栈](C-AI-Agent全栈/) | C1  LLM基础与Prompt | 41KB | 7 | Token/采样/Ollama/OpenAI API/Prompt模板/LangChain入门 |
| | C2  数据处理 | 51KB | 4 | Markdown/JSONL/PII脱敏/分块策略/规范化（Agent·RAG流水线前置） |
| | C3  RAG与知识库 | 53KB | 7 | 嵌入模型/pgvector检索/重排序/混合检索/评测 |
| | C4  Function Calling | 52KB | 4 | OpenAI协议/Pydantic schema/结构化JSON/工具调用往返 |
| | C5  工具链与MCP | 38KB | 3 | Skills封装/MCP协议/外部工具连接/权限边界/多Server注册 |
| | C6  单Agent开发 | 51KB | 3 | ReAct循环/停止条件/记忆分层/Planner-Executor |
| | C7  多Agent协作 | 44KB | 2 | 监督者路由/Fan-out-in/LangGraph/CrewAI概念 |
| | C8  Agent可观测性 | 56KB | 3 | LangSmith/日志追踪/trace_id/Span/Prometheus+Grafana |
| [D-求职面试](D-求职面试/) | — | 35KB | — | 面试题与参考答案/STAR项目故事线模板/薪资谈判/面试检查清单 |
| [Resume](Resume/) | — | — | — | 简历 LaTeX 工具链（见该目录 README） |

> 理论大小均为约数；demos 计数含 `.py` 脚本，不含 README/配置文件。

## 章节内约定

- 理论稿：各章目录下的 `理论讲解.md`
- 示例代码：各章 `demos/` 下的 `.py` 文件，命名 `01_xxx.py`、`02_xxx.py`
- 每个 demo 文件头部注释说明对应理论节、运行方式和依赖
- 模块 **C**（AI Agent 全栈）：索引与依赖说明见 [C-AI-Agent全栈/README.md](C-AI-Agent全栈/README.md)
- 运行 Demo 需本机安装 **Python 3.11+**；部分章节依赖额外包或本地服务（Docker/Redis 等），以各章 `理论讲解.md`、`demos/README.md` 或脚本头部注释为准

## 根目录其他文件

- [学习流程-5步循环.md](学习流程-5步循环.md)：每章的 **理论 → Demo → 实操 → 更新进度** 固定节奏
- [学习进度.md](学习进度.md)：章节状态与周复盘记录

## 学习流程（5 步循环）

1. **生成理论文档**：AI 根据学习路线生成 `理论讲解.md`
2. **生成 Demo 代码**：每个知识点配套可运行 `.py` 文件
3. **学习理论知识**：阅读理论文档，理解概念和原理
4. **实操 Demo**：逐个运行 `demos/` 代码，改参数看输出变化
5. **更新学习进度**：在 `学习进度.md` 记录完成日期和掌握程度

## 隐私与 `.gitignore`

以下不入库，仅保留在本地（见 [.gitignore](.gitignore)）：

- `Resume/` 下的 `.jpg`、`.pdf`、`.docx`、`.tex`
- `**/.ipynb_checkpoints/`
- `.DS_Store`

## 贡献与许可

私人学习用途；内容不构成课程或商业承诺。若你 fork 自用，请自行注意敏感信息勿提交。
