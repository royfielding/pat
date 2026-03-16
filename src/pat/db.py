"""Database connection management for pat."""

import sqlite3
from contextlib import contextmanager
from collections.abc import Generator

from pat.config import get_db_path


def get_connection(db_path: str | None = None) -> sqlite3.Connection:
    """Create a new database connection with recommended settings."""
    path = db_path or get_db_path()
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def transaction(conn: sqlite3.Connection) -> Generator[sqlite3.Connection]:
    """Context manager for database transactions."""
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def init_schema(conn: sqlite3.Connection) -> None:
    """Create all tables and seed data. Used for testing and init command."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS asset_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT
        );

        INSERT OR IGNORE INTO asset_categories (name, description) VALUES
            ('cash', 'Cash and cash equivalents'),
            ('public_stock', 'Publicly traded stocks and funds'),
            ('real_estate', 'Real estate properties'),
            ('boats', 'Boats and watercraft'),
            ('cars', 'Cars and vehicles'),
            ('instruments', 'Musical instruments');

        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            acquired_date TEXT,
            disposed_date TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES asset_categories(id)
        );

        CREATE TABLE IF NOT EXISTS asset_values (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id INTEGER NOT NULL,
            value_date TEXT NOT NULL,
            amount REAL NOT NULL,
            currency TEXT NOT NULL DEFAULT 'USD',
            note TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE,
            UNIQUE (asset_id, value_date)
        );
    """)
