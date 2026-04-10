# C4 Function Calling 与结构化输出 — `demos/` 说明

与 [`../理论讲解.md`](../理论讲解.md) 配套：`tools` 闭环、Ollama 兼容端、Pydantic 校验结构化 JSON。

**依赖安装**（调用远端模型的脚本需要 `requests`；结构化示例需要 Pydantic）：

```bash
cd demos
pip install -r requirements.txt
```

```bash
# 01：无模型、无网络
python3 01_tool_loop_mock.py

# 02：需本机 Ollama（或其它 OpenAI 兼容端）+ 支持 tool calling 的模型
# 环境变量：OPENAI_BASE_URL（默认 http://localhost:11434/v1）、OPENAI_API_KEY（Ollama 可填 ollama）、OPENAI_MODEL
python3 02_openai_tools_ollama.py

# 03：仅 Pydantic 校验演示，不连模型
python3 03_structured_json_pydantic.py
```

| 文件 | 要点 | 依赖 |
|------|------|------|
| `01_tool_loop_mock.py` | 模拟「模型提议 tool → 宿主执行 → 写回」；`safe_calc` 用 `ast` 受限求值 | 无 |
| `02_openai_tools_ollama.py` | Chat Completions + `tools` + 一轮 `tool_calls` 执行 | `requests` |
| `03_structured_json_pydantic.py` | `model_validate_json`、非法 JSON 的 `ValidationError` | `pydantic` |

`requirements.txt` 已列出 `requests`、`pydantic`；若只跑 `01`，可不装任何包。
