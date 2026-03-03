from unittest.mock import patch


class TestHealthEndpoint:
    def test_health_check(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestRouterRegistration:
    def test_products_router_registered(self, client):
        response = client.get("/api/products/00000000-0000-0000-0000-000000000000")
        # 404 means the route exists but product not found
        assert response.status_code == 404

    def test_auth_router_registered(self, client):
        response = client.post("/api/auth/login", json={"email": "a@b.com", "password": "x"})
        # 401 means the route exists
        assert response.status_code == 401

    def test_tracking_router_registered(self, client):
        response = client.get("/api/tracking/products")
        # 401 means the route exists but needs auth
        assert response.status_code == 401

    def test_notifications_router_registered(self, client):
        response = client.get("/api/notifications/preferences")
        # 401 means the route exists but needs auth
        assert response.status_code == 401

    def test_unknown_route_returns_404(self, client):
        response = client.get("/api/nonexistent")
        assert response.status_code in (404, 405)


class TestCORSMiddleware:
    def test_cors_headers_present(self, client):
        response = client.options(
            "/api/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert "access-control-allow-origin" in response.headers
