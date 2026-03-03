import pytest


class TestGetPreferences:
    def test_get_preferences(self, client, auth_headers, sample_user):
        response = client.get("/api/notifications/preferences", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["notify_email"] is True
        assert data["notify_push"] is True
        assert data["push_subscription"] is None

    def test_get_preferences_unauthenticated(self, client):
        response = client.get("/api/notifications/preferences")
        assert response.status_code == 401


class TestUpdatePreferences:
    def test_update_preferences(self, client, auth_headers):
        response = client.put(
            "/api/notifications/preferences",
            json={
                "notify_email": False,
                "notify_push": True,
                "push_subscription": {
                    "endpoint": "https://push.example.com/sub123",
                    "keys": {"p256dh": "key", "auth": "auth"},
                },
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["notify_email"] is False
        assert data["notify_push"] is True

    def test_update_preferences_partial(self, client, auth_headers):
        """Update only email/push without changing subscription."""
        response = client.put(
            "/api/notifications/preferences",
            json={
                "notify_email": False,
                "notify_push": False,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["notify_email"] is False
        assert data["notify_push"] is False

    def test_update_preferences_unauthenticated(self, client):
        response = client.put(
            "/api/notifications/preferences",
            json={"notify_email": False, "notify_push": False},
        )
        assert response.status_code == 401
