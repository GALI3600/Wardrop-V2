import uuid
from datetime import datetime
from decimal import Decimal

import pytest

from app.models.price_history import PriceHistory, SelectorCache, UserProduct
from app.models.product import Product, ProductGroup
from app.models.user import User


class TestUserModel:
    def test_create_user(self, db):
        user = User(
            email="model_test@example.com",
            password_hash="hashed",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        assert user.id is not None
        assert user.email == "model_test@example.com"
        assert user.notify_email is True  # default
        assert user.notify_push is True  # default
        assert user.push_subscription is None
        assert user.created_at is not None

    def test_email_uniqueness(self, db):
        user1 = User(email="unique@example.com", password_hash="hash1")
        db.add(user1)
        db.commit()

        user2 = User(email="unique@example.com", password_hash="hash2")
        db.add(user2)
        with pytest.raises(Exception):  # IntegrityError
            db.commit()


class TestProductModel:
    def test_create_product(self, db):
        product = Product(
            url="https://amazon.com.br/dp/B0MODEL123",
            marketplace="amazon",
            name="Test Product",
            current_price=Decimal("99.90"),
            currency="BRL",
        )
        db.add(product)
        db.commit()
        db.refresh(product)

        assert product.id is not None
        assert product.url == "https://amazon.com.br/dp/B0MODEL123"
        assert product.currency == "BRL"

    def test_url_uniqueness(self, db):
        p1 = Product(url="https://same-url.com", marketplace="test")
        db.add(p1)
        db.commit()

        p2 = Product(url="https://same-url.com", marketplace="test2")
        db.add(p2)
        with pytest.raises(Exception):
            db.commit()

    def test_product_group_relationship(self, db):
        group = ProductGroup(canonical_name="iPhone 15", ean="1234567890")
        db.add(group)
        db.commit()

        product = Product(
            url="https://example.com/p1",
            marketplace="amazon",
            group_id=group.id,
        )
        db.add(product)
        db.commit()
        db.refresh(product)

        assert product.group is not None
        assert product.group.canonical_name == "iPhone 15"
        assert len(group.products) == 1


class TestPriceHistoryModel:
    def test_create_price_history(self, db, sample_product):
        entry = PriceHistory(
            product_id=sample_product.id,
            price=Decimal("199.90"),
            seller="Test Seller",
            available=True,
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)

        assert entry.id is not None
        assert entry.price == Decimal("199.90")
        assert entry.available is True
        assert entry.scraped_at is not None

    def test_cascade_delete(self, db, sample_product, sample_price_history):
        """Deleting product should delete its price history."""
        product_id = sample_product.id
        db.delete(sample_product)
        db.commit()

        remaining = db.query(PriceHistory).filter_by(product_id=product_id).all()
        assert len(remaining) == 0


class TestUserProductModel:
    def test_create_tracking(self, db, sample_user, sample_product):
        up = UserProduct(
            user_id=sample_user.id,
            product_id=sample_product.id,
            target_price=Decimal("100.00"),
            notify_on_any_drop=True,
        )
        db.add(up)
        db.commit()

        assert up.user_id == sample_user.id
        assert up.product_id == sample_product.id
        assert up.target_price == Decimal("100.00")

    def test_cascade_delete_user(self, db, tracked_product, sample_user, sample_product):
        """Deleting user should delete tracking entries."""
        db.delete(sample_user)
        db.commit()

        remaining = db.query(UserProduct).filter_by(product_id=sample_product.id).all()
        assert len(remaining) == 0


class TestSelectorCacheModel:
    def test_create_cache(self, db):
        cache = SelectorCache(
            url_pattern="amazon.com.br/dp/*",
            selectors={"name": "#productTitle", "price": ".a-price-whole"},
        )
        db.add(cache)
        db.commit()
        db.refresh(cache)

        assert cache.id is not None
        assert cache.success_count == 0
        assert cache.fail_count == 0
        assert "name" in cache.selectors
