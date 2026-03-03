"""
Camada 1: Extract product data from schema.org JSON-LD embedded in HTML.
Many marketplaces include structured data like:

<script type="application/ld+json">
{
  "@type": "Product",
  "name": "iPhone 15 128GB",
  "gtin13": "7891234567890",
  "offers": { "price": "4299.00", "priceCurrency": "BRL" }
}
</script>

If found, this is cheaper and more reliable than calling the LLM.
"""

import json
import logging
import re
from decimal import Decimal, InvalidOperation

from bs4 import BeautifulSoup

from app.schemas.product import ParsedProduct
from app.services.ean_validator import validate_ean

logger = logging.getLogger(__name__)


def extract_schema_org(html: str) -> ParsedProduct | None:
    """Try to extract product data from schema.org JSON-LD in the HTML.

    Returns ParsedProduct if a valid Product schema is found, None otherwise.
    """
    soup = BeautifulSoup(html, "html.parser")
    ld_scripts = soup.find_all("script", type="application/ld+json")

    for script in ld_scripts:
        try:
            data = json.loads(script.string or "")
        except (json.JSONDecodeError, TypeError):
            logger.debug("Skipping invalid JSON-LD script block")
            continue

        product = _find_product(data)
        if product:
            parsed = _parse_product_schema(product)
            if parsed:
                logger.debug("Found schema.org Product: %s", parsed.name)
                return parsed

    logger.debug("No valid schema.org Product found in HTML")
    return None


def _find_product(data) -> dict | None:
    """Recursively search for a Product type in the JSON-LD data."""
    if isinstance(data, dict):
        schema_type = data.get("@type", "")
        # @type can be a string or list
        types = schema_type if isinstance(schema_type, list) else [schema_type]
        if "Product" in types:
            return data
        # Search nested structures (e.g., @graph)
        for value in data.values():
            result = _find_product(value)
            if result:
                return result
    elif isinstance(data, list):
        for item in data:
            result = _find_product(item)
            if result:
                return result
    return None


def _parse_product_schema(data: dict) -> ParsedProduct | None:
    """Convert a schema.org Product dict into a ParsedProduct."""
    name = data.get("name")
    if not name:
        return None

    # Extract price from offers
    price, currency, available, seller = _extract_offer(data)
    if price is None:
        return None

    # Extract EAN/GTIN — prefer dedicated GTIN fields, fallback to SKU-like fields
    raw_ean = (
        data.get("gtin13")
        or data.get("gtin14")
        or data.get("gtin12")
        or data.get("gtin8")
        or data.get("gtin")
    )
    if not raw_ean:
        # Fallback: try productID/mpn/sku but only if they pass validation
        raw_ean = data.get("productID") or data.get("mpn") or data.get("sku")

    ean = validate_ean(str(raw_ean)) if raw_ean else None

    # Extract image
    image = data.get("image")
    if isinstance(image, list):
        image = image[0] if image else None
    if isinstance(image, dict):
        image = image.get("url") or image.get("contentUrl")

    return ParsedProduct(
        name=str(name),
        price=price,
        currency=currency or "BRL",
        seller=seller,
        image_url=str(image) if image else None,
        available=available,
        ean=str(ean) if ean else None,
    )


def _extract_offer(data: dict) -> tuple[Decimal | None, str | None, bool, str | None]:
    """Extract price, currency, availability, and seller from offers."""
    offers = data.get("offers", data)

    # offers can be a single dict, a list, or nested in AggregateOffer
    if isinstance(offers, list):
        offers = offers[0] if offers else {}
    if isinstance(offers, dict):
        offer_type = offers.get("@type", "")
        if offer_type == "AggregateOffer":
            price_str = offers.get("lowPrice") or offers.get("price")
        else:
            price_str = offers.get("price")

        currency = offers.get("priceCurrency")
        seller_data = offers.get("seller")
        seller = None
        if isinstance(seller_data, dict):
            seller = seller_data.get("name")
        elif isinstance(seller_data, str):
            seller = seller_data

        # Availability
        availability = offers.get("availability", "")
        available = "InStock" in str(availability) if availability else True

        # Parse price
        if price_str is not None:
            try:
                # Handle comma as decimal separator (common in BR)
                price_clean = str(price_str).replace(".", "").replace(",", ".")
                # But if it looks like a normal decimal (e.g., "4299.00"), use as-is
                try:
                    price = Decimal(str(price_str))
                except InvalidOperation:
                    price = Decimal(price_clean)
                return price, currency, available, seller
            except (InvalidOperation, ValueError):
                pass

    return None, None, True, None
