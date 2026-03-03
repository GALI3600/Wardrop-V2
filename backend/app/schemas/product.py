from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, HttpUrl


class ParseRequest(BaseModel):
    html: str
    url: str
    image_url: str | None = None


class ParsedProduct(BaseModel):
    name: str
    price: Decimal
    currency: str = "BRL"
    seller: str | None = None
    image_url: str | None = None
    marketplace: str | None = None
    available: bool = True
    ean: str | None = None


class ProductOut(BaseModel):
    id: UUID
    url: str
    marketplace: str | None
    name: str | None
    image_url: str | None
    current_price: Decimal | None
    currency: str
    seller: str | None
    ean: str | None
    group_id: UUID | None
    last_scraped_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PriceHistoryOut(BaseModel):
    price: Decimal
    seller: str | None
    available: bool
    scraped_at: datetime

    model_config = {"from_attributes": True}


class ProductHistoryOut(BaseModel):
    product: ProductOut
    history: list[PriceHistoryOut]


class ProductGroupOut(BaseModel):
    id: UUID
    canonical_name: str | None
    ean: str | None
    products: list[ProductOut]

    model_config = {"from_attributes": True}


class GroupComparisonOut(BaseModel):
    group: ProductGroupOut
    price_histories: dict[str, list[PriceHistoryOut]]  # marketplace -> history


# ─── Public listing schemas ─────────────────────────────────


class SparklinePoint(BaseModel):
    price: Decimal
    scraped_at: datetime


class MarketplacePrice(BaseModel):
    marketplace: str | None
    current_price: Decimal | None
    product_id: UUID


class ProductListItem(BaseModel):
    id: UUID
    url: str
    marketplace: str | None
    name: str | None
    image_url: str | None
    current_price: Decimal | None
    currency: str
    seller: str | None
    ean: str | None
    group_id: UUID | None
    last_scraped_at: datetime | None
    created_at: datetime
    marketplace_prices: list[MarketplacePrice]
    price_max: Decimal | None
    sparkline: list[SparklinePoint]
    price_change_pct: float | None
    lowest_price: Decimal | None
    highest_price: Decimal | None
    is_at_lowest: bool


class ProductListResponse(BaseModel):
    products: list[ProductListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class MarketplaceOption(BaseModel):
    name: str
    count: int


class FilterOptionsResponse(BaseModel):
    marketplaces: list[MarketplaceOption]
    price_min: Decimal | None
    price_max: Decimal | None
    total_products: int
