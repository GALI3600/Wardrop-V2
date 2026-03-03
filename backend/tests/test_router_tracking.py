import pytest


class TestTrackProduct:
    def test_track_product_success(self, client, auth_headers, sample_product):
        response = client.post(
            "/api/tracking/track",
            json={
                "product_id": str(sample_product.id),
                "target_price": 100.00,
                "notify_on_any_drop": True,
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        assert response.json()["status"] == "tracking"

    def test_track_product_updates_existing(self, client, auth_headers, tracked_product, sample_product):
        """Tracking an already tracked product should update target_price."""
        response = client.post(
            "/api/tracking/track",
            json={
                "product_id": str(sample_product.id),
                "target_price": 50.00,
                "notify_on_any_drop": False,
            },
            headers=auth_headers,
        )
        assert response.status_code == 201

    def test_track_nonexistent_product(self, client, auth_headers):
        response = client.post(
            "/api/tracking/track",
            json={
                "product_id": "00000000-0000-0000-0000-000000000000",
                "notify_on_any_drop": True,
            },
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_track_unauthenticated(self, client, sample_product):
        response = client.post(
            "/api/tracking/track",
            json={
                "product_id": str(sample_product.id),
                "notify_on_any_drop": True,
            },
        )
        assert response.status_code == 401


class TestUntrackProduct:
    def test_untrack_success(self, client, auth_headers, tracked_product, sample_product):
        response = client.delete(
            f"/api/tracking/untrack/{sample_product.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "untracked"

    def test_untrack_not_tracking(self, client, auth_headers, sample_product):
        response = client.delete(
            f"/api/tracking/untrack/{sample_product.id}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_untrack_unauthenticated(self, client, sample_product):
        response = client.delete(f"/api/tracking/untrack/{sample_product.id}")
        assert response.status_code == 401


class TestGetTrackedProducts:
    def test_get_tracked_products(self, client, auth_headers, tracked_product, sample_product):
        response = client.get("/api/tracking/products", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == str(sample_product.id)
        assert data[0]["name"] == "Produto Teste"

    def test_get_tracked_products_empty(self, client, auth_headers):
        response = client.get("/api/tracking/products", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_get_tracked_products_unauthenticated(self, client):
        response = client.get("/api/tracking/products")
        assert response.status_code == 401
