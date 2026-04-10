# C1 LLM 基础与 Prompt — `demos/` 说明

多数脚本需 **本机 Ollama**（默认 `http://localhost:11434`）或 **OpenAI 兼容 API Key**；以各文件顶部注释为准。

```bash
cd demos
python3 01_ollama_basics.py
```

| 文件 | 要点 | 常见依赖 |
|------|------|----------|
| `01_ollama_basics.py` | 检测服务、列表模型、非流式/流式/多轮 | `requests` |
| `02_openai_api.py` | 兼容 OpenAI 的 chat/completions | `openai` 或 `httpx`（见文件） |
| `03_prompt_engineering.py` | Few-shot、角色、链式提示等 | 视文件 |
| `04_streaming_output.py` | 流式消费 SSE/chunk | `requests` / `openai` |
| `05_langchain_basics.py` | LangChain 最小链路与记忆 | `langchain` 等 |
| `06_token_counter.py` | Token 估算与上下文意识 | 视 tokenizer |
| `07_prompt_templates.py` | 模板变量与可复用 Prompt | 视文件 |

详细脉络与 5 日路径见上级 [`理论讲解.md`](../理论讲解.md)。
