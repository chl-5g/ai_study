"""
03_vector_search.py — 用 numpy/FAISS 实现简单的向量检索引擎

演示内容：
1. 纯 numpy 实现 Top-K 向量搜索（暴力搜索）
2. 如果安装了 FAISS，演示 FAISS 的高效向量搜索
3. 对比两种方式的结果

运行：python3 03_vector_search.py
依赖：numpy（必需），faiss-cpu（可选，pip3 install faiss-cpu）
"""

import numpy as np
import time
import re
from typing import List, Tuple, Dict
from collections import Counter


# ============================================================
# 简单的 TF-IDF 嵌入（比词袋更好一点）
# ============================================================
class TFIDFEmbedding:
    """
    简单的 TF-IDF 嵌入器。
    TF-IDF = 词频 × 逆文档频率，能区分出文档中的"关键词"。
    """

    def __init__(self):
        self.vocabulary: Dict[str, int] = {}
        self.idf: np.ndarray = None
        self.doc_count = 0

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"[\u4e00-\u9fff]|[a-zA-Z]+|[0-9]+", text.lower())

    def fit(self, documents: List[str]):
        """构建词汇表和 IDF"""
        self.doc_count = len(documents)
        all_tokens = set()
        doc_tokens = []

        for doc in documents:
            tokens = set(self._tokenize(doc))
            doc_tokens.append(tokens)
            all_tokens.update(tokens)

        self.vocabulary = {token: i for i, token in enumerate(sorted(all_tokens))}
        vocab_size = len(self.vocabulary)

        # 计算 IDF：log(文档总数 / 包含该词的文档数)
        df = np.zeros(vocab_size)
        for tokens in doc_tokens:
            for token in tokens:
                if token in self.vocabulary:
                    df[self.vocabulary[token]] += 1

        # 加 1 平滑防止除零
        self.idf = np.log((self.doc_count + 1) / (df + 1)) + 1

    def embed(self, text: str) -> np.ndarray:
        """将文本转为 TF-IDF 向量"""
        tokens = self._tokenize(text)
        token_counts = Counter(tokens)
        total = len(tokens) if tokens else 1

        vector = np.zeros(len(self.vocabulary))
        for token, count in token_counts.items():
            if token in self.vocabulary:
                tf = count / total
                vector[self.vocabulary[token]] = tf * self.idf[self.vocabulary[token]]

        # L2 归一化
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        return vector

    def embed_batch(self, texts: List[str]) -> np.ndarray:
        return np.array([self.embed(text) for text in texts])


# ============================================================
# 纯 numpy 向量搜索引擎
# ============================================================
class NumpyVectorStore:
    """
    用纯 numpy 实现的内存向量搜索引擎。
    使用暴力搜索（Brute-force），对小数据集足够用。
    """

    def __init__(self):
        self.vectors: np.ndarray = None      # (n, dim) 矩阵
        self.documents: List[str] = []       # 原始文本
        self.metadata: List[dict] = []       # 元数据

    def add(self, vectors: np.ndarray, documents: List[str], metadata: List[dict] = None):
        """添加向量和文档"""
        self.vectors = vectors
        self.documents = documents
        self.metadata = metadata or [{} for _ in documents]
        print(f"  已索引 {len(documents)} 条文档，向量维度 {vectors.shape[1]}")

    def search(self, query_vector: np.ndarray, top_k: int = 5) -> List[Tuple[int, float, str]]:
        """
        Top-K 向量搜索（余弦相似度）。

        因为向量已归一化，内积 = 余弦相似度。

        返回：[(文档索引, 相似度分数, 文档文本), ...]
        """
        # 计算 query 与所有文档的内积（因为已归一化，等于余弦相似度）
        scores = np.dot(self.vectors, query_vector)

        # 取 Top-K（部分排序，比全排序更快）
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            results.append((int(idx), float(scores[idx]), self.documents[idx]))
        return results


