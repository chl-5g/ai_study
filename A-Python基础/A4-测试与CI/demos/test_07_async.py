"""纯 asyncio 函数测试"""

import asyncio

import pytest


async def double(x: int) -> int:
    await asyncio.sleep(0)
    return x * 2


@pytest.mark.asyncio
async def test_double():
    assert await double(21) == 42
