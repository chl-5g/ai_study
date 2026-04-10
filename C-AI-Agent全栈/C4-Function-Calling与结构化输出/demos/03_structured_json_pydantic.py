#!/usr/bin/env python3
"""
03_structured_json_pydantic.py — 用 Pydantic 校验「模型应输出的 JSON」

依赖：pip install pydantic
运行：python3 03_structured_json_pydantic.py
"""

from __future__ import annotations

import json
from typing import Literal

try:
    from pydantic import BaseModel, Field, ValidationError
except ImportError:
    print("请安装: pip install pydantic")
    raise SystemExit(1) from None


class RouteDecision(BaseModel):
    """意图路由：演示结构化输出 schema。"""

    intent: Literal["weather", "refund", "other"] = Field(description="用户意图分类")
    confidence: float = Field(ge=0, le=1)
    reply_hint: str = Field(max_length=200)


def main() -> None:
    good = '{"intent":"weather","confidence":0.92,"reply_hint":"需要查天气API"}'
    bad = '{"intent":"unknown","confidence":2,"reply_hint":"x"}'

    print("合法 JSON →", RouteDecision.model_validate_json(good))

    try:
        RouteDecision.model_validate_json(bad)
    except ValidationError as e:
        print("\n非法 JSON 校验失败（生产可据此重试或降级）：\n", e)


if __name__ == "__main__":
    main()
