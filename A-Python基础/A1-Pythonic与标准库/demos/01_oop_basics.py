#!/usr/bin/env python3
"""
OOP 基础：类、继承、封装、多态
通过银行账户系统来演示面向对象编程的核心概念
"""


# ============================================================
# 1. 类的基本定义
# ============================================================
# 类是创建对象的蓝图/模板
# 对象是类的具体实例

class BankAccount:
    """
    银行账户类 —— 演示封装（Encapsulation）

    封装的核心思想：
    - 把数据（属性）和操作数据的方法绑在一起
    - 通过方法来访问/修改数据，而不是直接操作
    - Python 用下划线约定来表示"私有"（_单下划线=约定私有，__双下划线=名称改写）
    """

    # 类变量：所有实例共享的数据
    bank_name = "AI学习银行"
    total_accounts = 0  # 跟踪账户总数

    def __init__(self, owner: str, balance: float = 0.0):
        """
        构造方法：创建对象时自动调用

        参数:
            owner: 账户持有人姓名
            balance: 初始余额，默认为0

        self 是什么？
        - self 指向"当前这个对象自己"
        - 每个实例方法的第一个参数必须是 self
        - 调用时不需要手动传入，Python 自动处理
        """
        # 实例变量：每个对象独有的数据
        self.owner = owner            # 公开属性：外部可以直接访问
        self._balance = balance       # 约定私有：加单下划线，表示"请不要直接访问"
        self.__account_id = id(self)  # 强私有：双下划线，Python 会做名称改写

        # 每创建一个账户，总数 +1
        BankAccount.total_accounts += 1

    def deposit(self, amount: float) -> None:
        """
        存款方法
        为什么要通过方法操作而不是直接修改 _balance？
        因为我们可以在方法里加入验证逻辑，防止非法操作
        """
        if amount <= 0:
            print(f"  [错误] 存款金额必须为正数，收到: {amount}")
            return
        self._balance += amount
        print(f"  {self.owner} 存入 ¥{amount:.2f}，余额: ¥{self._balance:.2f}")

    def withdraw(self, amount: float) -> bool:
        """取款方法：返回是否成功"""
        if amount <= 0:
            print(f"  [错误] 取款金额必须为正数")
            return False
        if amount > self._balance:
            print(f"  [错误] 余额不足！当前余额: ¥{self._balance:.2f}")
            return False
        self._balance -= amount
        print(f"  {self.owner} 取出 ¥{amount:.2f}，余额: ¥{self._balance:.2f}")
        return True

    def get_balance(self) -> float:
        """获取余额（只读访问，这就是封装的好处）"""
        return self._balance

    def __str__(self) -> str:
        """
        __str__ 魔术方法：当 print(对象) 时调用
        返回给"用户"看的友好描述
        """
        return f"[{self.bank_name}] {self.owner} 的账户，余额: ¥{self._balance:.2f}"

    def __repr__(self) -> str:
        """
        __repr__ 魔术方法：给"开发者"看的精确描述
        在交互式环境中直接输入对象名时调用
        """
        return f"BankAccount(owner='{self.owner}', balance={self._balance})"


# ============================================================
# 2. 继承（Inheritance）
# ============================================================
# 继承让你基于已有的类创建新类，复用代码

class SavingsAccount(BankAccount):
    """
    储蓄账户：继承自 BankAccount
    新增功能：利息计算

    继承的核心思想：
    - 子类自动获得父类的所有属性和方法
    - 子类可以添加新的属性和方法
    - 子类可以覆盖（override）父类的方法
    """

    def __init__(self, owner: str, balance: float = 0.0, interest_rate: float = 0.03):
        """
        super().__init__() 调用父类的构造方法
        这样就不用重复写父类已有的初始化逻辑
        """
        super().__init__(owner, balance)  # 先调用父类的 __init__
        self.interest_rate = interest_rate  # 子类新增的属性

    def add_interest(self) -> None:
        """计算并添加利息（子类独有的方法）"""
        interest = self._balance * self.interest_rate
        self._balance += interest
        print(f"  {self.owner} 获得利息 ¥{interest:.2f}（利率 {self.interest_rate*100}%），余额: ¥{self._balance:.2f}")

    def __str__(self) -> str:
        """覆盖父类的 __str__，添加利率信息"""
        return f"[储蓄账户] {self.owner}，余额: ¥{self._balance:.2f}，年利率: {self.interest_rate*100}%"


