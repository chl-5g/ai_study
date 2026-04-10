# C3 RAG 与知识库 — `demos/` 说明

建议顺序：`01`→`02`→`03`→`04`→`05`；`06`/`07` 在能跑通流水线后再看。

```bash
cd demos
pip install chromadb requests   # 多数脚本至少需要这两项；其余见各文件头部
python3 01_text_chunking.py
```

| 文件 | 要点 |
|------|------|
| `01_text_chunking.py` | 分块策略与边界 |
| `02_embedding_basics.py` | 向量/相似度直觉 |
| `03_vector_search.py` | 近邻检索 |
| `04_chromadb_demo.py` | ChromaDB 本地集合 |
| `05_rag_pipeline.py` | 端到端：加载→分块→嵌入→检索→生成（Ollama 优先，可 Mock） |
| `06_rag_evaluation.py` | 指标与对比思路 |
| `07_hybrid_search.py` | 向量 + 关键词混合检索 |

架构、进阶 RAG、评测建议见上级 [`理论讲解.md`](../理论讲解.md)。
