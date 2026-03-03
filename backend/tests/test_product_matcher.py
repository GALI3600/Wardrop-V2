import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from app.models.product import Product, ProductGroup
from app.services.product_matcher import match_product_by_ean, trigger_reverse_similarity


class TestMatchProductByEAN:
    def test_no_match_without_ean(self, db, sample_product):
        """Products without EAN should not be matched."""
        sample_product.ean = None
        db.commit()

        result = match_product_by_ean(db, sample_product)
        assert result is None
        assert sample_product.group_id is None

    def test_creates_group_for_first_product_with_ean(self, db, sample_product):
        """First product with a given EAN should get a new group."""
        sample_product.ean = "7891234567890"
        db.commit()

        result = match_product_by_ean(db, sample_product)

        assert result is not None
        assert result.ean == "7891234567890"
        assert result.canonical_name == sample_product.name
        assert sample_product.group_id == result.id

    def test_matches_to_existing_group(self, db):
        """Second product with same EAN should join the existing group."""
        # Create a group
        group = ProductGroup(canonical_name="iPhone 15", ean="7891234567890")
        db.add(group)
        db.flush()

        # Create first product in group
        p1 = Product(
            url="https://amazon.com.br/dp/B0FIRST",
            marketplace="amazon",
            name="iPhone 15 128GB",
            ean="7891234567890",
            group_id=group.id,
        )
        db.add(p1)
        db.flush()

        # Create second product with same EAN
        p2 = Product(
            url="https://magazineluiza.com.br/produto/iphone15",
            marketplace="magalu",
            name="Apple iPhone 15 128 GB",
            ean="7891234567890",
        )
        db.add(p2)
        db.flush()

        result = match_product_by_ean(db, p2)

        assert result is not None
        assert result.id == group.id
        assert p2.group_id == group.id

    def test_links_two_ungrouped_products(self, db):
        """If two products have same EAN but no group, create one for both."""
        p1 = Product(
            url="https://amazon.com.br/dp/B0AAAA",
            marketplace="amazon",
            name="Samsung Galaxy S24",
            ean="1111111111111",
        )
        db.add(p1)
        db.flush()

        p2 = Product(
            url="https://mercadolivre.com.br/MLB-999",
            marketplace="mercadolivre",
            name="Galaxy S24 Samsung",
            ean="1111111111111",
        )
        db.add(p2)
        db.flush()

        result = match_product_by_ean(db, p2)

        assert result is not None
        assert p1.group_id == result.id
        assert p2.group_id == result.id
        assert result.ean == "1111111111111"

    def test_different_ean_creates_separate_groups(self, db):
        """Products with different EANs should be in separate groups."""
        p1 = Product(
            url="https://amazon.com.br/dp/B0PROD1",
            marketplace="amazon",
            name="Product A",
            ean="1111111111111",
        )
        p2 = Product(
            url="https://amazon.com.br/dp/B0PROD2",
            marketplace="amazon",
            name="Product B",
            ean="2222222222222",
        )
        db.add_all([p1, p2])
        db.flush()

        group1 = match_product_by_ean(db, p1)
        group2 = match_product_by_ean(db, p2)

        assert group1.id != group2.id
        assert p1.group_id != p2.group_id

    def test_third_product_joins_existing_group(self, db):
        """Third marketplace product should join the existing group."""
        # Setup: two products already grouped
        group = ProductGroup(canonical_name="Product X", ean="9999999999999")
        db.add(group)
        db.flush()

        p1 = Product(
            url="https://amazon.com.br/dp/B0X1",
            marketplace="amazon",
            ean="9999999999999",
            group_id=group.id,
        )
        p2 = Product(
            url="https://magalu.com.br/produto/x",
            marketplace="magalu",
            ean="9999999999999",
            group_id=group.id,
        )
        db.add_all([p1, p2])
        db.flush()

        # Third product arrives
        p3 = Product(
            url="https://mercadolivre.com.br/MLB-X",
            marketplace="mercadolivre",
            name="Product X",
            ean="9999999999999",
        )
        db.add(p3)
        db.flush()

        result = match_product_by_ean(db, p3)

        assert result.id == group.id
        assert p3.group_id == group.id
        # All three products should point to the same group
        db.commit()
        products_in_group = db.query(Product).filter_by(group_id=group.id).all()
        assert len(products_in_group) == 3


