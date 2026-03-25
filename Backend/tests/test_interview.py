"""
Tests for interview endpoints.
"""
import pytest


class TestInterviewSessions:
    def test_create_session(self, client, auth_headers):
        res = client.post("/api/interview/sessions", json={
            "job_title": "Software Engineer",
            "company": "TestCorp",
            "interview_type": "technical",
            "difficulty": "medium"
        }, headers=auth_headers)
        assert res.status_code in [200, 201]
        data = res.json()
        assert "id" in data

    def test_list_sessions(self, client, auth_headers):
        res = client.get("/api/interview/sessions", headers=auth_headers)
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    def test_get_session_not_found(self, client, auth_headers):
        res = client.get("/api/interview/sessions/99999", headers=auth_headers)
        assert res.status_code == 404

    def test_delete_session_not_found(self, client, auth_headers):
        res = client.delete("/api/interview/sessions/99999", headers=auth_headers)
        assert res.status_code == 404

    def test_generate_questions(self, client, auth_headers):
        res = client.post("/api/interview/questions", json={
            "job_title": "Frontend Developer",
            "skills": ["React", "JavaScript", "CSS"],
            "difficulty": "medium",
            "count": 3
        }, headers=auth_headers)
        assert res.status_code in [200, 201]

    def test_sessions_require_auth(self, client):
        res = client.get("/api/interview/sessions")
        assert res.status_code == 401
