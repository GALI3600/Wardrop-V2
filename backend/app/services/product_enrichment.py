"""Product enrichment service for adding analytics data to products."""
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.price_history import PriceHistory
from app.models.product import Product, ProductGroup
from app.schemas.product import ProductListItem, MarketplacePrice, SparklinePoint


def enrich_product_with_analytics(
    db: Session,
    product: Product,
    all_siblings: list[Product] | None = None
) -> ProductListItem:
    """
    Enrich a product with analytics data (sparkline, price trends, stats).

    Args:
        db: Database session
        product: The product to enrich (for grouped products, pass the cheapest one)
        all_siblings: For grouped products, list of all products in the group.
                     If None, will be fetched from database using product.group_id

    Returns:
        ProductListItem with full analytics data
    """
    is_grouped = product.group_id is not None

    if is_grouped:
        # For grouped products
        if all_siblings is None:
            # Fetch siblings if not provided
            all_siblings = db.execute(
                select(Product).where(Product.group_id == product.group_id)
            ).scalars().all()

        # Sort by price to ensure we're working with the cheapest
        sorted_by_price = sorted(
            all_siblings,
            key=lambda p: float(p.current_price) if p.current_price is not None else float("inf"),
        )
        cheapest = sorted_by_price[0]

        # Build marketplace prices list
        mp_prices = [
            MarketplacePrice(
                marketplace=p.marketplace,
                current_price=p.current_price,
                product_id=p.id,
            )
            for p in sorted_by_price
        ]

        # Calculate current min/max across group
        current_prices = [float(p.current_price) for p in all_siblings if p.current_price is not None]
        current_min = min(current_prices) if current_prices else None
        current_max = max(current_prices) if current_prices else None

        # Fetch price history for cheapest product (for sparkline)
        cheapest_history = db.execute(
            select(PriceHistory)
            .where(PriceHistory.product_id == cheapest.id)
            .order_by(PriceHistory.scraped_at.asc())
        ).scalars().all()

        sparkline_entries = cheapest_history[-20:] if len(cheapest_history) > 20 else cheapest_history
        sparkline = [SparklinePoint(price=h.price, scraped_at=h.scraped_at) for h in sparkline_entries]

        # Fetch history for ALL siblings to calculate lowest/highest
        all_history_prices: list[float] = []
        for p in all_siblings:
            hist = db.execute(
                select(PriceHistory.price).where(PriceHistory.product_id == p.id)
            ).scalars().all()
            all_history_prices.extend(float(pr) for pr in hist)

        lowest_price = min(all_history_prices) if all_history_prices else None
        highest_price = max(all_history_prices) if all_history_prices else None

        # Calculate price change percentage from cheapest product's history
        cheapest_prices = [float(h.price) for h in cheapest_history]
        if len(cheapest_prices) >= 2:
            price_change_pct = ((cheapest_prices[-1] - cheapest_prices[0]) / cheapest_prices[0]) * 100
        else:
            price_change_pct = None

        is_at_lowest = current_min is not None and lowest_price is not None and current_min <= lowest_price

        # Fetch group for canonical name
        group = db.get(ProductGroup, product.group_id)

        return ProductListItem(
            id=cheapest.id,
            url=cheapest.url,
            marketplace=cheapest.marketplace,
            name=(group.canonical_name if group and group.canonical_name else cheapest.name),
            image_url=cheapest.image_url or next((p.image_url for p in all_siblings if p.image_url), None),
            current_price=current_min,
            currency=cheapest.currency,
            seller=cheapest.seller,
            ean=group.ean if group else cheapest.ean,
            group_id=product.group_id,
            last_scraped_at=cheapest.last_scraped_at,
            created_at=min(p.created_at for p in all_siblings),
            marketplace_prices=mp_prices,
            price_max=current_max if current_max != current_min else None,
            sparkline=sparkline,
            price_change_pct=round(price_change_pct, 2) if price_change_pct is not None else None,
            lowest_price=lowest_price,
            highest_price=highest_price,
            is_at_lowest=is_at_lowest,
        )
    else:
        # For standalone products
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

        return ProductListItem(
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
        )