class TestTriggerReverseSimilarity:
    def test_triggers_for_similar_orphan(self, db):
        """Orphan with similar name from different marketplace should be scheduled."""
        product = Product(
            url="https://amazon.com.br/dp/B0RE",
            marketplace="amazon",
            name="Resident Evil Requiem PS5",
        )
        orphan = Product(
            url="https://kabum.com.br/produto/123",
            marketplace="kabum",
            name="Resident Evil Requiem PS5",
            ean=None,
            group_id=None,
        )
        db.add_all([product, orphan])
        db.flush()

        with patch("app.services.product_matcher.asyncio.create_task") as mock_create_task:
            trigger_reverse_similarity(db, product)
            mock_create_task.assert_called_once()
            # Verify it was called with a coroutine for the orphan
            coro = mock_create_task.call_args[0][0]
            coro.close()  # clean up unawaited coroutine

    def test_skips_orphan_same_marketplace(self, db):
        """Orphan from same marketplace should not be triggered."""
        product = Product(
            url="https://amazon.com.br/dp/B0RE",
            marketplace="amazon",
            name="Resident Evil Requiem PS5",
        )
        same_mp_orphan = Product(
            url="https://amazon.com.br/dp/B0RE2",
            marketplace="amazon",
            name="Resident Evil Requiem PS5",
            ean=None,
            group_id=None,
        )
        db.add_all([product, same_mp_orphan])
        db.flush()

        with patch("app.services.product_matcher.asyncio.create_task") as mock_create_task:
            trigger_reverse_similarity(db, product)
            mock_create_task.assert_not_called()

    def test_skips_orphan_with_ean(self, db):
        """Orphan that has an EAN should not be triggered (it went through EAN matching)."""
        product = Product(
            url="https://amazon.com.br/dp/B0RE",
            marketplace="amazon",
            name="Resident Evil Requiem PS5",
        )
        orphan_with_ean = Product(
            url="https://kabum.com.br/produto/123",
            marketplace="kabum",
            name="Resident Evil Requiem PS5",
            ean="5901234123457",
            group_id=None,
        )
        db.add_all([product, orphan_with_ean])
        db.flush()

        with patch("app.services.product_matcher.asyncio.create_task") as mock_create_task:
            trigger_reverse_similarity(db, product)
            mock_create_task.assert_not_called()

    def test_skips_orphan_already_grouped(self, db):
        """Products already in a group should not be triggered."""
        group = ProductGroup(canonical_name="Existing Group")
        db.add(group)
        db.flush()

        product = Product(
            url="https://amazon.com.br/dp/B0RE",
            marketplace="amazon",
            name="Resident Evil Requiem PS5",
        )
        grouped_product = Product(
            url="https://kabum.com.br/produto/123",
            marketplace="kabum",
            name="Resident Evil Requiem PS5",
            ean=None,
            group_id=group.id,
        )
        db.add_all([product, grouped_product])
        db.flush()

        with patch("app.services.product_matcher.asyncio.create_task") as mock_create_task:
            trigger_reverse_similarity(db, product)
            mock_create_task.assert_not_called()

    def test_no_crash_when_product_has_no_name(self, db):
        """Should return early when the product has no name."""
        product = Product(
            url="https://amazon.com.br/dp/B0RE",
            marketplace="amazon",
            name=None,
        )
        db.add(product)
        db.flush()

        # Should not raise
        trigger_reverse_similarity(db, product)
