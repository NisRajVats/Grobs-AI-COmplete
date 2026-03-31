"""
Tests for resume endpoints.
"""
import io
import pytest


class TestResumeEndpoints:
    def test_list_resumes_empty(self, client, auth_headers):
        res = client.get("/api/resumes", headers=auth_headers)
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    def test_list_resumes_unauthenticated(self, client):
        res = client.get("/api/resumes")
        assert res.status_code == 401

    def test_create_resume(self, client, auth_headers):
        res = client.post("/api/resumes", json={
            "full_name": "John Doe",
            "email": "john@example.com",
            "title": "My Software Engineer Resume",
            "summary": "Software Engineer with 5 years of experience"
        }, headers=auth_headers)
        assert res.status_code in [200, 201]
        data = res.json()
        assert "id" in data

    def test_get_resume_not_found(self, client, auth_headers):
        res = client.get("/api/resumes/99999", headers=auth_headers)
        assert res.status_code == 404

    def test_upload_resume_pdf(self, client, auth_headers):
        # Create a minimal fake PDF-like file
        fake_pdf = io.BytesIO(b"%PDF-1.4 test resume content John Doe Software Engineer")
        fake_pdf.name = "test_resume.pdf"
        res = client.post(
            "/api/resumes/upload",
            files={"file": ("test_resume.pdf", fake_pdf, "application/pdf")},
            headers=auth_headers
        )
        assert res.status_code in [200, 201, 422]  # 422 acceptable if PDF parse fails

    def test_delete_resume_not_found(self, client, auth_headers):
        res = client.delete("/api/resumes/99999", headers=auth_headers)
        assert res.status_code == 404


class TestATSEndpoints:
    def test_ats_score_no_resume(self, client, auth_headers):
        res = client.post("/api/resumes/99999/ats-score",
                          json={"job_description": "Python developer needed"},
                          headers=auth_headers)
        assert res.status_code == 404

    def test_ats_check_no_resume(self, client, auth_headers):
        res = client.post("/api/resumes/99999/ats-check",
                          json={"job_description": "React developer"},
                          headers=auth_headers)
        assert res.status_code == 404

    def test_job_recommendations_no_resume(self, client, auth_headers):
        res = client.get("/api/resumes/99999/job-recommendations",
                         headers=auth_headers)
        assert res.status_code == 404

    def test_optimize_resume_no_resume(self, client, auth_headers):
        res = client.post("/api/resumes/99999/optimize",
                          json={"optimization_type": "comprehensive"},
                          headers=auth_headers)
        assert res.status_code == 404

    def test_process_pipeline_no_resume(self, client, auth_headers):
        res = client.post("/api/resumes/99999/process-pipeline",
                          headers=auth_headers)
        assert res.status_code == 404
