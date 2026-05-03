#!/usr/bin/env python3
"""
B4 消息队列——生产消费者模式 + Redis Stream 概念演示

理论对应：B4-消息队列与任务队列/理论讲解.md §1-§3

运行方式：python3 05_producer_consumer_pattern.py
依赖：pip install redis（如需实际运行 Redis 部分）
"""

import time
import random
import threading
from queue import Queue, Empty
from dataclasses import dataclass, field
from typing import Callable


# ============================================================
# 1. 最简单的生产者-消费者（Python 进程内队列）
# ============================================================
print("=" * 60)
print("1. 生产者-消费者基础模式（queue.Queue）")
print("=" * 60)


def basic_producer_consumer():
    """
    用 Python 自带的 queue.Queue 演示生产者-消费者模式。

    模式角色：
    - 生产者（Producer）：产生"任务"并放入队列
    - 消费者（Consumer）：从队列取任务并处理
    - 队列（Queue）：生产者和消费者之间的缓冲区

    为什么不能直接调用？
    如果生产者直接调用消费者的处理函数：
      producer → consumer.process()  （同步阻塞）
    消费者忙的时候，生产者就得等着，什么都做不了。

    加入队列后：
      producer → Queue → consumer  （异步解耦）
    生产者只管往里扔，消费者按自己的节奏取。这叫"解耦"。
    """
    task_queue: Queue = Queue(maxsize=10)
    #   maxsize=10：队列最多存 10 个任务
    #   满了之后 put() 会阻塞 → 这叫"背压"（B6 §6.3）

    # 消费者线程
    def consumer(worker_id: int):
        """从队列取任务，处理它们"""
        while True:
            try:
                task, task_id = task_queue.get(timeout=3)
                #   get(timeout=3)：等 3 秒，没任务就抛 Empty 异常
                #   不设 timeout 的话会永远阻塞，线程退不出来

                print(f"  [Worker-{worker_id}] 处理任务 #{task_id}: {task}")
                time.sleep(random.uniform(0.2, 1.0))  # 模拟处理耗时

                task_queue.task_done()
                #   task_done() 告诉队列"这个任务处理完了"
                #   join() 会等所有 task_done 完成

            except Empty:
                print(f"  [Worker-{worker_id}] 队列空，退出")
                break

    # 测试：启动 2 个消费者，生产者放入 5 个任务
    workers = [
        threading.Thread(target=consumer, args=(i,), daemon=True)
        for i in range(2)
    ]
    for w in workers:
        w.start()

    # 生产者
    for i in range(5):
        task = f"处理数据块-{i}"
        print(f"  [Producer] 放入任务 #{i}")
        task_queue.put((task, i))
        time.sleep(0.3)

    # 等待队列清空
    task_queue.join()
    for w in workers:
        w.join(timeout=2)
    print("  全部任务处理完毕\n")


basic_producer_consumer()


# ============================================================
# 2. 消息确认（ACK）和重试——消息队列的核心价值
# ============================================================
print("=" * 60)
print("2. 消息确认（ACK）与重试机制演示")
print("=" * 60)


@dataclass
class Message:
    """模拟消息队列中的一条消息"""
    msg_id: str
    content: str
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class MessageBroker:
    """
    极简消息代理（模拟 Redis Stream / RabbitMQ 的核心行为）。

    关键概念：
    - Pending（待确认）：消费者取走了消息但还没 ACK
      → 如果消费者挂了，消息留在 pending 里，可以被重新投递
    - ACK（确认）：消费者处理完消息后告诉 broker "我处理好了"
      → broker 从 pending 里删除这条消息
    - NACK / 超时重试：消费者处理失败或超时
      → broker 重新把消息放回队列或移到死信队列
    """
    messages: list[Message] = field(default_factory=list)
    pending: dict[str, Message] = field(default_factory=dict)
    dead_letter: list[Message] = field(default_factory=list)

    def publish(self, content: str) -> str:
        """发布消息"""
        msg_id = f"msg-{len(self.messages)}"
        self.messages.append(Message(msg_id=msg_id, content=content))
        print(f"  [Broker] 发布消息 {msg_id}: {content}")
        return msg_id

    def consume(self) -> Message | None:
        """消费者取一条消息（放入 pending）"""
        if not self.messages:
            return None
        msg = self.messages.pop(0)
        self.pending[msg.msg_id] = msg
        print(f"  [Broker] 投递 {msg.msg_id} 给消费者 → pending")
        return msg

    def ack(self, msg_id: str):
        """消费者确认处理完成"""
        if msg_id in self.pending:
            del self.pending[msg_id]
            print(f"  [Broker] ACK {msg_id} → 已确认，消息删除")

    def nack(self, msg_id: str):
        """消费者处理失败，重试或移到死信"""
        msg = self.pending.pop(msg_id, None)
        if not msg:
            return

        msg.retry_count += 1
        if msg.retry_count < msg.max_retries:
            self.messages.append(msg)  # 重新入队
            print(f"  [Broker] NACK {msg_id} → 重试 ({msg.retry_count}/{msg.max_retries})")
        else:
            self.dead_letter.append(msg)  # 超过重试次数 → 死信
            print(f"  [Broker] {msg_id} → 死信队列（超过 {msg.max_retries} 次重试）")


