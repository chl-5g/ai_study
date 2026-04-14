"""
02_pydantic_deep.py — Pydantic V2 深度演示
纯 Pydantic，不需要 FastAPI 服务器，直接运行即可

演示：模型定义、字段校验、嵌套模型、自定义验证器、模型继承、schema 导出

运行：python3 02_pydantic_deep.py
安装：pip3 install pydantic
"""

from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
    ConfigDict,
    EmailStr,
    computed_field,
)
from datetime import datetime, date
from enum import Enum
from typing import Annotated
import json


# ============================================================
# 1. 基础模型定义与字段校验
# ============================================================

print("=" * 60)
print("1. 基础模型定义与字段校验")
print("=" * 60)


class UserBasic(BaseModel):
    """基础用户模型 — 演示各种 Field 校验"""

    name: str = Field(
        ...,                        # ... 表示必填
        min_length=2,
        max_length=50,
        description="用户名，2-50个字符",
    )
    age: int = Field(
        ge=0,                       # >= 0
        le=150,                     # <= 150
        description="年龄",
    )
    email: str = Field(
        pattern=r"^[\w.-]+@[\w.-]+\.\w+$",  # 正则校验
        description="邮箱地址",
    )
    score: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="分数，0-100",
    )
    tags: list[str] = Field(
        default_factory=list,       # 可变默认值用 default_factory
        description="用户标签",
    )


# 正常创建
user = UserBasic(name="Allen", age=30, email="allen@example.com", score=95.5, tags=["dev"])
print(f"创建成功: {user}")
print(f"转字典: {user.model_dump()}")
print(f"转JSON: {user.model_dump_json(indent=2)}")

# 校验失败示例
print("\n--- 校验失败示例 ---")
try:
    UserBasic(name="A", age=200, email="invalid-email")
except Exception as e:
    print(f"校验错误: {e}")


# ============================================================
# 2. 嵌套模型
# ============================================================

print("\n" + "=" * 60)
print("2. 嵌套模型")
print("=" * 60)


class Address(BaseModel):
    """地址模型"""
    province: str
    city: str
    street: str
    zip_code: str = Field(pattern=r"^\d{6}$", description="6位邮编")


class Company(BaseModel):
    """公司模型"""
    name: str
    address: Address                # 嵌套 Address 模型
    employee_count: int = Field(ge=1)


class UserProfile(BaseModel):
    """用户档案 — 演示多层嵌套"""
    user: UserBasic                 # 嵌套 UserBasic
    company: Company | None = None  # 可选嵌套
    hobbies: list[str] = []
    metadata: dict[str, str] = {}   # 字典类型


# 从嵌套字典直接创建（Pydantic 自动递归解析）
profile_data = {
    "user": {
        "name": "Allen",
        "age": 30,
        "email": "allen@example.com",
    },
    "company": {
        "name": "A公司",
        "address": {
            "province": "浙江",
            "city": "杭州",
            "street": "软件园A区",
            "zip_code": "310000",
        },
        "employee_count": 200,
    },
    "hobbies": ["coding", "reading"],
}

profile = UserProfile(**profile_data)
print(f"嵌套模型: {profile.user.name} @ {profile.company.name}")
print(f"公司地址: {profile.company.address.city}")


# ============================================================
# 3. 自定义验证器（field_validator / model_validator）
# ============================================================

print("\n" + "=" * 60)
print("3. 自定义验证器")
print("=" * 60)


class OrderItem(BaseModel):
    """订单模型 — 演示自定义验证器"""

    product_name: str
    price: float = Field(gt=0)
    quantity: int = Field(ge=1)
    discount: float = Field(default=0.0, ge=0.0)

    # --- field_validator：校验单个字段 ---

    @field_validator("product_name")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        """商品名不能是纯空白"""
        if not v.strip():
            raise ValueError("商品名不能为空")
        return v.strip()  # 顺便做清洗（去掉首尾空格）

    @field_validator("price")
    @classmethod
    def price_precision(cls, v: float) -> float:
        """价格保留两位小数"""
        return round(v, 2)

    # --- model_validator：校验整个模型（可以访问多个字段做交叉校验）---

    @model_validator(mode="after")
    def check_discount_not_exceed_total(self):
        """折扣不能超过总价"""
        total = self.price * self.quantity
        if self.discount > total:
            raise ValueError(f"折扣({self.discount}) 不能超过总价({total})")
        return self

    # --- computed_field：计算属性，会出现在序列化结果和 schema 中 ---

    @computed_field
    @property
    def total_price(self) -> float:
        """实付金额"""
        return round(self.price * self.quantity - self.discount, 2)


