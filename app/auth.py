"""Staff authentication for PATCH /orders/{id}/status."""
import os
import secrets
from typing import Optional

from fastapi import Header

from app.errors import ApiError

DEFAULT_STAFF_TOKEN = "dev-staff-token"


def staff_token() -> str:
    return os.environ.get("STAFF_TOKEN", DEFAULT_STAFF_TOKEN)


def require_staff(authorization: Optional[str] = Header(default=None)) -> None:
    if authorization is None or not authorization.startswith("Bearer "):
        raise ApiError(401, "unauthorized", "staff token required (Authorization: Bearer <token>)")
    token = authorization[len("Bearer "):]
    if not secrets.compare_digest(token, staff_token()):
        raise ApiError(403, "forbidden", "invalid staff token")
