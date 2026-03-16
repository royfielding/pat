"""Shared test fixtures."""

import sqlite3
from datetime import date

import pytest

from pat.db import init_schema
from pat.models import AssetCategory, AssetCreate, AssetValueCreate
from pat.repository import add_value, create_asset


@pytest.fixture
def conn():
    """Provide an in-memory database with schema and seed data."""
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    init_schema(connection)
    yield connection
    connection.close()


@pytest.fixture
def sample_data(conn):
    """Create sample assets and values for testing."""
    checking = create_asset(
        conn,
        AssetCreate(category=AssetCategory.CASH, name="Checking Account"),
    )
    savings = create_asset(
        conn,
        AssetCreate(category=AssetCategory.CASH, name="Savings Account"),
    )
    stock = create_asset(
        conn,
        AssetCreate(
            category=AssetCategory.PUBLIC_STOCK,
            name="AAPL",
            description="Apple Inc.",
        ),
    )
    house = create_asset(
        conn,
        AssetCreate(
            category=AssetCategory.REAL_ESTATE,
            name="Primary Residence",
            acquired_date=date(2020, 6, 15),
        ),
    )

    add_value(
        conn,
        AssetValueCreate(
            asset_id=checking.id,
            value_date=date(2025, 12, 31),
            amount=15000.00,
        ),
    )
    add_value(
        conn,
        AssetValueCreate(
            asset_id=savings.id,
            value_date=date(2025, 12, 31),
            amount=50000.00,
        ),
    )
    add_value(
        conn,
        AssetValueCreate(
            asset_id=stock.id,
            value_date=date(2025, 12, 31),
            amount=25000.00,
        ),
    )
    add_value(
        conn,
        AssetValueCreate(
            asset_id=house.id,
            value_date=date(2025, 12, 31),
            amount=500000.00,
        ),
    )
    add_value(
        conn,
        AssetValueCreate(
            asset_id=house.id,
            value_date=date(2025, 6, 30),
            amount=480000.00,
        ),
    )

    return {
        "checking": checking,
        "savings": savings,
        "stock": stock,
        "house": house,
    }
