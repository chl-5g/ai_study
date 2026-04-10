"""
05_rag_pipeline.py — 完整 RAG 流水线

端到端演示：加载文档 → 分块 → 嵌入 → 存储 → 检索 → 生成回答

LLM 部分：
- 优先调用 Ollama（本地部署的 LLM）
- 如果 Ollama 不可用，使用 Mock LLM（模板拼接）

运行：python3 05_rag_pipeline.py
依赖：pip3 install chromadb requests
"""

import os
import shutil
import json
from typing import List, Tuple

try:
    import chromadb
except ImportError:
    print("请先安装 ChromaDB：pip3 install chromadb")
    exit(1)

try:
    import requests
except ImportError:
    print("请先安装 requests：pip3 install requests")
    exit(1)


# ============================================================
# 第一步：文档加载（Document Loading）
# ============================================================
def load_documents() -> List[dict]:
    """
    加载文档。实际项目中会从文件系统读取 PDF/Markdown/HTML。
    这里用内置文档模拟。
    """
    # 模拟一组 Markdown 格式的知识文档
    raw_docs = [
        {
            "content": """# Python 异步编程

## asyncio 基础

asyncio 是 Python 3.4 引入的异步 I/O 框架。它使用事件循环（Event Loop）来调度协程（Coroutine），
实现非阻塞的并发编程。

核心概念：
- 协程（Coroutine）：用 async def 定义的函数，用 await 挂起执行
- 事件循环（Event Loop）：调度和执行协程的核心引擎
- Task：将协程包装为可调度的任务
- Future：表示一个异步操作的最终结果

## async/await 语法

Python 3.5 引入了 async/await 语法糖：

```python
import asyncio

async def fetch_data(url):
    # 模拟异步 HTTP 请求
    await asyncio.sleep(1)
    return f"Data from {url}"

async def main():
    # 并发执行多个协程
    results = await asyncio.gather(
        fetch_data("url1"),
        fetch_data("url2"),
        fetch_data("url3"),
    )
    print(results)

asyncio.run(main())
```

## 并发 vs 并行

- 并发（Concurrency）：多个任务交替执行，共享同一线程（asyncio 的方式）
- 并行（Parallelism）：多个任务同时执行，使用多线程或多进程

asyncio 适合 I/O 密集型任务（网络请求、文件读写），不适合 CPU 密集型任务。
对于 CPU 密集型任务，应使用 multiprocessing 或 concurrent.futures.ProcessPoolExecutor。

## 常见陷阱

1. 忘记 await：调用协程但不 await，协程不会执行
2. 阻塞调用：在异步函数中调用同步阻塞函数会卡住整个事件循环
3. 过度并发：同时发起太多请求可能导致服务端限流，应使用 asyncio.Semaphore 限制并发数
""",
            "metadata": {"source": "python_async.md", "title": "Python 异步编程"},
        },
        {
            "content": """# Python 类型系统

## 类型提示（Type Hints）

Python 3.5 引入了类型提示（PEP 484），允许为变量和函数参数添加类型注解。
类型提示不影响运行时行为，但能提升代码可读性和 IDE 支持。

```python
def greet(name: str) -> str:
    return f"Hello, {name}"

age: int = 25
names: list[str] = ["Alice", "Bob"]
```

## 常用类型

- 基本类型：int, str, float, bool, bytes
- 容器类型：list[T], dict[K, V], set[T], tuple[T, ...]
- 可选类型：Optional[T] 等价于 T | None
- 联合类型：Union[A, B] 或 A | B（Python 3.10+）
- 可调用类型：Callable[[参数类型], 返回类型]

## mypy 静态类型检查

mypy 是最常用的 Python 静态类型检查工具：

```bash
pip install mypy
mypy your_script.py
```

mypy 能在运行前发现类型错误，相当于给 Python 加上了编译期检查。
配合 strict 模式（mypy --strict）可以获得最严格的类型检查。

## Pydantic 数据验证

Pydantic 是一个数据验证库，利用类型提示在运行时进行数据校验：

```python
from pydantic import BaseModel

class User(BaseModel):
    name: str
    age: int
    email: str

user = User(name="Alice", age=25, email="alice@example.com")
```

Pydantic v2 基于 Rust 核心重写，性能大幅提升。FastAPI 深度集成了 Pydantic。
""",
            "metadata": {"source": "python_types.md", "title": "Python 类型系统"},
        },
    ]

    print(f"  加载了 {len(raw_docs)} 个文档")
    for doc in raw_docs:
        print(f"    - {doc['metadata']['title']} ({len(doc['content'])} 字符)")
    return raw_docs


