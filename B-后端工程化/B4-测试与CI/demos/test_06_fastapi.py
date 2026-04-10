"""FastAPI：同步 TestClient 与异步 httpx + ASGITransport"""

import httpx
import pytest
from fastapi.testclient import TestClient

from app_minimal import app


def test_health_sync():
    c = TestClient(app)
    r = c.get("/health")
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_item_query():
    c = TestClient(app)
    r = c.get("/items/42?q=hi")
    assert r.status_code == 200
    assert r.json() == {"item_id": 42, "q": "hi"}


@pytest.mark.asyncio
async def test_health_async():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/health")
        assert r.status_code == 200
