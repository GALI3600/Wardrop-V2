"""Add llm_usage table for LLM cost telemetry.

Revision ID: 002
Revises: 001
Create Date: 2026-03-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "llm_usage",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("operation", sa.String(50), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False),
        sa.Column("output_tokens", sa.Integer(), nullable=False),
        sa.Column("cost_usd", sa.Numeric(10, 6), nullable=False),
        sa.Column("product_id", UUID(as_uuid=True), sa.ForeignKey("products.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )
    op.create_index(
        "idx_llm_usage_created_at",
        "llm_usage",
        [sa.text("created_at DESC")],
    )


def downgrade() -> None:
    op.drop_index("idx_llm_usage_created_at", table_name="llm_usage")
    op.drop_table("llm_usage")
