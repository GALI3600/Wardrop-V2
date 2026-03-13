import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.utils import now_brasilia


class PriceHistory(Base):
    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE")
    )
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    seller: Mapped[str | None] = mapped_column(String(255), nullable=True)
    available: Mapped[bool] = mapped_column(Boolean, default=True)
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime, default=now_brasilia
    )

    product = relationship("Product", back_populates="price_history")

    __table_args__ = (
        Index("idx_price_history_product_time", "product_id", scraped_at.desc()),
    )


class UserProduct(Base):
    __tablename__ = "user_products"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        primary_key=True,
    )
    target_price: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    notify_on_any_drop: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=now_brasilia
    )

    user = relationship("User", back_populates="tracked_products")
    product = relationship("Product", back_populates="tracked_by")


class SelectorCache(Base):
    __tablename__ = "selector_cache"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    url_pattern: Mapped[str] = mapped_column(String(500), unique=True)
    selectors: Mapped[dict] = mapped_column(JSON, nullable=False)
    success_count: Mapped[int] = mapped_column(default=0)
    fail_count: Mapped[int] = mapped_column(default=0)
    last_validated_at: Mapped[datetime] = mapped_column(
        DateTime, default=now_brasilia
    )
