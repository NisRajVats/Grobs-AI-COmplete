# GrobsAI Backend

A robust Python-based FastAPI service for GrobsAI - an AI-powered career platform. This backend manages resumes, job listings, and provides AI-driven career tools.

## 🚀 Features

- **Resume Analysis**: AI-powered resume parsing and ATS compatibility scoring.
- **Job Engine**: Personalized job recommendations and application tracking.
- **Interview AI**: AI-generated mock interviews and real-time feedback.
- **Background Processing**: Celery-powered tasks for long-running AI processes.
- **Data Persistence**: SQLAlchemy-based PostgreSQL integration with Alembic migrations.

## 🛠️ Tech Stack

- **Framework**: FastAPI (Python 3.9+)
- **ORM**: SQLAlchemy
- **Migrations**: Alembic
- **Database**: PostgreSQL (Development supports SQLite)
- **Task Queue**: Celery with Redis
- **Testing**: Pytest
- **Security**: JWT-based authentication

## 📋 Prerequisites

- **Python 3.9+**
- **PostgreSQL** (Optional for development)
- **Redis** (For Celery tasks)

## ⚙️ Installation & Setup

1. **Clone the repository** (if not already done)
   ```bash
   git clone <repository-url>
   cd Backend
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   Copy `.env.example` to `.env` and configure your environment variables:
   ```bash
   cp .env.example .env
   ```

5. **Initialize Database**
   ```bash
   python setup.py
   ```

6. **Start the Development Server**
   ```bash
   uvicorn app.main:app --reload
   ```

## 🧪 Running Tests

Run the full test suite using Pytest:
```bash
pytest
```

For coverage reports:
```bash
pytest --cov=app
```

## 📁 Project Structure

```
Backend/
├── app/                  # Main application code
│   ├── core/            # Configuration and security
│   ├── models/          # SQLAlchemy database models
│   ├── routers/         # API endpoints
│   ├── schemas/         # Pydantic data validation
│   ├── services/        # Business logic and AI services
│   ├── workers/         # Celery background tasks
│   └── main.py          # Application entry point
├── migrations/          # Alembic database migrations
├── tests/               # Pytest unit and integration tests
├── requirements.txt     # Python dependencies
└── setup.py             # Database initialization script
```

## 📖 API Documentation

Once the server is running, interactive API documentation is available at:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## 🚢 Deployment

1. **Build Docker Image**
   ```bash
   docker build -t grobsai-backend .
   ```

2. **Run with Docker Compose** (Recommended)
   ```bash
   docker-compose up -d
   ```

---
*Part of the GrobsAI platform.*
