"""Orders: create, list, get, change status (staff only)."""
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from app.auth import require_staff
from app.db import get_db
from app.errors import ApiError
from app.schemas import Order, OrderCreate, OrderStatusUpdate, OrdersResponse

router = APIRouter(tags=["orders"])


def _row_to_order(row) -> Order:
    return Order(
        id=row["id"],
        table_id=row["table_id"],
        items=json.loads(row["items"]),
        total=row["total"],
        status=row["status"],
        created_at=row["created_at"],
    )


@router.get("/orders", response_model=OrdersResponse)
def list_orders(conn=Depends(get_db)):
    rows = conn.execute("SELECT * FROM orders ORDER BY id").fetchall()
    return OrdersResponse(orders=[_row_to_order(r) for r in rows])


@router.post("/orders", response_model=Order, status_code=201)
def create_order(body: OrderCreate, conn=Depends(get_db)):
    if conn.execute("SELECT id FROM tables WHERE id = ?", (body.table_id,)).fetchone() is None:
        raise ApiError(404, "table_not_found", "table {} does not exist".format(body.table_id))
    items = []
    total = 0.0
    for entry in body.items:
        row = conn.execute(
            "SELECT * FROM menu_items WHERE id = ?", (entry.menu_item_id,)
        ).fetchone()
        if row is None:
            raise ApiError(
                404, "menu_item_not_found", "menu item {} does not exist".format(entry.menu_item_id)
            )
        if not row["available"]:
            raise ApiError(400, "item_unavailable", '"{}" is not available'.format(row["name"]))
        items.append(
            {
                "menu_item_id": row["id"],
                "name": row["name"],
                "price": row["price"],
                "quantity": entry.quantity,
            }
        )
        total += row["price"] * entry.quantity
    created_at = datetime.now(timezone.utc).isoformat()
    cursor = conn.execute(
        "INSERT INTO orders (table_id, items, total, created_at) VALUES (?, ?, ?, ?)",
        (body.table_id, json.dumps(items, ensure_ascii=False), round(total, 2), created_at),
    )
    row = conn.execute("SELECT * FROM orders WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return _row_to_order(row)


@router.get("/orders/{order_id}", response_model=Order)
def get_order(order_id: int, conn=Depends(get_db)):
    row = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    if row is None:
        raise ApiError(404, "order_not_found", "order {} does not exist".format(order_id))
    return _row_to_order(row)


@router.patch(
    "/orders/{order_id}/status",
    response_model=Order,
    dependencies=[Depends(require_staff)],
)
def update_order_status(order_id: int, body: OrderStatusUpdate, conn=Depends(get_db)):
    row = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    if row is None:
        raise ApiError(404, "order_not_found", "order {} does not exist".format(order_id))
    conn.execute("UPDATE orders SET status = ? WHERE id = ?", (body.status, order_id))
    updated = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    return _row_to_order(updated)