# ============================================================
# FAISS 向量搜索引擎（可选）
# ============================================================
class FAISSVectorStore:
    """
    用 FAISS 实现的向量搜索引擎。
    FAISS（Facebook AI Similarity Search）是 Meta 开源的高效向量检索库。

    支持多种索引类型：
    - IndexFlatL2：暴力搜索（精确，适合小数据集）
    - IndexFlatIP：内积搜索（归一化后等于余弦相似度）
    - IndexIVFFlat：倒排索引（近似搜索，适合大数据集）
    - IndexHNSW：HNSW 图索引（高召回率 + 高速度）
    """

    def __init__(self):
        self.index = None
        self.documents: List[str] = []
        self.dim = 0

    def add(self, vectors: np.ndarray, documents: List[str]):
        """添加向量"""
        import faiss

        self.dim = vectors.shape[1]
        self.documents = documents

        # 使用 IndexFlatIP（内积索引），归一化向量下等价于余弦相似度
        self.index = faiss.IndexFlatIP(self.dim)

        # FAISS 要求 float32
        vectors_f32 = vectors.astype(np.float32)
        self.index.add(vectors_f32)
        print(f"  FAISS 已索引 {self.index.ntotal} 条文档，维度 {self.dim}")

    def search(self, query_vector: np.ndarray, top_k: int = 5) -> List[Tuple[int, float, str]]:
        """Top-K 搜索"""
        query_f32 = query_vector.astype(np.float32).reshape(1, -1)
        scores, indices = self.index.search(query_f32, top_k)

        results = []
        for i in range(top_k):
            idx = int(indices[0][i])
            if idx >= 0:  # FAISS 用 -1 表示无结果
                results.append((idx, float(scores[0][i]), self.documents[idx]))
        return results


# ============================================================
# 知识库文档
# ============================================================
KNOWLEDGE_BASE = [
    "Python 使用引用计数作为主要的垃圾回收机制，每个对象维护一个引用计数器。",
    "当对象的引用计数归零时，Python 会立即回收该对象占用的内存。",
    "循环引用是引用计数的主要缺陷，两个对象互相引用导致计数永远不为零。",
    "Python 的标记清除算法专门用于处理循环引用问题，定期遍历容器对象。",
    "分代回收将对象分为三代，新对象在第 0 代，存活越久代数越高。",
    "gc 模块提供了手动控制垃圾回收的接口，如 gc.collect() 和 gc.disable()。",
    "Java 的垃圾回收器包括 G1、ZGC、Shenandoah 等，都是基于分代假说设计的。",
    "Rust 使用所有权系统在编译期管理内存，不需要垃圾回收器。",
    "JavaScript 的 V8 引擎使用分代垃圾回收，新生代用 Scavenge，老生代用 Mark-Sweep。",
    "内存泄漏是指程序分配了内存但不再使用且无法释放，导致可用内存持续减少。",
    "Redis 是一个基于内存的键值数据库，常用于缓存和消息队列。",
    "Docker 容器技术使用 Linux 的 cgroups 来限制容器的 CPU 和内存使用。",
    "PostgreSQL 支持通过 pgvector 扩展进行向量相似度搜索。",
    "机器学习模型的训练过程需要大量的 GPU 显存来存储梯度和激活值。",
    "FastAPI 是一个现代的 Python Web 框架，支持异步请求处理和自动 API 文档生成。",
]


