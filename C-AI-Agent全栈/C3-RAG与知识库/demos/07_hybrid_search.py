"""
07_hybrid_search.py — 混合检索：向量搜索 + 关键词搜索(BM25) 结合

演示内容：
1. BM25 关键词检索（从零实现）
2. 向量语义检索（TF-IDF 嵌入）
3. 混合检索 + RRF 融合
4. 对比三种检索方式的效果差异

纯 Python + numpy 实现，不依赖外部服务。
运行：python3 07_hybrid_search.py
"""

import re
import math
import numpy as np
from collections import Counter
from typing import List, Tuple, Dict


# ============================================================
# BM25 关键词检索（从零实现）
# ============================================================
class BM25:
    """
    BM25（Best Matching 25）是经典的关键词检索算法。

    核心思想：
    - TF（词频）：词在文档中出现越多，文档越相关（但有饱和效应）
    - IDF（逆文档频率）：越稀有的词，区分度越高
    - 文档长度归一化：长文档天然包含更多词，需要惩罚

    公式：
    score(q, d) = Σ IDF(qi) × (tf(qi, d) × (k1 + 1)) / (tf(qi, d) + k1 × (1 - b + b × |d|/avgdl))

    参数：
    - k1：控制词频饱和速度（通常 1.2~2.0）
    - b：控制文档长度归一化强度（通常 0.75）
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.doc_lengths: List[int] = []
        self.avg_dl: float = 0
        self.doc_count: int = 0
        self.doc_freqs: Dict[str, int] = {}   # 每个词出现在多少篇文档中
        self.doc_tokens: List[List[str]] = []  # 每篇文档的分词结果
        self.idf: Dict[str, float] = {}

    def _tokenize(self, text: str) -> List[str]:
        """中英文混合分词"""
        return re.findall(r"[\u4e00-\u9fff]|[a-zA-Z]+|[0-9]+", text.lower())

    def fit(self, documents: List[str]):
        """索引文档集合"""
        self.doc_count = len(documents)
        self.doc_tokens = []
        self.doc_freqs = {}

        for doc in documents:
            tokens = self._tokenize(doc)
            self.doc_tokens.append(tokens)
            self.doc_lengths.append(len(tokens))

            # 统计文档频率（每个词在多少文档中出现）
            unique_tokens = set(tokens)
            for token in unique_tokens:
                self.doc_freqs[token] = self.doc_freqs.get(token, 0) + 1

        self.avg_dl = sum(self.doc_lengths) / self.doc_count if self.doc_count > 0 else 0

        # 计算 IDF
        for token, df in self.doc_freqs.items():
            # IDF 公式：log((N - df + 0.5) / (df + 0.5) + 1)
            self.idf[token] = math.log((self.doc_count - df + 0.5) / (df + 0.5) + 1)

    def score(self, query: str, doc_index: int) -> float:
        """计算 query 与指定文档的 BM25 分数"""
        query_tokens = self._tokenize(query)
        doc_tokens = self.doc_tokens[doc_index]
        doc_len = self.doc_lengths[doc_index]

        # 统计文档中每个词的词频
        tf_dict = Counter(doc_tokens)

        score = 0.0
        for qt in query_tokens:
            if qt not in self.idf:
                continue

            tf = tf_dict.get(qt, 0)
            idf = self.idf[qt]

            # BM25 公式
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / self.avg_dl)
            score += idf * numerator / denominator

        return score

    def search(self, query: str, top_k: int = 5) -> List[Tuple[int, float]]:
        """检索 Top-K 文档"""
        scores = [(i, self.score(query, i)) for i in range(self.doc_count)]
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


# ============================================================
# 向量语义检索（TF-IDF）
# ============================================================
class VectorSearch:
    """TF-IDF 向量语义检索"""

    def __init__(self):
        self.vocabulary = {}
        self.idf = None
        self.doc_vecs = None

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"[\u4e00-\u9fff]|[a-zA-Z]+|[0-9]+", text.lower())

    def fit(self, documents: List[str]):
        all_tokens = set()
        doc_token_sets = []
        for doc in documents:
            tokens = set(self._tokenize(doc))
            doc_token_sets.append(tokens)
            all_tokens.update(tokens)

        self.vocabulary = {t: i for i, t in enumerate(sorted(all_tokens))}
        df = np.zeros(len(self.vocabulary))
        for tokens in doc_token_sets:
            for t in tokens:
                if t in self.vocabulary:
                    df[self.vocabulary[t]] += 1
        self.idf = np.log((len(documents) + 1) / (df + 1)) + 1

        self.doc_vecs = np.array([self._embed(doc) for doc in documents])

    def _embed(self, text: str) -> np.ndarray:
        tokens = self._tokenize(text)
        counts = Counter(tokens)
        total = max(len(tokens), 1)
        vec = np.zeros(len(self.vocabulary))
        for t, c in counts.items():
            if t in self.vocabulary:
                vec[self.vocabulary[t]] = (c / total) * self.idf[self.vocabulary[t]]
        norm = np.linalg.norm(vec)
        return vec / norm if norm > 0 else vec

    def search(self, query: str, top_k: int = 5) -> List[Tuple[int, float]]:
        query_vec = self._embed(query)
        scores = np.dot(self.doc_vecs, query_vec)
        top_indices = np.argsort(scores)[::-1][:top_k]
        return [(int(idx), float(scores[idx])) for idx in top_indices]


# ============================================================
# 混合检索 + RRF 融合
# ============================================================
def reciprocal_rank_fusion(
    results_list: List[List[Tuple[int, float]]],
    k: int = 60,
    weights: List[float] = None,
) -> List[Tuple[int, float]]:
    """
    RRF（Reciprocal Rank Fusion）融合多路检索结果。

    公式：RRF_score(d) = Σ weight_i / (k + rank_i(d))

    其中：
    - k 是常数（通常 60），防止排名靠前的结果权重过大
    - rank_i(d) 是文档 d 在第 i 路检索中的排名（从 1 开始）
    - weight_i 是第 i 路检索的权重

    参数：
        results_list: 多路检索结果 [[(doc_idx, score), ...], ...]
        k: RRF 常数
        weights: 各路检索的权重，默认等权
    """
    if weights is None:
        weights = [1.0] * len(results_list)

    # 收集所有文档的 RRF 分数
    rrf_scores: Dict[int, float] = {}

    for results, weight in zip(results_list, weights):
        for rank, (doc_idx, _) in enumerate(results, 1):
            rrf_scores[doc_idx] = rrf_scores.get(doc_idx, 0) + weight / (k + rank)

    # 按 RRF 分数排序
    sorted_results = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_results


# ============================================================
# 知识库
# ============================================================
DOCUMENTS = [
    "Python 3.12 引入了新的垃圾回收优化，显著减少了 GC 暂停时间，特别是在多线程环境下表现更好。",
    "引用计数是 CPython 的主要内存管理机制，每个对象维护 ob_refcnt 字段记录引用次数。",
    "gc.collect() 函数可以手动触发 Python 的垃圾回收，gc.disable() 可以禁用自动 GC。",
    "循环引用是引用计数无法处理的情况，Python 使用标记-清除算法来检测和回收循环引用对象。",
    "分代回收将对象分为三代，新对象在第 0 代，存活越久代数越高，高代对象 GC 频率越低。",
    "Rust 使用所有权和借用检查器在编译期管理内存，完全不需要运行时垃圾回收器。",
    "RTX-4090 拥有 24GB GDDR6X 显存，16384 个 CUDA 核心，TDP 为 450W。",
    "PostgreSQL 的 pgvector 扩展支持向量相似度搜索，可以使用 SQL 语法进行 ANN 查询。",
    "FastAPI 基于 Starlette 和 Pydantic，支持异步请求处理和自动 OpenAPI 文档生成。",
    "Redis 7.0 引入了 Redis Functions，替代了 Lua 脚本，提供更好的持久化和集群支持。",
    "Docker 容器使用 Linux cgroups 限制 CPU 和内存资源，namespaces 实现进程隔离。",
    "Python 的 weakref 模块提供弱引用功能，弱引用不增加对象的引用计数，常用于缓存和观察者模式。",
    "内存泄漏排查可以使用 tracemalloc 模块，它能追踪 Python 中每块内存的分配来源。",
    "Python 3.13 计划引入 free-threaded 模式（no-GIL），允许多线程真正并行执行 Python 代码。",
    "Java 的 ZGC 是低延迟垃圾回收器，暂停时间不超过 10ms，适合大堆内存场景。",
]


def main():
    print("=" * 70)
    print("混合检索演示：向量搜索 + BM25 关键词搜索")
    print("=" * 70)

    # --- 构建索引 ---
    print("\n--- 构建索引 ---")

    bm25 = BM25(k1=1.5, b=0.75)
    bm25.fit(DOCUMENTS)
    print(f"  BM25 索引完成：{len(DOCUMENTS)} 篇文档")

    vector_search = VectorSearch()
    vector_search.fit(DOCUMENTS)
    print(f"  向量索引完成：维度 {len(vector_search.vocabulary)}")

    # --- 测试查询 ---
    test_queries = [
        # 场景 1：语义查询（向量检索擅长）
        "Python 怎样管理不再使用的内存？",
        # 场景 2：精确关键词查询（BM25 擅长）
        "RTX-4090 的显存和 CUDA 核心数量",
        # 场景 3：混合查询
        "Python gc.collect 手动垃圾回收",
        # 场景 4：概念性查询
        "哪些编程语言不需要垃圾回收？",
        # 场景 5：版本相关查询
        "Python 3.13 的 no-GIL 特性",
    ]

    for query in test_queries:
        print(f"\n{'=' * 70}")
        print(f"Q: {query}")
        print("=" * 70)

        # BM25 检索
        bm25_results = bm25.search(query, top_k=5)
        print(f"\n  【BM25 关键词检索】")
        for rank, (idx, score) in enumerate(bm25_results[:3], 1):
            print(f"    Top-{rank}: [{score:.4f}] {DOCUMENTS[idx][:60]}...")

        # 向量检索
        vec_results = vector_search.search(query, top_k=5)
        print(f"\n  【向量语义检索】")
        for rank, (idx, score) in enumerate(vec_results[:3], 1):
            print(f"    Top-{rank}: [{score:.4f}] {DOCUMENTS[idx][:60]}...")

        # 混合检索（RRF 融合）
        hybrid_results = reciprocal_rank_fusion(
            [bm25_results, vec_results],
            k=60,
            weights=[1.0, 1.0],  # 等权融合
        )
        print(f"\n  【混合检索（RRF 融合）】")
        for rank, (idx, score) in enumerate(hybrid_results[:3], 1):
            # 检查各路检索的贡献
            bm25_rank = next((r + 1 for r, (i, _) in enumerate(bm25_results) if i == idx), "-")
            vec_rank = next((r + 1 for r, (i, _) in enumerate(vec_results) if i == idx), "-")
            print(f"    Top-{rank}: [RRF={score:.4f}] (BM25排名={bm25_rank}, 向量排名={vec_rank})")
            print(f"           {DOCUMENTS[idx][:70]}...")

    # --- 权重调整对比 ---
    print(f"\n{'=' * 70}")
    print("权重调整对比：BM25 权重 vs 向量权重")
    print("=" * 70)

    query = "Python gc.collect 手动垃圾回收"
    bm25_results = bm25.search(query, top_k=5)
    vec_results = vector_search.search(query, top_k=5)

    weight_configs = [
        ([2.0, 1.0], "BM25 权重翻倍"),
        ([1.0, 1.0], "等权融合"),
        ([1.0, 2.0], "向量权重翻倍"),
    ]

    print(f"\n  Q: {query}\n")

    for weights, desc in weight_configs:
        hybrid = reciprocal_rank_fusion([bm25_results, vec_results], weights=weights)
        print(f"  {desc} (BM25={weights[0]}, Vec={weights[1]}):")
        for rank, (idx, score) in enumerate(hybrid[:3], 1):
            print(f"    Top-{rank}: [{score:.4f}] {DOCUMENTS[idx][:60]}...")
        print()

    # --- 总结 ---
    print("=" * 70)
    print("总结")
    print("=" * 70)
    print("""
  BM25 关键词检索：
    - 擅长精确匹配（产品型号、API 名称、版本号）
    - 不理解语义（"内存管理" 搜不到 "垃圾回收"）
    - 实现简单，无需嵌入模型

  向量语义检索：
    - 擅长语义理解（"管理内存" ≈ "垃圾回收"）
    - 对精确关键词匹配较弱（"RTX-4090" 可能匹配不准）
    - 需要嵌入模型

  混合检索（推荐）：
    - 同时使用 BM25 + 向量检索，RRF 融合结果
    - 兼顾精确匹配和语义理解
    - 几乎总能提升检索效果
    - 生产环境推荐 BM25:向量 = 0.3:0.7 或 0.4:0.6 作为起始配置

  RRF 融合的优势：
    - 无需归一化不同检索器的分数（只看排名）
    - 对异常分数不敏感
    - 超参数少（只有 k=60），鲁棒性好
    """)


if __name__ == "__main__":
    main()
