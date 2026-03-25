# GrobsAI Frontend

A modern React-based frontend application for GrobsAI - an AI-powered career development platform that helps users optimize their resumes, find matching jobs, and prepare for interviews.

## 🚀 Features

### Resume Management
- **Resume Builder**: Create professional resumes with an intuitive builder
- **Resume Upload**: Upload existing resumes (PDF, DOCX) for parsing
- **ATS Analysis**: Analyze resumes against job descriptions for ATS compatibility
- **Resume Optimization**: Get AI-powered suggestions to improve your resume
- **Resume Preview**: Preview resumes in multiple formats

### Job Center
- **Job Search**: Search and discover new job opportunities
- **Job Recommendations**: Get personalized job matches based on your resume
- **Saved Jobs**: Bookmark jobs for later
- **Application Tracker**: Track all your job applications in one place

### Interview Preparation
- **Interview Prep**: Comprehensive interview preparation resources
- **Practice Questions**: Access categorized practice questions by topic
- **Mock Interviews**: Practice with AI-generated mock interviews and get feedback

### Profile & Settings
- **Profile Management**: View and edit your profile information
- **Dashboard**: Overview of your job search progress and stats
- **Settings**: Customize your account preferences

### Admin Dashboard
- User management
- System analytics
- Content moderation

## 📋 Prerequisites

Before running the application, ensure you have the following installed:

- **Node.js** (v18 or higher)
- **npm** or **yarn**
- **GrobsAI Backend** running (see [Backend Setup](../Backend/README.md))

## 🛠️ Installation

1. **Clone the repository**

```bash
git clone <repository-url>
cd Frontend
```

2. **Install dependencies**

```bash
npm install
```

Or if you prefer yarn:

```bash
yarn install
```

3. **Environment Configuration**

Create a `.env` file in the root directory:

```env
# API Configuration
VITE_API_URL=http://localhost:8000

# Optional: Theme Configuration
VITE_DEFAULT_THEME=dark
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API base URL | `http://localhost:8000` |
| `VITE_DEFAULT_THEME` | Default theme (light/dark) | `dark` |

### API Integration

The frontend communicates with the GrobsAI backend API. Ensure the backend is running and accessible. See [Backend Architecture](../docs/backend_architecture.md) for more details on API endpoints.

## 🏃 Running the Application

### Development Mode

```bash
npm run dev
```

The application will start at `http://localhost:5173` (default Vite port).

### Production Build

```bash
npm run build
```

The build output will be in the `dist` directory.

### Preview Production Build

```bash
npm run preview
```

## 📚 API Reference

The frontend uses a centralized API service located at `src/services/api.js`. Here's an overview of available API modules:

### Authentication (`authAPI`)
- `login(username, password)` - User login
- `register(email, password)` - User registration
- `logout(refreshToken)` - User logout
- `getCurrentUser()` - Get current user info
- `changePassword(oldPassword, newPassword)` - Change password

### Users (`usersAPI`)
- `getProfile()` - Get user profile
- `updateProfile(data)` - Update profile information
- `getDashboardStats()` - Get dashboard statistics

### Resumes (`resumeAPI`)
- `getResumes()` - List all resumes
- `getResume(id)` - Get resume details
- `createResume(data)` - Create a new resume
- `updateResume(id, data)` - Update resume
- `deleteResume(id)` - Delete resume
- `uploadResume(file, title, targetRole)` - Upload resume file
- `parseResume(id)` - Parse uploaded resume
- `getAtsScore(id, jobDescription)` - Get ATS compatibility score
- `getJobRecommendations(id, limit)` - Get job recommendations
- `atsCheck(id, jobDescription)` - Full ATS check
- `optimizeResume(id, optimizationType)` - Optimize resume

### Interviews (`interviewAPI`)
- `generateQuestions(data)` - Generate interview questions
- `createSession(data)` - Create mock interview session
- `getSessions(status, limit)` - List interview sessions
- `getSession(id)` - Get session details
- `submitAnswer(sessionId, data)` - Submit interview answer
- `getFeedback(sessionId, questionId)` - Get AI feedback
- `completeSession(id)` - Complete interview session

