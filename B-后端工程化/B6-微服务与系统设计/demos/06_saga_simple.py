#!/usr/bin/env python3
"""
B6 微服务——Saga 模式：跨服务事务 + 补偿

理论对应：B6-微服务与系统设计/理论讲解.md §9（分布式事务与 Saga）

运行方式：python3 06_saga_simple.py
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable


# ============================================================
# 1. Saga 的核心概念
# ============================================================
print("=" * 60)
print("1. Saga = 多个本地事务 + 补偿操作")
print("=" * 60)

print("""
Saga 解决什么？
  单体里：一个事务 BEGIN → 扣库存 → 创建订单 → 扣款 → COMMIT
         全部在同一个数据库，ACID 事务搞定。

  微服务里：订单服务有自己的库，库存服务有自己的库，支付服务有自己的库
          没有"跨 3 个数据库的事务"这种东西。

Saga 的解法：
  把一个跨服务的大操作拆成多个步骤，每个步骤：
    - 在自己的数据库里做本地事务（可 COMMIT/ROLLBACK）
    - 有一个对应的补偿操作（如何"撤销"这一步）

  如果某一步失败，按逆序执行已完成步骤的补偿操作。

类比：旅行预订
  1. 订机票 ✓（补偿：退票扣手续费）
  2. 订酒店 ✓（补偿：取消预订）
  3. 租车   ✗（失败！）
  → 补偿步骤 2：取消酒店
  → 补偿步骤 1：退机票
""")


# ============================================================
# 2. Saga 的实现
# ============================================================
print("=" * 60)
print("2. Saga 代码实现：下单流程")
print("=" * 60)


@dataclass
class SagaStep:
    """Saga 中的一个步骤"""
    name: str
    action: Callable  # 执行的操作
    compensate: Callable  # 补偿（撤销）操作


class OrderSaga:
    """
    下单 Saga：创建订单 → 锁定库存 → 扣款

    每一步都是独立的本地事务。失败时逆序补偿。
    """

    def __init__(self):
        self.steps: list[SagaStep] = []
        self.completed_steps: list[SagaStep] = []  # 已成功执行、待补偿的步骤
        self.order_id: str | None = None
        self.inventory_locked: bool = False

    def execute(self, user_id: str, product_id: str,
                quantity: int, amount: float) -> str:
        """
        执行下单 Saga。

        正常流程：
          Step 1: 创建订单 →
          Step 2: 锁定库存 →
          Step 3: 扣款 →
          Step 4: 更新订单状态为"已支付"

        如果 Step 3 失败：
          补偿 Step 2: 释放库存
          补偿 Step 1: 取消订单
        """
        try:
            # ==========================================
            # Step 1: 创建订单（订单服务本地事务）
            # ==========================================
            self.order_id = self._create_order(user_id, amount)
            # 记录：如果后续步骤失败，需要取消这个订单
            # 这在实际实现中可以用一个步骤列表 + 逆序遍历
            self.inventory_locked = False

            # ══════════════════════════════════════════
            # Step 2: 锁定库存（库存服务本地事务）
            # ══════════════════════════════════════════
            self._lock_inventory(product_id, quantity)
            self.inventory_locked = True

            # ══════════════════════════════════════════
            # Step 3: 扣款（支付服务本地事务）
            # ══════════════════════════════════════════
            # 模拟：30% 概率支付失败
            import random
            if random.random() < 0.3:
                raise Exception("支付失败：余额不足")

            self._charge(user_id, amount)

            # ══════════════════════════════════════════
            # 全部成功！
            # ══════════════════════════════════════════
            self._update_order_status("paid")
            return f"订单 {self.order_id} 创建成功，已支付"

        except Exception as e:
            print(f"\n  ❌ Saga 执行失败: {e}")
            print(f"  ⏪ 开始补偿（逆序撤销）...")
            self._compensate()
            return f"订单失败，已回滚: {e}"

    def _compensate(self):
        """逆序补偿已完成的步骤"""
        # 步骤顺序：创建订单 → 锁定库存 → 扣款
        # 补偿顺序：扣款(已失败，无需补偿) ← 释放库存 ← 取消订单

        if self.inventory_locked:
            self._unlock_inventory()

        if self.order_id:
            self._cancel_order()

    # —— 正向操作 ——
    def _create_order(self, user_id: str, amount: float) -> str:
        order_id = f"ORD-{hash(user_id) % 10000:04d}"
        print(f"  ✅ Step 1: 创建订单 {order_id}（金额 ¥{amount}）")
        return order_id

    def _lock_inventory(self, product_id: str, quantity: int):
        print(f"  ✅ Step 2: 锁定库存（商品={product_id}, 数量={quantity}）")

    def _charge(self, user_id: str, amount: float):
        print(f"  ✅ Step 3: 扣款 ¥{amount}（用户={user_id}）")

    def _update_order_status(self, status: str):
        print(f"  ✅ Step 4: 更新订单状态 → {status}")

    # —— 补偿操作 ——
    def _unlock_inventory(self):
        print(f"  ↩️  补偿：释放库存")

    def _cancel_order(self):
        print(f"  ↩️  补偿：取消订单 {self.order_id}")


# 测试——多次运行，观察失败和补偿路径
print("\n  --- 测试 1：正常流程 ---")
saga1 = OrderSaga()
result1 = saga1.execute("user-001", "PROD-ABC", 2, 199.0)
print(f"  📋 结果: {result1}")

print("\n  --- 测试 2：支付失败（演示补偿）---")
saga2 = OrderSaga()
result2 = saga2.execute("user-002", "PROD-XYZ", 1, 599.0)
print(f"  📋 结果: {result2}")


# ============================================================
# 3. Saga vs 两阶段提交（2PC）
# ============================================================
print("\n" + "=" * 60)
print("3. Saga vs 两阶段提交（2PC）")
print("=" * 60)

print("""
两阶段提交（2PC）：
  Phase 1（准备）：协调者问所有参与者"准备好了吗？"
  Phase 2（提交）：所有人说 OK → 全部提交；有人说 NO → 全部回滚

  优点：强一致性（要么全成，要么全败）
  缺点：慢（等最慢的那个）、阻塞（参与者要锁资源等协调者通知）、
        单点（协调者挂了全卡住）

  互联网场景很少用 2PC 做跨服务事务。

Saga：
  优点：不阻塞（每个服务自己提交）、高可用（无协调者单点）
  缺点：最终一致性（在补偿完成之前，数据是"不一致"的）、
        补偿不一定完美（比如发出去的邮件撤不回）
""")


# ============================================================
# 4. 发件箱模式——保证 Saga 的可靠性
# ============================================================
print("=" * 60)
print("4. Saga + 发件箱 = 可靠的分布式事务")
print("=" * 60)

print("""
Saga 的弱点：
  如果 Step 1 成功、Step 2 执行之前进程崩溃了——
  没人知道 Step 1 已经执行，Step 2 永远不会被调用。

发件箱加持的 Saga：
  每个服务在自己的本地事务里：
    INSERT INTO orders VALUES (...)      ← 业务数据
    INSERT INTO outbox VALUES (...)       ← "我已完成了创建订单，下一步请锁库存"

  一个独立的消息中继进程扫描 outbox 表，投递到 MQ。

  这样：
  - 只要数据库事务提交了，消息就一定会被投递（at-least-once）
  - MQ 的消费者做幂等处理，应对重复投递
  - 即使某个服务临时挂了，消息也不会丢

这就是 B4（消息队列）+ B6（Saga）协同工作的完整图景。
""")

print("✅ B6 Saga 模式演示完成")
