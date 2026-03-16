"""Lint runner for poetry run lint."""

import subprocess
import sys


def run() -> None:
    """Run flake8 and black --check."""
    ret = 0
    ret |= subprocess.call([sys.executable, "-m", "flake8", "src/", "tests/"])
    ret |= subprocess.call([sys.executable, "-m", "black", "--check", "src/", "tests/"])
    sys.exit(ret)
