"""
01_text_chunking.py — 文档分块策略实战

演示三种常见的文本分块方法：
1. 固定大小分块（Fixed-size Chunking）
2. 递归字符分割（Recursive Character Splitting）
3. 按语义分块（Semantic Chunking）— 基于简单的句子相似度

纯 Python + numpy 实现，不依赖外部服务。
运行：python3 01_text_chunking.py
"""

import re
from typing import List, Tuple

# ============================================================
# 示例文档（用于演示分块效果）
# ============================================================
SAMPLE_TEXT = """
# Python 垃圾回收机制

## 引用计数

Python 的主要垃圾回收机制是引用计数（Reference Counting）。每个对象都维护一个引用计数器，
当引用计数归零时，对象立即被回收。这种机制简单高效，能及时释放不再使用的内存。

引用计数的缺点是无法处理循环引用。例如，两个对象互相引用对方，即使外部不再使用它们，
引用计数也不会归零，导致内存泄漏。

## 标记-清除

为了解决循环引用问题，Python 引入了标记-清除（Mark-and-Sweep）算法。
垃圾回收器会定期遍历所有容器对象（列表、字典、类实例等），标记从根对象可达的所有对象，
然后清除不可达的对象。

标记-清除算法会暂停程序执行（Stop-the-World），因此频繁触发会影响性能。

## 分代回收

Python 使用分代回收（Generational GC）来优化标记-清除的效率。
对象被分为三代（Generation 0、1、2），新创建的对象在第 0 代。

如果一个对象在一次垃圾回收中存活下来，它会被提升到下一代。
高代的对象被回收的频率更低，因为长期存活的对象通常会继续存活。
这种策略基于"弱分代假说"——大多数对象的生命周期很短。

## 手动控制

通过 gc 模块可以手动控制垃圾回收：
- gc.collect() 强制执行一次垃圾回收
- gc.disable() 禁用自动垃圾回收
- gc.get_threshold() 获取分代回收的阈值
- gc.set_threshold() 设置分代回收的阈值

在对延迟敏感的场景（如游戏、实时系统），可以在空闲时手动触发垃圾回收，
避免在关键时刻被 GC 暂停。
""".strip()


# ============================================================
# 方法一：固定大小分块
# ============================================================
def fixed_size_chunking(text: str, chunk_size: int = 200, overlap: int = 50) -> List[str]:
    """
    固定大小分块：按字符数将文本切成等长片段。

    参数：
        text: 原始文本
        chunk_size: 每个块的最大字符数
        overlap: 相邻块的重叠字符数

    返回：
        分块后的文本列表
    """
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        # 下一块从 (start + chunk_size - overlap) 开始
        start += chunk_size - overlap
    return chunks


# ============================================================
# 方法二：递归字符分割
# ============================================================
def recursive_character_splitting(
    text: str,
    chunk_size: int = 300,
    overlap: int = 50,
    separators: List[str] = None,
) -> List[str]:
    """
    递归字符分割：按优先级尝试不同分隔符分割文本。

    优先在段落边界分割 (\\n\\n)，其次换行 (\\n)，
    再其次句号 (。/.)，最后空格，最后逐字符。

    参数：
        text: 原始文本
        chunk_size: 每个块的最大字符数
        overlap: 重叠字符数
        separators: 分隔符优先级列表
    """
    if separators is None:
        separators = ["\n\n", "\n", "。", ".", " ", ""]

    chunks = []

    def _split(text: str, seps: List[str]) -> List[str]:
        """递归分割核心逻辑"""
        if not text:
            return []

        # 如果文本已经小于 chunk_size，直接返回
        if len(text) <= chunk_size:
            return [text]

        # 找到第一个能有效分割的分隔符
        sep = seps[0]
        remaining_seps = seps[1:] if len(seps) > 1 else [""]

        if sep == "":
            # 最后手段：逐字符切割
            result = []
            for i in range(0, len(text), chunk_size - overlap):
                result.append(text[i : i + chunk_size])
            return result

        # 用当前分隔符分割
        parts = text.split(sep)

        # 合并小片段，直到接近 chunk_size
        result = []
        current = ""
        for part in parts:
            candidate = current + sep + part if current else part
            if len(candidate) <= chunk_size:
                current = candidate
            else:
                if current:
                    result.append(current)
                # 如果单个 part 还是太大，递归用下一级分隔符分割
                if len(part) > chunk_size:
                    result.extend(_split(part, remaining_seps))
                else:
                    current = part
                    continue
                current = ""
        if current:
            result.append(current)
        return result

    raw_chunks = _split(text, separators)

    # 添加 Overlap
    if overlap > 0 and len(raw_chunks) > 1:
        overlapped = [raw_chunks[0]]
        for i in range(1, len(raw_chunks)):
            prev = raw_chunks[i - 1]
            # 取前一个块的最后 overlap 个字符作为重叠前缀
            overlap_text = prev[-overlap:] if len(prev) >= overlap else prev
            overlapped.append(overlap_text + raw_chunks[i])
        return overlapped

    return raw_chunks