def main():
    print("=" * 70)
    print("向量检索引擎演示")
    print("=" * 70)

    # --- 1. 构建嵌入 ---
    print("\n--- 构建 TF-IDF 嵌入 ---")
    embedder = TFIDFEmbedding()
    embedder.fit(KNOWLEDGE_BASE)
    doc_vectors = embedder.embed_batch(KNOWLEDGE_BASE)
    print(f"  文档数量：{len(KNOWLEDGE_BASE)}")
    print(f"  向量维度：{doc_vectors.shape[1]}")

    # --- 2. 纯 numpy 搜索 ---
    print("\n--- Numpy 向量搜索引擎 ---")
    np_store = NumpyVectorStore()
    np_store.add(doc_vectors, KNOWLEDGE_BASE)

    queries = [
        "Python 怎么管理内存？",
        "什么是循环引用？",
        "有哪些常用的数据库？",
    ]

    for query in queries:
        print(f"\n  查询：「{query}」")
        query_vec = embedder.embed(query)

        start = time.perf_counter()
        results = np_store.search(query_vec, top_k=3)
        elapsed = (time.perf_counter() - start) * 1000

        for rank, (idx, score, doc) in enumerate(results, 1):
            print(f"    Top-{rank}: [{score:.4f}] {doc}")
        print(f"    耗时：{elapsed:.3f} ms")

    # --- 3. FAISS 搜索（如果可用） ---
    try:
        import faiss
        print("\n" + "─" * 70)
        print("FAISS 向量搜索引擎（已安装 faiss-cpu）")
        print("─" * 70)

        faiss_store = FAISSVectorStore()
        faiss_store.add(doc_vectors, KNOWLEDGE_BASE)

        for query in queries:
            print(f"\n  查询：「{query}」")
            query_vec = embedder.embed(query)

            start = time.perf_counter()
            results = faiss_store.search(query_vec, top_k=3)
            elapsed = (time.perf_counter() - start) * 1000

            for rank, (idx, score, doc) in enumerate(results, 1):
                print(f"    Top-{rank}: [{score:.4f}] {doc}")
            print(f"    耗时：{elapsed:.3f} ms")

    except ImportError:
        print("\n" + "─" * 70)
        print("FAISS 未安装，跳过 FAISS 演示")
        print("安装命令：pip3 install faiss-cpu")
        print("─" * 70)

    # --- 4. 性能对比（大数据量模拟） ---
    print("\n" + "─" * 70)
    print("性能模拟：10,000 条随机向量的搜索耗时")
    print("─" * 70)

    dim = 256
    n_docs = 10000
    np.random.seed(42)

    # 生成随机向量并归一化
    random_vectors = np.random.randn(n_docs, dim).astype(np.float32)
    norms = np.linalg.norm(random_vectors, axis=1, keepdims=True)
    random_vectors = random_vectors / norms
    random_query = np.random.randn(dim).astype(np.float32)
    random_query = random_query / np.linalg.norm(random_query)

    fake_docs = [f"文档_{i}" for i in range(n_docs)]

    # Numpy 暴力搜索
    np_store2 = NumpyVectorStore()
    np_store2.add(random_vectors, fake_docs)

    start = time.perf_counter()
    for _ in range(100):
        np_store2.search(random_query, top_k=5)
    np_time = (time.perf_counter() - start) / 100 * 1000
    print(f"\n  Numpy 暴力搜索：{np_time:.3f} ms / 次（{n_docs} 条, {dim} 维）")

    try:
        import faiss
        faiss_store2 = FAISSVectorStore()
        faiss_store2.add(random_vectors, fake_docs)

        start = time.perf_counter()
        for _ in range(100):
            faiss_store2.search(random_query, top_k=5)
        faiss_time = (time.perf_counter() - start) / 100 * 1000
        print(f"  FAISS 搜索    ：{faiss_time:.3f} ms / 次（{n_docs} 条, {dim} 维）")
        print(f"  FAISS 加速比  ：{np_time / faiss_time:.1f}x")
    except ImportError:
        pass

    print("\n" + "=" * 70)
    print("总结")
    print("=" * 70)
    print("""
  1. 向量搜索的本质：计算 Query 向量与所有文档向量的距离，返回最近的 K 个
  2. 暴力搜索（Brute-force）精确但慢，复杂度 O(n × d)
  3. FAISS 等专用库使用 ANN（近似最近邻）算法加速，牺牲少量精度换取巨大速度提升
  4. 生产环境中，10 万条以下用暴力搜索可接受；百万级以上必须用 ANN 索引
    """)


if __name__ == "__main__":
    main()
