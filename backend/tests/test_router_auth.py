import pytest


class TestRegister:
    def test_register_success(self, client):
        response = client.post(
            "/api/auth/register",
            json={"email": "new@example.com", "password": "strongpassword"},
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_register_duplicate_email(self, client, sample_user):
        response = client.post(
            "/api/auth/register",
            json={"email": "test@example.com", "password": "password123"},
        )
        assert response.status_code == 409
        assert "already registered" in response.json()["detail"]

    def test_register_invalid_email(self, client):
        response = client.post(
            "/api/auth/register",
            json={"email": "not-an-email", "password": "password123"},
        )
        assert response.status_code == 422


class TestLogin:
    def test_login_success(self, client, sample_user):
        response = client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    def test_login_wrong_password(self, client, sample_user):
        response = client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "wrong"},
        )
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        response = client.post(
            "/api/auth/login",
            json={"email": "nobody@example.com", "password": "password123"},
        )
        assert response.status_code == 401


class TestGetMe:
    def test_get_me_authenticated(self, client, sample_user, auth_headers):
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["id"] == str(sample_user.id)

    def test_get_me_unauthenticated(self, client):
        response = client.get("/api/auth/me")
        assert response.status_code == 401

    def test_get_me_invalid_token(self, client):
        response = client.get(
            "/api/auth/me", headers={"Authorization": "Bearer invalid"}
        )
        assert response.status_code == 401
