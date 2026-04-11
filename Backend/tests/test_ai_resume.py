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
    
    with patch("app.services.resume_service.ats_analyzer.llm_service.generate_structured_output_async", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_llm_result
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
    # Mock LLM failure
    with patch("app.services.resume_service.ats_analyzer.llm_service.generate_structured_output_async", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = None
        result = await calculate_ats_score(mock_resume, "Some job")
        
        # Should now return heuristic score instead of 0
        assert result["overall_score"] > 0
        assert result["status"] == "Partial"
        assert result["llm_powered"] is False
        assert "Advanced AI analysis currently unavailable" in result["issues"][-1] or "Advanced AI analysis currently unavailable" in "".join(result["issues"])
