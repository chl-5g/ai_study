"""
06_rag_evaluation.py — RAG 评测

评测内容：
1. Hit Rate（命中率）：正确答案是否出现在 Top-K 中
2. MRR（Mean Reciprocal Rank）：正确答案在 Top-K 中的排名
3. 对比不同分块策略对检索效果的影响

纯 Python + numpy 实现，不依赖外部服务。
运行：python3 06_rag_evaluation.py
"""

import re
import numpy as np
from collections import Counter
from typing import List, Dict, Tuple


# ============================================================
# 嵌入器（复用 TF-IDF 方案）
# ============================================================
class TFIDFEmbedding:
    """简单 TF-IDF 嵌入器"""

    def __init__(self):
        self.vocabulary = {}
        self.idf = None

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"[\u4e00-\u9fff]|[a-zA-Z]+|[0-9]+", text.lower())

    def fit(self, documents: List[str]):
        all_tokens = set()
        doc_tokens = []
        for doc in documents:
            tokens = set(self._tokenize(doc))
            doc_tokens.append(tokens)
            all_tokens.update(tokens)

        self.vocabulary = {t: i for i, t in enumerate(sorted(all_tokens))}
        df = np.zeros(len(self.vocabulary))
        for tokens in doc_tokens:
            for t in tokens:
                if t in self.vocabulary:
                    df[self.vocabulary[t]] += 1
        self.idf = np.log((len(documents) + 1) / (df + 1)) + 1

    def embed(self, text: str) -> np.ndarray:
        tokens = self._tokenize(text)
        counts = Counter(tokens)
        total = max(len(tokens), 1)
        vec = np.zeros(len(self.vocabulary))
        for t, c in counts.items():
            if t in self.vocabulary:
                vec[self.vocabulary[t]] = (c / total) * self.idf[self.vocabulary[t]]
        norm = np.linalg.norm(vec)
        return vec / norm if norm > 0 else vec

    def embed_batch(self, texts: List[str]) -> np.ndarray:
        return np.array([self.embed(t) for t in texts])


# ============================================================
# 向量检索
# ============================================================
def vector_search(query_vec: np.ndarray, doc_vecs: np.ndarray, top_k: int = 5) -> List[Tuple[int, float]]:
    """返回 [(文档索引, 相似度分数), ...]"""
    scores = np.dot(doc_vecs, query_vec)
    top_indices = np.argsort(scores)[::-1][:top_k]
    return [(int(idx), float(scores[idx])) for idx in top_indices]


# ============================================================
# 评测指标
# ============================================================
def hit_rate(results: List[List[Tuple[int, float]]], ground_truths: List[List[int]], k: int = 5) -> float:
    """
    Hit Rate @ K：在 Top-K 结果中，正确答案至少出现一次的查询比例。

    参数：
        results: 每个查询的检索结果 [(doc_idx, score), ...]
        ground_truths: 每个查询的正确文档索引列表
        k: 取前 K 个结果

    返回：
        命中率 (0.0 ~ 1.0)
    """
    hits = 0
    for result, gt in zip(results, ground_truths):
        top_k_ids = [idx for idx, _ in result[:k]]
        if any(gt_id in top_k_ids for gt_id in gt):
            hits += 1
    return hits / len(results) if results else 0.0


def mrr(results: List[List[Tuple[int, float]]], ground_truths: List[List[int]], k: int = 5) -> float:
    """
    MRR @ K（Mean Reciprocal Rank）：正确答案首次出现的排名的倒数，取均值。

    例如：
        正确答案在第 1 位 → 1/1 = 1.0
        正确答案在第 2 位 → 1/2 = 0.5
        正确答案在第 3 位 → 1/3 = 0.33
        正确答案不在 Top-K 中 → 0

    MRR 越接近 1.0，说明正确答案排名越靠前。
    """
    reciprocal_ranks = []
    for result, gt in zip(results, ground_truths):
        top_k_ids = [idx for idx, _ in result[:k]]
        rr = 0.0
        for rank, doc_id in enumerate(top_k_ids, 1):
            if doc_id in gt:
                rr = 1.0 / rank
                break
        reciprocal_ranks.append(rr)
    return np.mean(reciprocal_ranks) if reciprocal_ranks else 0.0


