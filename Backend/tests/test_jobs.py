"""
Tests for jobs and applications endpoints.
"""
import pytest


class TestJobsEndpoints:
    def test_list_jobs_unauthenticated(self, client):
        res = client.get("/api/jobs")
        assert res.status_code == 401

    def test_list_jobs_authenticated(self, client, auth_headers):
        res = client.get("/api/jobs", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert "jobs" in data
        assert isinstance(data["jobs"], list)

    def test_search_jobs(self, client, auth_headers):
        res = client.get("/api/jobs/search?q=software+engineer", headers=auth_headers)
        assert res.status_code == 200

    def test_get_job_not_found(self, client, auth_headers):
        res = client.get("/api/jobs/99999", headers=auth_headers)
        assert res.status_code == 404

    def test_get_saved_jobs(self, client, auth_headers):
        res = client.get("/api/jobs/saved", headers=auth_headers)
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    def test_save_nonexistent_job(self, client, auth_headers):
        res = client.post("/api/jobs/saved/99999", headers=auth_headers)
        assert res.status_code == 404


class TestApplicationsEndpoints:
    def test_list_applications_empty(self, client, auth_headers):
        res = client.get("/api/applications", headers=auth_headers)
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    def test_create_application_freeform(self, client, auth_headers):
        """Applications can be created without a job_id (manual tracking)."""
        res = client.post("/api/applications", json={
            "job_title": "Senior React Developer",
            "company": "TechCorp",
            "status": "applied",
            "notes": "Referral from John"
        }, headers=auth_headers)
        assert res.status_code in [200, 201]
        data = res.json()
        assert data["job_title"] == "Senior React Developer"
        assert data["company"] == "TechCorp"

    def test_create_application_missing_fields(self, client, auth_headers):
        res = client.post("/api/applications", json={
            "status": "applied"
        }, headers=auth_headers)
        assert res.status_code == 422

    def test_update_application_status(self, client, auth_headers):
        create_res = client.post("/api/applications", json={
            "job_title": "Backend Dev",
            "company": "StartupXYZ",
            "status": "applied"
        }, headers=auth_headers)
        if create_res.status_code in [200, 201]:
            app_id = create_res.json()["id"]
            update_res = client.put(f"/api/applications/{app_id}",
                                    json={"status": "interview"},
                                    headers=auth_headers)
            assert update_res.status_code == 200
            assert update_res.json()["status"] == "interview"

    def test_delete_application(self, client, auth_headers):
        create_res = client.post("/api/applications", json={
            "job_title": "DevOps Engineer",
            "company": "CloudCo",
            "status": "applied"
        }, headers=auth_headers)
        if create_res.status_code in [200, 201]:
            app_id = create_res.json()["id"]
            delete_res = client.delete(f"/api/applications/{app_id}", headers=auth_headers)
            assert delete_res.status_code in [200, 204]

    def test_list_applications_with_filter(self, client, auth_headers):
        res = client.get("/api/applications?status_filter=applied", headers=auth_headers)
        assert res.status_code == 200
