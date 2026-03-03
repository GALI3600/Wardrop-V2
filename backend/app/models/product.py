import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class ProductGroup(Base):
    __tablename__ = "product_groups"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    canonical_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ean: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    products = relationship("Product", back_populates="group")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    url: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    marketplace: Mapped[str | None] = mapped_column(String(100), nullable=True)
    name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_price: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    currency: Mapped[str] = mapped_column(String(10), default="BRL")
    seller: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ean: Mapped[str | None] = mapped_column(String(50), nullable=True)
    group_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("product_groups.id"), nullable=True
    )
    last_scraped_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    group = relationship("ProductGroup", back_populates="products")
    price_history = relationship(
        "PriceHistory", back_populates="product", cascade="all, delete-orphan"
    )
    tracked_by = relationship(
        "UserProduct", back_populates="product", cascade="all, delete-orphan"
    )
