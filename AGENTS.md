# Repository Guidelines

GrobsAI is a career platform featuring a FastAPI backend and a React frontend. The system manages resumes, job listings, and AI-driven career tools.

## Project Structure & Module Organization

- **Backend/**: Python-based FastAPI service.
  - `app/core/`: Configuration (Pydantic), security, and exceptions.
  - `app/models/`: SQLAlchemy models for database schema.
  - `app/routers/`: API endpoints grouped by feature.
  - `app/services/`: Business logic and external integrations (AI providers, database operations).
  - `app/workers/`: Celery tasks for background processing.
  - `tests/`: Pytest suite for unit and integration testing.
- **Frontend/**: Vite-powered React 19 application.
  - `src/features/`: Feature-specific modules containing components, hooks, and services.
  - `src/services/`: API clients using Axios.
  - `src/context/`: Global state management via React Context.

## Build, Test, and Development Commands

### Backend
- **Install Dependencies**: `pip install -r requirements.txt`
- **Initialize Database**: `python setup.py`
- **Start Dev Server**: `uvicorn app.main:app --reload`
- **Run Tests**: `pytest`
- **Run Single Test**: `pytest tests/test_auth.py`

### Frontend
- **Install Dependencies**: `npm install`
- **Start Dev Server**: `npm run dev`
- **Build Production**: `npm run build`
- **Lint Code**: `npm run lint`

## Coding Style & Naming Conventions

- **Frontend**: Enforced by ESLint 9 using `eslint.config.js`. Follows React 19 best practices.
- **Backend**: Uses Pydantic for data validation and SQLAlchemy for ORM. Naming follows PEP 8.
- **Environment**: Both tiers rely on `.env` files for configuration (see `.env.example` in respective directories).

## Testing Guidelines

- **Framework**: Pytest for backend testing.
- **Coverage**: Use `pytest --cov=app` for coverage reports.
- **Patterns**: Mock external AI services when testing resume analysis or interview features.

## Database Management

- **Migrations**: Alembic is used for schema migrations (`alembic upgrade head`).
- **Initialization**: `setup.py` seeds initial job listings for development.
