"""
04_chromadb_demo.py — 用 ChromaDB 实现完整的 RAG 存储和检索

ChromaDB 是一个轻量级的向量数据库，特点：
- Python 原生，开箱即用
- 内置嵌入模型（默认使用 all-MiniLM-L6-v2）
- 支持持久化存储
- 支持元数据过滤

运行：python3 04_chromadb_demo.py
依赖：pip3 install chromadb
"""

try:
    import chromadb
except ImportError:
    print("请先安装 ChromaDB：pip3 install chromadb")
    print("安装后重新运行本脚本。")
    exit(1)

import os
import shutil


# ============================================================
# 准备知识库文档
# ============================================================
DOCUMENTS = [
    {
        "text": "Python 使用引用计数作为主要的垃圾回收机制。每个对象内部维护一个引用计数器 ob_refcnt，当有新的引用指向该对象时计数加一，引用失效时减一。当计数归零时，对象立即被回收。",
        "metadata": {"source": "python_gc.md", "section": "引用计数", "language": "Python"},
    },
    {
        "text": "循环引用是引用计数的致命缺陷。当两个或多个对象互相引用时，即使外部没有任何引用指向它们，引用计数也不会归零，导致内存泄漏。Python 通过标记-清除算法来解决这个问题。",
        "metadata": {"source": "python_gc.md", "section": "循环引用", "language": "Python"},
    },
    {
        "text": "Python 的分代垃圾回收将对象分为三代：第 0 代（新对象）、第 1 代和第 2 代。新创建的对象放在第 0 代，经过一次 GC 存活后提升到第 1 代，以此类推。高代对象 GC 频率更低。",
        "metadata": {"source": "python_gc.md", "section": "分代回收", "language": "Python"},
    },
    {
        "text": "Rust 的所有权系统在编译期就确定了每块内存的生命周期，不需要运行时垃圾回收。每个值有且只有一个所有者，当所有者离开作用域时值被自动释放（Drop）。",
        "metadata": {"source": "rust_memory.md", "section": "所有权", "language": "Rust"},
    },
    {
        "text": "Go 语言使用并发标记-清除垃圾回收器，从 Go 1.5 开始引入三色标记法。GC 暂停时间（STW）通常控制在亚毫秒级别，适合低延迟场景。",
        "metadata": {"source": "go_gc.md", "section": "并发GC", "language": "Go"},
    },
    {
        "text": "Java 的 G1 垃圾回收器将堆内存划分为多个大小相等的 Region，通过优先回收垃圾最多的 Region 来实现高效回收。G1 是 JDK 9 及以后的默认垃圾回收器。",
        "metadata": {"source": "java_gc.md", "section": "G1", "language": "Java"},
    },
    {
        "text": "ZGC 是 Java 的低延迟垃圾回收器，暂停时间不超过 10 毫秒，且不随堆大小增长。ZGC 使用着色指针（Colored Pointers）和读屏障（Load Barriers）技术。",
        "metadata": {"source": "java_gc.md", "section": "ZGC", "language": "Java"},
    },
    {
        "text": "FastAPI 是一个现代的 Python Web 框架，基于 Starlette 和 Pydantic 构建。它支持异步请求处理，自动生成 OpenAPI 文档，类型提示驱动开发。",
        "metadata": {"source": "fastapi.md", "section": "概述", "language": "Python"},
    },
    {
        "text": "Redis 是一个开源的内存数据库，支持字符串、列表、集合、哈希表、有序集合等数据结构。常用于缓存、会话管理、消息队列和排行榜等场景。",
        "metadata": {"source": "redis.md", "section": "概述", "language": ""},
    },
    {
        "text": "gc 模块提供了控制 Python 垃圾回收器的接口。gc.collect() 手动触发一次垃圾回收，gc.disable() 禁用自动回收，gc.get_objects() 返回所有被跟踪的对象列表。",
        "metadata": {"source": "python_gc.md", "section": "gc模块", "language": "Python"},
    },
]