# ============================================================
# 第二步：文本分块（Text Splitting）
# ============================================================
def split_documents(
    documents: List[dict],
    chunk_size: int = 300,
    overlap: int = 50,
) -> List[dict]:
    """
    递归分割文档为小块。
    保留元数据，并为每个块添加块编号。
    """
    all_chunks = []

    for doc in documents:
        text = doc["content"]
        metadata = doc["metadata"]

        # 按段落分割（优先在 \n\n 处分割）
        paragraphs = text.split("\n\n")
        chunks = []
        current = ""

        for para in paragraphs:
            if len(current) + len(para) <= chunk_size:
                current = current + "\n\n" + para if current else para
            else:
                if current:
                    chunks.append(current.strip())
                if len(para) > chunk_size:
                    # 段落太长，按句子分割
                    sentences = para.replace("\n", " ").split("。")
                    sub_current = ""
                    for sent in sentences:
                        if len(sub_current) + len(sent) <= chunk_size:
                            sub_current = sub_current + "。" + sent if sub_current else sent
                        else:
                            if sub_current:
                                chunks.append(sub_current.strip())
                            sub_current = sent
                    if sub_current:
                        chunks.append(sub_current.strip())
                else:
                    current = para
                    continue
                current = ""

        if current.strip():
            chunks.append(current.strip())

        # 为每个块添加元数据
        for i, chunk in enumerate(chunks):
            if chunk:
                all_chunks.append({
                    "text": chunk,
                    "metadata": {
                        **metadata,
                        "chunk_index": i,
                        "chunk_total": len(chunks),
                    },
                })

    print(f"  分块完成：{len(all_chunks)} 个块")
    for i, chunk in enumerate(all_chunks[:3]):
        print(f"    块 {i}: {chunk['text'][:50]}... ({len(chunk['text'])} 字符)")
    if len(all_chunks) > 3:
        print(f"    ...（省略 {len(all_chunks) - 3} 个块）")

    return all_chunks


# ============================================================
# 第三步：嵌入 + 存储（Embedding + Vector Store）
# ============================================================
def create_vector_store(chunks: List[dict], persist_dir: str) -> chromadb.Collection:
    """
    将文档块嵌入并存储到 ChromaDB。
    ChromaDB 内置嵌入模型，自动完成嵌入过程。
    """
    if os.path.exists(persist_dir):
        shutil.rmtree(persist_dir)

    client = chromadb.PersistentClient(path=persist_dir)
    collection = client.create_collection(
        name="rag_knowledge",
        metadata={"hnsw:space": "cosine"},  # 使用余弦距离
    )

    # 批量添加
    collection.add(
        ids=[f"chunk_{i}" for i in range(len(chunks))],
        documents=[c["text"] for c in chunks],
        metadatas=[c["metadata"] for c in chunks],
    )

    print(f"  向量存储创建完成：{collection.count()} 条记录")
    return collection


# ============================================================
# 第四步：检索（Retrieval）
# ============================================================
def retrieve(collection: chromadb.Collection, query: str, top_k: int = 3) -> List[dict]:
    """
    检索与 Query 最相关的文档块。
    """
    results = collection.query(
        query_texts=[query],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    retrieved = []
    for i in range(len(results["documents"][0])):
        retrieved.append({
            "text": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i],
        })

    return retrieved


# ============================================================
# 第五步：LLM 生成回答
# ============================================================
def call_ollama(prompt: str, model: str = "qwen2.5:latest") -> str:
    """
    调用本地 Ollama API 生成回答。
    Ollama 需要提前安装并运行：https://ollama.ai
    """
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.3, "num_predict": 512},
            },
            timeout=30,
        )
        if response.status_code == 200:
            return response.json()["response"]
        else:
            return None
    except (requests.ConnectionError, requests.Timeout):
        return None


def mock_llm(query: str, context: str) -> str:
    """
    Mock LLM：当 Ollama 不可用时，用模板拼接模拟回答。
    实际 RAG 系统中，这里调用真实的 LLM。
    """
    return f"""[Mock LLM 回答]

基于检索到的上下文，以下是与问题「{query}」相关的信息摘要：

{context[:500]}

---
注意：这是 Mock 回答。安装并启动 Ollama 后可获得真实的 LLM 生成回答。
安装：curl -fsSL https://ollama.ai/install.sh | sh
运行模型：ollama run qwen2.5
"""


