# Personal Asset Tracker (pat) - Implementation Plan

## Status: COMPLETE (2026-03-16)

All phases implemented. See below for the original plan.

---

## Context

The pat project is a personal asset tracker for recording and querying asset values over time. It currently has only scaffolding (empty `src/pat/__init__.py`, empty `tests/__init__.py`, and a `pyproject.toml` with no dependencies). All application code, database layer, and tests need to be built from scratch.

The goal is a **CLI-based** Python tool backed by SQLite that lets a single user track values of assets across six categories (cash, public stock, real estate, boats, cars, instruments), with import/export support for financial statement files.

---

## Database Schema

Three tables:

**`asset_categories`** (reference/lookup, pre-seeded)
| Column | Type | Constraints |
|---|---|---|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| name | TEXT | NOT NULL UNIQUE |
| description | TEXT | |

Seed values: `cash`, `public_stock`, `real_estate`, `boats`, `cars`, `instruments`

**`assets`** (individual assets)
| Column | Type | Constraints |
|---|---|---|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| category_id | INTEGER | NOT NULL, FK -> asset_categories.id |
| name | TEXT | NOT NULL |
| description | TEXT | |
| acquired_date | TEXT (ISO 8601) | |
| disposed_date | TEXT (ISO 8601) | NULL if still held |
| created_at | TEXT | NOT NULL DEFAULT CURRENT_TIMESTAMP |
| updated_at | TEXT | NOT NULL DEFAULT CURRENT_TIMESTAMP |

**`asset_values`** (value snapshots over time)
| Column | Type | Constraints |
|---|---|---|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| asset_id | INTEGER | NOT NULL, FK -> assets.id ON DELETE CASCADE |
| value_date | TEXT (ISO 8601) | NOT NULL |
| amount | REAL | NOT NULL |
| currency | TEXT | NOT NULL DEFAULT 'USD' |
| note | TEXT | |
| created_at | TEXT | NOT NULL DEFAULT CURRENT_TIMESTAMP |

Unique constraint on `(asset_id, value_date)`.

---

## File Tree

```
pat/
  pyproject.toml
  .gitignore
  .flake8
  alembic.ini
  LEARNINGS.md
  plans/implementation-plan.md
  alembic/
    env.py
    script.py.mako
    versions/
      001_initial_schema.py
  src/pat/
    __init__.py
    cli.py
    config.py
    db.py
    models.py
    repository.py
    io.py
    _lint.py
    _migrate.py
  tests/
    conftest.py
    test_models.py
    test_repository.py
    test_io.py
    test_cli.py
    st/
      sample_portfolio.json
      sample_portfolio.csv
```

## Verification

- `poetry install` - all dependencies resolve
- `poetry run test` - 52 tests pass
- `poetry run lint` - flake8 + black clean
- CLI commands all functional via `pat` entry point
