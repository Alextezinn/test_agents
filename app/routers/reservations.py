"""Reservations: create, list, get, cancel."""
from datetime import timedelta

from fastapi import APIRouter, Depends

from app.db import get_db
from app.errors import ApiError
from app.schemas import Reservation, ReservationCreate, ReservationsResponse
from app.time_utils import RESERVATION_DURATION_HOURS, parse_iso8601

router = APIRouter(tags=["reservations"])


def _row_to_reservation(row) -> Reservation:
    return Reservation(
        id=row["id"],
        table_id=row["table_id"],
        guest_name=row["guest_name"],
        phone=row["phone"],
        time=row["time"],
        end_time=row["end_time"],
        guests_count=row["guests_count"],
        status=row["status"],
    )


@router.get("/reservations", response_model=ReservationsResponse)
def list_reservations(conn=Depends(get_db)):
    rows = conn.execute("SELECT * FROM reservations ORDER BY time, id").fetchall()
    return ReservationsResponse(reservations=[_row_to_reservation(r) for r in rows])


@router.post("/reservations", response_model=Reservation, status_code=201)
def create_reservation(body: ReservationCreate, conn=Depends(get_db)):
    table = conn.execute("SELECT * FROM tables WHERE id = ?", (body.table_id,)).fetchone()
    if table is None:
        raise ApiError(404, "table_not_found", "table {} does not exist".format(body.table_id))
    if body.guests_count > table["seats"]:
        raise ApiError(
            400,
            "seats_exceeded",
            "table {} has only {} seats, but {} guests requested".format(
                table["number"], table["seats"], body.guests_count
            ),
        )
    end_time = (parse_iso8601(body.time) + timedelta(hours=RESERVATION_DURATION_HOURS)).isoformat()
    cursor = conn.execute(
        "INSERT INTO reservations (table_id, guest_name, phone, time, end_time, guests_count) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (body.table_id, body.guest_name, body.phone, body.time, end_time, body.guests_count),
    )
    row = conn.execute("SELECT * FROM reservations WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return _row_to_reservation(row)


@router.get("/reservations/{reservation_id}", response_model=Reservation)
def get_reservation(reservation_id: int, conn=Depends(get_db)):
    row = conn.execute("SELECT * FROM reservations WHERE id = ?", (reservation_id,)).fetchone()
    if row is None:
        raise ApiError(
            404, "reservation_not_found", "reservation {} does not exist".format(reservation_id)
        )
    return _row_to_reservation(row)


@router.delete("/reservations/{reservation_id}", response_model=Reservation)
def cancel_reservation(reservation_id: int, conn=Depends(get_db)):
    row = conn.execute("SELECT * FROM reservations WHERE id = ?", (reservation_id,)).fetchone()
    if row is None:
        raise ApiError(
            404, "reservation_not_found", "reservation {} does not exist".format(reservation_id)
        )
    conn.execute("UPDATE reservations SET status = 'cancelled' WHERE id = ?", (reservation_id,))
    updated = conn.execute(
        "SELECT * FROM reservations WHERE id = ?", (reservation_id,)
    ).fetchone()
    return _row_to_reservation(updated)
