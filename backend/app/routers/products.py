import asyncio
import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from app.db.database import get_db
from app.models.price_history import PriceHistory
from app.models.product import Product, ProductGroup
from app.schemas.product import (
    FilterOptionsResponse,
    GroupComparisonOut,
    MarketplaceOption,
    MarketplacePrice,
    ParseRequest,
    PriceHistoryOut,
    ProductGroupOut,
    ProductHistoryOut,
    ProductListItem,
    ProductListResponse,
    ProductOut,
    SparklinePoint,
)
from app.services.llm_parser import parse_product_html
from app.services.url_normalizer import marketplace_from_url, normalize_product_url
from app.services.price_analyzer import check_price_drop
from app.services.product_matcher import (
    match_product_by_ean,
    match_product_by_similarity_background,
    trigger_reverse_similarity,
)
from app.services.similarity_matcher import match_product_by_similarity

router = APIRouter()


@router.post("/parse", response_model=ProductOut)
async def parse_product(req: ParseRequest, db: Session = Depends(get_db)):
    """Receive HTML from the extension, parse via LLM, save and return product."""
    canonical_url = normalize_product_url(req.url)
    marketplace = marketplace_from_url(req.url)
    logger.info("Parse request received for URL: %s (canonical: %s)", req.url, canonical_url)
    parsed = await parse_product_html(req.html, req.url, db=db)

    # Check if product already exists by canonical URL
    existing = db.execute(
        select(Product).where(Product.url == canonical_url)
    ).scalar_one_or_none()

    now = datetime.utcnow()

    if existing:
        logger.info("Updating existing product %s (%s)", existing.id, req.url)
        check_price_drop(db, existing, parsed.price)
        existing.name = parsed.name
        existing.current_price = parsed.price
        existing.currency = parsed.currency
        existing.seller = parsed.seller
        existing.image_url = parsed.image_url or req.image_url or existing.image_url
        existing.marketplace = parsed.marketplace or marketplace
        existing.ean = parsed.ean
        existing.last_scraped_at = now
        product = existing
    else:
        logger.info("Creating new product for URL: %s", req.url)
        product = Product(
            url=canonical_url,
            name=parsed.name,
            current_price=parsed.price,
            currency=parsed.currency,
            seller=parsed.seller,
            image_url=parsed.image_url or req.image_url,
            marketplace=parsed.marketplace or marketplace,
            ean=parsed.ean,
            last_scraped_at=now,
        )
        db.add(product)

    db.flush()

    # Camada 2: Match by EAN/GTIN
    match_product_by_ean(db, product)

    if product.group_id:
        # Product got grouped (by EAN) — check if orphans from other
        # marketplaces can now be matched via similarity
        trigger_reverse_similarity(db, product)
    else:
        # No group yet — schedule similarity matching for this product.
        # It will find orphans as candidates, no need for reverse trigger.
        logger.info("Scheduling background similarity match for product %s", product.id)
        asyncio.create_task(match_product_by_similarity_background(product.id))

    # Record price history
    history_entry = PriceHistory(
        product_id=product.id,
        price=parsed.price,
        seller=parsed.seller,
        available=parsed.available,
        scraped_at=now,
    )
    db.add(history_entry)
    db.commit()
    db.refresh(product)

    return product


@router.post("/{product_id}/match", response_model=ProductGroupOut | None)
async def trigger_similarity_match(
    product_id: UUID, db: Session = Depends(get_db)
):
    """Manually trigger similarity matching for a product (synchronous)."""
    logger.info("Manual similarity match triggered for product %s", product_id)
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    group = await match_product_by_similarity(db, product)
    if group:
        db.commit()
        db.refresh(group)
        products = db.execute(
            select(Product).where(Product.group_id == group.id)
        ).scalars().all()
        return ProductGroupOut(
            id=group.id,
            canonical_name=group.canonical_name,
            ean=group.ean,
            products=[ProductOut.model_validate(p) for p in products],
        )
    return None


