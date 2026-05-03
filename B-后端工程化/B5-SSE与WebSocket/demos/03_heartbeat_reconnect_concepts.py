#!/usr/bin/env python3
"""
B5 SSE + WebSocket —— 心跳保活、断线重连与多连接管理

理论对应：B5-SSE与WebSocket/理论讲解.md §4（SSE）、§12（心跳与断连）

运行方式：python3 03_heartbeat_reconnect_concepts.py
不依赖外部包，纯概念演示。
"""

import time
import threading
import random
from dataclasses import dataclass, field
from enum import Enum


# ============================================================
# 1. 心跳机制——保活 + 探活
# ============================================================
print("=" * 60)
print("1. 心跳（Heartbeat）机制：保活 + 探活")
print("=" * 60)


class ConnectionState(Enum):
    ALIVE = "alive"        # 连接存活
    SUSPECT = "suspect"     # 疑似断开（心跳超时）
    DEAD = "dead"          # 确定断开


@dataclass
class HeartbeatDemo:
    """
    心跳机制有两个作用：

    1. 保活（Keep-Alive）：
       中间网络设备（NAT、LB、反向代理）看到连接长时间没数据，
       会把它当成"僵尸连接"回收。定期发心跳告诉它们"我还活着"。

    2. 探活（Health Check）：
       对端可能网络断开但 TCP 没收到 RST（比如拔网线、WiFi 断了），
       服务器以为连接还在。心跳超时能发现这种"假死"。

    SSE 里的心跳：服务端定期发 ": heartbeat\n\n"
    客户端收到后忽略（: 开头是 SSE 注释），但 TCP 层面算"有数据"

    WebSocket 里的心跳：
    - 原生：Ping/Pong 帧（协议层）
    - 应用层：双方约定 {"type":"ping"} / {"type":"pong"} JSON 消息
    """
    heartbeat_interval: float = 15.0   # 每 15 秒发一次心跳
    heartbeat_timeout: float = 45.0    # 45 秒没收到心跳 → 判定断开

    def __post_init__(self):
        self.last_pong: float = time.time()
        self.state = ConnectionState.ALIVE
        self.sent_count: int = 0
        self.received_count: int = 0

    def send_heartbeat(self):
        """服务端发送心跳"""
        self.sent_count += 1
        print(f"  [Server] 发送心跳 ({self.sent_count})")

    def receive_pong(self):
        """收到客户端回应"""
        self.received_count += 1
        self.last_pong = time.time()
        self.state = ConnectionState.ALIVE
        print(f"  [Server] 收到 pong ({self.received_count})")

    def check_timeout(self) -> bool:
        """检测心跳超时"""
        elapsed = time.time() - self.last_pong
        if elapsed > self.heartbeat_timeout:
            self.state = ConnectionState.DEAD
            print(f"  ⚠️ 心跳超时 {elapsed:.0f}s，连接判定为 DEAD")
            return True
        elif elapsed > self.heartbeat_timeout / 2:
            print(f"  ⚠️ 疑似超时 {elapsed:.0f}s")
        return False


def simulate_heartbeat():
    """模拟心跳机制：3 次正常 → 1 次丢失 → 恢复正常"""
    hb = HeartbeatDemo(heartbeat_interval=3, heartbeat_timeout=10)

    scenarios = [
        ("send_pong", 0.5),   # 正常
        ("send_pong", 0.5),   # 正常
        ("send_pong", 0.5),   # 正常
        ("no_response", 6.0), # 客户端没回应（模拟断线）
        ("send_pong", 0.5),   # 恢复
    ]

    current_time = 0.0
    for action, delay in scenarios:
        current_time += delay
        hb.send_heartbeat()

        if action == "send_pong":
            hb.receive_pong()
        else:
            print(f"  [Client] 收到心跳但未回应...")

        if hb.check_timeout():
            print(f"  🔴 触发重连机制")

    print(f"\n  最终状态: {hb.state.value}")
    print(f"  发送心跳 {hb.sent_count} 次，收到回应 {hb.received_count} 次")


simulate_heartbeat()


# ============================================================
# 2. 指数退避重连——别让所有客户端同时重连
# ============================================================
print("\n" + "=" * 60)
print("2. 断线重连——指数退避 + 抖动")
print("=" * 60)


