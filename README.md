# GrobsAI - AI-Powered Career Platform

GrobsAI is a comprehensive full-stack AI career platform that helps users with resume management, job matching, ATS analysis, mock interviews, and application tracking.

## 🚀 Project Overview

- **Frontend**: React 19, Vite, Tailwind CSS, Recharts, Framer Motion
- **Backend**: FastAPI, SQLAlchemy, SQLite/PostgreSQL
- **AI**: Google Gemini / OpenAI / Anthropic (configurable)
- **Auth**: JWT with refresh tokens

---

## 📁 Project Structure

- **[Backend/](./Backend/)**: Python-based FastAPI service.
  - AI-driven resume parsing and ATS scoring.
  - Mock interview generation and feedback.
  - Job recommendation engine.
  - PostgreSQL database with SQLAlchemy ORM.
  - Celery for background tasks.
- **[Frontend/](./Frontend/)**: Vite-powered React 19 application.
  - Modern UI with Tailwind CSS.
  - Resume builder and management.
  - Interactive job center and interview preparation.
  - Real-time AI chat integration.

---

## 🚀 Quick Start (Local Development)

### Prerequisites
- **Node.js** (v18+)
- **Python** (v3.10+)
- **PostgreSQL** (or SQLite for development)
- **Redis** (for Celery workers)

### Step 1: Setup the Backend
```bash
cd Backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # Configure your environment variables
python setup.py           # Initialize database
uvicorn app.main:app --reload
```

### Step 2: Setup the Frontend
```bash
cd Frontend
npm install
cp .env.example .env      # Configure your environment variables
npm run dev
```

---

## 🔑 AI Features Setup

To enable AI features (resume analysis, ATS scoring, interview questions), add an API key to your backend `.env`:

### Google Gemini (Recommended)
```env
LLM_PROVIDER=google
GEMINI_API_KEY=your-key-from-aistudio.google.com
```

### OpenAI
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your-openai-key
```

### Anthropic Claude
```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your-anthropic-key
```

---

## ✅ Core Features

- **Resume Management**: Upload PDF resumes or create them with the built-in builder.
- **AI Resume Analysis**: ATS score calculation, keyword analysis, and AI-powered optimization.
- **Job Search**: Personalized job recommendations and application tracking.
- **Interview Preparation**: AI-generated practice questions and mock interview sessions with real-time feedback.
- **Analytics Dashboard**: Real-time application statistics and activity tracking.

---

## 🧪 Testing & Quality

### Backend Tests
```bash
cd Backend
pytest tests/ -v
```

### Frontend Quality
```bash
cd Frontend
npm run lint
```

---

## 📖 Additional Documentation

- [Backend Documentation](./Backend/README.md)
- [Frontend Documentation](./Frontend/README.md)
- [System Architecture](./docs/METHODOLOGY.md)
- [User Navigation Flow](./docs/user_navigation.md)

---

## 🛠️ Troubleshooting

- **Backend won't start**: Ensure `venv` is active and `SECRET_KEY` is set in `.env`.
- **Frontend "Failed to load"**: Verify backend is running on port 8000 and `VITE_API_URL` is correct.
- **No jobs showing**: Run `python setup.py` to seed sample jobs.
- **AI features not working**: Check `LLM_PROVIDER` and API key in backend `.env`.

---

## 📄 License

This project is proprietary and part of the GrobsAI platform.