def generate_answer(query: str, retrieved_docs: List[dict], use_ollama: bool = True) -> str:
    """
    组装 Prompt 并调用 LLM 生成回答。
    """
    # 拼接检索到的上下文
    context_parts = []
    for i, doc in enumerate(retrieved_docs):
        source = doc["metadata"].get("source", "未知")
        context_parts.append(f"[来源: {source}]\n{doc['text']}")

    context = "\n\n---\n\n".join(context_parts)

    # 构建 RAG Prompt
    prompt = f"""你是一个专业的技术助手。请根据以下参考资料回答用户的问题。
如果参考资料中没有相关信息，请明确说明你不知道，不要编造答案。

## 参考资料

{context}

## 用户问题

{query}

## 回答

请用中文简洁准确地回答："""

    if use_ollama:
        answer = call_ollama(prompt)
        if answer:
            return answer

    # Ollama 不可用，使用 Mock
    return mock_llm(query, context)


# ============================================================
# 主函数：完整 RAG 流水线
# ============================================================
def main():
    print("=" * 70)
    print("完整 RAG 流水线演示")
    print("=" * 70)

    persist_dir = "/tmp/rag_pipeline_demo"

    # 步骤一：加载文档
    print("\n【步骤一】加载文档")
    print("─" * 40)
    documents = load_documents()

    # 步骤二：文本分块
    print("\n【步骤二】文本分块")
    print("─" * 40)
    chunks = split_documents(documents, chunk_size=300, overlap=50)

    # 步骤三：嵌入 + 存储
    print("\n【步骤三】嵌入 + 向量存储")
    print("─" * 40)
    collection = create_vector_store(chunks, persist_dir)

    # 步骤四 + 五：检索 + 生成
    print("\n【步骤四 + 五】检索 + 生成回答")
    print("─" * 40)

    # 检测 Ollama 是否可用
    ollama_available = False
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=3)
        if r.status_code == 200:
            models = [m["name"] for m in r.json().get("models", [])]
            print(f"  Ollama 可用，已安装模型：{models}")
            ollama_available = True
    except:
        print("  Ollama 不可用，将使用 Mock LLM")

    # 多轮问答
    questions = [
        "Python 的 async/await 怎么用？",
        "asyncio 适合什么样的任务？CPU 密集型可以用吗？",
        "Pydantic 是什么？和 FastAPI 有什么关系？",
        "如何在 Python 中进行静态类型检查？",
    ]

    for q in questions:
        print(f"\n{'─' * 70}")
        print(f"Q: {q}")
        print("─" * 70)

        # 检索
        retrieved = retrieve(collection, q, top_k=3)
        print(f"\n  检索到 {len(retrieved)} 个相关片段：")
        for i, doc in enumerate(retrieved):
            source = doc["metadata"].get("source", "?")
            dist = doc["distance"]
            preview = doc["text"][:60].replace("\n", " ")
            print(f"    [{i+1}] (距离={dist:.4f}) [{source}] {preview}...")

        # 生成回答
        print(f"\n  回答：")
        answer = generate_answer(q, retrieved, use_ollama=ollama_available)
        # 缩进输出
        for line in answer.strip().split("\n"):
            print(f"    {line}")

    # 清理
    if os.path.exists(persist_dir):
        shutil.rmtree(persist_dir)

    print("\n" + "=" * 70)
    print("RAG 流水线总结")
    print("=" * 70)
    print("""
  完整流程：
    1. 文档加载 → 从 PDF/MD/HTML 读取原始文本
    2. 文本分块 → 按语义边界切成 200-500 字符的小块
    3. 向量嵌入 → 用嵌入模型将文本块转为向量
    4. 向量存储 → 存入 ChromaDB/Qdrant 等向量数据库
    5. 语义检索 → 用 Query 向量找到 Top-K 最相关的块
    6. Prompt 组装 → 将检索结果拼入 System Prompt
    7. LLM 生成 → 基于上下文生成准确回答

  关键优化点：
    - 分块策略直接影响检索质量
    - 嵌入模型决定语义理解的上限
    - 检索策略（Top-K、阈值过滤、Reranker）影响精度
    - Prompt 模板影响 LLM 的回答质量和幻觉率
    """)


if __name__ == "__main__":
    main()
