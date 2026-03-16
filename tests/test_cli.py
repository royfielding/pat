"""Tests for the CLI interface."""

import json
import os
import sqlite3
import tempfile
from unittest.mock import patch

import pytest

from pat.cli import main
from pat.db import init_schema


@pytest.fixture
def cli_db():
    """Provide a temp database file for CLI tests."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    init_schema(conn)
    conn.close()
    with patch.dict(os.environ, {"PAT_DB_PATH": path}):
        yield path
    os.unlink(path)


def run_cli(*args):
    """Run the CLI with given arguments, capturing SystemExit."""
    import sys
    from io import StringIO

    old_argv = sys.argv
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.argv = ["pat"] + list(args)
    out = StringIO()
    err = StringIO()
    sys.stdout = out
    sys.stderr = err
    exit_code = 0
    try:
        main()
    except SystemExit as e:
        exit_code = e.code or 0
    finally:
        sys.argv = old_argv
        sys.stdout = old_stdout
        sys.stderr = old_stderr
    return exit_code, out.getvalue(), err.getvalue()


class TestInit:
    def test_init(self):
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        os.unlink(path)
        try:
            with patch.dict(os.environ, {"PAT_DB_PATH": path}):
                code, out, _ = run_cli("init")
                assert code == 0
                assert "initialized" in out.lower()
        finally:
            if os.path.exists(path):
                os.unlink(path)


class TestAssetCommands:
    def test_add_and_list(self, cli_db):
        code, out, _ = run_cli(
            "asset", "add", "--category", "cash", "--name", "Checking"
        )
        assert code == 0
        assert "Created asset #1" in out

        code, out, _ = run_cli("asset", "list")
        assert code == 0
        assert "Checking" in out

    def test_show(self, cli_db):
        run_cli("asset", "add", "--category", "cash", "--name", "Checking")
        code, out, _ = run_cli("asset", "show", "1")
        assert code == 0
        assert "Checking" in out

    def test_show_not_found(self, cli_db):
        code, _, err = run_cli("asset", "show", "999")
        assert code == 1

    def test_update(self, cli_db):
        run_cli("asset", "add", "--category", "cash", "--name", "Checking")
        code, out, _ = run_cli("asset", "update", "1", "--name", "Main Checking")
        assert code == 0
        assert "Main Checking" in out

    def test_delete(self, cli_db):
        run_cli("asset", "add", "--category", "cash", "--name", "Checking")
        code, out, _ = run_cli("asset", "delete", "1")
        assert code == 0
        assert "Deleted" in out


class TestValueCommands:
    def test_add_and_list(self, cli_db):
        run_cli("asset", "add", "--category", "cash", "--name", "Checking")
        code, out, _ = run_cli(
            "value",
            "add",
            "1",
            "--date",
            "2025-12-31",
            "--amount",
            "15000",
        )
        assert code == 0
        assert "15,000.00" in out

        code, out, _ = run_cli("value", "list", "1")
        assert code == 0
        assert "15,000.00" in out

    def test_delete(self, cli_db):
        run_cli("asset", "add", "--category", "cash", "--name", "Checking")
        run_cli(
            "value",
            "add",
            "1",
            "--date",
            "2025-12-31",
            "--amount",
            "15000",
        )
        code, out, _ = run_cli("value", "delete", "1")
        assert code == 0


class TestReportCommands:
    def test_net_worth(self, cli_db):
        run_cli("asset", "add", "--category", "cash", "--name", "Checking")
        run_cli(
            "value",
            "add",
            "1",
            "--date",
            "2025-12-31",
            "--amount",
            "15000",
        )
        code, out, _ = run_cli("report", "net-worth", "--as-of", "2025-12-31")
        assert code == 0
        assert "15,000.00" in out

    def test_history(self, cli_db):
        run_cli("asset", "add", "--category", "cash", "--name", "Checking")
        run_cli(
            "value",
            "add",
            "1",
            "--date",
            "2025-12-31",
            "--amount",
            "15000",
        )
        code, out, _ = run_cli("report", "history")
        assert code == 0
        assert "Checking" in out


class TestImportExport:
    def test_json_roundtrip(self, cli_db):
        run_cli("asset", "add", "--category", "cash", "--name", "Checking")
        run_cli(
            "value",
            "add",
            "1",
            "--date",
            "2025-12-31",
            "--amount",
            "15000",
        )

        fd, path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        try:
            code, out, _ = run_cli("export", path, "--format", "json")
            assert code == 0
            assert "Exported" in out

            with open(path) as f:
                data = json.load(f)
            assert len(data["assets"]) == 1
        finally:
            os.unlink(path)
