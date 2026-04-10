"""
02_embedding_basics.py — 嵌入向量原理演示

用 numpy 手动实现：
1. 词袋模型（Bag of Words）生成简单嵌入
2. 余弦相似度（Cosine Similarity）
3. 欧式距离（Euclidean Distance）
4. 内积（Dot Product）
5. 理解为什么余弦相似度是向量检索的首选

运行：python3 02_embedding_basics.py
依赖：numpy（pip3 install numpy）
"""

import numpy as np
from collections import Counter
from typing import List, Dict, Tuple


# ============================================================
# 简单的词袋嵌入（用于演示原理，非生产用途）
# ============================================================
class SimpleEmbedding:
    """
    一个极简的词袋（Bag of Words）嵌入器。

    真正的嵌入模型（如 BERT、BGE）使用深度学习捕捉语义，
    这里用词袋模型仅为演示向量运算的原理。
    """

    def __init__(self):
        self.vocabulary: Dict[str, int] = {}

    def _tokenize(self, text: str) -> List[str]:
        """简单分词：转小写，按非字母数字字符分割"""
        import re
        tokens = re.findall(r"[\u4e00-\u9fff]+|[a-zA-Z]+|[0-9]+", text.lower())
        return tokens

    def fit(self, documents: List[str]):
        """构建词汇表"""
        all_tokens = set()
        for doc in documents:
            all_tokens.update(self._tokenize(doc))
        self.vocabulary = {token: i for i, token in enumerate(sorted(all_tokens))}
        print(f"词汇表大小：{len(self.vocabulary)}")

    def embed(self, text: str) -> np.ndarray:
        """将文本转为词袋向量"""
        tokens = self._tokenize(text)
        token_counts = Counter(tokens)
        vector = np.zeros(len(self.vocabulary))
        for token, count in token_counts.items():
            if token in self.vocabulary:
                vector[self.vocabulary[token]] = count
        return vector

    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """批量嵌入"""
        return np.array([self.embed(text) for text in texts])


# ============================================================
# 向量距离/相似度计算
# ============================================================
def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """
    余弦相似度：衡量两个向量方向的一致性。

    公式：cos(θ) = (A · B) / (||A|| × ||B||)

    取值范围：[-1, 1]
      1  = 方向完全一致（最相似）
      0  = 正交（不相关）
     -1  = 方向完全相反

    在文本检索中，值通常在 [0, 1] 区间（因为词频不为负）。
    """
    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot_product / (norm_a * norm_b)


def euclidean_distance(a: np.ndarray, b: np.ndarray) -> float:
    """
    欧式距离（L2 距离）：衡量两个向量在空间中的绝对距离。

    公式：d = √(Σ(ai - bi)²)

    取值范围：[0, +∞)
    值越小 = 越相似

    缺点：受向量长度影响。同样语义的长文本和短文本，
    因为词频差异大，欧式距离可能很远。
    """
    return np.linalg.norm(a - b)


def dot_product(a: np.ndarray, b: np.ndarray) -> float:
    """
    内积（点积）：两个向量对应元素乘积之和。

    公式：A · B = Σ(ai × bi)

    当向量已归一化（||A|| = ||B|| = 1）时，内积 = 余弦相似度。
    某些向量数据库使用内积以获得更好的计算性能。
    """
    return np.dot(a, b)


