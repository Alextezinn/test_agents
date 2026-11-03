"""Restaurant API — FastAPI application entry point.

Run:  python3 -m uvicorn main:app --reload
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import init_db
from app.errors import register_error_handlers
from app.routers import menu, orders, reservations, tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Restaurant API", version="0.1.0", lifespan=lifespan)
register_error_handlers(app)

for router in (menu.router, tables.router, reservations.router, orders.router):
    app.include_router(router, prefix="/api/v1")
