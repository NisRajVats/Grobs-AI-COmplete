# GrobsAI Backend Testing Guide

## Overview

This document provides comprehensive guidance on testing the GrobsAI backend application. The testing strategy includes unit tests, integration tests, security tests, and performance tests to ensure code quality, reliability, and security.

## Test Structure

### Test Organization

```
Backend/
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Basic pytest configuration
│   ├── conftest_enhanced.py     # Enhanced fixtures and utilities
│   ├── test_auth.py             # Authentication endpoint tests
│   ├── test_jobs.py             # Job endpoint tests
│   ├── test_resumes.py          # Resume endpoint tests
│   ├── test_interview.py        # Interview endpoint tests
│   ├── test_analytics.py        # Analytics endpoint tests
│   ├── test_users.py            # User endpoint tests
│   ├── test_security.py         # Security module tests
│   ├── test_resume_service.py   # Resume service tests
│   ├── test_matching_scoring.py # Matching and scoring engine tests
│   ├── test_models.py           # Database model tests
│   ├── test_integration.py      # Integration and workflow tests
│   └── test_ai_resume.py        # AI resume analysis tests
├── run_tests.py                 # Test runner script
└── test_reports/                # Generated test reports
```

### Test Categories

1. **Unit Tests** (`-m unit`)
   - Individual function/method testing
   - Service layer testing
   - Model testing
   - Business logic testing

2. **Integration Tests** (`-m integration`)
   - End-to-end workflow testing
   - API endpoint testing
   - Database integration testing
   - Service interaction testing

3. **Security Tests** (`-m security`)
   - Authentication and authorization
   - Input validation
   - Token handling
   - Security vulnerability testing

4. **Performance Tests** (`-m performance`)
   - Load testing
   - Response time testing
   - Resource usage testing

## Running Tests

### Basic Test Execution

```bash
# Run all tests
python run_tests.py --mode all

# Run unit tests only
python run_tests.py --mode unit

# Run integration tests only
python run_tests.py --mode integration

# Run security tests
python run_tests.py --mode security
```

### Advanced Test Execution

```bash
# Run with verbose output
python run_tests.py --mode all --verbose

# Run with coverage report
python run_tests.py --mode all --coverage

# Run in parallel (faster execution)
python run_tests.py --mode all --parallel

# Run specific test file
python run_tests.py --mode file --file tests/test_auth.py

# Run tests matching pattern
python run_tests.py --mode pattern --pattern "test_login"
```

### Direct pytest Usage

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_auth.py

# Run tests with pattern
pytest -k "test_login"

# Run with coverage
pytest --cov=app --cov-report=html

# Run in parallel
pytest -n auto

# Run with verbose output
pytest -v

# Stop on first failure
pytest -x
```

## Test Configuration

### Environment Setup

The tests use an in-memory SQLite database for isolation and speed. The configuration is automatically set up in `conftest.py`.

### Test Fixtures

Key fixtures available:

- `db_session`: Database session with transaction rollback
- `test_user`: Pre-created test user
- `test_user_with_resume`: User with complete resume data
- `test_job`: Sample job listing
- `test_application`: Sample job application
- `authenticated_client`: HTTP client with authentication
- `mock_llm_service`: Mocked LLM service for testing
- `sample_resume_data`: Sample resume data dictionary

### Test Markers

- `@pytest.mark.unit`: Unit tests
- `@pytest.mark.integration`: Integration tests
- `@pytest.mark.security`: Security tests
- `@pytest.mark.performance`: Performance tests
- `@pytest.mark.slow`: Tests that take longer to run

## Test Coverage

### Current Coverage Areas

1. **Authentication & Security**
   - User registration and login
   - JWT token creation and validation
   - Password hashing and verification
   - Token refresh and rotation
   - Password reset workflow
   - Email verification

2. **Resume Management**
   - Resume creation, update, deletion
   - File upload and parsing
   - ATS analysis and scoring
   - Resume optimization
   - Skill extraction and matching

3. **Job Management**
   - Job listing and search
   - Job application workflow
   - Job matching algorithms
   - Saved jobs functionality

4. **Interview Preparation**
   - Interview session management
   - Question generation
   - Answer evaluation

5. **Analytics & Reporting**
   - User analytics
   - Application tracking
   - Resume scoring metrics

6. **Database Models**
   - Model creation and validation
   - Relationship testing
   - Constraint validation
   - Data integrity testing

### Coverage Goals

- **Target Coverage**: 85%+ line coverage
- **Critical Areas**: 95%+ coverage
  - Authentication and security
  - Data validation and sanitization
  - Business logic and calculations
  - Error handling

## Writing Tests

### Unit Test Example

```python
import pytest
from app.services.resume_service.parser import extract_email

