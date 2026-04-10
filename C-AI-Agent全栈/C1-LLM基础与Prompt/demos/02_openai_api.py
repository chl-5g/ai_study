#!/usr/bin/env python3
"""
02_openai_api.py — OpenAI 兼容 API 调用示例（纯 requests 实现）

演示内容：
1. OpenAI Chat Completions API 请求结构
2. 响应解析（完整字段说明）
3. 流式输出（SSE 解析）
4. 多轮对话
5. 兼容不同 Provider（OpenAI / DeepSeek / Ollama）

依赖：requests
运行：python3 02_openai_api.py

环境变量（可选）：
  OPENAI_API_KEY  — OpenAI API Key
  OPENAI_BASE_URL — 自定义 API 端点（默认尝试 Ollama）
"""

import os
import sys
import json
import requests

# ============================================================
# 配置：优先使用环境变量，回退到 Ollama 本地
# ============================================================
API_KEY = os.environ.get("OPENAI_API_KEY", "")
BASE_URL = os.environ.get("OPENAI_BASE_URL", "")

# 如果没有设置环境变量，尝试使用 Ollama 的 OpenAI 兼容接口
if not BASE_URL:
    BASE_URL = "http://localhost:11434/v1"
    if not API_KEY:
        API_KEY = "ollama"  # Ollama 不需要真实的 API Key

# 模型名称（Ollama 用本地模型名，OpenAI 用 gpt-4o 等）
MODEL = os.environ.get("OPENAI_MODEL", "qwen2.5:7b")


def check_api_available():
    """检查 API 是否可用"""
    try:
        resp = requests.get(
            f"{BASE_URL}/models",
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=5
        )
        return resp.status_code == 200
    except (requests.ConnectionError, requests.Timeout):
        return False


def demo_basic_request():
    """
    演示 1：基础 Chat Completions 请求

    请求体核心字段：
    - model: 模型名称
    - messages: 消息列表，每条包含 role 和 content
    - temperature: 温度参数（0.0-2.0）
    - max_tokens: 最大生成 Token 数
    """
    print(f"\n{'='*60}")
    print("演示 1：基础 Chat Completions 请求")
    print(f"{'='*60}")

    url = f"{BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    # 构造请求体 —— 这是 OpenAI API 的标准格式
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",       # 系统消息：设定助手行为
                "content": "你是一个简洁的技术助手，回答控制在 100 字以内。"
            },
            {
                "role": "user",         # 用户消息
                "content": "什么是 RESTful API？"
            }
        ],
        "temperature": 0.7,             # 温度
        "max_tokens": 300,              # 最大输出 Token
        "stream": False,                # 非流式
    }

    print(f"  请求 URL: {url}")
    print(f"  模型: {MODEL}")
    print(f"  消息: {json.dumps(payload['messages'], ensure_ascii=False, indent=4)}")
    print()

    resp = requests.post(url, headers=headers, json=payload, timeout=60)

    if resp.status_code != 200:
        print(f"  请求失败: HTTP {resp.status_code}")
        print(f"  响应: {resp.text[:500]}")
        return

    data = resp.json()

    # ---- 解析响应 ----
    print("  === 响应解析 ===")
    print(f"  响应 ID:    {data.get('id', 'N/A')}")
    print(f"  模型:       {data.get('model', 'N/A')}")
    print(f"  创建时间:   {data.get('created', 'N/A')}")

    # choices 是一个列表，通常只有一个元素
    choices = data.get("choices", [])
    if choices:
        choice = choices[0]
        message = choice.get("message", {})
        print(f"  角色:       {message.get('role', 'N/A')}")
        print(f"  内容:       {message.get('content', '(空)')}")
        print(f"  结束原因:   {choice.get('finish_reason', 'N/A')}")
        # finish_reason 含义：
        #   stop     — 正常结束
        #   length   — 达到 max_tokens 限制
        #   tool_calls — 需要调用工具

    # usage 包含 Token 使用统计
    usage = data.get("usage", {})
    if usage:
        print(f"\n  === Token 使用 ===")
        print(f"  输入 Tokens:  {usage.get('prompt_tokens', 'N/A')}")
        print(f"  输出 Tokens:  {usage.get('completion_tokens', 'N/A')}")
        print(f"  总计 Tokens:  {usage.get('total_tokens', 'N/A')}")

    return data


