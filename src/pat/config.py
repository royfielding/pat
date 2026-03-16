"""Centralized configuration for pat."""

import os
from pathlib import Path


def get_db_path() -> str:
    """Return the database path from env var or default."""
    return os.environ.get("PAT_DB_PATH", str(Path.cwd() / "pat.db"))
