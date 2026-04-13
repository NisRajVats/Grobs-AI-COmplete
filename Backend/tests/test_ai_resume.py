"""
Tests for AI Resume Analysis logic.
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from app.models import Resume, Skill, Education, Experience, Project
from app.services.resume_service.ats_analyzer import calculate_ats_score

@pytest.fixture
def anyio_backend():
    return 'asyncio'

@pytest.fixture
def mock_resume():
    resume = MagicMock(spec=Resume)
    resume.id = 1
    resume.content = None  # Ensure we don't use raw_text mock
    resume.full_name = "John Doe"
    resume.email = "john@example.com"
    resume.phone = "1234567890"
    resume.linkedin_url = "https://linkedin.com/in/johndoe"
    resume.title = "Software Engineer"
    resume.target_role = "Senior Software Engineer"
    resume.summary = "Experienced engineer"
    
    # Mock relationships
    resume.education = [
        MagicMock(spec=Education, school="Stanford University", degree="B.S.", major="Computer Science", start_date="2010", end_date="2014")
    ]
    resume.experience = [
        MagicMock(spec=Experience, company="Google", role="Senior Software Engineer", start_date="2015", end_date="2023", 
                  description="Led development of high-scale systems. Managed 10+ engineers. Reduced latency by 40% and saved $2M annually. Spearheaded cloud migration.",
                  current=True)
    ]
    resume.projects = [
        MagicMock(spec=Project, project_name="E-commerce Platform", description="Built a full-stack platform serving 1M users.", technologies="Python, FastAPI, React, Docker")
    ]
    
    skill_names = ["Python", "FastAPI", "Docker", "Kubernetes", "AWS", "SQL", "Git", "React", "Linux", "CI/CD", 
                   "Leadership", "Communication", "Agile", "System Design", "Microservices"]
    
    def create_mock_skill(name):
        s = MagicMock(spec=Skill)
        s.name = name
        return s
        
    resume.skills = [create_mock_skill(name) for name in skill_names]
    
    return resume

@pytest.mark.anyio
async def test_calculate_ats_score_success(mock_resume):
    # Mock analysis result
    mock_result = {
        "overall_score": 85,
        "confidence": 0.9,
        "analysis_time_ms": 100,
        "job_description": "Looking for a Python dev with Kubernetes",
        "analysis_timestamp": "2026-04-13T12:00:00Z",
        "components": {
            "keyword_match": 80,
            "experience": 90,
            "skills_coverage": 85
        },
        "skill_analysis": {
            "matched_skills": ["Python", "FastAPI", "Kubernetes"],
            "missing_skills": ["Docker"],
            "hard_skills": ["Python", "FastAPI"],
            "soft_skills": ["Leadership"],
            "tools": ["Docker"]
        },
        "recommendations": ["Quantify achievements"],
        "parsing_result": {"method": "ensemble", "confidence": 0.95, "data": {}}
    }
    
    with patch("app.services.resume_service.ats_analyzer.EnhancedATSAnalyzer.analyze_resume", new_callable=AsyncMock) as mock_analyze:
        mock_analyze.return_value = mock_result
        result = await calculate_ats_score(mock_resume, "Looking for a Python dev with Kubernetes")
        
        assert 70 <= result["overall_score"] <= 95
        assert result["status"] == "Complete"
        assert result["llm_powered"] is True
        assert "keyword_match" in result["category_scores"]
        assert result["category_scores"]["keyword_match"] > 0
        assert "Python" in result["skill_analysis"]["hard_skills"]
        assert "FastAPI" in result["skill_analysis"]["hard_skills"]
        assert "kubernetes" in [m.lower() for m in result["keyword_gap"]["matched"]]

@pytest.mark.anyio
async def test_calculate_ats_score_failure(mock_resume):
    # Mock analysis failure (heuristic fallback)
    mock_result = {
        "overall_score": 30,
        "confidence": 0.6,
        "analysis_time_ms": 50,
        "job_description": "Some job",
        "analysis_timestamp": "2026-04-13T12:00:00Z",
        "components": {"keyword_match": 30},
        "skill_analysis": {"matched_skills": [], "missing_skills": []},
        "recommendations": [],
        "parsing_result": {"method": "heuristic", "confidence": 0.6, "data": {}}
    }
    
    with patch("app.services.resume_service.ats_analyzer.EnhancedATSAnalyzer.analyze_resume", new_callable=AsyncMock) as mock_analyze:
        mock_analyze.return_value = mock_result
        result = await calculate_ats_score(mock_resume, "Some job", provider="heuristic")
        
        # Should now return heuristic score instead of 0
        assert result["overall_score"] > 0
        assert result["status"] == "Partial"
        assert result["llm_powered"] is False
        assert "Advanced AI analysis currently unavailable" in result["issues"][-1] or "Advanced AI analysis currently unavailable" in "".join(result["issues"])