def demo_streaming():
    """
    演示 2：流式输出（Server-Sent Events）

    设置 stream=True 后，响应以 SSE 格式返回：
    - 每行以 "data: " 开头
    - 每个 chunk 包含增量内容（delta）
    - 最后一行是 "data: [DONE]"
    """
    print(f"\n{'='*60}")
    print("演示 2：流式输出（SSE）")
    print(f"{'='*60}")

    url = f"{BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": "用 3 个要点介绍 Docker 的优势"}
        ],
        "temperature": 0.7,
        "max_tokens": 300,
        "stream": True,    # 开启流式输出
    }

    print(f"  提问: {payload['messages'][0]['content']}")
    print(f"  回答: ", end="", flush=True)

    resp = requests.post(
        url, headers=headers, json=payload,
        stream=True,     # requests 的 stream 参数，逐块读取响应
        timeout=60
    )

    if resp.status_code != 200:
        print(f"\n  请求失败: HTTP {resp.status_code}")
        return

    # 解析 SSE 流
    full_content = ""
    for line in resp.iter_lines(decode_unicode=True):
        if not line:
            continue

        # 去掉 "data: " 前缀
        if line.startswith("data: "):
            data_str = line[6:]  # len("data: ") == 6
        else:
            continue

        # 检查是否结束
        if data_str.strip() == "[DONE]":
            break

        try:
            chunk = json.loads(data_str)
            # 从 delta 中提取增量内容
            delta = chunk["choices"][0].get("delta", {})
            content = delta.get("content", "")
            if content:
                print(content, end="", flush=True)
                full_content += content
        except (json.JSONDecodeError, KeyError, IndexError):
            pass

    print()  # 换行
    print(f"\n  (完整内容长度: {len(full_content)} 字符)")


def demo_multi_turn():
    """
    演示 3：多轮对话

    多轮对话的关键：将历史消息全部放入 messages 列表
    模型本身无状态，需要客户端维护对话历史
    """
    print(f"\n{'='*60}")
    print("演示 3：多轮对话")
    print(f"{'='*60}")

    url = f"{BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    # 维护消息历史
    messages = [
        {"role": "system", "content": "你是一个 Python 教学助手，回答简洁。"}
    ]

    # 模拟两轮对话
    questions = [
        "什么是列表推导式？给一个简单例子",
        "它和普通 for 循环相比有什么优势？"
    ]

    for i, question in enumerate(questions, 1):
        print(f"\n  --- 第 {i} 轮 ---")
        print(f"  User: {question}")

        # 添加用户消息
        messages.append({"role": "user", "content": question})

        payload = {
            "model": MODEL,
            "messages": messages,  # 每次发送完整历史
            "temperature": 0.7,
            "max_tokens": 200,
            "stream": False,
        }

        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        if resp.status_code != 200:
            print(f"  请求失败: HTTP {resp.status_code}")
            return

        data = resp.json()
        assistant_content = data["choices"][0]["message"]["content"]
        print(f"  Assistant: {assistant_content}")

        # 将助手回复加入历史，用于下一轮
        messages.append({"role": "assistant", "content": assistant_content})

    print(f"\n  对话历史共 {len(messages)} 条消息")


def demo_different_providers():
    """
    演示 4：展示不同 Provider 的配置方式

    OpenAI 兼容 API 的好处是只需改 base_url 和 api_key
    """
    print(f"\n{'='*60}")
    print("演示 4：不同 Provider 的配置（仅展示，不实际调用）")
    print(f"{'='*60}")

    providers = {
        "OpenAI": {
            "base_url": "https://api.openai.com/v1",
            "model": "gpt-4o",
            "api_key": "sk-xxx（从 platform.openai.com 获取）",
        },
        "DeepSeek": {
            "base_url": "https://api.deepseek.com/v1",
            "model": "deepseek-chat",
            "api_key": "sk-xxx（从 platform.deepseek.com 获取）",
        },
        "通义千问 (Qwen)": {
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "model": "qwen-plus",
            "api_key": "sk-xxx（从阿里云控制台获取）",
        },
        "Ollama 本地": {
            "base_url": "http://localhost:11434/v1",
            "model": "qwen2.5:7b",
            "api_key": "ollama（随意填写）",
        },
        "vLLM 本地": {
            "base_url": "http://localhost:8000/v1",
            "model": "自定义模型名",
            "api_key": "token-xxx（vLLM 启动时配置）",
        },
    }

    for name, config in providers.items():
        print(f"\n  {name}:")
        print(f"    base_url = {config['base_url']}")
        print(f"    model    = {config['model']}")
        print(f"    api_key  = {config['api_key']}")

    print("\n  所有 Provider 使用完全相同的请求格式，只需替换上述三个参数。")


# ============================================================
# 主程序
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("OpenAI 兼容 API 调用示例（纯 requests 实现）")
    print("=" * 60)
    print(f"\n当前配置:")
    print(f"  BASE_URL: {BASE_URL}")
    print(f"  MODEL:    {MODEL}")
    print(f"  API_KEY:  {'已设置' if API_KEY and API_KEY != 'ollama' else '未设置（使用 Ollama）'}")

    # 检查 API 是否可用
    api_ok = check_api_available()

    if api_ok:
        print(f"\n  API 服务可用，开始演示...\n")
        demo_basic_request()
        demo_streaming()
        demo_multi_turn()
    else:
        print(f"\n  API 服务不可用（{BASE_URL}）")
        print("  可能的原因：")
        print("    1. Ollama 未启动 → ollama serve")
        print("    2. 需要设置环境变量：")
        print("       export OPENAI_API_KEY='your-key'")
        print("       export OPENAI_BASE_URL='https://api.openai.com/v1'")
        print("       export OPENAI_MODEL='gpt-4o'")
        print("\n  跳过实际调用，展示 Provider 配置信息...\n")

    # 不管 API 是否可用，都展示 Provider 配置
    demo_different_providers()

    print(f"\n{'='*60}")
    print("演示完成！")
    print("=" * 60)
