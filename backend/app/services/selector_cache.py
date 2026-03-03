"""
Selector cache service: caches CSS selectors discovered by the LLM
to avoid repeated API calls for the same marketplace URL patterns.
"""

import logging
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.price_history import SelectorCache
from app.schemas.product import ParsedProduct

logger = logging.getLogger(__name__)


def url_to_pattern(url: str) -> str:
    """Convert a product URL to a cache-friendly pattern.

    Examples:
        https://amazon.com.br/dp/B0ABC123  →  amazon.com.br/dp/*
        https://www.mercadolivre.com.br/MLB-12345  →  mercadolivre.com.br/MLB-*
    """
    parsed = urlparse(url)
    host = parsed.hostname or ""
    host = re.sub(r"^www\.", "", host)

    path = parsed.path.rstrip("/")
    # Replace final path segment with wildcard
    parts = path.rsplit("/", 1)
    if len(parts) == 2:
        pattern = f"{host}{parts[0]}/*"
    else:
        pattern = f"{host}/*"

    return pattern


def get_cached_selectors(db: Session, url: str) -> dict | None:
    """Look up cached selectors for a URL pattern."""
    pattern = url_to_pattern(url)
    cache_entry = db.execute(
        select(SelectorCache).where(SelectorCache.url_pattern == pattern)
    ).scalar_one_or_none()

    if not cache_entry:
        logger.debug("No cached selectors for pattern %s", pattern)
        return None

    # Skip cache if failure rate is too high (>50% failures with at least 3 attempts)
    total = cache_entry.success_count + cache_entry.fail_count
    if total >= 3 and cache_entry.fail_count / total > 0.5:
        logger.info(
            "Skipping cached selectors for %s — high failure rate (%d/%d)",
            pattern, cache_entry.fail_count, total,
        )
        return None

    logger.debug("Using cached selectors for pattern %s", pattern)
    return cache_entry.selectors


def try_cached_extraction(html: str, selectors: dict) -> ParsedProduct | None:
    """Try to extract product data using cached CSS selectors.

    Returns ParsedProduct if extraction succeeds, None if it fails.
    """
    soup = BeautifulSoup(html, "html.parser")

    name_sel = selectors.get("name")
    price_sel = selectors.get("price")

    if not name_sel or not price_sel:
        return None

    # Extract name
    name_el = soup.select_one(name_sel)
    if not name_el:
        return None
    name = name_el.get_text(strip=True)
    if not name:
        return None

    # Extract price
    price_el = soup.select_one(price_sel)
    if not price_el:
        return None
    price_text = price_el.get_text(strip=True)
    # Clean price text: remove currency symbols, thousands separators
    price_text = re.sub(r"[^\d.,]", "", price_text)
    price_text = price_text.replace(".", "").replace(",", ".")
    try:
        price = Decimal(price_text)
        if price <= 0:
            return None
    except (InvalidOperation, ValueError):
        return None

    # Optional fields
    seller = None
    seller_sel = selectors.get("seller")
    if seller_sel:
        seller_el = soup.select_one(seller_sel)
        if seller_el:
            seller = seller_el.get_text(strip=True) or None

    image_url = None
    image_sel = selectors.get("image")
    if image_sel:
        image_el = soup.select_one(image_sel)
        if image_el:
            image_url = image_el.get("src") or image_el.get("data-src")

    return ParsedProduct(
        name=name,
        price=price,
        currency=selectors.get("currency", "BRL"),
        seller=seller,
        image_url=image_url,
        available=True,
    )


def save_selectors(db: Session, url: str, selectors: dict) -> None:
    """Save or update cached selectors for a URL pattern."""
    pattern = url_to_pattern(url)
    logger.info("Saving selectors for pattern %s", pattern)
    existing = db.execute(
        select(SelectorCache).where(SelectorCache.url_pattern == pattern)
    ).scalar_one_or_none()

    if existing:
        existing.selectors = selectors
        existing.last_validated_at = datetime.utcnow()
    else:
        entry = SelectorCache(
            url_pattern=pattern,
            selectors=selectors,
            success_count=0,
            fail_count=0,
            last_validated_at=datetime.utcnow(),
        )
        db.add(entry)


def record_cache_result(db: Session, url: str, success: bool) -> None:
    """Increment success or failure count for a URL pattern's cache."""
    pattern = url_to_pattern(url)
    entry = db.execute(
        select(SelectorCache).where(SelectorCache.url_pattern == pattern)
    ).scalar_one_or_none()

    if entry:
        if success:
            entry.success_count += 1
        else:
            entry.fail_count += 1
        entry.last_validated_at = datetime.utcnow()
