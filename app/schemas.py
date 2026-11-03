"""Pydantic schemas for the Restaurant API."""
from typing import List

from pydantic import BaseModel, Field, field_validator

from app.time_utils import parse_iso8601

ORDER_STATUSES = ("new", "preparing", "ready", "served", "cancelled")


class MenuItem(BaseModel):
    id: int
    name: str
    category: str
    price: float
    description: str
    available: bool


class MenuResponse(BaseModel):
    items: List[MenuItem]


class Table(BaseModel):
    id: int
    number: int
    seats: int


class TablesResponse(BaseModel):
    tables: List[Table]


class ReservationCreate(BaseModel):
    table_id: int
    guest_name: str = Field(min_length=1, max_length=100)
    phone: str = Field(min_length=1, max_length=50)
    time: str
    guests_count: int = Field(ge=1)

    @field_validator("time")
    @classmethod
    def validate_time(cls, value: str) -> str:
        try:
            parse_iso8601(value)
        except ValueError:
            raise ValueError("time must be ISO 8601, e.g. 2026-11-03T19:00:00+03:00")
        return value


class Reservation(BaseModel):
    id: int
    table_id: int
    guest_name: str
    phone: str
    time: str
    end_time: str
    guests_count: int
    status: str


class ReservationsResponse(BaseModel):
    reservations: List[Reservation]


class OrderItemIn(BaseModel):
    menu_item_id: int
    quantity: int = Field(ge=1)


class OrderCreate(BaseModel):
    table_id: int
    items: List[OrderItemIn] = Field(min_length=1)


class OrderItem(BaseModel):
    menu_item_id: int
    name: str
    price: float
    quantity: int


class Order(BaseModel):
    id: int
    table_id: int
    items: List[OrderItem]
    total: float
    status: str
    created_at: str


class OrdersResponse(BaseModel):
    orders: List[Order]


class OrderStatusUpdate(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in ORDER_STATUSES:
            raise ValueError("status must be one of: " + ", ".join(ORDER_STATUSES))
        return value
