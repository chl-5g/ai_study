"""共享 fixture 示例（pytest 自动加载同目录及子目录的 conftest.py）"""

import pytest


@pytest.fixture
def sample_user() -> dict:
    return {"id": 1, "name": "demo"}


@pytest.fixture(scope="module")
def module_counter() -> dict:
    return {"n": 0}