### Jobs (`jobsAPI`)
- `getJobs(skip, limit)` - List all jobs
- `getJob(id)` - Get job details
- `searchJobs(query, limit)` - Search jobs
- `getJobRecommendations(resumeId, limit)` - Get resume-matched jobs
- `saveJob(jobId)` - Save a job
- `unsaveJob(jobId)` - Remove saved job

### Applications (`applicationsAPI`)
- `getApplications(statusFilter)` - List applications
- `getApplication(id)` - Get application details
- `createApplication(data)` - Create new application
- `updateApplication(id, data)` - Update application
- `deleteApplication(id)` - Delete application
- `getApplicationStats()` - Get application statistics

For complete API documentation, see the [Backend API Documentation](../docs/backend_architecture.md).

## 📁 Project Structure

```
Frontend/
├── public/                  # Static assets
├── src/
│   ├── app/                # App configuration
│   ├── assets/            # Images, icons, fonts
│   ├── components/        # Reusable React components
│   │   ├── layout/        # Layout components (Sidebar, Topbar)
│   │   └── ui/            # UI components
│   ├── context/           # React contexts (Auth, Theme)
│   ├── features/          # Feature modules
│   │   ├── admin/         # Admin dashboard
│   │   ├── ai/            # AI chat feature
│   │   ├── analytics/     # Analytics dashboard
│   │   ├── applications/  # Application tracking
│   │   ├── auth/          # Authentication
│   │   ├── calendar/      # Calendar view
│   │   ├── dashboard/     # Main dashboard
│   │   ├── interview/     # Interview preparation
│   │   ├── jobs/          # Job center
│   │   ├── profile/       # Profile management
│   │   ├── resume/        # Resume management
│   │   └── subscriptions/  # Subscription management
│   ├── hooks/             # Custom React hooks
│   ├── layouts/           # Route layouts
│   ├── pages/             # Page components
│   ├── providers/         # React providers
│   ├── routes/            # Route definitions
│   ├── services/          # API services
│   ├── styles/            # Global styles
│   └── utils/             # Utility functions
├── index.html              # Entry HTML
├── package.json            # Dependencies
├── tailwind.config.js      # Tailwind configuration
└── vite.config.js          # Vite configuration
```

## 🔧 Technology Stack

- **Framework**: React 19
- **Build Tool**: Vite 7
- **Styling**: Tailwind CSS 4
- **Routing**: React Router DOM 7
- **HTTP Client**: Axios
- **State Management**: React Context
- **Animations**: Framer Motion
- **Charts**: Recharts
- **Internationalization**: i18next
- **Icons**: Lucide React

## 🚢 Deployment

### Building for Production

1. Run the build command:
```bash
npm run build
```

2. The production-ready files will be in the `dist` directory.

### Deployment Options

#### Static Hosting
The frontend can be deployed to any static hosting service:

- **Vercel**: `npm i -g vercel && vercel`
- **Netlify**: Drag and drop the `dist` folder
- **AWS S3 + CloudFront**: Upload `dist` to S3 bucket
- **GitHub Pages**: Use GitHub Actions

#### Docker (Optional)

Create a `Dockerfile`:

```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

Build and run:
```bash
docker build -t grobsai-frontend .
docker run -p 80:80 grobsai-frontend
```

## 🔐 Security

- JWT token-based authentication
- Token stored in localStorage
- Automatic token refresh via interceptors
- Protected routes with authentication guards
- CORS configuration on backend

## 🧪 Development

### Code Style

The project uses ESLint for code linting:

```bash
npm run lint
```

### Adding New Features

1. Create feature components in `src/features/`
2. Add routes in `src/routes/AppRoutes.jsx`
3. Add API endpoints in `src/services/api.js`
4. Update navigation in `src/components/layout/Sidebar.jsx`

## 📖 Additional Documentation

- [Backend Architecture](../docs/backend_architecture.md) - Complete backend system architecture
- [AI Pipeline](../docs/ai_pipeline_diagram.md) - AI processing workflows
- [Database Schema](../docs/database_diagram.md) - Data models and relationships
- [User Flow](../docs/user_flow_diagram.md) - User journey and interactions
- [Security](../docs/security_diagram.md) - Security controls and measures
- [Deployment](../docs/deployment_diagram.md) - Infrastructure and deployment

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is part of GrobsAI. See the main repository for license information.

---

*For technical support and questions, please refer to the main project documentation or create an issue in the repository.*

