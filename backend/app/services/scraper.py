import asyncio
import logging
from datetime import datetime
from decimal import Decimal

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from app.models.price_history import PriceHistory, UserProduct
from app.models.product import Product
from app.services.llm_parser import parse_product_html
from app.services.price_analyzer import check_price_drop
from app.services.product_matcher import (
    match_product_by_ean,
    match_product_by_similarity_background,
)
from app.services.selector_cache import (
    get_cached_selectors,
    record_cache_result,
    save_selectors,
    try_cached_extraction,
)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)


async def scrape_product(db: Session, product: Product):
    """Re-scrape a product's page and update price data.

    Extraction strategy (cheapest first):
      1. schema.org JSON-LD (handled inside parse_product_html)
      2. Cached CSS selectors from previous LLM calls
      3. LLM parsing (most expensive, generates new selectors to cache)
    """
    try:
        logger.info("Scraping product: %s", product.url)
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=30.0,
            headers={"User-Agent": USER_AGENT},
        ) as client:
            response = await client.get(product.url)
            response.raise_for_status()
        logger.debug("HTTP %d for %s (%d bytes)", response.status_code, product.url, len(response.text))

        html = response.text
        parsed = None

        # Try cached selectors before full parse (skip LLM if cache works)
        cached_selectors = get_cached_selectors(db, product.url)
        if cached_selectors:
            parsed = try_cached_extraction(html, cached_selectors)
            if parsed:
                record_cache_result(db, product.url, success=True)
                logger.info("Selector cache hit for %s", product.url)
            else:
                record_cache_result(db, product.url, success=False)
                logger.info("Selector cache miss for %s, falling back to LLM", product.url)

        # Full parse (schema.org → LLM)
        if not parsed:
            parsed = await parse_product_html(html, product.url, db=db)

            # Save selectors from LLM response if available
            selectors = getattr(parsed, "_selectors", None)
            if selectors and isinstance(selectors, dict):
                save_selectors(db, product.url, selectors)

        new_price = Decimal(str(parsed.price))

        # Check for price drop before updating
        check_price_drop(db, product, new_price)

        # Update product
        product.name = parsed.name
        product.current_price = new_price
        product.seller = parsed.seller
        product.image_url = parsed.image_url
        product.ean = parsed.ean or product.ean
        product.last_scraped_at = datetime.utcnow()

        # Try EAN matching if not grouped yet
        if not product.group_id:
            match_product_by_ean(db, product)

        # Camada 2b: Similarity matching (background, fire-and-forget)
        if not product.group_id and not product.ean:
            logger.info("Scheduling background similarity match for product %s", product.id)
            asyncio.create_task(match_product_by_similarity_background(product.id))

        # Record price history
        history = PriceHistory(
            product_id=product.id,
            price=new_price,
            seller=parsed.seller,
            available=parsed.available,
            scraped_at=datetime.utcnow(),
        )
        db.add(history)
        db.commit()

        logger.info("Scraped %s: R$%s", product.url, new_price)

    except Exception as e:
        logger.error("Scrape failed for %s: %s", product.url, e)


MAX_CONCURRENT_SCRAPES = 10


async def scrape_all_tracked_products(db: Session):
    """Scrape all products that have at least one user tracking them.

    Uses asyncio.gather with a semaphore to scrape up to
    MAX_CONCURRENT_SCRAPES products in parallel.  Each task gets its own
    DB session so there are no shared-session issues.
    """
    from app.db.database import SessionLocal

    tracked_product_ids = db.execute(
        select(UserProduct.product_id).distinct()
    ).scalars().all()

    if not tracked_product_ids:
        logger.info("No tracked products to scrape")
        return

    product_ids = db.execute(
        select(Product.id).where(Product.id.in_(tracked_product_ids))
    ).scalars().all()

    logger.info("Scraping %d tracked products (concurrency=%d)...", len(product_ids), MAX_CONCURRENT_SCRAPES)

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_SCRAPES)
    start = asyncio.get_event_loop().time()

    async def _bounded_scrape(product_id: int):
        async with semaphore:
            session = SessionLocal()
            try:
                product = session.execute(
                    select(Product).where(Product.id == product_id)
                ).scalar_one_or_none()
                if product:
                    await scrape_product(session, product)
            finally:
                session.close()

    await asyncio.gather(*[_bounded_scrape(pid) for pid in product_ids])

    elapsed = asyncio.get_event_loop().time() - start
    logger.info("Scrape batch finished: %d products in %.1fs", len(product_ids), elapsed)
