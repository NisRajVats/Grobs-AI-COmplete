# 5. METHODOLOGY

The development of **GROBS.AI** follows a modular, **service-oriented three-tier architecture** designed for scalability and maintainability. An **Agile methodology** was adopted to facilitate iterative development, continuous testing, and seamless integration of AI capabilities throughout the project lifecycle.

## 5.1 System Architecture Design
The system enforces a strict **separation of concerns** between the frontend, backend, and data layers. The **React 19** frontend, bundled with **Vite**, manages user interactions and state via `AuthContext` with JWT tokens stored securely. The **FastAPI** backend serves as the orchestration layer, encapsulating business logic, RESTful API routing, and a **background worker system** for heavy computational tasks. The data layer utilizes **SQLAlchemy ORM** with **Alembic migrations**, supporting both **SQLite** for local development and **PostgreSQL** for production environments.

## 5.2 Asynchronous Resume Parsing and Extraction
Resume processing is handled through an **asynchronous pipeline**. Uploaded PDF resumes are processed using the `pdfplumber` library for high-fidelity text extraction. A dedicated **background worker** cleans and normalizes the text before passing it through a section identification pipeline. **Named Entity Recognition (NER)** and rule-based patterns extract structured data (education, experience, skills), which are then stored as **encrypted records** in the database to ensure privacy.

## 5.3 Unified AI Service Layer
The platform features a **Unified LLM Service Layer** that provides a consistent interface for multiple AI providers, including **Google Gemini**, **OpenAI (GPT-4o)**, and **Anthropic (Claude 3.5)**. This abstraction allows the system to switch between models for different tasks—such as text generation, structured JSON output, or streaming responses—ensuring high availability and flexibility in AI orchestration.

## 5.4 Semantic Embedding and Matchmaking
Job descriptions and resume content are matched using **vector embeddings** generated via **HuggingFace (Sentence-Transformers)** or **OpenAI embeddings**. By applying **Cosine Similarity** principles, the system ranks job listings based on contextual relevance rather than simple keyword matching. This enables the discovery of semantically related opportunities that traditional ATS systems might overlook.

## 5.5 AI-Driven Resume Optimization
Utilizing the **LLM Service**, the system analyzes the tone, grammar, and structural alignment of resumes against target job descriptions. The **OptimizeResume** module generates actionable feedback, including **ATS keyword gap analysis** and suggestions for stronger action verbs. These insights are delivered via the `/api/resumes/{id}/optimize` endpoint and presented in a categorized, user-friendly interface.

## 5.6 Application Tracking and Management
The platform includes a robust **Application Tracking Module** supported by the `JobApplication` model. It provides full **CRUD operations** for both internal and external job applications. The **Applications.jsx** component implements a **kanban-style board**, allowing users to manage their pipeline (Applied → Interview → Offer/Rejected) with real-time status updates and persistence in the SQLite/PostgreSQL database.

## 5.7 AI Interview Preparation and Chat
A specialized **Interview Prep module** generates context-aware practice questions based on specific job descriptions. Users can engage in **mock interview sessions** with real-time AI feedback. Additionally, a persistent **AI Career Chatbot** leverages conversation history to provide tailored advice on career planning and interview strategies, with a graceful fallback mechanism for offline scenarios.

## 5.8 Security, Privacy, and Encryption
Data security is a core priority. User authentication employs a **JWT-based system** with **access and refresh token rotation**. Sensitive Personal Identifiable Information (PII) is **encrypted at rest** using Fernet symmetric encryption. The backend enforces strict **CORS policies** and **Role-Based Access Control (RBAC)** to ensure data isolation and protect against unauthorized access.

## 5.9 Infrastructure and Integrations
The system integrates several third-party services to provide a complete experience:
- **Stripe**: For subscription and payment processing.
- **SMTP/Email Workers**: For automated notifications and user communications.
- **Cloud Storage**: For secure file handling of uploaded documents.
- **Uvicorn/ASGI**: For high-performance asynchronous serving.

## 5.10 Testing and Quality Assurance
A comprehensive testing strategy is implemented using **pytest**, covering unit and integration tests for all backend API endpoints. The test suite utilizes an **isolated in-memory database** and shared fixtures to validate authentication flows, resume CRUD operations, job matching logic, and analytics accuracy, ensuring a bug-free and reliable user experience.

## 5.11 Real-time Notifications and Analytics
The platform features a **live notification system** that alerts users to status changes and system events. The **Analytics Dashboard** replaces static mock-ups with **live aggregated metrics** using **Recharts**. It visualizes application trends, ATS score distributions, and skill gap charts by querying actual database records, providing users with data-driven career insights.

## 5.12 Resume Builder and Profile Management
The **ResumeBuilder** component allows for modular, section-by-section resume composition. User profiles are managed via the **ProfileEdit** module, which synchronizes personal details, job titles, and professional links with the backend. Functional settings for password management and account security are integrated through dedicated authentication routes, providing a seamless management experience.
