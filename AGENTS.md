# Project: Personal Asset Tracker (pat)

This is a Python-based application for a personal asset tracker containing
a database of personal asset values over time for a single user.
Asset categories include cash, public stock, real estate, boats, and cars.

You do not have access to real financial statements.
You may read any test financial statements under ./tests/st/
You may write test financial statements under ./tests/st/gen/

## Architecture Overview

*   **Language**: Python 3.14+
*   **Database**: sqlite3
*   **Dependencies**: Handled by `poetry` (`pyproject.toml`)
*   **Key Directories**:
    *   `./src/` - Source code
    *   `./tests/` - Unit and integration tests
*   **Coding Style**:
    *   Follow PEP 8 guidelines.
    *   Use type hints extensively with `mypy`.
    *   Prioritize modular and reusable code.

## Commands

These are the exact commands to run tasks.

*   `poetry install` — Install project dependencies
*   `poetry run dev` — Start the development server
*   `poetry run test` — Run all unit and integration tests
*   `poetry run lint` — Run `flake8` and `black` code style checks
*   `poetry run migrate` — Apply database migrations (using Alembic)

## Core Principles

*   **Error Handling**: Implement comprehensive error handling and use `logging` instead of `print` statements.
*   **Minimal Changes**: Focus on making minimal, clean changes to achieve the requested task.
*   **Testing**: All new features must include corresponding unit tests in the `./tests/` directory.

## LEARNING LOOP
* always create a ./LEARNINGS.md file if it's not there. It should be checked in and then in context for any agent code sessions.
* Log Every Friction Point: If a build fails, a test hangs, or a logic error occurs, document the root cause and the specific fix before proceeding.
* Mandatory Update on Intervention: If you stop to ask for guidance, or if I provide a correction, you must update ./LEARNINGS.md with the "Signpost" (the specific instruction or realization) that prevented you from succeeding independently.
* Iterate Toward Autonomy: Use the existing log to avoid repeating mistakes. Your goal is to reach a state where you can complete the objective without manual triggers.
