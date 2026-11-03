"""API tests for the Restaurant API."""
import pytest
from fastapi.testclient import TestClient

from main import app

STAFF_TOKEN = "test-staff-token"

RESERVATION = {
    "table_id": 3,
    "guest_name": "Иван Петров",
    "phone": "+7 900 123-45-67",
    "time": "2026-11-10T19:00:00+03:00",
    "guests_count": 2,
}


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("RESTAURANT_DB", str(tmp_path / "test.db"))
    monkeypatch.setenv("STAFF_TOKEN", STAFF_TOKEN)
    with TestClient(app) as test_client:
        yield test_client


def create_order(client, table_id=2, items=None):
    if items is None:
        items = [{"menu_item_id": 1, "quantity": 2}]
    res = client.post("/api/v1/orders", json={"table_id": table_id, "items": items})
    assert res.status_code == 201
    return res.json()["id"]


# --- menu ---

def test_menu_returns_only_available_by_default(client):
    res = client.get("/api/v1/menu")
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) == 9  # 10 seeded, 1 unavailable
    assert all(item["available"] for item in items)


def test_menu_category_filter(client):
    res = client.get("/api/v1/menu", params={"category": "salads"})
    items = res.json()["items"]
    assert [item["name"] for item in items] == ["Цезарь с курицей", "Греческий салат"]


def test_menu_available_false_returns_unavailable(client):
    res = client.get("/api/v1/menu", params={"available": "false"})
    items = res.json()["items"]
    assert len(items) == 1
    assert items[0]["name"] == "Устрицы"
    assert not items[0]["available"]


def test_menu_unknown_category_returns_empty(client):
    res = client.get("/api/v1/menu", params={"category": "sushi"})
    assert res.json()["items"] == []


# --- tables ---

def test_tables(client):
    res = client.get("/api/v1/tables")
    tables = res.json()["tables"]
    assert len(tables) == 6
    assert tables[0] == {"id": 1, "number": 1, "seats": 2}


# --- reservations ---

def test_create_reservation_sets_end_time_plus_2h(client):
    res = client.post("/api/v1/reservations", json=RESERVATION)
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "active"
    assert data["time"] == "2026-11-10T19:00:00+03:00"
    assert data["end_time"] == "2026-11-10T21:00:00+03:00"


def test_reservation_unknown_table(client):
    body = dict(RESERVATION, table_id=99)
    res = client.post("/api/v1/reservations", json=body)
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "table_not_found"


def test_reservation_too_many_guests(client):
    body = dict(RESERVATION, table_id=1, guests_count=3)  # table 1 has 2 seats
    res = client.post("/api/v1/reservations", json=body)
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "seats_exceeded"


def test_reservation_invalid_time(client):
    body = dict(RESERVATION, time="not-a-time")
    res = client.post("/api/v1/reservations", json=body)
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "validation_error"


def test_cancel_reservation(client):
    res = client.post("/api/v1/reservations", json=RESERVATION)
    reservation_id = res.json()["id"]
    res = client.delete("/api/v1/reservations/{}".format(reservation_id))
    assert res.status_code == 200
    assert res.json()["status"] == "cancelled"
    listed = client.get("/api/v1/reservations").json()["reservations"]
    assert [r["status"] for r in listed] == ["cancelled"]


# --- orders ---

def test_create_order_computes_total(client):
    res = client.post(
        "/api/v1/orders",
        json={
            "table_id": 2,
            "items": [{"menu_item_id": 1, "quantity": 2}, {"menu_item_id": 9, "quantity": 1}],
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "new"
    assert data["total"] == 540.0 * 2 + 180.0
    assert [i["name"] for i in data["items"]] == ["Цезарь с курицей", "Эспрессо"]


def test_create_order_rejects_unavailable_item(client):
    res = client.post(
        "/api/v1/orders", json={"table_id": 2, "items": [{"menu_item_id": 10, "quantity": 1}]}
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "item_unavailable"


def test_create_order_unknown_item(client):
    res = client.post(
        "/api/v1/orders", json={"table_id": 2, "items": [{"menu_item_id": 999, "quantity": 1}]}
    )
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "menu_item_not_found"


def test_create_order_unknown_table(client):
    res = client.post(
        "/api/v1/orders", json={"table_id": 99, "items": [{"menu_item_id": 1, "quantity": 1}]}
    )
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "table_not_found"


def test_create_order_empty_items_rejected(client):
    res = client.post("/api/v1/orders", json={"table_id": 2, "items": []})
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "validation_error"


# --- order status (staff only) ---

def test_patch_status_requires_token(client):
    order_id = create_order(client)
    res = client.patch("/api/v1/orders/{}/status".format(order_id), json={"status": "preparing"})
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "unauthorized"


def test_patch_status_rejects_wrong_token(client):
    order_id = create_order(client)
    res = client.patch(
        "/api/v1/orders/{}/status".format(order_id),
        json={"status": "preparing"},
        headers={"Authorization": "Bearer wrong-token"},
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "forbidden"


def test_patch_status_ok(client):
    order_id = create_order(client)
    res = client.patch(
        "/api/v1/orders/{}/status".format(order_id),
        json={"status": "preparing"},
        headers={"Authorization": "Bearer {}".format(STAFF_TOKEN)},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "preparing"
    listed = client.get("/api/v1/orders").json()["orders"]
    assert any(o["id"] == order_id and o["status"] == "preparing" for o in listed)


def test_patch_status_invalid_value(client):
    order_id = create_order(client)
    res = client.patch(
        "/api/v1/orders/{}/status".format(order_id),
        json={"status": "banned"},
        headers={"Authorization": "Bearer {}".format(STAFF_TOKEN)},
    )
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "validation_error"


def test_patch_status_unknown_order(client):
    res = client.patch(
        "/api/v1/orders/999/status",
        json={"status": "preparing"},
        headers={"Authorization": "Bearer {}".format(STAFF_TOKEN)},
    )
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "order_not_found"


# --- error format ---

def test_unknown_route_uses_unified_error_format(client):
    res = client.get("/api/v1/nope")
    assert res.status_code == 404
    body = res.json()
    assert set(body.keys()) == {"error"}
    assert "code" in body["error"] and "message" in body["error"]


def test_unhandled_error_uses_unified_error_format(tmp_path, monkeypatch):
    monkeypatch.setenv("RESTAURANT_DB", str(tmp_path / "test.db"))

    def boom():
        raise RuntimeError("boom")

    app.add_api_route("/api/v1/_boom", boom, methods=["GET"])
    try:
        with TestClient(app, raise_server_exceptions=False) as test_client:
            res = test_client.get("/api/v1/_boom")
    finally:
        app.router.routes = [
            route for route in app.router.routes if getattr(route, "path", None) != "/api/v1/_boom"
        ]
    assert res.status_code == 500
    assert res.json() == {
        "error": {"code": "internal_error", "message": "internal server error"}
    }
