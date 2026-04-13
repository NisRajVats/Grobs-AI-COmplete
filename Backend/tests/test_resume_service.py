"""
Comprehensive tests for resume service - parser, analyzer, optimizer, and manager.
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from app.services.resume_service.parser import (
    extract_text_from_file,
    clean_text,
    extract_email,
    extract_phone,
    extract_linkedin,
    extract_github,
    extract_portfolio,
    extract_name,
    extract_title,
    extract_sections,
    extract_education_details,
    extract_experience_details,
    extract_project_details,
    extract_skills,
    extract_skills_from_text as parser_extract_skills,
    parse_resume_with_llm,
)
from app.services.resume_service.matcher import (
    match_skills,
    extract_skills_from_text as matcher_extract_skills,
)
from app.services.resume_service.ats_analyzer import (
    calculate_ats_score,
    _parse_jd_requirements,
    _split_jd_sections,
    _normalise_skill,
    _match_skills,
)
from app.models import Resume, Skill, Education, Experience, Project


# ==================== Parser Tests ====================

class TestTextExtraction:
    """Tests for text extraction from various file formats."""
    
    def test_clean_text_removes_extra_whitespace(self):
        text = "Hello    World\n\n\nTest"
        cleaned = clean_text(text)
        assert "  " not in cleaned
        assert "\n\n\n" not in cleaned
    
    def test_clean_text_handles_none(self):
        cleaned = clean_text(None)
        assert cleaned == ""
    
    def test_clean_text_handles_empty_string(self):
        cleaned = clean_text("")
        assert cleaned == ""


class TestContactExtraction:
    """Tests for extracting contact information from text."""
    
    def test_extract_email_valid(self):
        text = "Contact me at john.doe@example.com for more info"
        email = extract_email(text)
        assert email == "john.doe@example.com"
    
    def test_extract_email_multiple(self):
        text = "Email: john@example.com or jane@company.org"
        email = extract_email(text)
        assert email in ["john@example.com", "jane@company.org"]
    
    def test_extract_email_none(self):
        text = "No email address in this text"
        email = extract_email(text)
        assert email is None
    
    def test_extract_phone_valid(self):
        text = "Call me at +1-555-123-4567"
        phone = extract_phone(text)
        assert phone is not None
        assert "555" in phone or "123" in phone
    
    def test_extract_phone_none(self):
        text = "No phone number here"
        phone = extract_phone(text)
        assert phone is None
    
    def test_extract_linkedin_valid(self):
        text = "Find me on LinkedIn: linkedin.com/in/johndoe"
        url = extract_linkedin(text)
        assert url is not None
        assert "johndoe" in url
    
    def test_extract_linkedin_full_url(self):
        text = "https://www.linkedin.com/in/janedoe"
        url = extract_linkedin(text)
        assert url is not None
        assert "janedoe" in url
    
    def test_extract_linkedin_none(self):
        text = "No LinkedIn profile"
        url = extract_linkedin(text)
        assert url is None
    
    def test_extract_github_valid(self):
        text = "Check my GitHub: github.com/johndoe"
        url = extract_github(text)
        assert url is not None
        assert "johndoe" in url
    
    def test_extract_github_none(self):
        text = "No GitHub profile"
        url = extract_github(text)
        assert url is None
    
    def test_extract_portfolio_valid(self):
        text = "Visit my portfolio at johndoe.dev"
        url = extract_portfolio(text)
        assert url is not None
    
    def test_extract_portfolio_none(self):
        text = "No portfolio website"
        url = extract_portfolio(text)
        assert url is None


class TestNameExtraction:
    """Tests for name extraction from resume text."""
    
    def test_extract_name_from_header(self):
        text = "JOHN DOE\nSoftware Engineer\njohn@example.com"
        name = extract_name(text)
        assert name is not None
        assert "john" in name.lower()
    
    def test_extract_name_none(self):
        text = ""
        name = extract_name(text)
        assert name is not None  # Should return something, even if generic


class TestTitleExtraction:
    """Tests for job title extraction."""
    
    def test_extract_title_valid(self):
        text = "John Doe\nSenior Software Engineer\nExperience:"
        title = extract_title(text)
        assert title is not None
        assert "software" in title.lower() or "engineer" in title.lower()
    
    def test_extract_title_none(self):
        text = "Just some random text without a title"
        title = extract_title(text)
        # May return None or something generic


class TestSectionExtraction:
    """Tests for extracting resume sections."""
    
    def test_extract_sections_identifies_headers(self):
        text = """
JOHN DOE
Email: john@example.com

EXPERIENCE
Software Engineer at TechCorp
- Built web applications

EDUCATION
B.S. in Computer Science
University of Technology

