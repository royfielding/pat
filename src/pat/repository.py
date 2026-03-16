"""Data access layer for pat."""

import sqlite3
from datetime import date

from pat.models import (
    Asset,
    AssetCreate,
    AssetUpdate,
    AssetValue,
    AssetValueCreate,
    CategorySummary,
    NetWorthSummary,
)


def _get_category_id(conn: sqlite3.Connection, name: str) -> int | None:
    """Look up a category id by name."""
    row = conn.execute(
        "SELECT id FROM asset_categories WHERE name = ?", (name,)
    ).fetchone()
    return row["id"] if row else None


def _row_to_asset(row: sqlite3.Row) -> Asset:
    """Convert a database row to an Asset model."""
    return Asset(
        id=row["id"],
        category_id=row["category_id"],
        category=row["category"],
        name=row["name"],
        description=row["description"],
        acquired_date=row["acquired_date"],
        disposed_date=row["disposed_date"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_value(row: sqlite3.Row) -> AssetValue:
    """Convert a database row to an AssetValue model."""
    return AssetValue(
        id=row["id"],
        asset_id=row["asset_id"],
        value_date=row["value_date"],
        amount=row["amount"],
        currency=row["currency"],
        note=row["note"],
        created_at=row["created_at"],
    )


ASSET_SELECT = """
    SELECT a.id, a.category_id, c.name as category, a.name, a.description,
           a.acquired_date, a.disposed_date, a.created_at, a.updated_at
    FROM assets a
    JOIN asset_categories c ON a.category_id = c.id
"""


def create_asset(conn: sqlite3.Connection, data: AssetCreate) -> Asset:
    """Create a new asset and return it."""
    category_id = _get_category_id(conn, data.category.value)
    if category_id is None:
        raise ValueError(f"Unknown category: {data.category.value}")

    cursor = conn.execute(
        """INSERT INTO assets (category_id, name, description, acquired_date)
           VALUES (?, ?, ?, ?)""",
        (
            category_id,
            data.name,
            data.description,
            data.acquired_date.isoformat() if data.acquired_date else None,
        ),
    )
    conn.commit()
    return get_asset(conn, cursor.lastrowid)  # type: ignore[return-value]


def get_asset(conn: sqlite3.Connection, asset_id: int) -> Asset | None:
    """Get a single asset by id."""
    row = conn.execute(ASSET_SELECT + " WHERE a.id = ?", (asset_id,)).fetchone()
    return _row_to_asset(row) if row else None


def list_assets(conn: sqlite3.Connection, category: str | None = None) -> list[Asset]:
    """List all assets, optionally filtered by category name."""
    if category:
        rows = conn.execute(
            ASSET_SELECT + " WHERE c.name = ? ORDER BY a.name",
            (category,),
        ).fetchall()
    else:
        rows = conn.execute(ASSET_SELECT + " ORDER BY c.name, a.name").fetchall()
    return [_row_to_asset(r) for r in rows]


def update_asset(
    conn: sqlite3.Connection, asset_id: int, data: AssetUpdate
) -> Asset | None:
    """Update an existing asset. Returns None if not found."""
    existing = get_asset(conn, asset_id)
    if existing is None:
        return None

    updates: list[str] = []
    params: list[object] = []
    if data.name is not None:
        updates.append("name = ?")
        params.append(data.name)
    if data.description is not None:
        updates.append("description = ?")
        params.append(data.description)
    if data.acquired_date is not None:
        updates.append("acquired_date = ?")
        params.append(data.acquired_date.isoformat())
    if data.disposed_date is not None:
        updates.append("disposed_date = ?")
        params.append(data.disposed_date.isoformat())

    if updates:
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(asset_id)
        conn.execute(
            f"UPDATE assets SET {', '.join(updates)} WHERE id = ?",
            params,
        )
        conn.commit()

    return get_asset(conn, asset_id)


def delete_asset(conn: sqlite3.Connection, asset_id: int) -> bool:
    """Delete an asset and its values. Returns True if deleted."""
    cursor = conn.execute("DELETE FROM assets WHERE id = ?", (asset_id,))
    conn.commit()
    return cursor.rowcount > 0


def add_value(conn: sqlite3.Connection, data: AssetValueCreate) -> AssetValue:
    """Record a new value snapshot for an asset."""
    cursor = conn.execute(
        """INSERT INTO asset_values (asset_id, value_date, amount, currency, note)
           VALUES (?, ?, ?, ?, ?)""",
        (
            data.asset_id,
            data.value_date.isoformat(),
            data.amount,
            data.currency,
            data.note,
        ),
    )
    conn.commit()
    row = conn.execute(
        "SELECT * FROM asset_values WHERE id = ?", (cursor.lastrowid,)
    ).fetchone()
    return _row_to_value(row)


def get_values(
    conn: sqlite3.Connection,
    asset_id: int,
    start: date | None = None,
    end: date | None = None,
) -> list[AssetValue]:
    """Get value history for an asset, optionally filtered by date range."""
    query = "SELECT * FROM asset_values WHERE asset_id = ?"
    params: list[object] = [asset_id]

    if start:
        query += " AND value_date >= ?"
        params.append(start.isoformat())
    if end:
        query += " AND value_date <= ?"
        params.append(end.isoformat())

    query += " ORDER BY value_date"
    rows = conn.execute(query, params).fetchall()
    return [_row_to_value(r) for r in rows]


def delete_value(conn: sqlite3.Connection, value_id: int) -> bool:
    """Delete a value record. Returns True if deleted."""
    cursor = conn.execute("DELETE FROM asset_values WHERE id = ?", (value_id,))
    conn.commit()
    return cursor.rowcount > 0


def get_latest_values(conn: sqlite3.Connection) -> list[AssetValue]:
    """Get the most recent value for each asset."""
    rows = conn.execute("""
        SELECT av.* FROM asset_values av
        INNER JOIN (
            SELECT asset_id, MAX(value_date) as max_date
            FROM asset_values
            GROUP BY asset_id
        ) latest ON av.asset_id = latest.asset_id
            AND av.value_date = latest.max_date
        ORDER BY av.asset_id
    """).fetchall()
    return [_row_to_value(r) for r in rows]


def get_net_worth(
    conn: sqlite3.Connection, as_of: date | None = None
) -> NetWorthSummary:
    """Calculate net worth summary, optionally as of a specific date."""
    if as_of is None:
        as_of = date.today()

    rows = conn.execute(
        """
        SELECT c.name as category,
               COUNT(DISTINCT a.id) as asset_count,
               COALESCE(SUM(av.amount), 0) as total
        FROM asset_categories c
        LEFT JOIN assets a ON a.category_id = c.id
            AND (a.disposed_date IS NULL OR a.disposed_date > ?)
        LEFT JOIN asset_values av ON av.asset_id = a.id
            AND av.value_date = (
                SELECT MAX(av2.value_date)
                FROM asset_values av2
                WHERE av2.asset_id = a.id AND av2.value_date <= ?
            )
        GROUP BY c.name
        ORDER BY c.name
        """,
        (as_of.isoformat(), as_of.isoformat()),
    ).fetchall()

    categories = [
        CategorySummary(
            category=r["category"],
            total=r["total"],
            asset_count=r["asset_count"],
        )
        for r in rows
    ]
    total = sum(c.total for c in categories)

    return NetWorthSummary(
        as_of=as_of,
        total=total,
        categories=categories,
    )