@router.get("/list", response_model=ProductListResponse)
def list_products(
    search: str | None = None,
    marketplace: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    page: int = 1,
    page_size: int = 24,
    db: Session = Depends(get_db),
):
    """Public endpoint: list products grouped by group_id."""
    # Step 1: filter products
    query = select(Product)
    if search:
        query = query.where(Product.name.ilike(f"%{search}%"))
    if marketplace:
        query = query.where(Product.marketplace == marketplace)
    if min_price is not None:
        query = query.where(Product.current_price >= min_price)
    if max_price is not None:
        query = query.where(Product.current_price <= max_price)

    matching_products = db.execute(query).scalars().all()

    # Step 2: collect group_ids from matches, fetch ALL siblings for those groups
    matched_group_ids = {p.group_id for p in matching_products if p.group_id}
    standalone = [p for p in matching_products if not p.group_id]

    group_products: dict[UUID, list[Product]] = {}
    if matched_group_ids:
        all_siblings = db.execute(
            select(Product).where(Product.group_id.in_(matched_group_ids))
        ).scalars().all()
        for p in all_siblings:
            group_products.setdefault(p.group_id, []).append(p)

    # Step 3: build display items
    display_items: list[ProductListItem] = []

    for group_id, products in group_products.items():
        group = db.get(ProductGroup, group_id)
        sorted_by_price = sorted(
            products,
            key=lambda p: float(p.current_price) if p.current_price is not None else float("inf"),
        )
        cheapest = sorted_by_price[0]

        mp_prices = [
            MarketplacePrice(
                marketplace=p.marketplace,
                current_price=p.current_price,
                product_id=p.id,
            )
            for p in sorted_by_price
        ]

        current_prices = [float(p.current_price) for p in products if p.current_price is not None]
        current_min = min(current_prices) if current_prices else None
        current_max = max(current_prices) if current_prices else None

        # History & sparkline from cheapest product
        cheapest_history = db.execute(
            select(PriceHistory)
            .where(PriceHistory.product_id == cheapest.id)
            .order_by(PriceHistory.scraped_at.asc())
        ).scalars().all()

        sparkline_entries = cheapest_history[-20:] if len(cheapest_history) > 20 else cheapest_history
        sparkline = [SparklinePoint(price=h.price, scraped_at=h.scraped_at) for h in sparkline_entries]

        # Stats from ALL products' histories
        all_history_prices: list[float] = []
        for p in products:
            hist = db.execute(
                select(PriceHistory.price).where(PriceHistory.product_id == p.id)
            ).scalars().all()
            all_history_prices.extend(float(pr) for pr in hist)

        lowest_price = min(all_history_prices) if all_history_prices else None
        highest_price = max(all_history_prices) if all_history_prices else None

        cheapest_prices = [float(h.price) for h in cheapest_history]
        if len(cheapest_prices) >= 2:
            price_change_pct = ((cheapest_prices[-1] - cheapest_prices[0]) / cheapest_prices[0]) * 100
        else:
            price_change_pct = None

        is_at_lowest = current_min is not None and lowest_price is not None and current_min <= lowest_price

        display_items.append(ProductListItem(
            id=cheapest.id,
            url=cheapest.url,
            marketplace=cheapest.marketplace,
            name=(group.canonical_name if group and group.canonical_name else cheapest.name),
            image_url=cheapest.image_url or next((p.image_url for p in products if p.image_url), None),
            current_price=current_min,
            currency=cheapest.currency,
            seller=cheapest.seller,
            ean=group.ean if group else cheapest.ean,
            group_id=group_id,
            last_scraped_at=cheapest.last_scraped_at,
            created_at=min(p.created_at for p in products),
            marketplace_prices=mp_prices,
            price_max=current_max if current_max != current_min else None,
            sparkline=sparkline,
            price_change_pct=round(price_change_pct, 2) if price_change_pct is not None else None,
            lowest_price=lowest_price,
            highest_price=highest_price,
            is_at_lowest=is_at_lowest,
        ))

    # Standalone products
    for product in standalone:
        history = db.execute(
            select(PriceHistory)
            .where(PriceHistory.product_id == product.id)
            .order_by(PriceHistory.scraped_at.asc())
        ).scalars().all()

        sparkline_entries = history[-20:] if len(history) > 20 else history
        sparkline = [SparklinePoint(price=h.price, scraped_at=h.scraped_at) for h in sparkline_entries]

        prices = [float(h.price) for h in history]
        lowest_price = min(prices) if prices else None
        highest_price = max(prices) if prices else None
        current = float(product.current_price) if product.current_price else None

        if len(prices) >= 2:
            price_change_pct = ((prices[-1] - prices[0]) / prices[0]) * 100 if prices[0] else None
        else:
            price_change_pct = None

        is_at_lowest = current is not None and lowest_price is not None and current <= lowest_price

        display_items.append(ProductListItem(
            id=product.id,
            url=product.url,
            marketplace=product.marketplace,
            name=product.name,
            image_url=product.image_url,
            current_price=product.current_price,
            currency=product.currency,
            seller=product.seller,
            ean=product.ean,
            group_id=None,
            last_scraped_at=product.last_scraped_at,
            created_at=product.created_at,
            marketplace_prices=[MarketplacePrice(
                marketplace=product.marketplace,
                current_price=product.current_price,
                product_id=product.id,
            )],
            price_max=None,
            sparkline=sparkline,
            price_change_pct=round(price_change_pct, 2) if price_change_pct is not None else None,
            lowest_price=lowest_price,
            highest_price=highest_price,
            is_at_lowest=is_at_lowest,
        ))

    # Sort
    sort_key = {
        "name": lambda x: (x.name or "").lower(),
        "current_price": lambda x: float(x.current_price or 0),
        "created_at": lambda x: x.created_at,
    }.get(sort_by, lambda x: x.created_at)
    display_items.sort(key=sort_key, reverse=(sort_order == "desc"))

    # Paginate
    total = len(display_items)
    offset = (page - 1) * page_size
    paginated = display_items[offset : offset + page_size]
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

    return ProductListResponse(
        products=paginated,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/filters", response_model=FilterOptionsResponse)
def get_filter_options(db: Session = Depends(get_db)):
    """Public endpoint: return filter options for the product listing UI."""
    # Marketplace counts
    marketplace_rows = db.execute(
        select(Product.marketplace, func.count(Product.id))
        .where(Product.marketplace.is_not(None))
        .group_by(Product.marketplace)
        .order_by(func.count(Product.id).desc())
    ).all()

    marketplaces = [
        MarketplaceOption(name=row[0], count=row[1])
        for row in marketplace_rows
    ]

    # Price range
    price_stats = db.execute(
        select(func.min(Product.current_price), func.max(Product.current_price))
        .where(Product.current_price.is_not(None))
    ).one()

    total = db.execute(select(func.count(Product.id))).scalar() or 0

    return FilterOptionsResponse(
        marketplaces=marketplaces,
        price_min=price_stats[0],
        price_max=price_stats[1],
        total_products=total,
    )


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: UUID, db: Session = Depends(get_db)):
    """Get product by ID."""
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("/{product_id}/history", response_model=ProductHistoryOut)
def get_product_history(product_id: UUID, db: Session = Depends(get_db)):
    """Get product with full price history."""
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    history = db.execute(
        select(PriceHistory)
        .where(PriceHistory.product_id == product_id)
        .order_by(PriceHistory.scraped_at.asc())
    ).scalars().all()

    return ProductHistoryOut(
        product=ProductOut.model_validate(product),
        history=[PriceHistoryOut.model_validate(h) for h in history],
    )


