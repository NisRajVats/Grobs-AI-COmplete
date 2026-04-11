"""
Enhanced pytest configuration with additional fixtures and utilities for comprehensive testing.
"""
import pytest
import os
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database.session import Base, get_db
from app.core.config import settings
from app.core.security import get_password_hash
from app.models import User, Resume, Skill, Education, Experience, Project, Job, JobApplication, JobSkill


# Force testing environment
settings.ENVIRONMENT = "testing"

# Use in-memory SQLite for tests with better isolation
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool  # Better for testing
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create all tables before tests, drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    """Provide a test database session with transaction rollback."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def test_user(db_session):
    """Provide a test user with common attributes."""
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Test User",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_user_with_resume(db_session, test_user):
    """Provide a test user with a complete resume."""
    resume = Resume(
        user_id=test_user.id,
        full_name="John Doe",
        email="john@example.com",
        title="Software Engineer Resume",
        summary="Experienced software engineer with 5 years in Python development",
        target_role="Senior Software Engineer"
    )
    db_session.add(resume)
    db_session.commit()
    db_session.refresh(resume)
    
    # Add skills
    skills = [
        Skill(name="Python", category="Technical"),
        Skill(name="Django", category="Technical"),
        Skill(name="React", category="Technical"),
        Skill(name="Communication", category="Soft")
    ]
    db_session.add_all(skills)
    db_session.commit()
    
    resume.skills = skills
    db_session.commit()
    
    # Add education
    education = Education(
        resume_id=resume.id,
        school="Tech University",
        degree="B.S.",
        major="Computer Science",
        start_date="2010",
        end_date="2014",
        gpa="3.8"
    )
    db_session.add(education)
    
    # Add experience
    experience = Experience(
        resume_id=resume.id,
        company="TechCorp",
        role="Software Engineer",
        start_date="2015",
        end_date="2020",
        description="Developed web applications using Python and Django"
    )
    db_session.add(experience)
    
    # Add project
    project = Project(
        resume_id=resume.id,
        project_name="E-Commerce Platform",
        description="Built a full-stack e-commerce solution",
        technologies="React, Node.js, MongoDB"
    )
    db_session.add(project)
    
    db_session.commit()
    return test_user, resume


@pytest.fixture
def test_job(db_session):
    """Provide a test job listing."""
    job = Job(
        title="Software Engineer",
        company="TechCorp",
        location="San Francisco, CA",
        description="Looking for experienced software engineer",
        requirements="5+ years experience in Python",
        salary_min=80000,
        salary_max=120000,
        job_type="Full-time",
        remote=True,
        posted_date="2024-01-01"
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    
    # Add job skills
    skills = [
        Skill(name="Python", category="Technical"),
        Skill(name="Django", category="Technical"),
        Skill(name="PostgreSQL", category="Technical")
    ]
    db_session.add_all(skills)
    db_session.commit()
    
    # Associate skills with job
    for skill in skills:
        job_skill = JobSkill(job_id=job.id, skill_id=skill.id)
        db_session.add(job_skill)
    
    db_session.commit()
    return job


@pytest.fixture
def test_application(db_session, test_user, test_job):
    """Provide a test job application."""
    application = JobApplication(
        user_id=test_user.id,
        job_id=test_job.id,
        job_title=test_job.title,
        company=test_job.company,
        status="applied",
        notes="Applied through company website"
    )
    db_session.add(application)
    db_session.commit()
    db_session.refresh(application)
    return application


@pytest.fixture
def authenticated_client(client, test_user):
    """Provide an authenticated test client."""
    # Login to get token
    login_response = client.post("/api/auth/token", data={
        "username": test_user.email,
        "password": "password123"
    })
    token = login_response.json().get("access_token")
    
    # Create client with auth headers
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


@pytest.fixture
def mock_llm_service():
    """Provide a mock LLM service for testing."""
    with patch("app.services.llm_service.llm_service.generate_structured_output_async") as mock_llm:
        mock_llm.return_value = {
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
                "hard_skills": ["Python", "Django"],
                "soft_skills": ["Communication"],
                "tools": ["Git"]
            },
            "keyword_gap": {
                "matched": ["Python", "Django"],
                "missing": ["FastAPI"],
                "optional": ["AWS"]
            },
            "industry_tips": ["Focus on backend skills"]
        }
        yield mock_llm


@pytest.fixture
def mock_embedding_service():
    """Provide a mock embedding service for testing."""
    with patch("app.services.llm_service.llm_service.generate_embeddings") as mock_embed:
        mock_embed.return_value = [
            {"embedding": [0.1, 0.2, 0.3], "text": "test text"}
        ]
        yield mock_embed


@pytest.fixture
def sample_resume_data():
    """Provide sample resume data for testing."""
    return {
        "full_name": "John Doe",
        "email": "john@example.com",
        "phone": "123-456-7890",
        "linkedin_url": "https://linkedin.com/in/johndoe",
        "title": "Software Engineer Resume",
        "summary": "Experienced software engineer with 5 years in Python development",
        "target_role": "Senior Software Engineer",
        "skills": [
            {"name": "Python", "category": "Technical"},
            {"name": "Django", "category": "Technical"},
            {"name": "React", "category": "Technical"}
        ],
        "education": [
            {
                "school": "Tech University",
                "degree": "B.S.",
                "major": "Computer Science",
                "start_date": "2010",
                "end_date": "2014",
                "gpa": "3.8"
            }
        ],
        "experience": [
            {
                "company": "TechCorp",
                "role": "Software Engineer",
                "start_date": "2015",
                "end_date": "2020",
                "description": "Developed web applications using Python and Django"
            }
        ],
        "projects": [
            {
                "project_name": "E-Commerce Platform",
                "description": "Built a full-stack e-commerce solution",
                "technologies": "React, Node.js, MongoDB"
            }
        ]
    }


@pytest.fixture
def sample_job_data():
    """Provide sample job data for testing."""
    return {
        "title": "Software Engineer",
        "company": "TechCorp",
        "location": "San Francisco, CA",
        "description": "Looking for experienced software engineer",
        "requirements": "5+ years experience in Python",
        "salary_min": 80000,
        "salary_max": 120000,
        "job_type": "Full-time",
        "remote": True,
        "skills": [
            {"name": "Python", "category": "Technical"},
            {"name": "Django", "category": "Technical"},
            {"name": "PostgreSQL", "category": "Technical"}
        ]
    }


# Test data generators
class TestDataGenerator:
    """Utility class for generating test data."""
    
    @staticmethod
    def create_user(email="test@example.com", full_name="Test User", password="password123"):
        """Create a user object for testing."""
        return User(
            email=email,
            hashed_password=get_password_hash(password),
            full_name=full_name,
            is_active=True
        )
    
    @staticmethod
    def create_resume(user_id, title="Test Resume", summary="Test summary"):
        """Create a resume object for testing."""
        return Resume(
            user_id=user_id,
            full_name="Test User",
            email="test@example.com",
            title=title,
            summary=summary,
            target_role="Software Engineer"
        )
    
    @staticmethod
    def create_job(title="Test Job", company="Test Corp", description="Test description"):
        """Create a job object for testing."""
        return Job(
            title=title,
            company=company,
            location="Test City",
            description=description,
            requirements="Test requirements",
            salary_min=50000,
            salary_max=100000,
            job_type="Full-time",
            remote=False
        )


@pytest.fixture
def data_generator():
    """Provide test data generator."""
    return TestDataGenerator


# Performance testing utilities
@pytest.fixture
def performance_timer():
    """Provide a performance timer for testing."""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
        
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return Timer()


# Mock file fixtures for testing file uploads
@pytest.fixture
def sample_pdf_file():
    """Provide a sample PDF file for testing."""
    import io
    
    # Create a minimal PDF-like file
    pdf_content = b"%PDF-1.4 test resume content John Doe Software Engineer"
    return io.BytesIO(pdf_content)


@pytest.fixture
def sample_docx_file():
    """Provide a sample DOCX file for testing."""
    import io
    
    # Create a minimal DOCX-like file
    docx_content = b"PK\x03\x04 test docx content"
    return io.BytesIO(docx_content)


# Error simulation fixtures
@pytest.fixture
def simulate_llm_failure():
    """Simulate LLM service failure."""
    with patch("app.services.llm_service.llm_service.generate_structured_output_async") as mock_llm:
        mock_llm.return_value = None
        yield mock_llm


@pytest.fixture
def simulate_database_error():
    """Simulate database errors."""
    with patch("app.database.session.get_db") as mock_db:
        mock_db.side_effect = Exception("Database connection failed")
        yield mock_db


# Configuration for different test environments
@pytest.fixture(scope="session", params=["sqlite", "postgresql"])
def db_type(request):
    """Parameterize tests for different database types."""
    return request.param


# Test markers for categorizing tests
pytest.mark.slow = pytest.mark.slow
pytest.mark.integration = pytest.mark.integration
pytest.mark.unit = pytest.mark.unit
pytest.mark.security = pytest.mark.security
pytest.mark.performance = pytest.mark.performance


# Custom pytest hooks
def pytest_configure(config):
    """Configure custom pytest settings."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "security: marks tests as security tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        # Add slow marker to tests that might be slow
        if "integration" in item.name or "workflow" in item.name:
            item.add_marker(pytest.mark.slow)
        
        # Add integration marker to integration tests
        if "integration" in item.name:
            item.add_marker(pytest.mark.integration)
        
        # Add unit marker to unit tests
        if "test_" in item.name and "integration" not in item.name:
            item.add_marker(pytest.mark.unit)