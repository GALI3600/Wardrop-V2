import uuid
from datetime import datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.models.price_history import PriceHistory
from app.models.product import Product, ProductGroup


class TestListProductGroups:
    def test_returns_groups_with_multiple_products(self, client: TestClient, db):
        group = ProductGroup(canonical_name="iPhone 15", ean="7891234567890")
        db.add(group)
        db.flush()

        p1 = Product(
            url="https://amazon.com.br/dp/B0TEST1",
            marketplace="amazon",
            name="iPhone 15 128GB",
            current_price=Decimal("4299.00"),
            ean="7891234567890",
            group_id=group.id,
        )
        p2 = Product(
            url="https://magalu.com.br/produto/iphone15",
            marketplace="magalu",
            name="Apple iPhone 15",
            current_price=Decimal("4199.00"),
            ean="7891234567890",
            group_id=group.id,
        )
        db.add_all([p1, p2])
        db.commit()

        response = client.get("/api/products/groups/list")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["canonical_name"] == "iPhone 15"
        assert len(data[0]["products"]) == 2

    def test_excludes_single_product_groups(self, client: TestClient, db):
        """Groups with only 1 product should not appear in comparison."""
        group = ProductGroup(canonical_name="Solo Product", ean="1111111111111")
        db.add(group)
        db.flush()

        p = Product(
            url="https://amazon.com.br/dp/B0SOLO",
            marketplace="amazon",
            name="Solo Product",
            group_id=group.id,
        )
        db.add(p)
        db.commit()

        response = client.get("/api/products/groups/list")
        assert response.status_code == 200
        assert len(response.json()) == 0

    def test_returns_empty_when_no_groups(self, client: TestClient):
        response = client.get("/api/products/groups/list")
        assert response.status_code == 200
        assert response.json() == []


class TestCompareGroup:
    def test_returns_comparison_data(self, client: TestClient, db):
        group = ProductGroup(canonical_name="Galaxy S24", ean="2222222222222")
        db.add(group)
        db.flush()

        p1 = Product(
            url="https://amazon.com.br/dp/B0GALAXY",
            marketplace="amazon",
            name="Samsung Galaxy S24",
            current_price=Decimal("3499.00"),
            ean="2222222222222",
            group_id=group.id,
        )
        p2 = Product(
            url="https://magalu.com.br/produto/galaxy-s24",
            marketplace="magalu",
            name="Galaxy S24 Samsung",
            current_price=Decimal("3399.00"),
            ean="2222222222222",
            group_id=group.id,
        )
        db.add_all([p1, p2])
        db.flush()

        # Add price history
        now = datetime.utcnow()
        db.add(PriceHistory(product_id=p1.id, price=Decimal("3599.00"), scraped_at=now))
        db.add(PriceHistory(product_id=p1.id, price=Decimal("3499.00"), scraped_at=now))
        db.add(PriceHistory(product_id=p2.id, price=Decimal("3399.00"), scraped_at=now))
        db.commit()

        response = client.get(f"/api/products/groups/{group.id}/compare")
        assert response.status_code == 200

        data = response.json()
        assert data["group"]["canonical_name"] == "Galaxy S24"
        assert len(data["group"]["products"]) == 2
        assert "amazon" in data["price_histories"]
        assert "magalu" in data["price_histories"]
        assert len(data["price_histories"]["amazon"]) == 2
        assert len(data["price_histories"]["magalu"]) == 1

    def test_returns_404_for_nonexistent_group(self, client: TestClient):
        fake_id = uuid.uuid4()
        response = client.get(f"/api/products/groups/{fake_id}/compare")
        assert response.status_code == 404
