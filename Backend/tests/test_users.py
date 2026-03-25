"""
Tests for user profile and dashboard endpoints.
"""
import pytest


class TestUserProfile:
    def test_get_profile(self, client, auth_headers):
        res = client.get("/api/users/me", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert "email" in data
        assert "id" in data

    def test_get_profile_unauthenticated(self, client):
        res = client.get("/api/users/me")
        assert res.status_code == 401

    def test_update_profile(self, client, auth_headers):
        res = client.put("/api/users/me", json={
            "full_name": "Jane Developer",
            "phone": "+1 555 000 1234",
            "location": "Austin, TX",
            "title": "Full Stack Developer"
        }, headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert data["full_name"] == "Jane Developer"
        assert data["title"] == "Full Stack Developer"

    def test_update_profile_partial(self, client, auth_headers):
        res = client.put("/api/users/me", json={
            "location": "Seattle, WA"
        }, headers=auth_headers)
        assert res.status_code == 200

    def test_get_dashboard_stats(self, client, auth_headers):
        res = client.get("/api/users/me/dashboard-stats", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert "total_resumes" in data
        assert "total_applications" in data


class TestNotifications:
    def test_list_notifications(self, client, auth_headers):
        res = client.get("/api/notifications", headers=auth_headers)
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    def test_unread_count(self, client, auth_headers):
        res = client.get("/api/notifications/unread-count", headers=auth_headers)
        assert res.status_code == 200
        assert "count" in res.json()

    def test_mark_all_read(self, client, auth_headers):
        res = client.put("/api/notifications/read-all", headers=auth_headers)
        assert res.status_code in [200, 204]
