"""
Tests for authentication endpoints.
"""
import pytest


class TestRegister:
    def test_register_success(self, client):
        res = client.post("/api/auth/register", json={
            "email": "new@example.com",
            "password": "StrongPass123!"
        })
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_register_duplicate_email(self, client):
        payload = {"email": "dup@example.com", "password": "StrongPass123!"}
        client.post("/api/auth/register", json=payload)
        res = client.post("/api/auth/register", json=payload)
        assert res.status_code == 400

    def test_register_invalid_email(self, client):
        res = client.post("/api/auth/register", json={
            "email": "not-an-email",
            "password": "StrongPass123!"
        })
        assert res.status_code == 422


class TestLogin:
    def test_login_success(self, client):
        client.post("/api/auth/register", json={
            "email": "login@example.com",
            "password": "StrongPass123!"
        })
        res = client.post("/api/auth/token", data={
            "username": "login@example.com",
            "password": "StrongPass123!"
        })
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_login_wrong_password(self, client):
        client.post("/api/auth/register", json={
            "email": "wrong@example.com",
            "password": "StrongPass123!"
        })
        res = client.post("/api/auth/token", data={
            "username": "wrong@example.com",
            "password": "WrongPassword!"
        })
        assert res.status_code == 401

    def test_login_nonexistent_user(self, client):
        res = client.post("/api/auth/token", data={
            "username": "nobody@example.com",
            "password": "anypassword"
        })
        assert res.status_code == 401


class TestProtectedRoutes:
    def test_get_me_authenticated(self, client, auth_headers):
        res = client.get("/api/auth/me", headers=auth_headers)
        assert res.status_code == 200
        assert "email" in res.json()

    def test_get_me_unauthenticated(self, client):
        res = client.get("/api/auth/me")
        assert res.status_code == 401

    def test_get_me_invalid_token(self, client):
        res = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
        assert res.status_code == 401

    def test_logout(self, client, auth_headers):
        # Get refresh token first
        login_res = client.post("/api/auth/token", data={
            "username": "testuser@example.com",
            "password": "TestPassword123!"
        })
        refresh_token = login_res.json().get("refresh_token", "")
        res = client.post("/api/auth/logout",
                          json={"refresh_token": refresh_token},
                          headers=auth_headers)
        assert res.status_code in [200, 204]
