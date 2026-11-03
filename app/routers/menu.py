"""Menu: list items with category and availability filters, create item (staff only)."""
from typing import Optional

from fastapi import APIRouter, Depends

from app.auth import require_staff
from app.db import get_db
from app.schemas import MenuItem, MenuItemCreate, MenuResponse

router = APIRouter(tags=["menu"])


def _row_to_item(row) -> MenuItem:
    return MenuItem(
        id=row["id"],
        name=row["name"],
        category=row["category"],
        price=row["price"],
        description=row["description"],
        available=bool(row["available"]),
    )


@router.get("/menu", response_model=MenuResponse)
def get_menu(
    category: Optional[str] = None,
    available: bool = True,
    conn=Depends(get_db),
):
    query = "SELECT * FROM menu_items WHERE available = ?"
    params = [int(available)]
    if category is not None:
        query += " AND category = ?"
        params.append(category)
    rows = conn.execute(query + " ORDER BY id", params).fetchall()
    return MenuResponse(items=[_row_to_item(row) for row in rows])


@router.post(
    "/menu",
    response_model=MenuItem,
    status_code=201,
    dependencies=[Depends(require_staff)],
)
def create_menu_item(body: MenuItemCreate, conn=Depends(get_db)):
    cursor = conn.execute(
        "INSERT INTO menu_items (name, category, price, description, available) "
        "VALUES (?, ?, ?, ?, ?)",
        (body.name, body.category, body.price, body.description, int(body.available)),
    )
    row = conn.execute("SELECT * FROM menu_items WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return _row_to_item(row)
