"""
Pytest configuration and shared fixtures for GrobsAI tests.
"""
import pytest
import httpx

# Workaround for Starlette 0.27.0 + httpx 0.28.1 incompatibility
# httpx 0.28.1 removed the 'app' argument from Client.__init__, but Starlette 0.27.0 still passes it.
_original_httpx_client_init = httpx.Client.__init__

def _patched_httpx_client_init(self, *args, **kwargs):
    if "app" in kwargs:
        app = kwargs.pop("app")
        if "transport" not in kwargs:
            from httpx import ASGITransport
            kwargs["transport"] = ASGITransport(app=app)
    _original_httpx_client_init(self, *args, **kwargs)

httpx.Client.__init__ = _patched_httpx_client_init

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database.session import Base, get_db
from app.core.config import settings

# Force testing environment
settings.ENVIRONMENT = "testing"
settings.SKIP_LLM_PARSING = False

# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create all tables before tests, drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    """Provide a test database session with automatic rollback."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def mock_user(db_session):
    """Provide a test user."""
    from app.models import User
    from app.core.security import get_password_hash
    
    user = db_session.query(User).filter_by(email="test@example.com").first()
    if not user:
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
def client():
    """Provide a test HTTP client with DB override."""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client):
    """Register a test user and return auth headers."""
    client.post("/api/auth/register", json={
        "email": "testuser@example.com",
        "password": "TestPassword123!"
    })
    res = client.post("/api/auth/token", data={
        "username": "testuser@example.com",
        "password": "TestPassword123!"
    })
    token = res.json().get("access_token", "")
    return {"Authorization": f"Bearer {token}"}
