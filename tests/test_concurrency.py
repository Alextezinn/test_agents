import concurrent.futures

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("RESTAURANT_DB", str(tmp_path / "test.db"))
    monkeypatch.setenv("STAFF_TOKEN", "test-staff-token")
    with TestClient(app) as test_client:
        yield test_client


def test_concurrent_menu_requests(client):
    def hit(_):
        return client.get("/api/v1/menu").status_code

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        codes = list(pool.map(hit, range(24)))
    assert codes == [200] * 24