order = OrderItem(product_name="  MacBook Pro  ", price=14999.999, quantity=2, discount=1000)
print(f"订单: {order}")
print(f"商品名(已清洗): '{order.product_name}'")
print(f"价格(已四舍五入): {order.price}")
print(f"实付金额(computed_field): {order.total_price}")

# 交叉校验失败
print("\n--- 折扣超过总价 ---")
try:
    OrderItem(product_name="test", price=100, quantity=1, discount=200)
except Exception as e:
    print(f"校验错误: {e}")


# mode="before" 示例：在类型转换之前执行
class FlexibleDate(BaseModel):
    """演示 mode='before' — 在类型转换前做预处理"""
    date: date

    @field_validator("date", mode="before")
    @classmethod
    def parse_date(cls, v):
        """支持多种日期格式"""
        if isinstance(v, str):
            # 支持 "2024-01-01" 和 "2024/01/01" 两种格式
            return v.replace("/", "-")
        return v


print(f"\n灵活日期解析: {FlexibleDate(date='2024/06/15')}")


# ============================================================
# 4. 模型继承（FastAPI 最佳实践：Base → Create → Response）
# ============================================================

print("\n" + "=" * 60)
print("4. 模型继承")
print("=" * 60)


class Role(str, Enum):
    """用户角色枚举"""
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


# Base：共享字段
class UserBase(BaseModel):
    username: str = Field(min_length=3, max_length=30)
    email: str
    role: Role = Role.USER


# Create：创建时额外需要密码
class UserCreate(UserBase):
    password: str = Field(min_length=8, description="密码，至少8位")

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        """密码强度校验"""
        if not any(c.isupper() for c in v):
            raise ValueError("密码必须包含大写字母")
        if not any(c.isdigit() for c in v):
            raise ValueError("密码必须包含数字")
        return v


# Update：所有字段可选
class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=3, max_length=30)
    email: str | None = None
    role: Role | None = None


# Response：返回给前端，不包含密码，但包含 id 和时间戳
class UserResponse(UserBase):
    id: int
    created_at: datetime
    is_active: bool = True

    # 支持从 ORM 对象（如 SQLAlchemy model）直接构造
    model_config = ConfigDict(from_attributes=True)


# 模拟 ORM 对象（普通 class，不是 Pydantic 模型）
class FakeORMUser:
    def __init__(self):
        self.id = 1
        self.username = "allen"
        self.email = "allen@example.com"
        self.role = Role.ADMIN
        self.created_at = datetime(2024, 1, 1, 12, 0, 0)
        self.is_active = True
        self.password_hash = "hashed_xxx"  # 敏感字段，不会出现在 Response 中


orm_user = FakeORMUser()
response = UserResponse.model_validate(orm_user)  # 从 ORM 对象构造
print(f"从 ORM 构造: {response}")
print(f"注意：密码不会泄漏到响应中")

# 创建用户（密码校验）
user_create = UserCreate(username="newuser", email="new@test.com", password="MyPass123")
print(f"\n创建用户: {user_create.model_dump(exclude={'password'})}")


# ============================================================
# 5. Schema 导出（AI Function Calling）
# ============================================================

print("\n" + "=" * 60)
print("5. Schema 导出（给 AI Function Calling 用）")
print("=" * 60)


class WebSearch(BaseModel):
    """搜索互联网获取最新信息"""
    query: str = Field(description="搜索关键词")
    max_results: int = Field(default=5, ge=1, le=20, description="最大返回结果数")
    language: str = Field(default="zh", description="搜索语言，如 zh/en/ja")


