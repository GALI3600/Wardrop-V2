import json
from decimal import Decimal

import pytest

from app.services.schema_org import extract_schema_org


def _make_html(ld_json: dict) -> str:
    """Helper to create HTML with a JSON-LD script tag."""
    return (
        "<html><head>"
        f'<script type="application/ld+json">{json.dumps(ld_json)}</script>'
        "</head><body></body></html>"
    )


class TestExtractSchemaOrg:
    def test_extracts_basic_product(self):
        html = _make_html({
            "@type": "Product",
            "name": "iPhone 15 128GB",
            "offers": {
                "@type": "Offer",
                "price": "4299.00",
                "priceCurrency": "BRL",
                "availability": "https://schema.org/InStock",
            },
            "gtin13": "5901234123457",
            "image": "https://example.com/iphone.jpg",
        })
        result = extract_schema_org(html)

        assert result is not None
        assert result.name == "iPhone 15 128GB"
        assert result.price == Decimal("4299.00")
        assert result.currency == "BRL"
        assert result.ean == "5901234123457"
        assert result.available is True
        assert result.image_url == "https://example.com/iphone.jpg"

    def test_extracts_from_graph(self):
        html = _make_html({
            "@context": "https://schema.org",
            "@graph": [
                {"@type": "WebPage", "name": "Page"},
                {
                    "@type": "Product",
                    "name": "Samsung Galaxy S24",
                    "offers": {"price": "3499.00", "priceCurrency": "BRL"},
                },
            ],
        })
        result = extract_schema_org(html)

        assert result is not None
        assert result.name == "Samsung Galaxy S24"
        assert result.price == Decimal("3499.00")

    def test_extracts_aggregate_offer(self):
        html = _make_html({
            "@type": "Product",
            "name": "Notebook Dell",
            "offers": {
                "@type": "AggregateOffer",
                "lowPrice": "2999.00",
                "highPrice": "3499.00",
                "priceCurrency": "BRL",
            },
        })
        result = extract_schema_org(html)

        assert result is not None
        assert result.price == Decimal("2999.00")

    def test_extracts_with_seller(self):
        html = _make_html({
            "@type": "Product",
            "name": "Headphone",
            "offers": {
                "price": "199.90",
                "priceCurrency": "BRL",
                "seller": {"@type": "Organization", "name": "Loja XYZ"},
            },
        })
        result = extract_schema_org(html)

        assert result is not None
        assert result.seller == "Loja XYZ"

    def test_extracts_image_from_list(self):
        html = _make_html({
            "@type": "Product",
            "name": "Mouse",
            "image": ["https://example.com/img1.jpg", "https://example.com/img2.jpg"],
            "offers": {"price": "49.90", "priceCurrency": "BRL"},
        })
        result = extract_schema_org(html)

        assert result is not None
        assert result.image_url == "https://example.com/img1.jpg"

    def test_extracts_valid_ean_from_gtin_fields(self):
        """Valid EAN from GTIN fields should be extracted."""
        valid_ean = "5901234123457"
        for field in ["gtin13", "gtin14", "gtin12", "gtin8", "gtin"]:
            html = _make_html({
                "@type": "Product",
                "name": "Product",
                field: valid_ean,
                "offers": {"price": "10.00", "priceCurrency": "BRL"},
            })
            result = extract_schema_org(html)

            assert result is not None
            assert result.ean == valid_ean, f"Failed for field: {field}"

    def test_extracts_valid_ean_from_fallback_fields(self):
        """Valid EAN from productID/mpn/sku should be extracted."""
        valid_ean = "5901234123457"
        for field in ["productID", "mpn", "sku"]:
            html = _make_html({
                "@type": "Product",
                "name": "Product",
                field: valid_ean,
                "offers": {"price": "10.00", "priceCurrency": "BRL"},
            })
            result = extract_schema_org(html)

            assert result is not None
            assert result.ean == valid_ean, f"Failed for field: {field}"

    def test_rejects_invalid_ean_from_sku(self):
        """Internal SKU codes (like KaBum's 996782) should not be treated as EAN."""
        html = _make_html({
            "@type": "Product",
            "name": "Product",
            "sku": "996782",
            "offers": {"price": "10.00", "priceCurrency": "BRL"},
        })
        result = extract_schema_org(html)

        assert result is not None
        assert result.ean is None

    def test_rejects_non_numeric_product_id(self):
        """Non-numeric productID should not be treated as EAN."""
        html = _make_html({
            "@type": "Product",
            "name": "Product",
            "productID": "B0DJYFDR1R",
            "offers": {"price": "10.00", "priceCurrency": "BRL"},
        })
        result = extract_schema_org(html)

        assert result is not None
        assert result.ean is None

    def test_returns_none_for_no_schema(self):
        html = "<html><body><h1>No schema here</h1></body></html>"
        result = extract_schema_org(html)
        assert result is None

    def test_returns_none_for_non_product_schema(self):
        html = _make_html({"@type": "WebPage", "name": "Just a page"})
        result = extract_schema_org(html)
        assert result is None

    def test_returns_none_for_product_without_price(self):
        html = _make_html({"@type": "Product", "name": "No Price Product"})
        result = extract_schema_org(html)
        assert result is None

    def test_returns_none_for_product_without_name(self):
        html = _make_html({
            "@type": "Product",
            "offers": {"price": "10.00"},
        })
        result = extract_schema_org(html)
        assert result is None

    def test_handles_invalid_json(self):
        html = """
        <html><head>
        <script type="application/ld+json">
        {not valid json at all}
        </script>
        </head><body></body></html>
        """
        result = extract_schema_org(html)
        assert result is None

    def test_out_of_stock(self):
        html = _make_html({
            "@type": "Product",
            "name": "Out of Stock Product",
            "offers": {
                "price": "99.00",
                "priceCurrency": "BRL",
                "availability": "https://schema.org/OutOfStock",
            },
        })
        result = extract_schema_org(html)

        assert result is not None
        assert result.available is False

    def test_offers_as_list(self):
        html = _make_html({
            "@type": "Product",
            "name": "Multi-seller Product",
            "offers": [
                {"price": "99.00", "priceCurrency": "BRL", "seller": "Seller A"},
                {"price": "109.00", "priceCurrency": "BRL", "seller": "Seller B"},
            ],
        })
        result = extract_schema_org(html)

        assert result is not None
        assert result.price == Decimal("99.00")
        assert result.seller == "Seller A"
