# GrobsAI - AI-Powered Career Ecosystem

**GrobsAI** is a comprehensive, full-stack AI career platform engineered to revolutionize the job application lifecycle. By leveraging state-of-the-art Large Language Models (LLMs) and vector embeddings, the platform provides users with high-fidelity resume optimization, ATS-aligned scoring, personalized job matching, and real-time AI-driven interview preparation.

---

## 🏗️ System Architecture & Methodology

GrobsAI follows a modular, **service-oriented three-tier architecture** designed for high scalability, security, and maintainability.

### 1. Frontend: High-Performance React 19
- **Framework**: Built with **React 19** and **Vite** for optimized build times and modern rendering patterns.
- **State Management**: Context-based authentication (`AuthContext`) with JWT persistence and Axios-based API service layer.
- **UI/UX**: Styled with **Tailwind CSS** and **Framer Motion** for a fluid, interactive experience.
- **Data Visualization**: Real-time analytics dashboards using **Recharts** to visualize application trends and skill gaps.

### 2. Backend: Asynchronous FastAPI Orchestration
- **API Layer**: **FastAPI** provides a high-performance, asynchronous RESTful API with Pydantic-driven data validation.
- **ORM & Database**: **SQLAlchemy** with **Alembic** migrations, supporting **PostgreSQL** for production and **SQLite** for development.
- **Background Workers**: **Celery** with **Redis** handles heavy computational tasks like resume parsing and PDF generation asynchronously to ensure a responsive UI.

### 3. AI Service Layer: Unified LLM Orchestration
- **Abstraction Layer**: A **Unified LLM Service** provides a consistent interface for **Google Gemini**, **OpenAI (GPT-4o)**, and **Anthropic (Claude 3.5)**.
- **Semantic Matchmaking**: Job-to-resume matching using **vector embeddings** generated via **HuggingFace (Sentence-Transformers)** or OpenAI, utilizing **Cosine Similarity** for contextual relevance.
- **Hybrid Scoring**: Combines heuristic rule-based patterns with LLM analysis for robust ATS scoring.

---

## 🌟 Core Features & Modules

### 📄 Intelligent Resume Management
- **Asynchronous Parsing**: Uses `pdfplumber` for high-fidelity text extraction followed by an AI-driven normalization pipeline.
- **Resume Builder**: Modular, section-by-section builder for creating ATS-optimized resumes from scratch.
- **ATS Optimizer**: Analyzes tone, grammar, and keyword gaps against target job descriptions to provide actionable feedback.

### 🎯 Job Center & Matchmaking
- **Semantic Discovery**: Ranks job listings based on contextual alignment with user profiles rather than simple keyword matching.
- **Application Tracking**: A **Kanban-style board** implementing full CRUD operations for managing the job application pipeline (Applied → Interview → Offer).

### 🎤 AI-Driven Interview Preparation
- **Contextual Practice**: Generates practice questions tailored to specific job roles and user experience.
- **Real-time Feedback**: Provides AI-powered analysis of interview responses, focusing on clarity, technical depth, and delivery.

### 📈 Analytics & Career Insights
- **Skill Gap Analysis**: Visualizes the alignment between user skills and target industry requirements.
- **Engagement Metrics**: Tracks application success rates and profile visibility.

---

## 🧪 Evaluation & Quality Assurance

GrobsAI includes a rigorous **Evaluation Framework** (`EvaluationService`) that continuously monitors system performance:
- **Completeness**: Automated codebase scanning (Python/React) to track feature implementation progress.
- **Accuracy**: Real-world evaluation using a dataset of 500+ resumes to calibrate ATS scores and NER precision.
- **Latency Monitoring**: Sub-millisecond precision tracking using `perf_counter` to ensure optimal AI response times.

---

## 🚀 Quick Start (Local Development)

### Prerequisites
- **Node.js** (v18+) & **Python** (v3.10+)
- **PostgreSQL** & **Redis** (for background workers)

### 🛠️ Backend Setup
```bash
cd Backend
python -m venv venv
source venv/bin/activate  # venv\Scripts\activate on Windows
pip install -r requirements.txt
python setup.py           # Initialize DB and seed jobs
uvicorn app.main:app --reload
```

### 💻 Frontend Setup
```bash
cd Frontend
npm install
npm run dev
```

---

## 🔒 Security & Privacy
- **Authentication**: JWT-based system with access/refresh token rotation.
- **Data Protection**: Sensitive PII is **encrypted at rest** using Fernet symmetric encryption.
- **Isolation**: Strict CORS policies and Role-Based Access Control (RBAC).

---

## 📖 Related Documentation
- [**Methodology**](./docs/METHODOLOGY.md) - Deep dive into design decisions and algorithms.
- [**Backend Docs**](./Backend/README.md) - Detailed API references and service patterns.
- [**Frontend Docs**](./Frontend/README.md) - Component architecture and design system.

---
*GrobsAI is proprietary software focused on empowering the next generation of professional talent through AI.*