def simulate_message_broker():
    """模拟消费者-确认-重试-死信的完整流程"""
    broker = MessageBroker()

    # 发布消息
    broker.publish("正常消息")
    broker.publish("会失败的消息")
    broker.publish("另一条正常消息")

    # 消费者消费
    print()

    # 消息 1：正常处理
    msg1 = broker.consume()
    if msg1:
        print(f"  [Consumer] 处理 {msg1.msg_id}... 成功!")
        broker.ack(msg1.msg_id)

    print()

    # 消息 2：连续失败
    for i in range(3):
        msg2 = broker.consume()
        if msg2:
            print(f"  [Consumer] 处理 {msg2.msg_id}... 失败!")
            broker.nack(msg2.msg_id)  # 每次 nack → retry_count += 1
        print()

    # 消息 3：正常处理
    msg3 = broker.consume()
    if msg3:
        print(f"  [Consumer] 处理 {msg3.msg_id}... 成功!")
        broker.ack(msg3.msg_id)

    print(f"\n  Pending 消息数: {len(broker.pending)}")
    print(f"  死信消息数: {len(broker.dead_letter)}")
    for dlq in broker.dead_letter:
        print(f"    死信: {dlq.msg_id} - {dlq.content} (重试 {dlq.retry_count} 次)")


simulate_message_broker()


# ============================================================
# 3. Redis Stream 的 Python 封装演示（概念代码）
# ============================================================
print("\n" + "=" * 60)
print("3. Redis Stream 核心操作演示")
print("=" * 60)


def demo_redis_stream_concepts():
    """
    Redis Stream 的五个核心操作。

    Redis Stream 就像一个"追加日志"：
    - 只能追加（add），不能修改
    - 每条消息有唯一 ID（时间戳-序号，如 1680000000000-0）
    - 消费者组支持多个消费者并行消费

    对比 List 做队列：
    - List：pop 后消息消失（删掉了），消费者挂了就丢消息
    - Stream：读后消息还在，消费者 ACK 后才标记为"已处理"
    """
    operations = """
    Redis Stream 核心操作（对应 Redis 命令）：

    1. XADD stream_name * key value [key value ...]
       添加一条消息。* = 自动生成消息 ID。
       XADD orders * user_id 123 amount 99.9

    2. XREAD COUNT count STREAMS stream_name id
       读取消息（不删除）。id=0 从头读，id=$ 只读最新的。
       XREAD COUNT 10 STREAMS orders 0

    3. XREADGROUP GROUP group consumer COUNT count STREAMS stream_name id
       消费者组消费。> 表示只消费未分配给其他消费者的消息。
       XREADGROUP GROUP order_workers worker1 COUNT 1 STREAMS orders >

    4. XACK stream_name group message_id
       确认消费。消费者处理完后调用。
       XACK orders order_workers 1680000000000-0

    5. XPENDING stream_name group
       查看待确认（pending）的消息——消费者取走了但还没 ACK。
       XPENDING orders order_workers
       → 如果有 pending 消息，说明有消费者挂了或处理超时

    消息生命周期：
      生产者 XADD → Stream
      → 消费者 XREADGROUP → pending（待确认）
      → 消费者 XACK → 标记为已消费（消息还在 Stream 里）
      → 定期 XDEL 或等 Stream 的 MAXLEN 截断
    """
    print(operations)


demo_redis_stream_concepts()


# ============================================================
# 4. 发件箱模式（Outbox Pattern）概念演示
# ============================================================
print("=" * 60)
print("4. 发件箱模式（Outbox Pattern）")
print("=" * 60)


def demo_outbox_pattern():
    """
    发件箱模式：确保"写业务数据"和"发消息"的原子性。

    问题场景：
      用户下单：
        1. INSERT INTO orders (...)
        2. redis.xadd("order_events", ...)  发消息通知下游
      如果步骤 1 成功、步骤 2 之前进程崩溃了？
      → 订单写入了，但下游不知道 → 数据不一致

    发件箱解法：
      在同一个数据库事务里：
        1. INSERT INTO orders (...)
        2. INSERT INTO outbox (event_type, payload, status)
      事务提交 → 两个 INSERT 原子完成
      独立进程扫描 outbox 表，发消息，标记为 sent
    """
    outbox_sql = """
    -- 发件箱模式的关键 SQL

    -- 步骤 1：在同一个事务里写入业务数据 + outbox 记录
    BEGIN;
      INSERT INTO orders (id, user_id, amount, created_at)
      VALUES (gen_random_uuid(), 123, 99.9, NOW());

      INSERT INTO outbox (id, event_type, payload, status, created_at)
      VALUES (gen_random_uuid(), 'order.created',
              '{"order_id": "xxx", "user_id": 123, "amount": 99.9}',
              'pending', NOW());
    COMMIT;
    -- 这两个 INSERT 要么一起成功，要么一起失败！
    -- 不会出现"订单写入了但 outbox 没写"的情况。

    -- 步骤 2：独立投递进程扫描 outbox
    -- 这个进程和订单处理进程完全独立
    SELECT * FROM outbox WHERE status = 'pending' LIMIT 100;

    -- 对每条取出的记录：
    --  1. 发到 MQ (Redis Stream / RabbitMQ / Kafka)
    --  2. UPDATE outbox SET status = 'sent' WHERE id = xxx;
    -- 如果发 MQ 成功但 UPDATE 失败 → 下次扫描会重发
    -- 所以消息消费者必须做幂等（检查是否已处理过同一 order_id）

    -- 步骤 3：定期清理已发送的出箱记录
    DELETE FROM outbox WHERE status = 'sent' AND created_at < NOW() - INTERVAL '7 days';
    """

    print(outbox_sql)


demo_outbox_pattern()


print("\n✅ B4 消息队列核心模式演示完成")
print("理论对应：B4-消息队列与任务队列/理论讲解.md")
