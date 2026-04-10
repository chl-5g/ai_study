#!/usr/bin/env python3
"""
04_streaming_output.py — 流式输出（SSE）演示

演示内容：
1. 非流式 vs 流式输出的区别
2. Ollama 原生 API 流式输出
3. OpenAI 兼容 API 的 SSE 流式输出
4. Mock 数据模拟流式效果（无服务时）

核心概念：
- SSE（Server-Sent Events）：服务器向客户端推送数据的协议
- 流式输出让用户看到"逐字打印"效果，改善等待体验
- 首 Token 延迟（TTFT）：从请求到第一个 Token 返回的时间

依赖：requests
运行：python3 04_streaming_output.py
"""

import json
import time
import sys
import requests

# ============================================================
# 配置
# ============================================================
OLLAMA_URL = "http://localhost:11434"
MODEL = "qwen2.5:7b"


def check_ollama():
    """检查 Ollama 是否可用"""
    try:
        resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        return resp.status_code == 200
    except (requests.ConnectionError, requests.Timeout):
        return False


# ============================================================
# 演示 1：非流式 vs 流式的区别
# ============================================================
def demo_comparison(has_ollama):
    """对比非流式和流式输出的体验差异"""
    print(f"\n{'='*60}")
    print("演示 1：非流式 vs 流式输出对比")
    print(f"{'='*60}")

    prompt = "用 3 句话介绍 Python 语言的特点"

    if not has_ollama:
        print("\n  Ollama 不可用，使用 mock 数据演示...\n")
        demo_mock_comparison()
        return

    # ---- 非流式 ----
    print(f"\n  提问: {prompt}")
    print(f"\n  [非流式] 等待完整响应...")
    start = time.time()

    resp = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={"model": MODEL, "prompt": prompt, "stream": False,
              "options": {"num_predict": 200}},
        timeout=60
    )
    elapsed = time.time() - start
    data = resp.json()
    content = data.get("response", "")

    print(f"  [非流式] 等待 {elapsed:.2f}s 后一次性输出:")
    print(f"  {content}")

    # ---- 流式 ----
    print(f"\n  [流式] 逐 Token 输出:")
    start = time.time()
    first_token_time = None

    resp = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={"model": MODEL, "prompt": prompt, "stream": True,
              "options": {"num_predict": 200}},
        stream=True,
        timeout=60
    )

    print("  ", end="", flush=True)
    token_count = 0
    for line in resp.iter_lines():
        if line:
            chunk = json.loads(line)
            text = chunk.get("response", "")
            if text:
                if first_token_time is None:
                    first_token_time = time.time() - start
                print(text, end="", flush=True)
                token_count += 1

    elapsed = time.time() - start
    print()
    print(f"\n  [流式] 统计:")
    print(f"    首 Token 延迟 (TTFT): {first_token_time:.2f}s")
    print(f"    总耗时: {elapsed:.2f}s")
    print(f"    Token 数: {token_count}")
    if token_count > 0 and elapsed > 0:
        print(f"    生成速度: {token_count / elapsed:.1f} tokens/s")


def demo_mock_comparison():
    """使用 mock 数据演示流式效果"""
    mock_text = "Python 是一种解释型、面向对象的高级编程语言。它语法简洁优雅，拥有丰富的标准库和第三方生态。Python 广泛应用于 Web 开发、数据科学、人工智能等领域。"

    # 非流式模拟
    print("  [非流式模拟] 等待 2 秒后一次性输出...")
    time.sleep(1)
    print(f"  {mock_text}")

    # 流式模拟
    print(f"\n  [流式模拟] 逐字输出（模拟 Token 流）:")
    print("  ", end="", flush=True)
    for char in mock_text:
        print(char, end="", flush=True)
        time.sleep(0.05)  # 模拟 Token 间隔
    print()


# ============================================================
# 演示 2：Ollama 原生 API 流式输出
# ============================================================
def demo_ollama_stream(has_ollama):
    """Ollama /api/generate 的流式输出细节"""
    print(f"\n{'='*60}")
    print("演示 2：Ollama 原生 API 流式输出（逐 chunk 解析）")
    print(f"{'='*60}")

    if not has_ollama:
        print("\n  Ollama 不可用，展示响应格式说明...\n")
        print("  Ollama 流式响应格式（每行一个 JSON）：")
        print('  {"model":"qwen2.5:7b","response":"你","done":false}')
        print('  {"model":"qwen2.5:7b","response":"好","done":false}')
        print('  {"model":"qwen2.5:7b","response":"！","done":false}')
        print('  {"model":"qwen2.5:7b","response":"","done":true,'
              '"total_duration":1234567890,"eval_count":3}')
        print("\n  done=true 的最后一个 chunk 包含完整的统计信息。")
        return

    prompt = "什么是 API？一句话回答"
    print(f"\n  提问: {prompt}")
    print(f"  解析每个 chunk:\n")

    resp = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={"model": MODEL, "prompt": prompt, "stream": True,
              "options": {"num_predict": 100}},
        stream=True,
        timeout=60
    )

    chunk_num = 0
    for line in resp.iter_lines():
        if line:
            chunk = json.loads(line)
            chunk_num += 1
            text = chunk.get("response", "")
            done = chunk.get("done", False)

            if not done:
                # 显示前几个和最后一个 chunk 的详细信息
                if chunk_num <= 5:
                    print(f"  chunk #{chunk_num:3d}: "
                          f"response={repr(text):10s}  done={done}")
                elif chunk_num == 6:
                    print(f"  ... (省略中间 chunks) ...")
            else:
                print(f"  chunk #{chunk_num:3d}: "
                      f"response={repr(text):10s}  done={done}")
                # 打印统计信息
                duration = chunk.get("total_duration", 0) / 1e9
                eval_count = chunk.get("eval_count", 0)
                print(f"\n  统计: 总耗时={duration:.2f}s, "
                      f"生成 Token 数={eval_count}")


