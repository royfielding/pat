"""Initial schema.

Revision ID: 001
Revises:
Create Date: 2026-03-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "asset_categories",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.Text, nullable=False, unique=True),
        sa.Column("description", sa.Text),
    )

    op.execute(
        "INSERT INTO asset_categories (name, description) VALUES "
        "('cash', 'Cash and cash equivalents'), "
        "('public_stock', 'Publicly traded stocks and funds'), "
        "('real_estate', 'Real estate properties'), "
        "('boats', 'Boats and watercraft'), "
        "('cars', 'Cars and vehicles'), "
        "('instruments', 'Musical instruments')"
    )

    op.create_table(
        "assets",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "category_id",
            sa.Integer,
            sa.ForeignKey("asset_categories.id"),
            nullable=False,
        ),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("acquired_date", sa.Text),
        sa.Column("disposed_date", sa.Text),
        sa.Column(
            "created_at",
            sa.Text,
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.Text,
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )

    op.create_table(
        "asset_values",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "asset_id",
            sa.Integer,
            sa.ForeignKey("assets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("value_date", sa.Text, nullable=False),
        sa.Column("amount", sa.Float, nullable=False),
        sa.Column(
            "currency", sa.Text, nullable=False, server_default="USD"
        ),
        sa.Column("note", sa.Text),
        sa.Column(
            "created_at",
            sa.Text,
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.UniqueConstraint("asset_id", "value_date"),
    )


def downgrade() -> None:
    op.drop_table("asset_values")
    op.drop_table("assets")
    op.drop_table("asset_categories")