@router.get("/groups/list", response_model=list[ProductGroupOut])
def list_product_groups(db: Session = Depends(get_db)):
    """List all product groups with their products (for comparison view)."""
    groups = db.execute(
        select(ProductGroup)
    ).scalars().all()

    result = []
    for group in groups:
        products = db.execute(
            select(Product).where(Product.group_id == group.id)
        ).scalars().all()
        if len(products) >= 2:
            result.append(ProductGroupOut(
                id=group.id,
                canonical_name=group.canonical_name,
                ean=group.ean,
                products=[ProductOut.model_validate(p) for p in products],
            ))

    return result


@router.get("/groups/{group_id}/compare", response_model=GroupComparisonOut)
def compare_group(group_id: UUID, db: Session = Depends(get_db)):
    """Get full comparison data for a product group (prices per marketplace)."""
    group = db.get(ProductGroup, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    products = db.execute(
        select(Product).where(Product.group_id == group_id)
    ).scalars().all()

    price_histories = {}
    for product in products:
        marketplace = product.marketplace or product.url
        history = db.execute(
            select(PriceHistory)
            .where(PriceHistory.product_id == product.id)
            .order_by(PriceHistory.scraped_at.asc())
        ).scalars().all()
        price_histories[marketplace] = [
            PriceHistoryOut.model_validate(h) for h in history
        ]

    return GroupComparisonOut(
        group=ProductGroupOut(
            id=group.id,
            canonical_name=group.canonical_name,
            ean=group.ean,
            products=[ProductOut.model_validate(p) for p in products],
        ),
        price_histories=price_histories,
    )