# ============================================================
# 演示 3：OpenAI 兼容 API 的 SSE 流式输出
# ============================================================
def demo_openai_sse(has_ollama):
    """
    OpenAI 兼容 API 的 SSE 格式解析

    SSE 协议要点：
    - 每行以 "data: " 前缀开头
    - 数据是 JSON 格式
    - 增量内容在 choices[0].delta.content 中
    - 结束标记是 "data: [DONE]"
    """
    print(f"\n{'='*60}")
    print("演示 3：OpenAI 兼容 API 的 SSE 流式输出")
    print(f"{'='*60}")

    if not has_ollama:
        print("\n  服务不可用，展示 SSE 格式说明...\n")
        print("  SSE（Server-Sent Events）响应格式：")
        print()
        print('  data: {"id":"chatcmpl-123","choices":[{"delta":{"role":"assistant"},"index":0}]}')
        print('  data: {"id":"chatcmpl-123","choices":[{"delta":{"content":"你"},"index":0}]}')
        print('  data: {"id":"chatcmpl-123","choices":[{"delta":{"content":"好"},"index":0}]}')
        print('  data: {"id":"chatcmpl-123","choices":[{"delta":{"content":"！"},"index":0}]}')
        print('  data: [DONE]')
        print()
        print("  解析要点：")
        print("  1. 去掉 'data: ' 前缀")
        print("  2. 解析 JSON，读取 choices[0].delta.content")
        print("  3. 遇到 '[DONE]' 停止")
        return

    prompt = "HTTP 状态码 404 是什么意思？简单回答"
    url = f"{OLLAMA_URL}/v1/chat/completions"

    print(f"\n  提问: {prompt}")
    print(f"  URL: {url}")
    print(f"\n  SSE 数据流:\n")

    resp = requests.post(
        url,
        headers={"Content-Type": "application/json"},
        json={
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
            "max_tokens": 100,
        },
        stream=True,
        timeout=60
    )

    chunk_count = 0
    full_text = ""

    for line in resp.iter_lines(decode_unicode=True):
        if not line:
            continue

        if not line.startswith("data: "):
            continue

        data_str = line[6:]

        if data_str.strip() == "[DONE]":
            print(f"  {line}  ← 结束标记")
            break

        chunk_count += 1
        try:
            chunk = json.loads(data_str)
            delta = chunk["choices"][0].get("delta", {})
            content = delta.get("content", "")
            full_text += content

            # 只显示前 5 个和最后几个 chunk 的原始数据
            if chunk_count <= 5:
                print(f"  {line[:100]}{'...' if len(line) > 100 else ''}")
                print(f"    → delta.content = {repr(content)}")
        except (json.JSONDecodeError, KeyError, IndexError):
            pass

    print(f"\n  拼接结果: {full_text}")
    print(f"  总 chunk 数: {chunk_count}")


# ============================================================
# 演示 4：流式输出的实际应用模式
# ============================================================
def demo_practical_patterns():
    """展示流式输出在实际应用中的常见模式"""
    print(f"\n{'='*60}")
    print("演示 4：流式输出实用模式")
    print(f"{'='*60}")

    print("""
  1. 基本模式 — 逐字打印：
     for chunk in stream:
         print(chunk.content, end="", flush=True)

  2. 缓冲模式 — 按句子/段落输出：
     buffer = ""
     for chunk in stream:
         buffer += chunk.content
         if "。" in buffer or "\\n" in buffer:
             print(buffer, end="", flush=True)
             buffer = ""

  3. 回调模式 — Web 应用中常用：
     async def on_token(token: str):
         await websocket.send(token)

     async for chunk in stream:
         await on_token(chunk.content)

  4. 超时控制 — 防止流式请求挂死：
     start = time.time()
     for chunk in stream:
         if time.time() - start > TIMEOUT:
             break
         process(chunk)

  5. Token 计数 — 流式中实时统计：
     token_count = 0
     for chunk in stream:
         token_count += 1
         progress = f"[{token_count} tokens]"
         print(f"\\r{progress} {chunk.content}", end="")

  关键指标：
  - TTFT (Time To First Token): 首 Token 延迟，影响用户感知速度
  - TPS (Tokens Per Second): 生成速度，取决于模型和硬件
  - 流式不影响总 Token 消耗和计费，但改善用户体验
""")


# ============================================================
# 主程序
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("流式输出（SSE）演示")
    print("=" * 60)

    has_ollama = check_ollama()
    if has_ollama:
        print(f"\n  Ollama 可用，将进行实际流式调用")
    else:
        print(f"\n  Ollama 不可用，将使用 mock 数据和格式说明")
        print("  启动 Ollama 后重新运行可看到真实流式效果")

    demo_comparison(has_ollama)
    demo_ollama_stream(has_ollama)
    demo_openai_sse(has_ollama)
    demo_practical_patterns()

    print(f"\n{'='*60}")
    print("演示完成！")
    print("=" * 60)
