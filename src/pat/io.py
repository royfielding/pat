"""Import/export functions for pat."""

import csv
import json
import logging
import sqlite3
from datetime import date
from pathlib import Path

from pat.models import AssetCategory, AssetCreate, AssetValueCreate
from pat.repository import (
    add_value,
    create_asset,
    get_latest_values,
    list_assets,
)

logger = logging.getLogger(__name__)


def import_json(conn: sqlite3.Connection, file_path: str | Path) -> int:
    """Import assets and values from a JSON file. Returns count of records imported."""
    path = Path(file_path)
    with path.open() as f:
        data = json.load(f)

    as_of = data.get("as_of", date.today().isoformat())
    count = 0

    for item in data.get("assets", []):
        category = item["category"]
        # Validate category
        AssetCategory(category)

        asset = create_asset(
            conn,
            AssetCreate(
                category=AssetCategory(category),
                name=item["name"],
                description=item.get("description"),
            ),
        )

        if "amount" in item:
            add_value(
                conn,
                AssetValueCreate(
                    asset_id=asset.id,
                    value_date=date.fromisoformat(item.get("value_date", as_of)),
                    amount=item["amount"],
                    currency=item.get("currency", "USD"),
                    note=item.get("note"),
                ),
            )
        count += 1

    logger.info("Imported %d assets from %s", count, path)
    return count


def export_json(
    conn: sqlite3.Connection,
    file_path: str | Path,
    as_of: date | None = None,
) -> int:
    """Export current portfolio to a JSON file. Returns count of assets exported."""
    if as_of is None:
        as_of = date.today()

    assets = list_assets(conn)
    latest = {v.asset_id: v for v in get_latest_values(conn)}

    records = []
    for asset in assets:
        if (
            asset.disposed_date
            and date.fromisoformat(str(asset.disposed_date)) <= as_of
        ):
            continue

        record: dict[str, object] = {
            "category": asset.category,
            "name": asset.name,
        }
        if asset.description:
            record["description"] = asset.description

        val = latest.get(asset.id)
        if val:
            record["amount"] = val.amount
            record["currency"] = val.currency
            record["value_date"] = val.value_date.isoformat()
            if val.note:
                record["note"] = val.note

        records.append(record)

    output = {
        "as_of": as_of.isoformat(),
        "assets": records,
    }

    path = Path(file_path)
    with path.open("w") as f:
        json.dump(output, f, indent=2)

    logger.info("Exported %d assets to %s", len(records), path)
    return len(records)


def import_csv(conn: sqlite3.Connection, file_path: str | Path) -> int:
    """Import assets and values from a CSV file. Returns count of records imported."""
    path = Path(file_path)
    count = 0

    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            category = row["category"]
            AssetCategory(category)

            asset = create_asset(
                conn,
                AssetCreate(
                    category=AssetCategory(category),
                    name=row["name"],
                ),
            )

            if row.get("amount"):
                add_value(
                    conn,
                    AssetValueCreate(
                        asset_id=asset.id,
                        value_date=date.fromisoformat(row["value_date"]),
                        amount=float(row["amount"]),
                        currency=row.get("currency", "USD"),
                        note=row.get("note"),
                    ),
                )
            count += 1

    logger.info("Imported %d assets from %s", count, path)
    return count


def export_csv(
    conn: sqlite3.Connection,
    file_path: str | Path,
    as_of: date | None = None,
) -> int:
    """Export current portfolio to a CSV file. Returns count of assets exported."""
    if as_of is None:
        as_of = date.today()

    assets = list_assets(conn)
    latest = {v.asset_id: v for v in get_latest_values(conn)}

    path = Path(file_path)
    count = 0

    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["category", "name", "value_date", "amount", "currency", "note"]
        )

        for asset in assets:
            if (
                asset.disposed_date
                and date.fromisoformat(str(asset.disposed_date)) <= as_of
            ):
                continue

            val = latest.get(asset.id)
            writer.writerow(
                [
                    asset.category,
                    asset.name,
                    val.value_date.isoformat() if val else "",
                    val.amount if val else "",
                    val.currency if val else "USD",
                    val.note or "" if val else "",
                ]
            )
            count += 1

    logger.info("Exported %d assets to %s", count, path)
    return count
