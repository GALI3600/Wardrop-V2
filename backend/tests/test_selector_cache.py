from datetime import datetime

import pytest

from app.models.price_history import SelectorCache
from app.services.selector_cache import (
    get_cached_selectors,
    record_cache_result,
    save_selectors,
    try_cached_extraction,
    url_to_pattern,
)


class TestUrlToPattern:
    def test_amazon_dp(self):
        url = "https://www.amazon.com.br/dp/B0ABCDEF12"
        assert url_to_pattern(url) == "amazon.com.br/dp/*"

    def test_amazon_gp_product(self):
        url = "https://amazon.com.br/gp/product/B0ABCDEF12"
        assert url_to_pattern(url) == "amazon.com.br/gp/product/*"

    def test_mercadolivre(self):
        url = "https://www.mercadolivre.com.br/MLB-123456789"
        assert url_to_pattern(url) == "mercadolivre.com.br/*"

    def test_magalu(self):
        url = "https://www.magazineluiza.com.br/produto/abc123def/"
        assert url_to_pattern(url) == "magazineluiza.com.br/produto/*"

    def test_strips_www(self):
        url = "https://www.example.com/products/123"
        assert url_to_pattern(url) == "example.com/products/*"


class TestTryCachedExtraction:
    def test_extracts_with_valid_selectors(self):
        html = """
        <html><body>
            <h1 id="title">iPhone 15</h1>
            <span class="price">R$ 4.299,00</span>
        </body></html>
        """
        selectors = {"name": "#title", "price": ".price"}
        result = try_cached_extraction(html, selectors)

        assert result is not None
        assert result.name == "iPhone 15"
        assert result.price == 4299

    def test_returns_none_when_name_not_found(self):
        html = "<html><body><span class='price'>100</span></body></html>"
        selectors = {"name": "#title", "price": ".price"}
        result = try_cached_extraction(html, selectors)
        assert result is None

    def test_returns_none_when_price_not_found(self):
        html = "<html><body><h1 id='title'>Product</h1></body></html>"
        selectors = {"name": "#title", "price": ".price"}
        result = try_cached_extraction(html, selectors)
        assert result is None

    def test_returns_none_when_no_selectors(self):
        result = try_cached_extraction("<html></html>", {})
        assert result is None

    def test_extracts_seller_and_image(self):
        html = """
        <html><body>
            <h1 id="title">Product</h1>
            <span class="price">99,90</span>
            <span class="seller">Loja ABC</span>
            <img class="main-img" src="https://example.com/img.jpg" />
        </body></html>
        """
        selectors = {
            "name": "#title",
            "price": ".price",
            "seller": ".seller",
            "image": ".main-img",
        }
        result = try_cached_extraction(html, selectors)

        assert result is not None
        assert result.seller == "Loja ABC"
        assert result.image_url == "https://example.com/img.jpg"


class TestSelectorCacheDB:
    def test_save_and_get_selectors(self, db):
        selectors = {"name": "#title", "price": ".price"}
        save_selectors(db, "https://amazon.com.br/dp/B0TEST", selectors)
        db.commit()

        result = get_cached_selectors(db, "https://amazon.com.br/dp/B0OTHER")
        assert result is not None
        assert result["name"] == "#title"

    def test_get_returns_none_when_not_cached(self, db):
        result = get_cached_selectors(db, "https://unknown.com/product/123")
        assert result is None

    def test_record_success(self, db):
        save_selectors(db, "https://example.com/product/1", {"name": "#t", "price": ".p"})
        db.commit()

        record_cache_result(db, "https://example.com/product/2", success=True)
        db.commit()

        entry = db.query(SelectorCache).filter_by(
            url_pattern="example.com/product/*"
        ).one()
        assert entry.success_count == 1
        assert entry.fail_count == 0

    def test_record_failure(self, db):
        save_selectors(db, "https://example.com/p/1", {"name": "#t", "price": ".p"})
        db.commit()

        record_cache_result(db, "https://example.com/p/2", success=False)
        db.commit()

        entry = db.query(SelectorCache).filter_by(
            url_pattern="example.com/p/*"
        ).one()
        assert entry.fail_count == 1

    def test_skips_cache_with_high_failure_rate(self, db):
        """Cache with >50% failure rate should be skipped."""
        entry = SelectorCache(
            url_pattern="failing.com/product/*",
            selectors={"name": "#t", "price": ".p"},
            success_count=1,
            fail_count=3,
            last_validated_at=datetime.utcnow(),
        )
        db.add(entry)
        db.commit()

        result = get_cached_selectors(db, "https://failing.com/product/123")
        assert result is None

    def test_update_existing_selectors(self, db):
        save_selectors(db, "https://example.com/item/1", {"name": "#old"})
        db.commit()

        save_selectors(db, "https://example.com/item/2", {"name": "#new", "price": ".p"})
        db.commit()

        result = get_cached_selectors(db, "https://example.com/item/3")
        assert result["name"] == "#new"
