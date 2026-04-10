# C6 单 Agent 开发 — `demos/` 说明

与 [`../理论讲解.md`](../理论讲解.md) 配套：ReAct 风格「思考 → 工具 → 观察」多步循环；先 mock，再 Ollama。

```bash
cd demos
python3 01_react_loop_mock.py

# 需 Ollama + 支持 tools 的模型；环境变量同 C4 的 02
pip install requests   # 若尚未安装
python3 02_react_with_ollama.py
```

| 文件 | 要点 | 依赖 |
|------|------|------|
| `01_react_loop_mock.py` | 规则假 LLM + `search_kb` 工具，多步直到最终答复 | 无 |
| `02_react_with_ollama.py` | 真实 Chat Completions + `kb_lookup` 一轮工具回环 | `requests` |
