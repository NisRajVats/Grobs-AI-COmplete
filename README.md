# GrobsAI - AI-Powered Career Platform

GrobsAI is a full-stack AI career platform that helps users with resume management, job matching, ATS analysis, mock interviews, and application tracking.

---

## Tech Stack

- **Frontend**: React 19, Vite, Tailwind CSS, Recharts, Framer Motion
- **Backend**: FastAPI, SQLAlchemy, SQLite/PostgreSQL
- **AI**: Google Gemini / OpenAI / Anthropic (configurable)
- **Auth**: JWT with refresh tokens

---

## Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **npm or yarn**

---

## 🚀 Quick Start (Local Development)

### Step 1: Clone / Extract the Project

```bash
# If using the provided zip, extract to a folder:
unzip GrobsAI.zip -d GrobsAI
cd GrobsAI
```

### Step 2: Setup the Backend

```bash
cd Backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Configure Backend Environment

```bash
# Copy the example env file
cp .env.example .env

# Edit .env with your settings:
# - Set SECRET_KEY to a long random string
# - Add your AI provider API key (Gemini/OpenAI/Anthropic)
# Example:
# SECRET_KEY=my-very-long-secret-key-32-chars-minimum
# GEMINI_API_KEY=AIza...
```

### Step 4: Initialize the Database

```bash
# While still in the Backend folder with venv active:
python setup.py
```

This creates the SQLite database and seeds sample job listings.

### Step 5: Run the Backend

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be running at: **http://localhost:8000**  
API docs at: **http://localhost:8000/docs**

---

### Step 6: Setup the Frontend

Open a **new terminal**:

```bash
cd Frontend

# Install dependencies
npm install

# Copy env file
cp .env.example .env
# (Default VITE_API_URL=http://localhost:8000 is fine for local dev)

# Start the frontend dev server
npm run dev
```

Frontend will be running at: **http://localhost:5173**

---

## 🔑 AI Features Setup

To enable AI features (resume analysis, ATS scoring, interview questions), add an API key to your `.env`:

### Google Gemini (Recommended - Free tier available)
```
LLM_PROVIDER=google
GEMINI_API_KEY=your-key-from-aistudio.google.com
```

### OpenAI
```
LLM_PROVIDER=openai
OPENAI_API_KEY=your-openai-key
```

### Anthropic Claude
```
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your-anthropic-key
```

> ⚠️ Without an AI API key, the system still works but AI features return placeholder responses.

---

## Features

### ✅ Authentication
- Register / Login
- JWT with refresh tokens
- Profile management

### ✅ Resume Management
- Upload PDF resumes
- Create resumes with builder
- Multi-resume support
- Version history

### ✅ AI Resume Analysis
- ATS score calculation
- Missing keywords analysis
- AI-powered suggestions
- Resume optimization

### ✅ Job Search
- Browse job listings
- Search by title/company
- Save jobs to bookmark list
- Real job data from Greenhouse/Lever APIs (admin can trigger ingestion)

### ✅ Application Tracking
- Track all job applications
- Status updates (Applied → Interview → Offer/Rejected)
- Notes and next steps
- Application statistics

### ✅ Interview Preparation
- AI-generated practice questions
- Mock interview sessions
- AI feedback and scoring
- Session history

### ✅ Analytics Dashboard
- Real application statistics
- Resume score tracking
- Interview rate metrics
- Activity feed

### ✅ Notifications
- In-app notifications for key events
- Auto-refresh every 30 seconds

---

## API Documentation

Once the backend is running, visit: **http://localhost:8000/docs**

This shows all available API endpoints with interactive testing.

---

## Running Tests

The backend includes a test suite covering auth, resumes, jobs, applications, users, and analytics.

```bash
cd Backend

# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run all tests
pytest tests/ -v

# Run a specific test file
pytest tests/test_auth.py -v

# Run with coverage report
pip install pytest-cov
pytest tests/ --cov=app --cov-report=term-missing
```

Test files:
- `tests/test_auth.py` — Register, login, logout, token validation
- `tests/test_resumes.py` — Resume CRUD, upload, ATS endpoints
- `tests/test_jobs.py` — Job listing, search, save, applications CRUD
- `tests/test_users.py` — Profile get/update, dashboard stats, notifications
- `tests/test_analytics.py` — Analytics with various time ranges
- `tests/test_interview.py` — Interview sessions, question generation

---

## Project Structure

```
GrobsAI/
├── Backend/
│   ├── app/
│   │   ├── core/          # Config, security, exceptions
│   │   ├── models/        # SQLAlchemy models
│   │   ├── routers/       # API endpoints
│   │   ├── services/      # Business logic
│   │   ├── workers/       # Background tasks
│   │   └── main.py        # App entry point
│   ├── .env.example
│   ├── requirements.txt
│   └── setup.py
│
└── Frontend/
    ├── src/
    │   ├── components/    # Shared components
    │   ├── context/       # React contexts
    │   ├── features/      # Feature modules
    │   ├── layouts/       # Page layouts
    │   ├── pages/         # Route pages
    │   ├── routes/        # App routing
    │   └── services/      # API client
    ├── .env.example
    └── package.json
```

---

## Troubleshooting

### Backend won't start
- Make sure venv is activated
- Check all required packages are installed: `pip install -r requirements.txt`
- Verify `.env` exists with `SECRET_KEY` set

### Frontend shows "Failed to load"
- Make sure backend is running on port 8000
- Check `VITE_API_URL` in frontend `.env` matches backend URL
- Look at browser console for CORS errors

### No jobs showing
- Run `python setup.py` to seed sample jobs
- Or use the admin job ingestion endpoint: `POST /api/jobs/ingest` (requires admin account)

### AI features not working
- Add your API key to backend `.env`
- Set the correct `LLM_PROVIDER` for your key
- Check backend logs for AI-related errors

### Database errors
- Delete `grobs.db` and run `python setup.py` again
- This creates a fresh database

---

## Production Deployment

For production:
1. Use PostgreSQL instead of SQLite
2. Set strong `SECRET_KEY` and `REFRESH_SECRET_KEY`
3. Set `ENVIRONMENT=production`
4. Configure a proper SMTP server for emails
5. Use environment variables, not `.env` file
6. Run behind nginx/traefik with HTTPS

---

## Development Notes

- Backend auto-reloads on file changes with `--reload` flag
- Frontend hot-reloads automatically with Vite
- SQLite database file: `Backend/grobs.db`
- Uploaded resumes stored in: `Backend/uploads/`
- API docs: http://localhost:8000/docs