SKILLS
Python, JavaScript, React
"""
        sections = extract_sections(text)
        assert isinstance(sections, dict)
        assert "experience" in sections or "EXPERIENCE" in sections
        assert "education" in sections or "EDUCATION" in sections
        assert "skills" in sections or "SKILLS" in sections


class TestEducationExtraction:
    """Tests for extracting education details."""
    
    def test_extract_education_details(self):
        lines = [
            "EDUCATION",
            "B.S. in Computer Science",
            "University of Technology",
            "2010 - 2014",
            "GPA: 3.8"
        ]
        education = extract_education_details(lines)
        assert isinstance(education, list)
        if education:
            edu = education[0]
            assert isinstance(edu, dict)


class TestExperienceExtraction:
    """Tests for extracting experience details."""
    
    def test_extract_experience_details(self):
        lines = [
            "EXPERIENCE",
            "Senior Software Engineer",
            "TechCorp Inc.",
            "2015 - Present",
            "- Developed web applications using React and Node.js",
            "- Led a team of 5 developers"
        ]
        experience = extract_experience_details(lines)
        assert isinstance(experience, list)
        if experience:
            exp = experience[0]
            assert isinstance(exp, dict)


class TestProjectExtraction:
    """Tests for extracting project details."""
    
    def test_extract_project_details(self):
        lines = [
            "PROJECTS",
            "E-Commerce Platform",
            "Built a full-stack e-commerce solution",
            "Technologies: React, Node.js, MongoDB"
        ]
        projects = extract_project_details(lines)
        assert isinstance(projects, list)
        if projects:
            project = projects[0]
            assert isinstance(project, dict)


class TestSkillExtraction:
    """Tests for extracting skills from resume text."""
    
    def test_extract_skills_from_section(self):
        lines = [
            "SKILLS",
            "Technical: Python, JavaScript, React, Node.js",
            "Tools: Git, Docker, AWS"
        ]
        skills = extract_skills(lines)
        assert isinstance(skills, list)
        if skills:
            skill = skills[0]
            assert isinstance(skill, dict)
            assert "name" in skill
    
    def test_extract_skills_from_text(self):
        text = "Proficient in Python, JavaScript, React, Node.js, and AWS"
        skills = parser_extract_skills(text)
        assert isinstance(skills, list)
        # Should identify at least some skills
        skill_names = [s.get("name", "").lower() for s in skills]
        assert any("python" in name for name in skill_names) or len(skills) > 0


# ==================== Matcher Tests ====================

class TestSkillMatcher:
    """Tests for skill matching functionality."""
    
    def test_match_skills_exact_match(self):
        resume_skills = ["Python", "JavaScript", "React"]
        job_skills = ["Python", "React", "Node.js"]
        result = match_skills(resume_skills, job_skills)
        matched = result["matched"]
        missing = result["missing"]
        
        assert "python" in [m.lower() for m in matched]
        assert "react" in [m.lower() for m in matched]
        assert "node.js" in [m.lower() for m in missing] or "javascript" in [m.lower() for m in matched]
    
    def test_match_skills_no_match(self):
        resume_skills = ["Java", "Spring"]
        job_skills = ["Python", "Django"]
        result = match_skills(resume_skills, job_skills)
        matched = result["matched"]
        missing = result["missing"]
        
        assert len(matched) == 0
        assert len(missing) == 2
    
    def test_match_skills_perfect_match(self):
        resume_skills = ["Python", "Django", "PostgreSQL"]
        job_skills = ["Python", "Django", "PostgreSQL"]
        result = match_skills(resume_skills, job_skills)
        matched = result["matched"]
        missing = result["missing"]
        
        assert len(matched) == 3
        assert len(missing) == 0
    
    def test_extract_skills_from_text_for_matching(self):
        text = "Looking for Python developer with Django and PostgreSQL experience"
        skill_db = ["Python", "Django", "PostgreSQL", "React"]
        skills = matcher_extract_skills(text, skill_db)
        assert isinstance(skills, list)
        skill_names = [s.lower() for s in skills]
        assert "python" in skill_names


# ==================== ATS Analyzer Tests ====================

class TestJDRequirementParsing:
    """Tests for parsing job description requirements."""
    
    def test_parse_jd_requirements(self):
        jd = """
        We are looking for a Senior Python Developer with:
        - 5+ years of experience in Python development
        - Strong knowledge of Django and Flask
        - Experience with PostgreSQL and Redis
        - Familiarity with Docker and Kubernetes
        """
        requirements = _parse_jd_requirements(jd)
        assert isinstance(requirements, dict)
        assert "years_required" in requirements or "required_skills" in requirements
    
    def test_parse_jd_requirements_empty(self):
        jd = ""
        requirements = _parse_jd_requirements(jd)
        assert isinstance(requirements, dict)
    
    def test_split_jd_sections(self):
        jd = """
        Job Title: Senior Developer
        
        Description: We are looking for a talented developer.
        
        Requirements: Must have 5 years experience.
        """
        description, requirements = _split_jd_sections(jd)
        assert isinstance(description, str)
        assert isinstance(requirements, str)
    
    def test_normalise_skill(self):
        assert _normalise_skill("Python ") == "python"
        assert _normalise_skill("  JavaScript  ") == "javascript"
        assert _normalise_skill("C++") == "c++"
    
    def test_match_skills_function(self):
        resume_skills = ["python", "django"]
        jd_skills = ["python", "flask", "django"]
        result = _match_skills(resume_skills, jd_skills)
        matched = result["matched"]
        missing = result["missing"]
        
        assert "python" in matched
        assert "django" in matched
        assert "flask" in missing


class TestATSScoreCalculation:
    """Tests for ATS score calculation (integration with LLM mocked)."""
    
    @pytest.fixture
    def sample_resume(self):
        resume = MagicMock(spec=Resume)
        resume.id = 1
        resume.content = None
        resume.full_name = "John Doe"
        resume.email = "john@example.com"
        resume.phone = "123-456-7890"
        resume.linkedin_url = "https://linkedin.com/in/johndoe"
        resume.title = "Software Engineer"
        resume.target_role = "Senior Software Engineer"
        resume.summary = "Experienced software engineer with 5 years in Python development"
        
        resume.education = [
            MagicMock(spec=Education, school="Tech University", degree="B.S.", major="Computer Science", start_date="2010", end_date="2014")
        ]
        resume.experience = [
            MagicMock(spec=Experience, company="TechCorp", role="Software Engineer", start_date="2015", end_date="2020", description="Developed web applications using Python and Django")
        ]
        resume.projects = [
            MagicMock(spec=Project, project_name="E-Commerce Platform", description="Built a full-stack e-commerce solution")
        ]
        
        skill1 = MagicMock(spec=Skill)
        skill1.name = "Python"
        skill2 = MagicMock(spec=Skill)
        skill2.name = "Django"
        skill3 = MagicMock(spec=Skill)
        skill3.name = "PostgreSQL"
        resume.skills = [skill1, skill2, skill3]
        
        return resume
    
    @pytest.fixture
    def anyio_backend(self):
        return "asyncio"

    @pytest.mark.anyio
    async def test_calculate_ats_score_with_mock_llm(self, sample_resume):
        mock_llm_result = {
            "full_name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "+1234567890",
            "location": "San Francisco, CA",
            "title": "Senior Software Engineer",
            "summary": "Experienced developer with a focus on Python and cloud technologies.",
            "education": [
                {
                    "school": "University of Technology",
                    "degree": "Bachelor of Science",
                    "major": "Computer Science",
                    "start_date": "2010",
                    "end_date": "2014"
                }
            ],
            "experience": [
                {
                    "company": "Tech Corp",
                    "role": "Software Engineer",
                    "start_date": "2015",
                    "end_date": "Present",
                    "description": "Developing scalable web applications.",
                    "points": ["Built microservices", "Optimized database queries"]
                }
            ],
            "skills": [
                {"name": "Python", "category": "Programming"},
                {"name": "Django", "category": "Frameworks"},
                {"name": "AWS", "category": "Cloud"}
            ]
        }
        
        with patch("app.services.resume_service.ats_analyzer.llm_service.generate_structured_output", new_callable=MagicMock) as mock_gen:
            mock_gen.return_value = mock_llm_result
            jd = "Looking for a Python developer with Django experience"
            result = await calculate_ats_score(sample_resume, jd)
            
            assert result["status"] == "Complete"
            assert result["llm_powered"] is True
            assert 0 <= result["overall_score"] <= 100
            assert "category_scores" in result
            assert "skill_analysis" in result
    
    @pytest.mark.anyio
    async def test_calculate_ats_score_llm_failure_fallback(self, sample_resume):
        with patch("app.services.resume_service.ats_analyzer.llm_service.generate_structured_output", new_callable=MagicMock) as mock_gen:
            mock_gen.return_value = None
            jd = "Some job description"
            result = await calculate_ats_score(sample_resume, jd)
            
            # Should fall back to heuristic scoring
            assert result["status"] == "Partial"
            assert result["llm_powered"] is False
            assert result["overall_score"] > 0  # Should still have a score
    
    @pytest.mark.anyio
    async def test_calculate_ats_score_empty_jd(self, sample_resume):
        with patch("app.services.resume_service.ats_analyzer.llm_service.generate_structured_output", new_callable=MagicMock) as mock_gen:
            mock_gen.return_value = None
            result = await calculate_ats_score(sample_resume, "")
            assert result is not None