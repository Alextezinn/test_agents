"""SQLite storage for the Restaurant API.

Storage path can be overridden with the RESTAURANT_DB environment variable
(useful for tests). The database is created and seeded on first start.
"""
import os
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def get_db_path() -> Path:
    return Path(os.environ.get("RESTAURANT_DB", str(BASE_DIR / "restaurant.db")))


SCHEMA = """
CREATE TABLE IF NOT EXISTS menu_items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    category    TEXT    NOT NULL,
    price       REAL    NOT NULL,
    description TEXT    NOT NULL DEFAULT '',
    available   INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS tables (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    number INTEGER NOT NULL UNIQUE,
    seats  INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS reservations (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    table_id     INTEGER NOT NULL REFERENCES tables(id),
    guest_name   TEXT    NOT NULL,
    phone        TEXT    NOT NULL,
    time         TEXT    NOT NULL,
    end_time     TEXT    NOT NULL,
    guests_count INTEGER NOT NULL,
    status       TEXT    NOT NULL DEFAULT 'active'
);

CREATE TABLE IF NOT EXISTS orders (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    table_id   INTEGER NOT NULL REFERENCES tables(id),
    items      TEXT    NOT NULL,
    total      REAL    NOT NULL,
    status     TEXT    NOT NULL DEFAULT 'new',
    created_at TEXT    NOT NULL
);
"""

SEED_MENU = [
    ("Цезарь с курицей", "salads", 540.00, "Романо, пармезан, соус цезарь", 1),
    ("Греческий салат", "salads", 480.00, "Оливки, фета, огурцы, томаты", 1),
    ("Стейк рибай", "main", 1450.00, "Говядина зернового откорма, 300 г", 1),
    ("Борщ", "main", 380.00, "Классический борщ со сметаной", 1),
    ("Паста карбонара", "main", 620.00, "Спагетти, бекон, пармезан", 1),
    ("Тирамису", "desserts", 390.00, "Маскарпоне, кофе, какао", 1),
    ("Чизкейк", "desserts", 420.00, "Сливочный сыр, песочная основа", 1),
    ("Морс клюквенный", "drinks", 250.00, "Домашний морс", 1),
    ("Эспрессо", "drinks", 180.00, "Свежесваренный эспрессо", 1),
    ("Устрицы", "main", 990.00, "Полдюжины свежих устриц", 0),
]

SEED_TABLES = [(1, 2), (2, 2), (3, 4), (4, 4), (5, 6), (6, 8)]


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(get_db_path()))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    conn = connect()
    try:
        conn.executescript(SCHEMA)
        if conn.execute("SELECT COUNT(*) FROM menu_items").fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO menu_items (name, category, price, description, available) "
                "VALUES (?, ?, ?, ?, ?)",
                SEED_MENU,
            )
        if conn.execute("SELECT COUNT(*) FROM tables").fetchone()[0] == 0:
            conn.executemany("INSERT INTO tables (number, seats) VALUES (?, ?)", SEED_TABLES)
        conn.commit()
    finally:
        conn.close()


def get_db():
    """FastAPI dependency: one connection per request."""
    conn = connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
