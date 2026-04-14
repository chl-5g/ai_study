"""参数化：一组输入对应同一测试逻辑"""

import pytest


@pytest.mark.parametrize("a,b,expect", [(1, 2, 3), (0, 0, 0), (-1, 1, 0)])
def test_add_param(a, b, expect):
    assert a + b == expect
