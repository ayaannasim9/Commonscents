from fastapi.testclient import TestClient

from counterpart.app import create_app


def test_health():
    assert TestClient(create_app(":memory:")).get("/health").json() == {"status": "ok"}
