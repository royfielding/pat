"""Tests for import/export functions."""

import json
import os
import tempfile
from datetime import date

from pat.io import export_csv, export_json, import_csv, import_json
from pat.repository import list_assets, get_values


class TestJsonImport:
    def test_import_json(self, conn):
        data = {
            "as_of": "2025-12-31",
            "assets": [
                {
                    "category": "cash",
                    "name": "Checking",
                    "amount": 15000.0,
                    "currency": "USD",
                    "note": "Year end",
                },
                {
                    "category": "public_stock",
                    "name": "AAPL",
                    "amount": 25000.0,
                },
            ],
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            f.flush()
            path = f.name

        try:
            count = import_json(conn, path)
            assert count == 2
            assets = list_assets(conn)
            assert len(assets) == 2
            values = get_values(conn, assets[0].id)
            assert len(values) == 1
        finally:
            os.unlink(path)


class TestJsonExport:
    def test_export_json(self, conn, sample_data):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name

        try:
            count = export_json(conn, path, as_of=date(2025, 12, 31))
            assert count == 4

            with open(path) as f:
                data = json.load(f)
            assert data["as_of"] == "2025-12-31"
            assert len(data["assets"]) == 4
        finally:
            os.unlink(path)


class TestJsonRoundTrip:
    def test_roundtrip(self, conn, sample_data):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name

        try:
            export_json(conn, path, as_of=date(2025, 12, 31))

            # Import into a fresh db
            import sqlite3
            from pat.db import init_schema

            conn2 = sqlite3.connect(":memory:")
            conn2.row_factory = sqlite3.Row
            conn2.execute("PRAGMA foreign_keys=ON")
            init_schema(conn2)

            count = import_json(conn2, path)
            assert count == 4
            assets = list_assets(conn2)
            assert len(assets) == 4
            conn2.close()
        finally:
            os.unlink(path)


class TestCsvImport:
    def test_import_csv(self, conn):
        csv_content = (
            "category,name,value_date,amount,currency,note\n"
            "cash,Checking,2025-12-31,15000.0,USD,Year end\n"
            "public_stock,AAPL,2025-12-31,25000.0,USD,\n"
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            path = f.name

        try:
            count = import_csv(conn, path)
            assert count == 2
            assets = list_assets(conn)
            assert len(assets) == 2
        finally:
            os.unlink(path)


class TestCsvExport:
    def test_export_csv(self, conn, sample_data):
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            path = f.name

        try:
            count = export_csv(conn, path, as_of=date(2025, 12, 31))
            assert count == 4

            with open(path) as f:
                lines = f.readlines()
            assert len(lines) == 5  # header + 4 rows
        finally:
            os.unlink(path)
