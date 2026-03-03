"""
URL normalization for product pages.

Strips tracking params, session IDs, and other noise from marketplace URLs
to avoid duplicate products when the same page is visited with different params.
"""

import re
from urllib.parse import urlparse, urlunparse


def normalize_product_url(url: str) -> str:
    """Normalize a product URL to its canonical form.

    Amazon:  keep only /dp/ASIN or /gp/product/ASIN
    Others:  strip common tracking params, keep the path clean
    """
    parsed = urlparse(url)
    hostname = parsed.hostname or ""

    if "amazon" in hostname:
        return _normalize_amazon(parsed)
    if "mercadolivre" in hostname or "mercadolibre" in hostname:
        return _normalize_mercadolivre(parsed)
    if "magazineluiza" in hostname or "magalu" in hostname:
        return _normalize_magalu(parsed)
    if "shopee" in hostname:
        return _normalize_shopee(parsed)

    # Generic: strip query params entirely, keep scheme + host + path
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))


def _normalize_amazon(parsed) -> str:
    """Amazon: extract /dp/ASIN or /gp/product/ASIN."""
    path = parsed.path

    # Match /dp/ASIN (10 alphanumeric chars)
    match = re.search(r"/(dp|gp/product)/([A-Z0-9]{10})", path)
    if match:
        kind, asin = match.group(1), match.group(2)
        return urlunparse((parsed.scheme, parsed.netloc, f"/{kind}/{asin}", "", "", ""))

    # Fallback: keep path, strip query
    return urlunparse((parsed.scheme, parsed.netloc, path, "", "", ""))


def _normalize_mercadolivre(parsed) -> str:
    """Mercado Livre: keep path up to MLB ID, strip query params."""
    path = parsed.path
    match = re.search(r"(.*MLB-?\d+)", path)
    if match:
        return urlunparse((parsed.scheme, parsed.netloc, match.group(1), "", "", ""))
    return urlunparse((parsed.scheme, parsed.netloc, path, "", "", ""))


def _normalize_magalu(parsed) -> str:
    """Magazine Luiza: keep /produto/SLUG/ or /p/SLUG/."""
    path = parsed.path
    match = re.search(r"/(produto|p)/([a-z0-9-]+)/?", path, re.IGNORECASE)
    if match:
        kind, slug = match.group(1), match.group(2)
        return urlunparse((parsed.scheme, parsed.netloc, f"/{kind}/{slug}/", "", "", ""))
    return urlunparse((parsed.scheme, parsed.netloc, path, "", "", ""))


def _normalize_shopee(parsed) -> str:
    """Shopee: keep the product path with IDs."""
    path = parsed.path
    return urlunparse((parsed.scheme, parsed.netloc, path, "", "", ""))


_DOMAIN_TO_MARKETPLACE = {
    "amazon": "amazon",
    "mercadolivre": "mercadolivre",
    "mercadolibre": "mercadolivre",
    "magazineluiza": "magalu",
    "magalu": "magalu",
    "shopee": "shopee",
    "casasbahia": "casasbahia",
    "americanas": "americanas",
    "kabum": "kabum",
    "aliexpress": "aliexpress",
}


def marketplace_from_url(url: str) -> str | None:
    """Infer marketplace name from a product URL."""
    hostname = (urlparse(url).hostname or "").lower()
    for domain, name in _DOMAIN_TO_MARKETPLACE.items():
        if domain in hostname:
            return name
    return None