def main():
    print("=" * 70)
    print("ChromaDB 向量数据库演示")
    print("=" * 70)

    # --- 1. 创建 ChromaDB 客户端 ---
    # 使用临时目录进行持久化演示
    persist_dir = "/tmp/chromadb_demo"
    if os.path.exists(persist_dir):
        shutil.rmtree(persist_dir)

    print("\n--- 创建 ChromaDB 客户端（持久化到磁盘） ---")
    client = chromadb.PersistentClient(path=persist_dir)
    print(f"  存储路径：{persist_dir}")

    # --- 2. 创建 Collection ---
    print("\n--- 创建 Collection ---")
    # ChromaDB 默认使用 all-MiniLM-L6-v2 嵌入模型（首次运行会自动下载）
    collection = client.create_collection(
        name="knowledge_base",
        metadata={"description": "编程语言内存管理知识库"},
    )
    print(f"  Collection：{collection.name}")

    # --- 3. 添加文档 ---
    print("\n--- 添加文档 ---")
    collection.add(
        ids=[f"doc_{i}" for i in range(len(DOCUMENTS))],
        documents=[doc["text"] for doc in DOCUMENTS],
        metadatas=[doc["metadata"] for doc in DOCUMENTS],
    )
    print(f"  已添加 {collection.count()} 条文档")

    # --- 4. 基础查询 ---
    print("\n" + "─" * 70)
    print("查询一：语义搜索")
    print("─" * 70)

    queries = [
        "Python 如何回收不再使用的内存？",
        "哪种语言不需要垃圾回收？",
        "Java 有哪些低延迟的 GC？",
    ]

    for query in queries:
        print(f"\n  Q: {query}")
        results = collection.query(
            query_texts=[query],
            n_results=3,
        )

        for i in range(len(results["documents"][0])):
            doc = results["documents"][0][i]
            dist = results["distances"][0][i]
            meta = results["metadatas"][0][i]
            # ChromaDB 默认返回 L2 距离（越小越相似）
            print(f"    [{i+1}] (距离={dist:.4f}) [{meta.get('source', '')}] {doc[:60]}...")

    # --- 5. 带元数据过滤的查询 ---
    print("\n" + "─" * 70)
    print("查询二：元数据过滤（只搜索 Python 相关文档）")
    print("─" * 70)

    query = "内存管理"
    print(f"\n  Q: {query}（过滤条件：language=Python）")
    results = collection.query(
        query_texts=[query],
        n_results=5,
        where={"language": "Python"},  # 元数据过滤
    )

    for i in range(len(results["documents"][0])):
        doc = results["documents"][0][i]
        dist = results["distances"][0][i]
        meta = results["metadatas"][0][i]
        print(f"    [{i+1}] (距离={dist:.4f}) [{meta.get('section', '')}] {doc[:60]}...")

    # --- 6. 带文档内容过滤的查询 ---
    print("\n" + "─" * 70)
    print("查询三：文档内容过滤（文档必须包含 '垃圾回收' 关键词）")
    print("─" * 70)

    query = "高效的内存回收方案"
    print(f"\n  Q: {query}（文档过滤：包含 '垃圾回收'）")
    results = collection.query(
        query_texts=[query],
        n_results=5,
        where_document={"$contains": "垃圾回收"},  # 文档内容过滤
    )

    for i in range(len(results["documents"][0])):
        doc = results["documents"][0][i]
        dist = results["distances"][0][i]
        print(f"    [{i+1}] (距离={dist:.4f}) {doc[:70]}...")

    # --- 7. 更新和删除 ---
    print("\n" + "─" * 70)
    print("更新和删除操作")
    print("─" * 70)

    # 更新文档
    collection.update(
        ids=["doc_0"],
        documents=["Python 的引用计数（Reference Counting）是最基础的垃圾回收策略。对象的 ob_refcnt 字段记录被引用次数，归零时通过 tp_dealloc 立即释放内存。这是 CPython 的核心设计。"],
        metadatas=[{"source": "python_gc.md", "section": "引用计数", "language": "Python", "updated": True}],
    )
    print("  已更新 doc_0")

    # 删除文档
    collection.delete(ids=["doc_8"])  # 删除 Redis 那条（与主题不相关）
    print(f"  已删除 doc_8，剩余 {collection.count()} 条文档")

    # --- 8. 重新连接验证持久化 ---
    print("\n" + "─" * 70)
    print("持久化验证：重新创建客户端，数据是否还在？")
    print("─" * 70)

    client2 = chromadb.PersistentClient(path=persist_dir)
    collection2 = client2.get_collection("knowledge_base")
    print(f"  重新加载后文档数量：{collection2.count()}")

    results = collection2.query(query_texts=["Python 引用计数"], n_results=1)
    print(f"  查询「Python 引用计数」的 Top-1：")
    print(f"    {results['documents'][0][0][:80]}...")

    # --- 清理 ---
    shutil.rmtree(persist_dir)
    print(f"\n  已清理临时数据：{persist_dir}")

    # --- 总结 ---
    print("\n" + "=" * 70)
    print("总结")
    print("=" * 70)
    print("""
  ChromaDB 的核心 API：
    client = chromadb.PersistentClient(path="./db")  # 持久化客户端
    collection = client.create_collection("name")     # 创建集合
    collection.add(ids, documents, metadatas)          # 添加文档（自动嵌入）
    collection.query(query_texts, n_results, where)    # 语义搜索 + 过滤
    collection.update(ids, documents, metadatas)        # 更新文档
    collection.delete(ids)                             # 删除文档

  适用场景：原型开发、小规模 RAG（万级文档以内）
  生产环境建议使用 Qdrant、Milvus 或 pgvector
    """)


if __name__ == "__main__":
    main()