class CreditAccount(BankAccount):
    """
    信用账户：可以透支
    演示方法覆盖（Override）—— 多态的基础
    """

    def __init__(self, owner: str, balance: float = 0.0, credit_limit: float = 5000.0):
        super().__init__(owner, balance)
        self.credit_limit = credit_limit

    def withdraw(self, amount: float) -> bool:
        """
        覆盖父类的 withdraw 方法
        信用账户允许透支（在额度范围内）

        这就是多态（Polymorphism）：
        - 同样是 withdraw() 方法
        - 不同类型的账户有不同的行为
        """
        if amount <= 0:
            print(f"  [错误] 取款金额必须为正数")
            return False
        if amount > self._balance + self.credit_limit:
            print(f"  [错误] 超出信用额度！余额: ¥{self._balance:.2f}，额度: ¥{self.credit_limit:.2f}")
            return False
        self._balance -= amount
        print(f"  {self.owner} 取出 ¥{amount:.2f}，余额: ¥{self._balance:.2f}")
        return True

    def __str__(self) -> str:
        return f"[信用账户] {self.owner}，余额: ¥{self._balance:.2f}，信用额度: ¥{self.credit_limit:.2f}"


# ============================================================
# 3. 多态（Polymorphism）演示
# ============================================================

def print_account_info(account: BankAccount) -> None:
    """
    多态演示函数：
    接收任何 BankAccount 类型（包括子类）的对象
    调用同一个方法 (str/withdraw)，但不同类型的对象表现不同
    """
    print(f"  {account}")  # 自动调用对应类的 __str__


# ============================================================
# 主程序
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("1. 基本类的使用")
    print("=" * 60)

    # 创建对象（实例化）
    acc1 = BankAccount("张三", 1000)
    acc1.deposit(500)
    acc1.withdraw(200)
    acc1.withdraw(5000)  # 余额不足
    print(f"  余额查询: ¥{acc1.get_balance():.2f}")
    print(f"  print(对象): {acc1}")      # 调用 __str__
    print(f"  repr(对象): {repr(acc1)}")  # 调用 __repr__

    print()
    print("=" * 60)
    print("2. 继承与方法覆盖")
    print("=" * 60)

    savings = SavingsAccount("李四", 10000, interest_rate=0.05)
    savings.deposit(5000)      # 继承自父类的方法
    savings.add_interest()     # 子类独有的方法
    print(f"  {savings}")

    print()
    credit = CreditAccount("王五", 1000, credit_limit=3000)
    credit.withdraw(2000)      # 覆盖的方法：允许透支
    print(f"  {credit}")

    print()
    print("=" * 60)
    print("3. 多态演示")
    print("=" * 60)

    # 不同类型的对象，同一个函数，不同的行为
    accounts = [acc1, savings, credit]
    for acc in accounts:
        print_account_info(acc)

    print()
    print("=" * 60)
    print("4. 类变量 vs 实例变量")
    print("=" * 60)
    print(f"  银行名称（类变量，所有账户共享）: {BankAccount.bank_name}")
    print(f"  账户总数（类变量）: {BankAccount.total_accounts}")

    print()
    print("=" * 60)
    print("5. isinstance() 类型检查")
    print("=" * 60)
    print(f"  savings 是 SavingsAccount? {isinstance(savings, SavingsAccount)}")
    print(f"  savings 是 BankAccount?    {isinstance(savings, BankAccount)}")  # True! 子类也是父类
    print(f"  savings 是 CreditAccount?  {isinstance(savings, CreditAccount)}")
