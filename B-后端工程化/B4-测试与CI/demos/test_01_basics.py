"""pytest 基础：简单函数测试与异常断言"""


def add(a: int, b: int) -> int:
    return a + b


def test_add():
    assert add(2, 3) == 5


def test_div_zero():
    import pytest

    with pytest.raises(ZeroDivisionError):
        _ = 1 / 0
