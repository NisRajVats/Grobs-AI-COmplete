"""
Tests for analytics endpoints.
"""
import pytest


class TestAnalytics:
    def test_get_analytics_unauthenticated(self, client):
        res = client.get("/api/analytics/user")
        assert res.status_code == 401

    def test_get_analytics_default_range(self, client, auth_headers):
        res = client.get("/api/analytics/user", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert "keyMetrics" in data
        assert "totalApplications" in data["keyMetrics"]
        assert "avgResumeScore" in data["keyMetrics"]

    def test_get_analytics_7d(self, client, auth_headers):
        res = client.get("/api/analytics/user?time_range=7d", headers=auth_headers)
        assert res.status_code == 200

    def test_get_analytics_90d(self, client, auth_headers):
        res = client.get("/api/analytics/user?time_range=90d", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert "applicationTrend" in data["keyMetrics"]
