"""Tests for Pydantic models."""

from datetime import date

import pytest
from pydantic import ValidationError

from pat.models import (
    AssetCategory,
    AssetCreate,
    AssetUpdate,
    AssetValueCreate,
    CategorySummary,
    NetWorthSummary,
)


class TestAssetCategory:
    def test_valid_categories(self):
        for name in [
            "cash",
            "public_stock",
            "real_estate",
            "boats",
            "cars",
            "instruments",
        ]:
            assert AssetCategory(name).value == name

    def test_invalid_category(self):
        with pytest.raises(ValueError):
            AssetCategory("invalid")


class TestAssetCreate:
    def test_minimal(self):
        ac = AssetCreate(category=AssetCategory.CASH, name="Checking")
        assert ac.category == AssetCategory.CASH
        assert ac.name == "Checking"
        assert ac.description is None
        assert ac.acquired_date is None

    def test_full(self):
        ac = AssetCreate(
            category=AssetCategory.REAL_ESTATE,
            name="House",
            description="Primary residence",
            acquired_date=date(2020, 1, 1),
        )
        assert ac.acquired_date == date(2020, 1, 1)

    def test_missing_required(self):
        with pytest.raises(ValidationError):
            AssetCreate(category=AssetCategory.CASH)  # type: ignore[call-arg]


class TestAssetUpdate:
    def test_all_none(self):
        au = AssetUpdate()
        assert au.name is None
        assert au.disposed_date is None

    def test_partial(self):
        au = AssetUpdate(name="New Name")
        assert au.name == "New Name"
        assert au.description is None


class TestAssetValueCreate:
    def test_valid(self):
        avc = AssetValueCreate(
            asset_id=1,
            value_date=date(2025, 12, 31),
            amount=15000.0,
        )
        assert avc.currency == "USD"

    def test_custom_currency(self):
        avc = AssetValueCreate(
            asset_id=1,
            value_date=date(2025, 12, 31),
            amount=10000.0,
            currency="EUR",
        )
        assert avc.currency == "EUR"


class TestNetWorthSummary:
    def test_default(self):
        nw = NetWorthSummary(as_of=date(2025, 12, 31))
        assert nw.total == 0.0
        assert nw.categories == []

    def test_with_categories(self):
        nw = NetWorthSummary(
            as_of=date(2025, 12, 31),
            total=100000.0,
            categories=[
                CategorySummary(category="cash", total=50000.0, asset_count=2),
                CategorySummary(category="public_stock", total=50000.0, asset_count=1),
            ],
        )
        assert len(nw.categories) == 2
