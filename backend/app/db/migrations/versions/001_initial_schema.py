"""Initial schema - all tables.

Revision ID: 001
Revises: None
Create Date: 2026-03-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("push_subscription", JSON, nullable=True),
        sa.Column("notify_email", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("notify_push", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )

    # Product groups (for cross-marketplace matching)
    op.create_table(
        "product_groups",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("canonical_name", sa.String(500), nullable=True),
        sa.Column("ean", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )

    # Products
    op.create_table(
        "products",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("url", sa.Text(), unique=True, nullable=False),
        sa.Column("marketplace", sa.String(100), nullable=True),
        sa.Column("name", sa.String(500), nullable=True),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("current_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("currency", sa.String(10), server_default="BRL"),
        sa.Column("seller", sa.String(255), nullable=True),
        sa.Column("ean", sa.String(50), nullable=True),
        sa.Column("group_id", UUID(as_uuid=True), sa.ForeignKey("product_groups.id"), nullable=True),
        sa.Column("last_scraped_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )

    # Price history (time-series)
    op.create_table(
        "price_history",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("product_id", UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("seller", sa.String(255), nullable=True),
        sa.Column("available", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("scraped_at", sa.DateTime(), server_default=sa.text("now()")),
    )
    op.create_index(
        "idx_price_history_product_time",
        "price_history",
        ["product_id", sa.text("scraped_at DESC")],
    )

    # User-tracked products
    op.create_table(
        "user_products",
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("product_id", UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("target_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("notify_on_any_drop", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )

    # Selector cache (LLM optimization)
    op.create_table(
        "selector_cache",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("url_pattern", sa.String(500), unique=True, nullable=False),
        sa.Column("selectors", JSON, nullable=False),
        sa.Column("success_count", sa.Integer(), server_default=sa.text("0")),
        sa.Column("fail_count", sa.Integer(), server_default=sa.text("0")),
        sa.Column("last_validated_at", sa.DateTime(), server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("selector_cache")
    op.drop_table("user_products")
    op.drop_index("idx_price_history_product_time", table_name="price_history")
    op.drop_table("price_history")
    op.drop_table("products")
    op.drop_table("product_groups")
    op.drop_table("users")
