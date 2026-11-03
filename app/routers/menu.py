"""GET /menu — menu with category and availability filters."""
from typing import Optional

from fastapi import APIRouter, Depends

from app.db import get_db
from app.schemas import MenuItem, MenuResponse

router = APIRouter(tags=["menu"])


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
    items = [
        MenuItem(
            id=row["id"],
            name=row["name"],
            category=row["category"],
            price=row["price"],
            description=row["description"],
            available=bool(row["available"]),
        )
        for row in rows
    ]
    return MenuResponse(items=items)
