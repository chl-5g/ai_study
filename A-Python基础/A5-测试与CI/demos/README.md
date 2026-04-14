# A5 测试与 CI — `demos/` 说明

```bash
cd demos
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest -v
pytest -v test_06_fastapi.py
```

| 文件 | 要点 |
|------|------|
| `test_01_basics.py` | 断言、`pytest.raises` |
| `test_02_fixtures.py` | fixture 作用域、依赖 |
| `test_03_parametrize.py` | `@pytest.mark.parametrize` |
| `test_04_mock.py` | `unittest.mock.patch` |
| `test_05_monkeypatch.py` | `monkeypatch` 改环境变量 |
| `app_minimal.py` | 供 FastAPI 测试用的最小应用 |
| `test_06_fastapi.py` | `TestClient` / `httpx.AsyncClient` + `ASGITransport` |
| `test_07_async.py` | `@pytest.mark.asyncio` |
| `conftest.py` | 共享 fixture 示例 |

GitHub Actions 示例见本章 `理论讲解.md` 第 15 节；也可在本目录自行添加 `.github/workflows/ci.yml` 指向 `pip install -r demos/requirements.txt && pytest demos`。