def demo_reconnect_backoff():
    """
    断线后不要立刻重连——可能服务器还没恢复。

    指数退避：重连间隔 = min(base * 2^attempt, max_wait)
    - 第 1 次：1 秒后
    - 第 2 次：2 秒后
    - 第 3 次：4 秒后
    - 第 4 次：8 秒后
    - ...最多等 60 秒

    抖动（Jitter）：
    在计算出来的等待时间上加一个随机偏移（±25%）
    防止"惊群效应"——大量客户端在完全相同的时刻重连，瞬间把服务器打爆
    """
    base_wait = 1.0    # 基础等待时间（秒）
    max_wait = 60.0    # 最长等待时间
    attempt = 0

    print("  模拟 5 次重连尝试：")
    for _ in range(5):
        # 计算退避时间
        wait = min(base_wait * (2 ** attempt), max_wait)
        # 加抖动：±25%
        jitter_range = wait * 0.25
        wait_with_jitter = wait + random.uniform(-jitter_range, jitter_range)

        print(f"  第 {attempt + 1} 次重连：{wait_with_jitter:.1f}s 后 "
              f"(基础={wait:.0f}s, 抖动=±{jitter_range:.1f}s)")
        attempt += 1


demo_reconnect_backoff()


# ============================================================
# 3. 连接池管理——多个连接的生命周期
# ============================================================
print("\n" + "=" * 60)
print("3. 连接管理与池化概念")
print("=" * 60)


@dataclass
class ManagedConnection:
    """一个被管理的长连接（SSE 或 WebSocket）"""
    conn_id: str
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    reconnecting: bool = False
    reconnect_attempt: int = 0

    def is_idle(self, idle_timeout: float = 300) -> bool:
        """是否空闲超时（5 分钟没活动）"""
        return time.time() - self.last_activity > idle_timeout


class ConnectionManager:
    """
    连接管理器：跟踪所有活跃连接，处理心跳检测、空闲回收、优雅关闭。

    类比：酒店前台——知道每个房间有没有人、多久没活动、需要不要敲门。
    """

    def __init__(self):
        self.connections: dict[str, ManagedConnection] = {}
        self._lock = threading.Lock()

    def register(self, conn_id: str) -> ManagedConnection:
        """新连接注册"""
        conn = ManagedConnection(conn_id=conn_id)
        with self._lock:
            self.connections[conn_id] = conn
        print(f"  [Manager] 注册连接 {conn_id} (当前 {len(self.connections)} 个)")
        return conn

    def unregister(self, conn_id: str):
        """连接断开时注销"""
        with self._lock:
            if conn_id in self.connections:
                del self.connections[conn_id]
        print(f"  [Manager] 注销连接 {conn_id} (剩余 {len(self.connections)} 个)")

    def update_activity(self, conn_id: str):
        """更新连接活动时间"""
        if conn_id in self.connections:
            self.connections[conn_id].last_activity = time.time()

    def cleanup_idle(self, idle_timeout: float = 300):
        """清理空闲连接（超过 idle_timeout 没活动的）"""
        now = time.time()
        with self._lock:
            idle_conns = [
                cid for cid, c in self.connections.items()
                if now - c.last_activity > idle_timeout
            ]
        for cid in idle_conns:
            print(f"  [Manager] 清理空闲连接 {cid}")
            self.unregister(cid)

    def connection_count(self) -> int:
        """当前连接数——监控告警的关键指标"""
        return len(self.connections)

    def shutdown(self):
        """优雅关闭：通知所有连接、等待它们自己断开"""
        count = len(self.connections)
        print(f"  [Manager] 关闭 {count} 个连接...")
        with self._lock:
            self.connections.clear()
        print(f"  [Manager] 所有连接已关闭")


def demo_connection_manager():
    """演示连接管理器的典型使用"""
    mgr = ConnectionManager()

    # 模拟几个连接的生命周期
    conn1 = mgr.register("conn-alice")
    conn2 = mgr.register("conn-bob")
    conn3 = mgr.register("conn-carol")

    mgr.update_activity("conn-alice")
    mgr.update_activity("conn-bob")

    # 模拟 conn-carol 空闲（手动设置 last_activity）
    conn3.last_activity = time.time() - 600  # 10 分钟前

    # 清理空闲连接
    mgr.cleanup_idle(idle_timeout=300)
    print(f"  当前连接数: {mgr.connection_count()}")

    # 优雅关闭
    mgr.shutdown()


demo_connection_manager()

print("\n✅ B5 心跳与连接管理核心概念演示完成")
