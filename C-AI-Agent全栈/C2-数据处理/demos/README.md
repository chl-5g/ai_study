# C2 数据处理 — `demos/` 说明

与 [`../理论讲解.md`](../理论讲解.md) 配套：清洗 Markdown、对话 JSONL、文本规范化、PII 脱敏。均为**标准库**，无需 `pip`。

```bash
cd demos
python3 01_clean_markdown.py
```

| 文件 | 要点 | 依赖 |
|------|------|------|
| `01_clean_markdown.py` | 去 front matter、换行统一、压缩多余空行、行尾空白 | 无 |
| `02_jsonl_messages.py` | JSONL 读写、`role` 校验、合并为 API `messages` | 无 |
| `03_normalize_text.py` | 全角标点、零宽字符、重复空格 | 无 |
| `04_pii_redact.py` | 手机、邮箱等简单脱敏（演示用，生产需更严策略） | 无 |

建议顺序：`01` → `03` → `02` → `04`（先单文档清洗与规范化，再对话格式与敏感信息）。