# ============================================================
# 主函数
# ============================================================
def main():
    print("=" * 70)
    print("嵌入向量原理演示")
    print("=" * 70)

    # --- 1. 准备示例文本 ---
    documents = [
        "Python 的垃圾回收使用引用计数机制",
        "Python 通过引用计数来管理内存回收",       # 与第一句语义相似
        "Java 使用标记清除垃圾回收算法",            # 部分相关
        "机器学习需要大量的训练数据",               # 不相关
        "深度学习是机器学习的一个子领域",           # 与第四句相关
    ]

    query = "Python 如何回收不用的内存？"

    print("\n--- 文档列表 ---")
    for i, doc in enumerate(documents):
        print(f"  [{i}] {doc}")
    print(f"\n  查询：{query}")

    # --- 2. 构建词袋嵌入 ---
    print("\n" + "─" * 70)
    print("步骤一：构建词袋嵌入向量")
    print("─" * 70)

    embedder = SimpleEmbedding()
    embedder.fit(documents + [query])

    doc_vectors = embedder.embed_batch(documents)
    query_vector = embedder.embed(query)

    print(f"向量维度：{query_vector.shape[0]}")
    print(f"\n查询向量（前20维）：")
    print(f"  {query_vector[:20]}")

    # --- 3. 余弦相似度 ---
    print("\n" + "─" * 70)
    print("步骤二：用余弦相似度计算 Query 与各文档的相似程度")
    print("─" * 70)

    cos_scores = []
    for i, doc_vec in enumerate(doc_vectors):
        score = cosine_similarity(query_vector, doc_vec)
        cos_scores.append((i, score))
        print(f"  [{i}] 余弦相似度 = {score:.4f}  ← {documents[i]}")

    # 排序
    cos_scores.sort(key=lambda x: x[1], reverse=True)
    print(f"\n  排名（余弦相似度，从高到低）：")
    for rank, (i, score) in enumerate(cos_scores, 1):
        print(f"    第{rank}名：[{i}] {score:.4f}  {documents[i]}")

    # --- 4. 欧式距离 ---
    print("\n" + "─" * 70)
    print("步骤三：用欧式距离计算（值越小 = 越相似）")
    print("─" * 70)

    euc_scores = []
    for i, doc_vec in enumerate(doc_vectors):
        dist = euclidean_distance(query_vector, doc_vec)
        euc_scores.append((i, dist))
        print(f"  [{i}] 欧式距离 = {dist:.4f}  ← {documents[i]}")

    euc_scores.sort(key=lambda x: x[1])
    print(f"\n  排名（欧式距离，从小到大）：")
    for rank, (i, dist) in enumerate(euc_scores, 1):
        print(f"    第{rank}名：[{i}] {dist:.4f}  {documents[i]}")

    # --- 5. 内积 ---
    print("\n" + "─" * 70)
    print("步骤四：用内积计算")
    print("─" * 70)

    for i, doc_vec in enumerate(doc_vectors):
        dp = dot_product(query_vector, doc_vec)
        print(f"  [{i}] 内积 = {dp:.4f}  ← {documents[i]}")

    # --- 6. 归一化后的内积 = 余弦相似度 ---
    print("\n" + "─" * 70)
    print("步骤五：归一化后内积 = 余弦相似度（验证）")
    print("─" * 70)

    # L2 归一化
    query_norm = query_vector / (np.linalg.norm(query_vector) + 1e-10)
    print(f"  归一化后向量的模：{np.linalg.norm(query_norm):.6f}（应接近 1.0）")

    for i, doc_vec in enumerate(doc_vectors):
        doc_norm = doc_vec / (np.linalg.norm(doc_vec) + 1e-10)
        dp_normalized = dot_product(query_norm, doc_norm)
        cos_sim = cosine_similarity(query_vector, doc_vec)
        print(f"  [{i}] 归一化内积 = {dp_normalized:.4f},  余弦相似度 = {cos_sim:.4f}  "
              f"{'✓ 一致' if abs(dp_normalized - cos_sim) < 1e-6 else '✗ 不一致'}")

    # --- 7. 总结 ---
    print("\n" + "=" * 70)
    print("总结")
    print("=" * 70)
    print("""
  1. 嵌入（Embedding）= 把文本映射为固定维度的浮点向量
  2. 语义相近的文本，向量在空间中距离更近
  3. 余弦相似度是最常用的相似度度量（不受向量长度影响）
  4. 归一化后，内积 = 余弦相似度（很多向量数据库利用这一点加速）
  5. 本 demo 使用词袋模型，生产环境应使用深度学习嵌入模型
     （如 OpenAI text-embedding-3-small 或 BAAI/bge-large-zh）
    """)


if __name__ == "__main__":
    main()
