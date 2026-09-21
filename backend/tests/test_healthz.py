"""T5 /healthz 接口测试。"""

from fastapi.testclient import TestClient

from app.main import app


def test_healthz_returns_200_ok():
    client = TestClient(app)
    resp = client.get("/healthz")

    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
