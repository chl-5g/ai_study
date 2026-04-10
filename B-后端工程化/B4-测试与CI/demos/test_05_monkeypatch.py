"""monkeypatch：临时改环境变量 / 属性"""

import os


def test_env_flag(monkeypatch):
    monkeypatch.setenv("DEMO_FLAG", "yes")
    assert os.environ.get("DEMO_FLAG") == "yes"
