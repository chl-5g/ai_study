"""mock：替换模块内函数"""

from unittest.mock import patch


def fetch_label() -> str:
    raise RuntimeError("should be mocked")


def test_with_patch():
    with patch("test_04_mock.fetch_label", return_value="ok"):
        assert fetch_label() == "ok"
