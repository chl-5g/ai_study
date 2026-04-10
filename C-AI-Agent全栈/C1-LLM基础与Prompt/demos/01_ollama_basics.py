#!/usr/bin/env python3
"""
01_ollama_basics.py — Ollama 本地模型调用示例

演示内容：
1. 检测 Ollama 服务是否可用
2. 列出已下载的模型
3. 普通（非流式）调用
4. 流式输出调用
5. 对话模式（多轮消息）

依赖：requests（标准第三方库）
运行：python3 01_ollama_basics.py
"""

import requests
import json
import sys

# ============================================================
# 配置
# ============================================================
OLLAMA_BASE_URL = "http://localhost:11434"
# 默认使用的模型，可根据实际情况修改
DEFAULT_MODEL = "qwen2.5:7b"


def check_ollama_available():
    """检查 Ollama 服务是否在运行"""
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        resp.raise_for_status()
        return True
    except (requests.ConnectionError, requests.Timeout, requests.HTTPError):
        return False


def list_models():
    """列出 Ollama 已下载的模型"""
    resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=10)
    data = resp.json()
    models = data.get("models", [])
    if not models:
        print("  (没有已下载的模型，请先运行: ollama pull qwen2.5:7b)")
        return []

    print(f"  共 {len(models)} 个模型：")
    for m in models:
        name = m.get("name", "unknown")
        size_gb = m.get("size", 0) / (1024 ** 3)
        print(f"    - {name}  ({size_gb:.1f} GB)")
    return [m["name"] for m in models]


def get_available_model(models):
    """从已有模型中选择一个可用的模型"""
    # 优先使用默认模型
    for m in models:
        if DEFAULT_MODEL in m:
            return m
    # 否则用第一个
    return models[0] if models else None


def demo_generate(model):
    """
    演示 /api/generate 接口 —— 非流式调用
    这是最基础的文本生成接口
    """
    print(f"\n{'='*60}")
    print(f"演示 1：普通调用（/api/generate, stream=false）")
    print(f"{'='*60}")

    payload = {
        "model": model,
        "prompt": "用一句话解释什么是 Python 的装饰器？",
        "stream": False,  # 关闭流式，等待完整响应
        "options": {
            "temperature": 0.7,   # 温度参数，控制随机性
            "top_p": 0.9,         # Top-p 采样
            "num_predict": 200,   # 最大生成 Token 数
        }
    }

    print(f"  模型: {model}")
    print(f"  提示: {payload['prompt']}")
    print(f"  参数: temperature={payload['options']['temperature']}, "
          f"top_p={payload['options']['top_p']}")
    print()

    resp = requests.post(
        f"{OLLAMA_BASE_URL}/api/generate",
        json=payload,
        timeout=60
    )
    data = resp.json()

    # 解析响应
    print(f"  回答: {data.get('response', '(空)')}")
    print(f"  耗时: {data.get('total_duration', 0) / 1e9:.2f} 秒")
    print(f"  生成 Token 数: {data.get('eval_count', 'N/A')}")


def demo_generate_stream(model):
    """
    演示 /api/generate 接口 —— 流式调用
    流式输出可以实现"逐字打印"效果
    """
    print(f"\n{'='*60}")
    print(f"演示 2：流式输出（/api/generate, stream=true）")
    print(f"{'='*60}")

    payload = {
        "model": model,
        "prompt": "简单解释一下 HTTP 和 HTTPS 的区别",
        "stream": True,   # 开启流式输出
        "options": {
            "temperature": 0.7,
            "num_predict": 200,
        }
    }

    print(f"  提示: {payload['prompt']}")
    print(f"  回答: ", end="", flush=True)

    # 流式请求：逐行读取响应
    resp = requests.post(
        f"{OLLAMA_BASE_URL}/api/generate",
        json=payload,
        stream=True,    # requests 的 stream 参数，逐块读取
        timeout=60
    )

    total_tokens = 0
    for line in resp.iter_lines():
        if line:
            chunk = json.loads(line)
            # 每个 chunk 包含一小段文本
            text = chunk.get("response", "")
            print(text, end="", flush=True)  # 逐字打印，不换行

            # 最后一个 chunk 的 done=True，包含统计信息
            if chunk.get("done", False):
                total_tokens = chunk.get("eval_count", 0)

    print()  # 换行
    print(f"  (共生成 {total_tokens} tokens)")


def demo_chat(model):
    """
    演示 /api/chat 接口 —— 对话模式
    支持 system/user/assistant 多轮消息
    """
    print(f"\n{'='*60}")
    print(f"演示 3：对话模式（/api/chat）")
    print(f"{'='*60}")

    # 构造多轮对话消息
    messages = [
        {
            "role": "system",
            "content": "你是一个简洁的编程助手，回答控制在 50 字以内。"
        },
        {
            "role": "user",
            "content": "Python 的 GIL 是什么？"
        }
    ]

    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.5,
        }
    }

    print(f"  System: {messages[0]['content']}")
    print(f"  User:   {messages[1]['content']}")

    resp = requests.post(
        f"{OLLAMA_BASE_URL}/api/chat",
        json=payload,
        timeout=60
    )
    data = resp.json()

    assistant_msg = data.get("message", {}).get("content", "(空)")
    print(f"  Assistant: {assistant_msg}")

    # 继续第二轮对话
    print(f"\n  --- 第二轮 ---")
    messages.append({"role": "assistant", "content": assistant_msg})
    messages.append({"role": "user", "content": "它对多线程有什么影响？"})

    payload["messages"] = messages
    print(f"  User: {messages[-1]['content']}")

    resp = requests.post(
        f"{OLLAMA_BASE_URL}/api/chat",
        json=payload,
        timeout=60
    )
    data = resp.json()
    print(f"  Assistant: {data.get('message', {}).get('content', '(空)')}")


# ============================================================
# 主程序
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("Ollama 本地模型调用示例")
    print("=" * 60)

    # 第一步：检查 Ollama 是否可用
    print("\n[检查 Ollama 服务]")
    if not check_ollama_available():
        print("  ⚠ Ollama 服务未运行！")
        print("  请先启动 Ollama：")
        print("    1. 安装: curl -fsSL https://ollama.com/install.sh | sh")
        print("    2. 启动: ollama serve")
        print("    3. 下载模型: ollama pull qwen2.5:7b")
        print("    4. 重新运行本脚本")
        sys.exit(0)

    print("  Ollama 服务正常运行")

    # 第二步：列出模型
    print("\n[已下载的模型]")
    models = list_models()
    model = get_available_model(models)
    if not model:
        print("  没有可用模型，请先下载: ollama pull qwen2.5:7b")
        sys.exit(0)
    print(f"\n  将使用模型: {model}")

    # 第三步：运行各种调用演示
    try:
        demo_generate(model)        # 普通调用
        demo_generate_stream(model)  # 流式输出
        demo_chat(model)            # 对话模式
    except requests.exceptions.RequestException as e:
        print(f"\n  请求出错: {e}")

    print(f"\n{'='*60}")
    print("演示完成！")
    print("=" * 60)