class TestEmailExtraction:
    def test_extract_email_valid(self):
        text = "Contact me at john@example.com for more info"
        email = extract_email(text)
        assert email == "john@example.com"
    
    def test_extract_email_none(self):
        text = "No email address in this text"
        email = extract_email(text)
        assert email is None
```

### Integration Test Example

```python
def test_complete_resume_workflow(self, client, auth_headers, db_session):
    """Test complete resume creation, update, and deletion workflow."""
    # Create resume
    create_res = client.post("/api/resumes", json={
        "full_name": "John Doe",
        "email": "john@example.com",
        "title": "Software Engineer Resume"
    }, headers=auth_headers)
    assert create_res.status_code in [200, 201]
    resume_id = create_res.json()["id"]
    
    # Get resume
    get_res = client.get(f"/api/resumes/{resume_id}", headers=auth_headers)
    assert get_res.status_code == 200
    assert get_res.json()["full_name"] == "John Doe"
    
    # Update resume
    update_res = client.put(f"/api/resumes/{resume_id}", json={
        "full_name": "John Doe",
        "email": "john@example.com",
        "title": "Senior Software Engineer Resume"
    }, headers=auth_headers)
    assert update_res.status_code == 200
    assert update_res.json()["title"] == "Senior Software Engineer Resume"
```

### Mocking External Services

```python
from unittest.mock import patch

def test_llm_integration(self, mock_llm_service):
    """Test LLM integration with mocked service."""
    with patch("app.services.llm_service.llm_service.generate_structured_output_async") as mock_llm:
        mock_llm.return_value = {
            "overall_score": 85,
            "keyword_optimization_score": 80,
            "semantic_relevance_score": 90
        }
        
        result = await calculate_ats_score(resume, job_description)
        assert result["overall_score"] == 85
```

## Test Data Management

### Test Data Generators

Use the `TestDataGenerator` class for creating consistent test data:

```python
from conftest_enhanced import TestDataGenerator

def test_user_creation(self, db_session):
    generator = TestDataGenerator()
    user = generator.create_user(
        email="test@example.com",
        full_name="Test User",
        password="password123"
    )
    db_session.add(user)
    db_session.commit()
```

### Test File Fixtures

For file upload testing:

```python
def test_pdf_upload(self, client, auth_headers, sample_pdf_file):
    """Test PDF file upload."""
    response = client.post(
        "/api/resumes/upload",
        files={"file": ("test_resume.pdf", sample_pdf_file, "application/pdf")},
        headers=auth_headers
    )
    assert response.status_code in [200, 201]
```

## Error Handling Tests

### Testing Error Scenarios

```python
def test_invalid_authentication(self, client):
    """Test API calls with invalid authentication."""
    res = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid.token"})
    assert res.status_code == 401

def test_missing_required_fields(self, client, auth_headers):
    """Test API calls with missing required fields."""
    res = client.post("/api/resumes", json={
        "full_name": "Test User"
        # Missing email, title, etc.
    }, headers=auth_headers)
    assert res.status_code == 422  # Validation error

def test_resource_not_found(self, client, auth_headers):
    """Test API calls for non-existent resources."""
    res = client.get("/api/resumes/99999", headers=auth_headers)
    assert res.status_code == 404
```

### Testing Security Vulnerabilities

```python
def test_sql_injection_prevention(self, client, auth_headers):
    """Test SQL injection prevention."""
    res = client.get("/api/jobs/search?q='; DROP TABLE jobs;--", headers=auth_headers)
    assert res.status_code in [200, 400]

def test_xss_prevention(self, client, auth_headers):
    """Test XSS prevention."""
    xss_payload = "<script>alert('XSS')</script>"
    res = client.post("/api/resumes", json={
        "full_name": xss_payload,
        "email": "xss@example.com",
        "title": "Test Resume"
    }, headers=auth_headers)
    assert res.status_code in [200, 201, 400]