def precision_at_k(results: List[List[Tuple[int, float]]], ground_truths: List[List[int]], k: int = 5) -> float:
    """
    Precision @ K：Top-K 结果中正确答案的比例。
    """
    precisions = []
    for result, gt in zip(results, ground_truths):
        top_k_ids = [idx for idx, _ in result[:k]]
        relevant = sum(1 for idx in top_k_ids if idx in gt)
        precisions.append(relevant / k)
    return np.mean(precisions) if precisions else 0.0


# ============================================================
# 分块策略
# ============================================================
def fixed_chunking(text: str, size: int = 200, overlap: int = 0) -> List[str]:
    """固定大小分块"""
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start:start + size])
        start += size - overlap
    return [c.strip() for c in chunks if c.strip()]


def paragraph_chunking(text: str) -> List[str]:
    """按段落分块"""
    paragraphs = text.split("\n\n")
    return [p.strip() for p in paragraphs if p.strip() and len(p.strip()) > 20]


def sentence_chunking(text: str, sentences_per_chunk: int = 3) -> List[str]:
    """按句子分块（每 N 句为一块）"""
    sentences = re.split(r"(?<=[。！？.!?])\s*", text)
    sentences = [s.strip() for s in sentences if s.strip()]

    chunks = []
    for i in range(0, len(sentences), sentences_per_chunk):
        chunk = " ".join(sentences[i:i + sentences_per_chunk])
        if chunk:
            chunks.append(chunk)
    return chunks


# ============================================================
# 测试数据
# ============================================================
KNOWLEDGE_TEXT = """
Python 的垃圾回收机制主要包括三个部分：引用计数、标记清除和分代回收。

引用计数是最基础的机制。每个 Python 对象内部都有一个 ob_refcnt 字段，记录被引用的次数。当引用计数归零时，对象会被立即回收，内存得到释放。这种机制简单高效，是 CPython 的核心设计。

引用计数的致命缺陷是无法处理循环引用。当 A 引用 B，同时 B 也引用 A 时，即使外部没有任何变量指向它们，两者的引用计数都不会归零。这会导致内存泄漏。

为了解决循环引用问题，Python 引入了标记清除算法。垃圾回收器会遍历所有容器对象（列表、字典、集合、类实例等），从根对象开始标记所有可达对象，然后清除不可达的对象。

分代回收是对标记清除的优化。Python 将对象分为三代：第 0 代存放新创建的对象，经过一次 GC 存活的对象被提升到第 1 代，再次存活则提升到第 2 代。高代对象被检查的频率更低，因为长期存活的对象通常会继续存活。

gc 模块提供了手动控制垃圾回收的接口。gc.collect() 可以手动触发一次完整的垃圾回收。gc.disable() 可以禁用自动垃圾回收，适用于对延迟敏感的场景。gc.get_threshold() 返回触发各代 GC 的阈值。

在实际开发中，大多数情况下不需要手动管理垃圾回收。但在以下场景需要注意：创建大量临时对象时、存在循环引用时、对延迟敏感的实时系统中。

Python 3.12 对垃圾回收器进行了优化，减少了 GC 暂停时间。特别是在多线程场景下，新的 GC 实现能更好地与线程调度协作。
"""

# 评测数据集：(问题, 正确答案应该包含的关键文档内容)
TEST_QUERIES = [
    {
        "query": "Python 的引用计数是什么？",
        "keywords": ["引用计数", "ob_refcnt", "归零", "回收"],
    },
    {
        "query": "什么是循环引用？怎么解决？",
        "keywords": ["循环引用", "标记清除", "A 引用 B"],
    },
    {
        "query": "Python 的分代回收是怎么工作的？",
        "keywords": ["分代", "三代", "第 0 代", "提升"],
    },
    {
        "query": "怎么手动控制 Python 的垃圾回收？",
        "keywords": ["gc 模块", "gc.collect", "gc.disable"],
    },
    {
        "query": "Python 3.12 的 GC 有什么改进？",
        "keywords": ["3.12", "暂停时间", "多线程"],
    },
]


