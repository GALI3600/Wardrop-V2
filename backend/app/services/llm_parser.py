import json
import logging
import re

from bs4 import BeautifulSoup

from app.config import settings
from app.services.llm_client import call_llm
from app.schemas.product import ParsedProduct
from app.services.ean_validator import validate_ean
from app.services.schema_org import extract_schema_org

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """\
You are a product data extractor. Given the HTML content of a product page from an e-commerce marketplace, extract the following information and return it as JSON.

Required fields:
- name: Product name/title
- price: The lowest available price as a number (no currency symbol). If the page shows multiple prices (e.g., Pix/à vista discount vs. installment/credit card price), always use the lowest price — typically the Pix or "à vista" price.
- currency: Currency code (e.g., "BRL", "USD")

Optional fields (include if found):
- seller: Seller/store name
- image_url: Main product image URL
- marketplace: Marketplace name (e.g., "amazon", "mercadolivre", "magalu", "shopee")
- available: Whether the product is in stock (true/false)
- ean: EAN/GTIN/barcode if visible on the page
- selectors: An object with CSS selectors you used to find each field. Example:
  {"name": "#productTitle", "price": "span.a-price-whole", "seller": "#sellerProfileTriggerId", "image": "#landingImage"}

Return ONLY valid JSON, no markdown formatting or extra text.
"""


def clean_html(raw_html: str) -> str:
    """Remove scripts, styles, nav, footer, and other non-content elements."""
    soup = BeautifulSoup(raw_html, "html.parser")

    for tag in soup.find_all(
        ["script", "style", "nav", "footer", "header", "iframe", "noscript"]
    ):
        tag.decompose()

    for tag in soup.find_all(attrs={"role": ["navigation", "banner", "contentinfo"]}):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)
    # Collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Keep it under ~8000 chars to save tokens
    if len(text) > 8000:
        text = text[:8000]

    return text


async def parse_product_html(html: str, url: str, db=None) -> ParsedProduct:
    """Extract product data from HTML.

    Strategy (cheapest first):
      1. Try schema.org JSON-LD extraction (free, instant)
      2. Fall back to LLM parsing (costs API call)

    If db is provided, LLM token usage will be tracked.
    """
    logger.debug("Parsing product HTML for %s", url)

    # Camada 1: schema.org
    schema_result = extract_schema_org(html)
    if schema_result:
        logger.info("Extracted product via schema.org for %s: %s", url, schema_result.name)
        return schema_result

    # Camada 3: LLM fallback
    logger.info("No schema.org data, falling back to LLM for %s", url)
    return await _parse_with_llm(html, url, db=db)


async def _parse_with_llm(html: str, url: str, db=None) -> ParsedProduct:
    """Send cleaned HTML to Claude and extract product data."""
    logger.debug("Cleaning HTML for LLM extraction (%s)", url)
    cleaned = clean_html(html)

    result = await call_llm(
        user_content=f"URL: {url}\n\nHTML content:\n{cleaned}",
        system_prompt=EXTRACTION_PROMPT,
    )

    # Track LLM token usage
    if db:
        from app.services.llm_usage_tracker import track_llm_usage

        track_llm_usage(
            db,
            "product_parsing",
            result.model,
            result.input_tokens,
            result.output_tokens,
        )

    response_text = result.text

    # Strip markdown code fences if present
    response_text = re.sub(r"^```(?:json)?\s*", "", response_text.strip())
    response_text = re.sub(r"\s*```$", "", response_text.strip())

    data = json.loads(response_text)

    # Extract selectors separately (not part of ParsedProduct)
    selectors = data.pop("selectors", None)

    product = ParsedProduct(**data)

    # Validate EAN returned by LLM
    if product.ean:
        product.ean = validate_ean(product.ean)

    # Attach selectors as extra attribute for the caller to use
    product._selectors = selectors

    logger.info("LLM extracted product for %s: %s (R$%s)", url, product.name, product.price)
    return product