# ============================================================
# 方法三：按语义分块（简化版）
# ============================================================
def semantic_chunking(text: str, similarity_threshold: float = 0.3) -> List[str]:
    """
    按语义分块：基于句子间的"词汇重叠度"来判断语义变化点。

    真正的语义分块需要嵌入模型计算句子向量相似度，
    这里用 Jaccard 相似度（词汇重叠）作为简化替代。

    当相邻句子的相似度低于阈值时，在此处分割。

    参数：
        text: 原始文本
        similarity_threshold: 分割阈值，越低越容易分割
    """

    def _split_sentences(text: str) -> List[str]:
        """将文本分割为句子"""
        # 按中英文句号、换行等分割
        sentences = re.split(r"(?<=[。！？.!?\n])\s*", text)
        return [s.strip() for s in sentences if s.strip()]

    def _jaccard_similarity(s1: str, s2: str) -> float:
        """计算两个句子的 Jaccard 词汇相似度"""
        # 简单分词：按非字母数字字符分割
        words1 = set(re.findall(r"\w+", s1.lower()))
        words2 = set(re.findall(r"\w+", s2.lower()))
        if not words1 or not words2:
            return 0.0
        intersection = words1 & words2
        union = words1 | words2
        return len(intersection) / len(union)

    sentences = _split_sentences(text)
    if not sentences:
        return []

    # 计算相邻句子的相似度，找到语义变化点
    chunks = []
    current_chunk = [sentences[0]]

    for i in range(1, len(sentences)):
        sim = _jaccard_similarity(sentences[i - 1], sentences[i])
        if sim < similarity_threshold:
            # 语义变化点，开始新的块
            chunks.append("\n".join(current_chunk))
            current_chunk = [sentences[i]]
        else:
            current_chunk.append(sentences[i])

    if current_chunk:
        chunks.append("\n".join(current_chunk))

    return chunks


# ============================================================
# Markdown 专用分块（按标题层级）
# ============================================================
def markdown_chunking(text: str) -> List[Tuple[str, str]]:
    """
    Markdown 专用分块：按标题层级分割。

    返回：
        [(标题, 内容), ...] 的列表
    """
    # 匹配 Markdown 标题
    pattern = r"^(#{1,6})\s+(.+)$"
    lines = text.split("\n")

    chunks = []
    current_title = "（无标题）"
    current_content = []

    for line in lines:
        match = re.match(pattern, line)
        if match:
            # 遇到新标题，保存之前的块
            if current_content:
                content_text = "\n".join(current_content).strip()
                if content_text:
                    chunks.append((current_title, content_text))
            level = len(match.group(1))
            title = "#" * level + " " + match.group(2)
            current_title = title
            current_content = []
        else:
            current_content.append(line)

    # 保存最后一个块
    if current_content:
        content_text = "\n".join(current_content).strip()
        if content_text:
            chunks.append((current_title, content_text))

    return chunks


# ============================================================
# 主函数：对比展示各种分块策略
# ============================================================
def main():
    print("=" * 70)
    print("文档分块策略实战演示")
    print("=" * 70)
    print(f"\n原始文档长度：{len(SAMPLE_TEXT)} 字符")

    # --- 固定大小分块 ---
    print("\n" + "─" * 70)
    print("【方法一】固定大小分块 (chunk_size=200, overlap=50)")
    print("─" * 70)
    chunks = fixed_size_chunking(SAMPLE_TEXT, chunk_size=200, overlap=50)
    for i, chunk in enumerate(chunks):
        print(f"\n  块 {i + 1} ({len(chunk)} 字符):")
        # 只显示前 80 个字符
        preview = chunk[:80].replace("\n", "↵")
        print(f"    {preview}...")

    print(f"\n  共 {len(chunks)} 个块")

    # --- 递归字符分割 ---
    print("\n" + "─" * 70)
    print("【方法二】递归字符分割 (chunk_size=300, overlap=50)")
    print("─" * 70)
    chunks = recursive_character_splitting(SAMPLE_TEXT, chunk_size=300, overlap=50)
    for i, chunk in enumerate(chunks):
        print(f"\n  块 {i + 1} ({len(chunk)} 字符):")
        preview = chunk[:80].replace("\n", "↵")
        print(f"    {preview}...")

    print(f"\n  共 {len(chunks)} 个块")

    # --- 语义分块 ---
    print("\n" + "─" * 70)
    print("【方法三】语义分块 (similarity_threshold=0.3)")
    print("─" * 70)
    chunks = semantic_chunking(SAMPLE_TEXT, similarity_threshold=0.3)
    for i, chunk in enumerate(chunks):
        print(f"\n  块 {i + 1} ({len(chunk)} 字符):")
        preview = chunk[:80].replace("\n", "↵")
        print(f"    {preview}...")

    print(f"\n  共 {len(chunks)} 个块")

    # --- Markdown 专用分块 ---
    print("\n" + "─" * 70)
    print("【方法四】Markdown 专用分块（按标题层级）")
    print("─" * 70)
    chunks = markdown_chunking(SAMPLE_TEXT)
    for i, (title, content) in enumerate(chunks):
        print(f"\n  块 {i + 1}  [{title}] ({len(content)} 字符):")
        preview = content[:80].replace("\n", "↵")
        print(f"    {preview}...")

    print(f"\n  共 {len(chunks)} 个块")

    # --- 对比总结 ---
    print("\n" + "=" * 70)
    print("对比总结")
    print("=" * 70)
    print("""
  固定大小分块：实现最简单，但会在语句中间截断
  递归字符分割：尽量在自然边界分割，LangChain 默认策略
  语义分块    ：块内语义一致性最高，但需要计算句子相似度
  Markdown分块：适合结构化文档，按章节自然分割
    """)


if __name__ == "__main__":
    main()