```

## Performance Testing

### Response Time Testing

```python
import time

def test_api_response_time(self, client, auth_headers):
    """Test API response time."""
    start_time = time.time()
    
    response = client.get("/api/resumes", headers=auth_headers)
    
    end_time = time.time()
    response_time = end_time - start_time
    
    assert response.status_code == 200
    assert response_time < 2.0  # Should respond within 2 seconds
```

### Load Testing

```python
import concurrent.futures

def test_concurrent_requests(self, client, auth_headers):
    """Test concurrent API requests."""
    def make_request():
        return client.get("/api/resumes", headers=auth_headers)
    
    # Make 10 concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request) for _ in range(10)]
        responses = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    # All requests should succeed
    for response in responses:
        assert response.status_code == 200
```

## Continuous Integration

### GitHub Actions Integration

Add to `.github/workflows/test.yml`:

```yaml
name: Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.10
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-html
      - name: Run tests
        run: python run_tests.py --mode all --coverage --verbose
      - name: Upload coverage reports
        uses: codecov/codecov-action@v1
        with:
          file: ./coverage.xml
```

### Pre-commit Hooks

Add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: python run_tests.py --mode fast --verbose
        language: system
        pass_filenames: false
        always_run: true
```

## Test Reports

### Generated Reports

The test runner generates several types of reports:

1. **HTML Reports**: Detailed test results with failure analysis
2. **JUnit XML**: Machine-readable test results for CI/CD
3. **Coverage Reports**: Code coverage analysis
4. **Text Output**: Detailed command output and logs

### Report Locations

```
Backend/test_reports/
├── unit_tests_20240101_120000.html
├── unit_tests_20240101_120000.xml
├── unit_tests_20240101_120000_output.txt
├── coverage/
│   ├── index.html
│   └── ...
└── ...
```

### Analyzing Test Results

```bash
# Analyze latest test reports
python run_tests.py --analyze

# View coverage report
open Backend/test_reports/coverage/index.html
```

## Best Practices

### Test Organization

1. **Group related tests** in classes with descriptive names
2. **Use clear test method names** that describe what is being tested
3. **Follow AAA pattern**: Arrange, Act, Assert
4. **Keep tests independent** - no dependencies between tests
5. **Use fixtures** for common setup and teardown

### Test Quality

1. **Test one thing at a time** - each test should have a single purpose
2. **Use meaningful assertions** - test the actual behavior, not implementation details
3. **Mock external dependencies** - isolate the code being tested
4. **Test edge cases** - empty inputs, invalid data, boundary conditions
5. **Test error conditions** - ensure proper error handling

### Performance Considerations

1. **Use in-memory databases** for faster tests
2. **Mock external services** to avoid network dependencies
3. **Run slow tests separately** from fast tests
4. **Use parallel execution** for faster test runs
5. **Optimize test data setup** - use factories and fixtures

### Security Testing

1. **Test input validation** - SQL injection, XSS, command injection
2. **Test authentication** - invalid tokens, expired tokens, missing auth
3. **Test authorization** - access control, privilege escalation
4. **Test data sanitization** - malicious input handling
5. **Test rate limiting** - API abuse prevention

## Troubleshooting

### Common Issues

1. **Database connection errors**: Ensure test database is properly configured
2. **Missing dependencies**: Install all required packages from requirements.txt
3. **Mock failures**: Check mock setup and return values
4. **Test isolation**: Ensure tests don't share state
5. **Timing issues**: Add appropriate delays for async operations

### Debugging Tests

```bash
# Run single test with verbose output
pytest tests/test_auth.py::TestAuth::test_login_success -v -s

# Run tests with pdb debugger
pytest tests/test_auth.py --pdb

# Run tests with detailed traceback
pytest tests/test_auth.py --tb=long
```

### Test Environment

Ensure the test environment is properly configured:

```bash
# Set environment variables
export ENVIRONMENT=testing
export DATABASE_URL=sqlite:///:memory:

# Install test dependencies
pip install -r requirements.txt
pip install pytest pytest-cov pytest-html pytest-xdist
```

## Conclusion

This comprehensive testing strategy ensures that the GrobsAI backend is reliable, secure, and performant. Regular testing helps catch issues early, maintain code quality, and build confidence in the application.

For questions or issues with the testing setup, refer to this guide or consult the test files for examples and best practices.