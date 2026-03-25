import React, { Suspense, lazy } from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import AppLayout from '../layouts/AppLayout/AppLayout';
import { useAuth } from '../context/AuthContext';

// Lazy load components
const LandingPage = lazy(() => import('../pages/LandingPage'));
const LoginPage = lazy(() => import('../pages/LoginPage'));
const RegisterPage = lazy(() => import('../pages/RegisterPage'));

// Dashboard
const Dashboard = lazy(() => import('../features/dashboard/Dashboard'));

// Resume Center Modules
const MyResumes = lazy(() => import('../features/resume/MyResumes'));
const ResumeBuilder = lazy(() => import('../features/resume/ResumeBuilder'));
const ResumeUpload = lazy(() => import('../features/resume/ResumeUpload'));
const ResumeDetail = lazy(() => import('../features/resume/ResumeDetail'));
const ATSAnalysis = lazy(() => import('../features/resume/ATSAnalysis'));
const OptimizeResume = lazy(() => import('../features/resume/OptimizeResume'));
const ResumePreview = lazy(() => import('../features/resume/ResumePreview'));
const ResumeEdit = lazy(() => import('../features/resume/ResumeEdit'));

// Job Center Modules
const JobCenter = lazy(() => import('../features/jobs/JobCenter'));
const JobSearch = lazy(() => import('../features/jobs/JobSearch'));
const RecommendedJobs = lazy(() => import('../features/jobs/RecommendedJobs'));
const SavedJobs = lazy(() => import('../features/jobs/SavedJobs'));
const ApplicationTracker = lazy(() => import('../features/jobs/ApplicationTracker'));

// Interview Prep Modules
const InterviewPrep = lazy(() => import('../features/interview/InterviewPrep'));
const PracticeQuestions = lazy(() => import('../features/interview/PracticeQuestions'));
const MockInterview = lazy(() => import('../features/interview/MockInterview'));

// Profile Modules
const Profile = lazy(() => import('../features/profile/Profile'));
const ProfileEdit = lazy(() => import('../features/profile/ProfileEdit'));
const Settings = lazy(() => import('../pages/Settings'));

// Legacy/Admin (kept for backward compatibility)
const AIChat = lazy(() => import('../features/ai/AIChat'));
const AnalyticsDashboard = lazy(() => import('../features/analytics/AnalyticsDashboard'));
const EvaluationPage = lazy(() => import('../features/evaluation/EvaluationPage'));
const AdminLayout = lazy(() => import('../layouts/AdminLayout/AdminLayout'));
const AdminDashboard = lazy(() => import('../features/admin/AdminDashboard'));

const LoadingFallback = () => (
  <div className="flex items-center justify-center min-h-screen">
    <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
  </div>
);

// Protected Route Wrapper
const ProtectedRoute = ({ children }) => {
  const { isLoggedIn, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return <LoadingFallback />;
  }

  if (!isLoggedIn) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
};

// Public Route Wrapper (redirects to dashboard if already logged in)
const PublicRoute = ({ children }) => {
  const { isLoggedIn, loading } = useAuth();

  if (loading) {
    return <LoadingFallback />;
  }

  if (isLoggedIn) {
    return <Navigate to="/app/dashboard" replace />;
  }

  return children;
};

const AppRoutes = () => {
  return (
    <Suspense fallback={<LoadingFallback />}>
      <Routes>
        {/* Public Routes */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/features" element={<LandingPage />} />
        <Route path="/pricing" element={<LandingPage />} />
        <Route path="/about" element={<LandingPage />} />
        
        {/* Auth Routes */}
        <Route path="/login" element={
          <PublicRoute>
            <LoginPage />
          </PublicRoute>
        } />
        <Route path="/register" element={
          <PublicRoute>
            <RegisterPage />
          </PublicRoute>
        } />
        <Route path="/forgot-password" element={
          <PublicRoute>
            <LoginPage />
          </PublicRoute>
        } />
        
        {/* App Routes - Main Layout */}
        <Route path="/app" element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }>
          <Route index element={<Navigate to="dashboard" replace />} />
          
          {/* Dashboard */}
          <Route path="dashboard" element={<Dashboard />} />
          
          {/* Resume Center */}
          <Route path="resumes" element={<MyResumes />} />
          <Route path="resumes/create" element={<ResumeBuilder />} />
          <Route path="resumes/upload" element={<ResumeUpload />} />
          <Route path="resumes/:resumeId" element={<ResumeDetail />} />
          <Route path="resumes/:resumeId/ats" element={<ATSAnalysis />} />
          <Route path="resumes/:resumeId/optimize" element={<Navigate to="../" relative="path" replace />} />
          <Route path="resumes/:resumeId/preview" element={<ResumePreview />} />
          <Route path="resumes/:resumeId/edit" element={<ResumeEdit />} />
          <Route path="resumes/:resumeId/jobs" element={<JobSearch />} />
          
          {/* Legacy resume routes - redirect to new structure */}
          <Route path="resume-builder" element={<Navigate to="/app/resumes/create" replace />} />
          <Route path="resume-parser" element={<Navigate to="/app/resumes" replace />} />
          <Route path="ats-checker" element={<Navigate to="/app/resumes" replace />} />
          
          {/* Job Center */}
          <Route path="jobs" element={<JobCenter />} />
          <Route path="jobs/recommended" element={<RecommendedJobs />} />
          <Route path="jobs/saved" element={<SavedJobs />} />
          <Route path="jobs/applications" element={<JobSearch />} />
          <Route path="jobs/tracker" element={<ApplicationTracker />} />
          
          {/* Legacy job routes */}
          <Route path="saved-jobs" element={<Navigate to="/app/jobs/saved" replace />} />
          <Route path="applications" element={<Navigate to="/app/jobs/tracker" replace />} />
          
          {/* Interview Preparation */}
          <Route path="interview" element={<InterviewPrep />} />
          <Route path="interview/questions" element={<PracticeQuestions />} />
          <Route path="interview/mock" element={<MockInterview />} />
          
          {/* Legacy interview route */}
          <Route path="interview-prep" element={<Navigate to="/app/interview" replace />} />
          
          {/* Profile & Settings */}
          <Route path="profile" element={<Profile />} />
          <Route path="profile/edit" element={<ProfileEdit />} />
          <Route path="settings" element={<Settings />} />
          
          {/* Legacy/Extra routes */}
          <Route path="ai-chat" element={<AIChat />} />
          <Route path="analytics" element={<AnalyticsDashboard />} />
          <Route path="evaluation" element={<EvaluationPage />} />
        </Route>

        {/* Admin Routes */}
        <Route path="/admin" element={
          <ProtectedRoute>
            <AdminLayout />
          </ProtectedRoute>
        }>
          <Route index element={<Navigate to="dashboard" replace />} />
          <Route path="dashboard" element={<AdminDashboard />} />
          <Route path="stats" element={<AdminDashboard />} />
          <Route path="users" element={<AdminDashboard />} />
          <Route path="resumes" element={<AdminDashboard />} />
          <Route path="jobs" element={<AdminDashboard />} />
          <Route path="system" element={<AdminDashboard />} />
          <Route path="settings" element={<AdminDashboard />} />
        </Route>

        {/* 404 Route */}
        <Route path="*" element={<Navigate to="/app/dashboard" replace />} />
      </Routes>
    </Suspense>
  );
};

export default AppRoutes;
