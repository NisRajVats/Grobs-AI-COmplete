"""
Tests for AI Resume Analysis logic.
"""
import pytest
from unittest.mock import MagicMock, patch
from app.models import Resume, Skill, Education, Experience, Project
from app.services.resume_service.ats_analyzer import calculate_ats_score

@pytest.fixture
def anyio_backend():
    return 'asyncio'

@pytest.fixture
def mock_resume():
    resume = MagicMock(spec=Resume)
    resume.id = 1
    resume.full_name = "John Doe"
    resume.email = "john@example.com"
    resume.phone = "1234567890"
    resume.linkedin_url = "https://linkedin.com/in/johndoe"
    resume.title = "Software Engineer"
    resume.target_role = "Senior Software Engineer"
    resume.summary = "Experienced engineer"
    
    # Mock relationships
    resume.education = [
        MagicMock(spec=Education, school="University A", degree="B.S.", major="CS", start_date="2010", end_date="2014")
    ]
    resume.experience = [
        MagicMock(spec=Experience, company="Company X", role="Dev", start_date="2015", end_date="2020", description="Built stuff")
    ]
    resume.projects = [
        MagicMock(spec=Project, project_name="Project Y", description="Did things")
    ]
    
    skill1 = MagicMock(spec=Skill)
    skill1.name = "Python"
    skill2 = MagicMock(spec=Skill)
    skill2.name = "FastAPI"
    resume.skills = [skill1, skill2]
    
    return resume

@pytest.mark.anyio
async def test_calculate_ats_score_success(mock_resume):
    # Mock LLM response
    mock_llm_result = {
        "overall_score": 85,
        "keyword_optimization_score": 80,
        "semantic_relevance_score": 90,
        "industry_alignment_score": 85,
        "formatting_score": 95,
        "structure_score": 90,
        "readability_score": 88,
        "contact_info_score": 100,
        "issues": ["Add more metrics"],
        "recommendations": ["Quantify achievements"],
        "skill_analysis": {
            "hard_skills": ["Python", "FastAPI"],
            "soft_skills": ["Leadership"],
            "tools": ["Docker"]
        },
        "keyword_gap": {
            "matched": ["Python"],
            "missing": ["Kubernetes"],
            "optional": ["AWS"]
        },
        "industry_tips": ["Focus on cloud skills"]
    }
    
    with patch("app.services.llm_service.llm_service.generate_structured_output_async", return_value=mock_llm_result):
        result = await calculate_ats_score(mock_resume, "Looking for a Python dev with Kubernetes")
        
        # Heuristics + LLM weightage (30/70)
        assert 70 <= result["overall_score"] <= 90
        assert result["status"] == "Complete"
        assert result["llm_powered"] is True
        assert "keyword_optimization" in result["category_scores"]
        assert result["category_scores"]["keyword_optimization"] > 0
        assert result["skill_analysis"]["hard_skills"] == ["Python", "FastAPI"]
        assert result["keyword_gap"]["missing"] == ["kubernetes"]

@pytest.mark.anyio
async def test_calculate_ats_score_failure(mock_resume):
    # Mock LLM failure
    with patch("app.services.llm_service.llm_service.generate_structured_output_async", return_value=None):
        result = await calculate_ats_score(mock_resume, "Some job")
        
        # Should now return heuristic score instead of 0
        assert result["overall_score"] > 0
        assert result["status"] == "Partial"
        assert result["llm_powered"] is False
        assert "Advanced AI analysis currently unavailable" in result["issues"][-1]