def find_ground_truth(chunks: List[str], keywords: List[str]) -> List[int]:
    """
    根据关键词找到正确答案对应的文档块索引。
    如果一个块包含至少一半的关键词，就认为是正确答案。
    """
    gt = []
    threshold = max(1, len(keywords) // 2)
    for i, chunk in enumerate(chunks):
        matched = sum(1 for kw in keywords if kw in chunk)
        if matched >= threshold:
            gt.append(i)
    return gt


# ============================================================
# 主函数：评测不同分块策略
# ============================================================
def main():
    print("=" * 70)
    print("RAG 评测：对比不同分块策略的检索效果")
    print("=" * 70)

    strategies = {
        "固定200字符（无Overlap）": lambda t: fixed_chunking(t, size=200, overlap=0),
        "固定200字符（50字Overlap）": lambda t: fixed_chunking(t, size=200, overlap=50),
        "固定100字符（无Overlap）": lambda t: fixed_chunking(t, size=100, overlap=0),
        "按段落分块": paragraph_chunking,
        "按句子分块（每3句）": lambda t: sentence_chunking(t, sentences_per_chunk=3),
        "按句子分块（每2句）": lambda t: sentence_chunking(t, sentences_per_chunk=2),
    }

    all_results = {}

    for strategy_name, chunk_fn in strategies.items():
        print(f"\n{'─' * 70}")
        print(f"策略：{strategy_name}")
        print("─" * 70)

        # 1. 分块
        chunks = chunk_fn(KNOWLEDGE_TEXT)
        print(f"  块数量：{len(chunks)}")
        for i, c in enumerate(chunks[:3]):
            print(f"    块{i}: {c[:50]}... ({len(c)}字符)")

        # 2. 构建嵌入
        embedder = TFIDFEmbedding()
        all_texts = chunks + [q["query"] for q in TEST_QUERIES]
        embedder.fit(all_texts)
        doc_vecs = embedder.embed_batch(chunks)

        # 3. 对每个查询进行检索
        search_results = []
        ground_truths = []

        for tq in TEST_QUERIES:
            query_vec = embedder.embed(tq["query"])
            results = vector_search(query_vec, doc_vecs, top_k=5)
            search_results.append(results)

            # 找正确答案
            gt = find_ground_truth(chunks, tq["keywords"])
            ground_truths.append(gt)

        # 4. 计算评测指标
        for k in [1, 3, 5]:
            hr = hit_rate(search_results, ground_truths, k=k)
            m = mrr(search_results, ground_truths, k=k)
            p = precision_at_k(search_results, ground_truths, k=k)
            if k == 3:  # 主要展示 @3 的结果
                all_results[strategy_name] = {"hit_rate": hr, "mrr": m, "precision": p}
            print(f"  @{k}  Hit Rate={hr:.2%}  MRR={m:.4f}  Precision={p:.4f}")

    # --- 详细分析最佳策略 ---
    print("\n" + "=" * 70)
    print("详细检索结果（按段落分块）")
    print("=" * 70)

    chunks = paragraph_chunking(KNOWLEDGE_TEXT)
    embedder = TFIDFEmbedding()
    embedder.fit(chunks + [q["query"] for q in TEST_QUERIES])
    doc_vecs = embedder.embed_batch(chunks)

    for tq in TEST_QUERIES:
        print(f"\n  Q: {tq['query']}")
        query_vec = embedder.embed(tq["query"])
        results = vector_search(query_vec, doc_vecs, top_k=3)
        gt = find_ground_truth(chunks, tq["keywords"])

        for rank, (idx, score) in enumerate(results, 1):
            is_correct = idx in gt
            marker = " [CORRECT]" if is_correct else ""
            print(f"    Top-{rank}: [{score:.4f}]{marker} {chunks[idx][:60]}...")

    # --- 总结 ---
    print("\n" + "=" * 70)
    print("评测总结 (@3)")
    print("=" * 70)
    print(f"\n  {'策略':<30} {'Hit Rate':>10} {'MRR':>10} {'Precision':>10}")
    print("  " + "─" * 62)
    for name, metrics in all_results.items():
        print(f"  {name:<30} {metrics['hit_rate']:>9.2%} {metrics['mrr']:>10.4f} {metrics['precision']:>10.4f}")

    print("""
  解读：
    - Hit Rate：越高越好，表示正确答案被检索到的概率
    - MRR：越接近 1.0 越好，表示正确答案的排名越靠前
    - Precision：越高越好，表示返回结果中正确答案的比例

  通常结论：
    - 有 Overlap 比无 Overlap 好（边界信息不丢失）
    - 按段落/语义分块优于固定大小分块（保持语义完整性）
    - 块太小会丢失上下文，块太大会引入噪声
    - 最优 chunk_size 因数据而异，需要通过评测来确定
    """)


if __name__ == "__main__":
    main()
