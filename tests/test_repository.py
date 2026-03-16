"""Tests for the repository layer."""

from datetime import date

import pytest

from pat.models import (
    AssetCategory,
    AssetCreate,
    AssetUpdate,
    AssetValueCreate,
)
from pat.repository import (
    add_value,
    create_asset,
    delete_asset,
    delete_value,
    get_asset,
    get_latest_values,
    get_net_worth,
    get_values,
    list_assets,
    update_asset,
)


class TestCreateAsset:
    def test_create_basic(self, conn):
        asset = create_asset(
            conn,
            AssetCreate(category=AssetCategory.CASH, name="Checking"),
        )
        assert asset.id is not None
        assert asset.name == "Checking"
        assert asset.category == "cash"

    def test_create_with_details(self, conn):
        asset = create_asset(
            conn,
            AssetCreate(
                category=AssetCategory.REAL_ESTATE,
                name="Condo",
                description="Downtown condo",
                acquired_date=date(2022, 3, 15),
            ),
        )
        assert asset.description == "Downtown condo"
        assert asset.acquired_date == date(2022, 3, 15)

    def test_create_invalid_category(self, conn):
        with pytest.raises(ValueError):
            create_asset(
                conn,
                AssetCreate(
                    category=AssetCategory("invalid"),  # type: ignore
                    name="Bad",
                ),
            )


class TestGetAsset:
    def test_found(self, conn, sample_data):
        asset = get_asset(conn, sample_data["checking"].id)
        assert asset is not None
        assert asset.name == "Checking Account"

    def test_not_found(self, conn):
        assert get_asset(conn, 9999) is None


class TestListAssets:
    def test_list_all(self, conn, sample_data):
        assets = list_assets(conn)
        assert len(assets) == 4

    def test_list_by_category(self, conn, sample_data):
        cash = list_assets(conn, category="cash")
        assert len(cash) == 2
        assert all(a.category == "cash" for a in cash)

    def test_list_empty_category(self, conn, sample_data):
        boats = list_assets(conn, category="boats")
        assert len(boats) == 0


class TestUpdateAsset:
    def test_update_name(self, conn, sample_data):
        updated = update_asset(
            conn,
            sample_data["checking"].id,
            AssetUpdate(name="Main Checking"),
        )
        assert updated is not None
        assert updated.name == "Main Checking"

    def test_update_disposed(self, conn, sample_data):
        updated = update_asset(
            conn,
            sample_data["stock"].id,
            AssetUpdate(disposed_date=date(2026, 1, 15)),
        )
        assert updated is not None
        assert updated.disposed_date == date(2026, 1, 15)

    def test_update_not_found(self, conn):
        result = update_asset(conn, 9999, AssetUpdate(name="X"))
        assert result is None


class TestDeleteAsset:
    def test_delete_existing(self, conn, sample_data):
        assert delete_asset(conn, sample_data["checking"].id)
        assert get_asset(conn, sample_data["checking"].id) is None

    def test_delete_nonexistent(self, conn):
        assert not delete_asset(conn, 9999)

    def test_cascade_values(self, conn, sample_data):
        asset_id = sample_data["house"].id
        values_before = get_values(conn, asset_id)
        assert len(values_before) > 0
        delete_asset(conn, asset_id)
        values_after = get_values(conn, asset_id)
        assert len(values_after) == 0


class TestAddValue:
    def test_add_value(self, conn, sample_data):
        val = add_value(
            conn,
            AssetValueCreate(
                asset_id=sample_data["checking"].id,
                value_date=date(2026, 1, 31),
                amount=16000.00,
            ),
        )
        assert val.id is not None
        assert val.amount == 16000.00

    def test_duplicate_date_rejected(self, conn, sample_data):
        with pytest.raises(Exception):
            add_value(
                conn,
                AssetValueCreate(
                    asset_id=sample_data["checking"].id,
                    value_date=date(2025, 12, 31),
                    amount=99999.00,
                ),
            )


class TestGetValues:
    def test_all_values(self, conn, sample_data):
        values = get_values(conn, sample_data["house"].id)
        assert len(values) == 2

    def test_date_range(self, conn, sample_data):
        values = get_values(
            conn,
            sample_data["house"].id,
            start=date(2025, 7, 1),
        )
        assert len(values) == 1
        assert values[0].amount == 500000.00

    def test_no_values(self, conn):
        values = get_values(conn, 9999)
        assert values == []


class TestDeleteValue:
    def test_delete_existing(self, conn, sample_data):
        values = get_values(conn, sample_data["checking"].id)
        assert delete_value(conn, values[0].id)

    def test_delete_nonexistent(self, conn):
        assert not delete_value(conn, 9999)


class TestGetLatestValues:
    def test_latest(self, conn, sample_data):
        latest = get_latest_values(conn)
        assert len(latest) == 4
        house_val = [v for v in latest if v.asset_id == sample_data["house"].id][0]
        assert house_val.amount == 500000.00


class TestGetNetWorth:
    def test_net_worth(self, conn, sample_data):
        nw = get_net_worth(conn, as_of=date(2025, 12, 31))
        assert nw.total == 590000.00
        cash_cat = [c for c in nw.categories if c.category == "cash"][0]
        assert cash_cat.total == 65000.00
        assert cash_cat.asset_count == 2

    def test_net_worth_earlier_date(self, conn, sample_data):
        nw = get_net_worth(conn, as_of=date(2025, 6, 30))
        # Only house has a value on or before 2025-06-30
        assert nw.total == 480000.00

    def test_net_worth_empty(self, conn):
        nw = get_net_worth(conn)
        assert nw.total == 0.0
