"""
UDP 服务端与客户端演示

本文件演示 UDP 通信的基本流程：
1. 服务端绑定端口，等待数据报
2. 客户端发送数据报（无需先建立连接）
3. 服务端收到后回复

UDP 特点：无连接、不可靠、数据报（消息边界清晰）、速度快

与 TCP 的主要区别：
- 不需要 listen() 和 accept()（无连接）
- 使用 sendto() 和 recvfrom() 而非 send() 和 recv()
- 每个数据报独立，不保证顺序和送达

运行方式：直接运行即可
    python3 02_udp_server_client.py

无需第三方库。
"""

import socket
import threading
import time


def udp_server(host: str = "127.0.0.1", port: int = 9002):
    """
    UDP 服务端

    注意和 TCP 的区别：
    - 使用 SOCK_DGRAM（数据报）而非 SOCK_STREAM（字节流）
    - 不需要 listen() 和 accept()
    - 使用 recvfrom() 获取数据和发送方地址
    """
    # socket.SOCK_DGRAM → UDP 协议（数据报 socket）
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # 绑定地址和端口
    server_socket.bind((host, port))
    print(f"[UDP服务端] 正在等待数据，监听 {host}:{port} ...")

    # recvfrom() 返回 (数据, 发送方地址)
    # UDP 没有连接概念，所以需要知道是谁发来的才能回复
    data, client_address = server_socket.recvfrom(1024)
    message = data.decode("utf-8")
    print(f"[UDP服务端] 收到来自 {client_address} 的消息: {message}")

    # 使用 sendto() 发送响应到指定地址
    # 因为没有连接，必须指定目标地址
    response = f"UDP服务端已收到: '{message}'"
    server_socket.sendto(response.encode("utf-8"), client_address)
    print(f"[UDP服务端] 已发送响应到 {client_address}")

    server_socket.close()
    print("[UDP服务端] 已关闭")


def udp_client(host: str = "127.0.0.1", port: int = 9002):
    """
    UDP 客户端

    注意：
    - 不需要 connect()（无连接）
    - 使用 sendto() 指定目标地址发送
    - 使用 recvfrom() 接收响应
    """
    # 创建 UDP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # 设置超时时间（秒），防止 recvfrom 永久阻塞
    # 因为 UDP 不保证送达，可能永远收不到响应
    client_socket.settimeout(5.0)

    # 发送数据（无需先建立连接，直接发）
    message = "你好，这是 UDP 客户端！"
    server_address = (host, port)
    client_socket.sendto(message.encode("utf-8"), server_address)
    print(f"[UDP客户端] 已发送到 {server_address}: {message}")

    try:
        # 接收响应
        data, server_addr = client_socket.recvfrom(1024)
        response = data.decode("utf-8")
        print(f"[UDP客户端] 收到响应: {response}")
    except socket.timeout:
        # UDP 不可靠，可能收不到响应
        print("[UDP客户端] 等待响应超时（UDP不保证送达）")

    client_socket.close()
    print("[UDP客户端] 已关闭")


def udp_vs_tcp_comparison():
    """打印 TCP 和 UDP 的对比信息"""
    print("\n" + "=" * 60)
    print("TCP vs UDP 对比")
    print("=" * 60)
    comparisons = [
        ("连接方式", "面向连接（三次握手）", "无连接"),
        ("可靠性", "可靠（确认、重传）", "不可靠（尽力而为）"),
        ("传输方式", "字节流（无边界）", "数据报（有边界）"),
        ("速度", "较慢（有确认机制）", "较快（无额外开销）"),
        ("头部大小", "20 字节起", "仅 8 字节"),
        ("适用场景", "网页、文件传输、邮件", "视频直播、DNS、游戏"),
        ("Python socket", "SOCK_STREAM", "SOCK_DGRAM"),
        ("发送方法", "send()", "sendto()"),
        ("接收方法", "recv()", "recvfrom()"),
    ]
    for feature, tcp, udp in comparisons:
        print(f"  {feature:12s} | TCP: {tcp:24s} | UDP: {udp}")


if __name__ == "__main__":
    print("=" * 60)
    print("UDP 通信演示")
    print("=" * 60)

    # 在线程中启动 UDP 服务端
    server_thread = threading.Thread(target=udp_server, daemon=True)
    server_thread.start()

    # 等待服务端启动
    time.sleep(0.5)

    # 运行客户端
    udp_client()

    # 等待服务端线程结束
    server_thread.join(timeout=2)

    # 打印对比信息
    udp_vs_tcp_comparison()

    print("\n" + "=" * 60)
    print("演示结束！")
    print("=" * 60)
