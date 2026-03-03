import uuid
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.price_history import PriceHistory, UserProduct
from app.models.product import Product
from app.schemas.product import ParsedProduct
from app.services.scraper import scrape_all_tracked_products, scrape_product


class TestScrapeProduct:
    @pytest.mark.asyncio
    @patch("app.services.scraper.parse_product_html")
    @patch("app.services.scraper.check_price_drop")
    @patch("app.services.scraper.httpx.AsyncClient")
    async def test_scrape_product_success(
        self, mock_client_cls, mock_check_drop, mock_parse, db, sample_product
    ):
        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.text = "<div>Product page</div>"
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        # Mock LLM parse
        mock_parse.return_value = ParsedProduct(
            name="Updated Product",
            price=Decimal("149.90"),
            currency="BRL",
            seller="New Seller",
            available=True,
        )

        await scrape_product(db, sample_product)

        # Verify product was updated
        db.refresh(sample_product)
        assert sample_product.current_price == Decimal("149.90")
        assert sample_product.name == "Updated Product"
        assert sample_product.seller == "New Seller"
        assert sample_product.last_scraped_at is not None

        # Verify price history was recorded
        history = db.query(PriceHistory).filter_by(product_id=sample_product.id).all()
        assert len(history) >= 1

        # Verify price drop check was called
        mock_check_drop.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.services.scraper.httpx.AsyncClient")
    async def test_scrape_product_http_error(self, mock_client_cls, db, sample_product):
        """Should handle HTTP errors gracefully."""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=Exception("Connection refused"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        # Should not raise
        await scrape_product(db, sample_product)

        # Product should remain unchanged
        original_price = sample_product.current_price
        db.refresh(sample_product)
        assert sample_product.current_price == original_price


class TestScrapeAllTrackedProducts:
    @pytest.mark.asyncio
    @patch("app.services.scraper.scrape_product")
    async def test_scrapes_tracked_products(
        self, mock_scrape, db, sample_product, tracked_product
    ):
        mock_scrape.return_value = None

        await scrape_all_tracked_products(db)

        mock_scrape.assert_called_once()
        call_args = mock_scrape.call_args[0]
        assert call_args[1].id == sample_product.id

    @pytest.mark.asyncio
    @patch("app.services.scraper.scrape_product")
    async def test_skips_when_no_tracked_products(self, mock_scrape, db):
        await scrape_all_tracked_products(db)
        mock_scrape.assert_not_called()
