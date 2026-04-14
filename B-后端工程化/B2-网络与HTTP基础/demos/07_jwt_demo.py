#!/usr/bin/env python3
"""
JWT（JSON Web Token）生成与验证
现代 API 认证的主流方案

安装：pip3 install PyJWT
"""

# ============================================================
# JWT 原理
# ============================================================
#
# JWT 由三部分组成，用 . 连接：
#   Header.Payload.Signature
#
# Header:  {"alg": "HS256", "typ": "JWT"}  → Base64 编码
# Payload: {"user_id": 1, "exp": 1234567}  → Base64 编码
# Signature: HMAC-SHA256(Header + "." + Payload, secret_key)
#
# 特点：
# - 服务端无状态（不需要存 Session）
# - Token 自包含用户信息
# - 签名防篡改（但不加密！Payload 可被 Base64 解码看到）
# - 适合微服务、API 认证

import jwt  # PyJWT 库
import time
import json
import base64
from datetime import datetime, timedelta, timezone


# 密钥（生产环境应该用环境变量，绝不硬编码！）
SECRET_KEY = "my-super-secret-key-请勿在生产环境使用"
ALGORITHM = "HS256"


def create_token(user_id: int, username: str, expires_minutes: int = 30) -> str:
    """
    创建 JWT Token

    Payload 中常见的字段（称为 Claims）：
    - sub: Subject（用户标识）
    - exp: Expiration（过期时间，Unix 时间戳）
    - iat: Issued At（签发时间）
    - iss: Issuer（签发者）
    - aud: Audience（受众）
    - 自定义字段：user_id, role 等
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),           # 用户标识
        "username": username,           # 自定义字段
        "role": "admin",                # 自定义字段
        "iat": now,                     # 签发时间
        "exp": now + timedelta(minutes=expires_minutes),  # 过期时间
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


def verify_token(token: str) -> dict:
    """
    验证并解码 JWT Token

    验证包括：
    1. 签名是否正确（防篡改）
    2. 是否过期（exp）
    3. 是否在有效期内（nbf, 如果设置了）
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {"valid": True, "payload": payload}
    except jwt.ExpiredSignatureError:
        return {"valid": False, "error": "Token 已过期"}
    except jwt.InvalidTokenError as e:
        return {"valid": False, "error": f"Token 无效: {e}"}


def decode_without_verify(token: str) -> dict:
    """
    不验证直接解码（仅用于查看内容）
    注意：永远不要在生产环境中信任未验证的 Token！
    """
    # JWT 是 Base64 编码，任何人都能解码看到内容
    parts = token.split(".")
    if len(parts) != 3:
        return {"error": "不是有效的 JWT 格式"}

    # 解码 Header
    header = json.loads(base64.urlsafe_b64decode(parts[0] + "=="))
    # 解码 Payload
    payload = json.loads(base64.urlsafe_b64decode(parts[1] + "=="))

    return {"header": header, "payload": payload}


if __name__ == "__main__":
    print("=" * 60)
    print("1. 创建 JWT Token")
    print("=" * 60)

    token = create_token(user_id=42, username="allen", expires_minutes=30)
    print(f"  Token: {token[:50]}...")
    print(f"  长度: {len(token)} 字符")

    # 分析 Token 结构
    parts = token.split(".")
    print(f"\n  Token 由 3 部分组成（用 . 分隔）:")
    print(f"    Header:    {parts[0][:30]}...")
    print(f"    Payload:   {parts[1][:30]}...")
    print(f"    Signature: {parts[2][:30]}...")

    print()
    print("=" * 60)
    print("2. 解码查看内容（Base64 解码，不验证）")
    print("=" * 60)

    decoded = decode_without_verify(token)
    print(f"  Header:  {json.dumps(decoded['header'], indent=4)}")
    print(f"  Payload: {json.dumps(decoded['payload'], indent=4, default=str)}")
    print(f"\n  ⚠️  JWT 不是加密！任何人都能看到 Payload 内容")
    print(f"  ⚠️  签名只防篡改，不防窥探。敏感信息不要放在 Payload 中")

    print()
    print("=" * 60)
    print("3. 验证 Token")
    print("=" * 60)

    # 正常验证
    result = verify_token(token)
    print(f"  正常验证: {result['valid']}")
    print(f"  用户信息: user_id={result['payload']['sub']}, username={result['payload']['username']}")

    # 篡改 Token（修改一个字符）
    tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
    result = verify_token(tampered)
    print(f"\n  篡改后验证: {result['valid']}")
    print(f"  错误信息: {result.get('error')}")

    # 过期 Token
    expired_token = create_token(user_id=1, username="test", expires_minutes=-1)
    result = verify_token(expired_token)
    print(f"\n  过期 Token: {result['valid']}")
    print(f"  错误信息: {result.get('error')}")

    print()
    print("=" * 60)
    print("4. JWT 在 API 中的使用方式")
    print("=" * 60)
    print("""
  登录流程:
    1. POST /api/login  (body: {"username": "allen", "password": "xxx"})
    2. 服务端验证密码，成功后返回 JWT Token
    3. 客户端保存 Token（localStorage / 内存）

  后续请求:
    GET /api/profile
    Headers:
      Authorization: Bearer eyJhbGci...  ← 在请求头中携带 Token

  服务端验证:
    1. 从 Authorization 头提取 Token
    2. jwt.decode() 验证签名和过期时间
    3. 从 Payload 获取 user_id
    4. 查数据库获取用户信息

  Token 刷新策略:
    - 短期 Access Token（15-30 分钟）+ 长期 Refresh Token（7-30 天）
    - Access Token 过期后用 Refresh Token 获取新的 Access Token
    - Refresh Token 过期则需要重新登录
    """)

    print("=" * 60)
    print("5. JWT vs Session 选型")
    print("=" * 60)
    print("""
  JWT 适合:
    ✓ 微服务架构（服务间无需共享 Session）
    ✓ 移动端/SPA 应用
    ✓ 第三方 API 认证
    ✓ 无状态水平扩展

  Session 适合:
    ✓ 传统服务端渲染 Web 应用
    ✓ 需要服务端主动踢人下线
    ✓ 需要即时吊销权限

  企业级 AI Agent 平台 → 大概率用 JWT
    """)
