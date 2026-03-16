"""Pydantic models for pat."""

from enum import Enum
from datetime import date

from pydantic import BaseModel, Field


class AssetCategory(str, Enum):
    """Supported asset categories."""

    CASH = "cash"
    PUBLIC_STOCK = "public_stock"
    REAL_ESTATE = "real_estate"
    BOATS = "boats"
    CARS = "cars"
    INSTRUMENTS = "instruments"


class AssetCreate(BaseModel):
    """Data required to create a new asset."""

    category: AssetCategory
    name: str
    description: str | None = None
    acquired_date: date | None = None


class AssetUpdate(BaseModel):
    """Data for updating an existing asset."""

    name: str | None = None
    description: str | None = None
    acquired_date: date | None = None
    disposed_date: date | None = None


class Asset(BaseModel):
    """A tracked asset."""

    id: int
    category_id: int
    category: str
    name: str
    description: str | None = None
    acquired_date: date | None = None
    disposed_date: date | None = None
    created_at: str
    updated_at: str


class AssetValueCreate(BaseModel):
    """Data required to record an asset value."""

    asset_id: int
    value_date: date
    amount: float
    currency: str = "USD"
    note: str | None = None


class AssetValue(BaseModel):
    """A recorded asset value snapshot."""

    id: int
    asset_id: int
    value_date: date
    amount: float
    currency: str
    note: str | None = None
    created_at: str


class CategorySummary(BaseModel):
    """Net worth breakdown for a single category."""

    category: str
    total: float = 0.0
    asset_count: int = 0


class NetWorthSummary(BaseModel):
    """Overall net worth summary."""

    as_of: date
    total: float = 0.0
    currency: str = "USD"
    categories: list[CategorySummary] = Field(default_factory=list)