class SendEmail(BaseModel):
    """发送电子邮件"""
    to: list[str] = Field(description="收件人邮箱列表")
    subject: str = Field(max_length=200, description="邮件主题")
    body: str = Field(description="邮件正文，支持 Markdown")
    is_urgent: bool = Field(default=False, description="是否紧急")


class CreateCalendarEvent(BaseModel):
    """创建日历事件"""
    title: str = Field(description="事件标题")
    start_time: datetime = Field(description="开始时间，ISO 8601 格式")
    end_time: datetime = Field(description="结束时间，ISO 8601 格式")
    location: str | None = Field(default=None, description="地点")
    attendees: list[str] = Field(default_factory=list, description="参与者邮箱列表")


# 导出 JSON Schema — 直接可用于 OpenAI / Anthropic 的 Function Calling
tools = [WebSearch, SendEmail, CreateCalendarEvent]

print("以下 schema 可直接用于 LLM Function Calling:\n")
for tool_cls in tools:
    schema = tool_cls.model_json_schema()
    print(f"--- {tool_cls.__name__} ---")
    print(json.dumps(schema, indent=2, ensure_ascii=False))
    print()


# 转换为 OpenAI Function Calling 格式的示例
def pydantic_to_openai_tool(model_cls: type[BaseModel]) -> dict:
    """将 Pydantic 模型转换为 OpenAI tool 格式"""
    schema = model_cls.model_json_schema()
    return {
        "type": "function",
        "function": {
            "name": model_cls.__name__,
            "description": model_cls.__doc__ or "",
            "parameters": schema,
        }
    }


print("=== OpenAI Tool 格式 ===")
openai_tools = [pydantic_to_openai_tool(t) for t in tools]
print(json.dumps(openai_tools, indent=2, ensure_ascii=False))


# ============================================================
# 6. 高级特性
# ============================================================

print("\n" + "=" * 60)
print("6. 高级特性")
print("=" * 60)


# 6.1 模型配置
class StrictUser(BaseModel):
    """严格模式 — 不允许额外字段，不做类型强转"""
    model_config = ConfigDict(
        strict=True,           # 严格类型（"123" 不会自动转 int）
        extra="forbid",        # 禁止额外字段
        frozen=True,           # 不可变（创建后不能修改属性）
        str_strip_whitespace=True,  # 自动去除字符串首尾空格
    )
    name: str
    age: int


print("--- 严格模式 ---")
strict = StrictUser(name="  Allen  ", age=30)
print(f"自动去空格: '{strict.name}'")

try:
    StrictUser(name="Allen", age="30")  # 严格模式不允许 "30" 转 int
except Exception as e:
    print(f"严格模式错误: {type(e).__name__}")

try:
    StrictUser(name="Allen", age=30, extra_field="xxx")  # 不允许额外字段
except Exception as e:
    print(f"额外字段错误: {type(e).__name__}")


# 6.2 泛型模型 — 通用分页响应
from typing import Generic, TypeVar

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """通用分页响应 — 用泛型让同一个模型适配不同数据类型"""
    total: int
    page: int
    page_size: int
    data: list[T]


# 使用泛型
users_page = PaginatedResponse[UserResponse](
    total=100,
    page=1,
    page_size=10,
    data=[
        UserResponse(
            id=1, username="allen", email="a@b.com",
            role=Role.ADMIN, created_at=datetime.now()
        )
    ]
)
print(f"\n泛型分页: {users_page.model_dump_json(indent=2)}")


# 6.3 序列化控制
class SensitiveData(BaseModel):
    """演示序列化时排除敏感字段"""
    username: str
    password: str
    api_key: str
    public_info: str


data = SensitiveData(
    username="allen", password="secret", api_key="sk-xxx", public_info="hello"
)
# 排除敏感字段
safe = data.model_dump(exclude={"password", "api_key"})
print(f"\n排除敏感字段: {safe}")

# 只包含指定字段
minimal = data.model_dump(include={"username", "public_info"})
print(f"只包含指定字段: {minimal}")


print("\n" + "=" * 60)
print("全部演示完成！")
print("=" * 60)
