"""
TCP 服务端与客户端演示

本文件演示 TCP 通信的基本流程：
1. 服务端监听端口，等待客户端连接
2. 客户端连接服务端
3. 双方收发消息
4. 关闭连接

TCP 特点：面向连接、可靠传输、字节流

运行方式：直接运行即可（会自动启动服务端和客户端）
    python3 01_tcp_server_client.py

无需第三方库，使用 Python 标准库 socket。
"""

import socket
import threading
import time


def tcp_server(host: str = "127.0.0.1", port: int = 9001):
    """
    TCP 服务端

    流程：
    1. 创建 socket 对象（指定 IPv4 + TCP）
    2. 绑定地址和端口
    3. 开始监听
    4. 接受客户端连接
    5. 收发数据
    6. 关闭连接
    """
    # socket.AF_INET    → IPv4 地址族
    # socket.SOCK_STREAM → TCP 协议（流式 socket）
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # SO_REUSEADDR 允许端口复用（避免 "Address already in use" 错误）
    # 当服务端重启时，端口可能还在 TIME_WAIT 状态，设置这个选项可以立即复用
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # 绑定地址和端口
    # 127.0.0.1 表示只监听本机回环地址
    # 如果要监听所有网卡，用 "0.0.0.0"
    server_socket.bind((host, port))

    # 开始监听，参数是等待连接的最大队列长度
    # backlog=5 表示最多允许 5 个客户端在队列中等待
    server_socket.listen(5)
    print(f"[服务端] 正在监听 {host}:{port} ...")

    # accept() 会阻塞，直到有客户端连接
    # 返回值：(新的 socket 对象用于通信, 客户端地址)
    client_socket, client_address = server_socket.accept()
    print(f"[服务端] 客户端已连接: {client_address}")

    # ---- 接收数据 ----
    # recv(1024) 表示一次最多接收 1024 字节
    # 返回的是 bytes 类型，需要 decode 成字符串
    data = client_socket.recv(1024)
    message = data.decode("utf-8")
    print(f"[服务端] 收到消息: {message}")

    # ---- 发送响应 ----
    # send() 发送的也必须是 bytes 类型
    response = f"服务端已收到你的消息: '{message}'"
    client_socket.send(response.encode("utf-8"))
    print(f"[服务端] 已发送响应")

    # ---- 关闭连接 ----
    # 先关闭与客户端的通信 socket，再关闭服务端监听 socket
    client_socket.close()
    server_socket.close()
    print("[服务端] 连接已关闭")


def tcp_client(host: str = "127.0.0.1", port: int = 9001):
    """
    TCP 客户端

    流程：
    1. 创建 socket 对象
    2. 连接到服务端（三次握手在此完成）
    3. 发送数据
    4. 接收响应
    5. 关闭连接
    """
    # 创建 TCP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # 连接服务端（这一步完成 TCP 三次握手）
    client_socket.connect((host, port))
    print(f"[客户端] 已连接到 {host}:{port}")

    # 发送消息
    message = "你好，这是 TCP 客户端！"
    client_socket.send(message.encode("utf-8"))
    print(f"[客户端] 已发送: {message}")

    # 接收服务端的响应
    data = client_socket.recv(1024)
    response = data.decode("utf-8")
    print(f"[客户端] 收到响应: {response}")

    # 关闭连接（四次挥手在此完成）
    client_socket.close()
    print("[客户端] 连接已关闭")


if __name__ == "__main__":
    print("=" * 60)
    print("TCP 通信演示")
    print("=" * 60)

    # 在一个线程中启动服务端，主线程运行客户端
    # 实际场景中，服务端和客户端通常在不同的机器/进程上
    server_thread = threading.Thread(target=tcp_server, daemon=True)
    server_thread.start()

    # 等待服务端启动完成
    time.sleep(0.5)

    # 运行客户端
    tcp_client()

    # 等待服务端线程结束
    server_thread.join(timeout=2)

    print("\n" + "=" * 60)
    print("演示结束！")
    print("=" * 60)
