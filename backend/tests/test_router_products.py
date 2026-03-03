import json
import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.product import Product, ProductGroup
from app.schemas.product import ParsedProduct


class TestParseProduct:
    @patch("app.routers.products.parse_product_html")
    def test_parse_new_product(self, mock_parse, client):
        mock_parse.return_value = ParsedProduct(
            name="Samsung Galaxy S24",
            price=Decimal("3499.00"),
            currency="BRL",
            seller="Samsung Oficial",
            image_url="https://example.com/s24.jpg",
            marketplace="amazon",
            available=True,
            ean="7891234567890",
        )

        response = client.post(
            "/api/products/parse",
            json={
                "html": "<div>Product page content</div>",
                "url": "https://www.amazon.com.br/dp/B0NEW12345",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Samsung Galaxy S24"
        assert data["current_price"] == "3499.00"
        assert data["marketplace"] == "amazon"
        assert data["url"] == "https://www.amazon.com.br/dp/B0NEW12345"

    @patch("app.routers.products.parse_product_html")
    def test_parse_existing_product_updates(self, mock_parse, client, sample_product):
        """Parsing a product that already exists should update it."""
        mock_parse.return_value = ParsedProduct(
            name="Produto Teste Atualizado",
            price=Decimal("149.90"),
            currency="BRL",
            marketplace="amazon",
        )

        response = client.post(
            "/api/products/parse",
            json={
                "html": "<div>Updated product</div>",
                "url": sample_product.url,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Produto Teste Atualizado"
        assert data["current_price"] == "149.90"
        assert data["id"] == str(sample_product.id)  # Same product


class TestGetProduct:
    def test_get_existing_product(self, client, sample_product):
        response = client.get(f"/api/products/{sample_product.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Produto Teste"
        assert data["marketplace"] == "amazon"

    def test_get_nonexistent_product(self, client):
        response = client.get("/api/products/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404


class TestGetProductHistory:
    def test_get_history_with_entries(self, client, sample_product, sample_price_history):
        response = client.get(f"/api/products/{sample_product.id}/history")
        assert response.status_code == 200
        data = response.json()
        assert data["product"]["id"] == str(sample_product.id)
        assert len(data["history"]) == 3
        # Should be ordered ascending
        prices = [h["price"] for h in data["history"]]
        assert prices == ["249.90", "229.90", "199.90"]

    def test_get_history_empty(self, client, sample_product):
        response = client.get(f"/api/products/{sample_product.id}/history")
        assert response.status_code == 200
        data = response.json()
        assert len(data["history"]) == 0

    def test_get_history_nonexistent_product(self, client):
        response = client.get(
            "/api/products/00000000-0000-0000-0000-000000000000/history"
        )
        assert response.status_code == 404


class TestTriggerSimilarityMatch:
    def test_match_nonexistent_product(self, client):
        response = client.post(
            "/api/products/00000000-0000-0000-0000-000000000000/match"
        )
        assert response.status_code == 404

    @patch("app.routers.products.match_product_by_similarity")
    def test_match_no_result(self, mock_match, client, sample_product):
        mock_match.return_value = None

        response = client.post(f"/api/products/{sample_product.id}/match")
        assert response.status_code == 200
        assert response.json() is None

    @patch("app.routers.products.match_product_by_similarity")
    def test_match_success(self, mock_match, client, db, sample_product):
        # Create a candidate and a group
        group = ProductGroup(canonical_name="Test Group")
        db.add(group)
        db.flush()

        candidate = Product(
            url="https://mercadolivre.com.br/MLB-123",
            marketplace="mercadolivre",
            name="Produto Teste ML",
            group_id=group.id,
        )
        db.add(candidate)
        db.flush()

        # Mock match_product_by_similarity to assign the group
        def side_effect(db_session, product):
            product.group_id = group.id
            return group

        mock_match.side_effect = side_effect

        response = client.post(f"/api/products/{sample_product.id}/match")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(group.id)
        assert data["canonical_name"] == "Test Group"
        assert len(data["products"]) >= 1
