import json
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from app.services.llm_client import LLMResponse
from app.services.llm_parser import clean_html, parse_product_html


class TestCleanHTML:
    def test_removes_scripts(self):
        html = "<div>Hello</div><script>alert('xss')</script>"
        result = clean_html(html)
        assert "alert" not in result
        assert "Hello" in result

    def test_removes_styles(self):
        html = "<style>.foo{color:red}</style><p>Content</p>"
        result = clean_html(html)
        assert "color:red" not in result
        assert "Content" in result

    def test_removes_nav_footer_header(self):
        html = """
        <nav>Navigation</nav>
        <header>Header</header>
        <main>Product Info</main>
        <footer>Footer</footer>
        """
        result = clean_html(html)
        assert "Navigation" not in result
        assert "Header" not in result
        assert "Footer" not in result
        assert "Product Info" in result

    def test_removes_elements_with_roles(self):
        html = """
        <div role="navigation">Nav</div>
        <div role="banner">Banner</div>
        <div>Content</div>
        <div role="contentinfo">Info</div>
        """
        result = clean_html(html)
        assert "Nav" not in result
        assert "Banner" not in result
        assert "Content" in result

    def test_collapses_blank_lines(self):
        html = "<p>A</p><br><br><br><br><br><p>B</p>"
        result = clean_html(html)
        # Should not have more than 2 consecutive newlines
        assert "\n\n\n" not in result

    def test_truncates_long_html(self):
        html = "<p>" + "x" * 10000 + "</p>"
        result = clean_html(html)
        assert len(result) <= 8000

    def test_handles_empty_html(self):
        result = clean_html("")
        assert isinstance(result, str)

    def test_removes_iframes_and_noscript(self):
        html = """
        <iframe src="ad.html"></iframe>
        <noscript>Enable JS</noscript>
        <div>Real content</div>
        """
        result = clean_html(html)
        assert "ad.html" not in result
        assert "Enable JS" not in result
        assert "Real content" in result


class TestSchemaOrgIntegration:
    @pytest.mark.asyncio
    async def test_uses_schema_org_when_available(self):
        """Should extract from schema.org and NOT call the LLM."""
        ld_json = json.dumps({
            "@type": "Product",
            "name": "Schema Product",
            "offers": {"price": "199.00", "priceCurrency": "BRL"},
            "gtin13": "5901234123457",
        })
        html = (
            '<html><head><script type="application/ld+json">'
            + ld_json
            + "</script></head><body></body></html>"
        )

        with patch("app.services.llm_parser.call_llm", new_callable=AsyncMock) as mock_llm:
            result = await parse_product_html(html, "https://example.com")
            mock_llm.assert_not_called()

        assert result.name == "Schema Product"
        assert result.price == Decimal("199.00")
        assert result.ean == "5901234123457"

    @pytest.mark.asyncio
    async def test_falls_back_to_llm_when_no_schema(self):
        """Should call LLM when no schema.org data is found."""
        mock_result = LLMResponse(
            text=json.dumps({"name": "LLM Product", "price": 99.00, "currency": "BRL"}),
            input_tokens=100, output_tokens=50, model="test-model",
        )

        with patch("app.services.llm_parser.call_llm", new_callable=AsyncMock, return_value=mock_result):
            result = await parse_product_html("<div>No schema here</div>", "https://example.com")

        assert result.name == "LLM Product"


class TestParseProductHTML:
    @pytest.mark.asyncio
    async def test_parses_product_successfully(self):
        mock_result = LLMResponse(
            text=json.dumps({
                "name": "iPhone 15 128GB",
                "price": 4299.00,
                "currency": "BRL",
                "seller": "Apple Store",
                "image_url": "https://example.com/iphone.jpg",
                "marketplace": "amazon",
                "available": True,
                "ean": "5901234123457",
            }),
            input_tokens=200, output_tokens=100, model="test-model",
        )

        with patch("app.services.llm_parser.call_llm", new_callable=AsyncMock, return_value=mock_result):
            result = await parse_product_html("<div>Product page</div>", "https://amazon.com.br/dp/B0TEST")

        assert result.name == "iPhone 15 128GB"
        assert result.price == Decimal("4299.00")
        assert result.currency == "BRL"
        assert result.seller == "Apple Store"
        assert result.marketplace == "amazon"
        assert result.available is True
        assert result.ean == "5901234123457"

    @pytest.mark.asyncio
    async def test_strips_markdown_fences_from_response(self):
        mock_result = LLMResponse(
            text='```json\n{"name": "Product", "price": 99.90, "currency": "BRL"}\n```',
            input_tokens=100, output_tokens=50, model="test-model",
        )

        with patch("app.services.llm_parser.call_llm", new_callable=AsyncMock, return_value=mock_result):
            result = await parse_product_html("<div>Page</div>", "https://example.com")

        assert result.name == "Product"
        assert result.price == Decimal("99.90")

    @pytest.mark.asyncio
    async def test_handles_minimal_response(self):
        """LLM returns only required fields."""
        mock_result = LLMResponse(
            text=json.dumps({"name": "Minimal Product", "price": 10.00, "currency": "BRL"}),
            input_tokens=100, output_tokens=50, model="test-model",
        )

        with patch("app.services.llm_parser.call_llm", new_callable=AsyncMock, return_value=mock_result):
            result = await parse_product_html("<div>Minimal</div>", "https://example.com")

        assert result.name == "Minimal Product"
        assert result.seller is None
        assert result.ean is None
        assert result.available is True  # default

    @pytest.mark.asyncio
    async def test_raises_on_invalid_json(self):
        mock_result = LLMResponse(
            text="not valid json at all",
            input_tokens=100, output_tokens=50, model="test-model",
        )

        with patch("app.services.llm_parser.call_llm", new_callable=AsyncMock, return_value=mock_result):
            with pytest.raises(Exception):
                await parse_product_html("<div>Bad</div>", "https://example.com")
