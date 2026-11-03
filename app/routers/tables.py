"""GET /tables — restaurant tables."""
from fastapi import APIRouter, Depends

from app.db import get_db
from app.schemas import Table, TablesResponse

router = APIRouter(tags=["tables"])


@router.get("/tables", response_model=TablesResponse)
def list_tables(conn=Depends(get_db)):
    rows = conn.execute("SELECT * FROM tables ORDER BY id").fetchall()
    return TablesResponse(
        tables=[Table(id=r["id"], number=r["number"], seats=r["seats"]) for r in rows]
    )
