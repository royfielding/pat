"""Migration runner for poetry run migrate."""

import subprocess
import sys


def run() -> None:
    """Run alembic upgrade head."""
    sys.exit(subprocess.call(["alembic", "upgrade", "head"]))
