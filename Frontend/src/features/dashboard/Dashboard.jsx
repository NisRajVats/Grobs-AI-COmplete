import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Rocket, 
  ChevronRight, 
  FileText, 
  Briefcase, 
  Zap, 
  UserCircle,
  Target,
  Sparkles,
  TrendingUp,
  Clock,
  ArrowRight,
  Building2,
  MapPin,
  Loader2
} from 'lucide-react';
import { motion } from 'framer-motion';
import { usersAPI, authAPI, resumeAPI, jobsAPI } from '../../services/api';

const Dashboard = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [user, setUser] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [loadingRecs, setLoadingRecs] = useState(false);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const [statsRes, userRes] = await Promise.all([
          usersAPI.getDashboardStats(),
          authAPI.getCurrentUser()
        ]);
        setStats(statsRes.data);
        setUser(userRes.data);
        
        // Fetch recommendations if user has resumes
        if (statsRes.data.total_resumes > 0) {
          fetchTopRecommendations();
        }
      } catch (error) {
        console.error("Error fetching dashboard data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  const fetchTopRecommendations = async () => {
    setLoadingRecs(true);
    try {
      const resumesRes = await resumeAPI.getResumes();
      if (resumesRes.data && resumesRes.data.length > 0) {
        const latestResumeId = resumesRes.data[0].id;
        const recsRes = await jobsAPI.getJobRecommendations(latestResumeId, 3);
        setRecommendations(recsRes.data.recommendations || []);
      }
    } catch (err) {
      console.error("Error fetching recommendations:", err);
    } finally {
      setLoadingRecs(false);
    }
  };

  const mainSections = [
    {
      id: 'resume',
      icon: FileText,
      title: 'Resume Center',
      description: 'Manage resumes, check ATS scores, and optimize for jobs',
      path: '/app/resumes',
      color: 'from-blue-600 to-blue-700',
      bgPattern: 'bg-blue-600/10'
    },
    {
      id: 'jobs',
      icon: Briefcase,
      title: 'Job Center',
      description: 'Find jobs, track applications, and manage your search',
      path: '/app/jobs',
      color: 'from-amber-600 to-amber-700',
      bgPattern: 'bg-amber-600/10'
    },
    {
      id: 'interview',
      icon: Zap,
      title: 'Interview Prep',
      description: 'Practice questions and mock interviews',
      path: '/app/interview',
      color: 'from-green-600 to-green-700',
      bgPattern: 'bg-green-600/10'
    },
    {
      id: 'profile',
      icon: UserCircle,
      title: 'Profile & Settings',
      description: 'Manage your account and preferences',
      path: '/app/profile',
      color: 'from-purple-600 to-purple-700',
      bgPattern: 'bg-purple-600/10'
    }
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  const statsData = [
    { label: 'Total Resumes', value: stats?.total_resumes || 0, icon: FileText, color: 'text-orange-400', bg: 'bg-orange-400/10' },
    { label: 'Avg. ATS Score', value: `${Math.round(stats?.avg_ats_score || 0)}%`, icon: Target, color: 'text-blue-400', bg: 'bg-blue-400/10' },
    { label: 'Applications', value: stats?.total_applications || 0, icon: Briefcase, color: 'text-rose-400', bg: 'bg-rose-400/10' },
    { label: 'Saved Jobs', value: stats?.total_saved_jobs || 0, icon: Sparkles, color: 'text-teal-400', bg: 'bg-teal-400/10' },
  ];

  return (
    <div className="space-y-8">
      {/* Welcome Card */}
      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="relative overflow-hidden card-glass p-8 md:p-10 border-0 flex flex-col md:flex-row items-center justify-between gap-8 group"
      >
        <div className="absolute inset-0 bg-linear-to-r from-blue-600/30 to-indigo-600/20 -z-10 opacity-60 group-hover:opacity-80 transition-opacity"></div>
        <div className="absolute top-0 right-0 -mr-20 -mt-20 w-96 h-96 bg-blue-500/20 blur-[100px] rounded-full"></div>
        
        <div className="relative z-10 flex-1 space-y-4 text-center md:text-left">
          <h1 className="text-4xl md:text-5xl font-bold text-white tracking-tight">Welcome Back, <span className="text-blue-400">{user?.full_name || user?.email?.split('@')[0] || 'User'}!</span></h1>
          <p className="text-xl text-slate-300">Ready to boost your career with AI?</p>
          <div className="flex flex-wrap items-center justify-center md:justify-start gap-4 pt-4">
            <button onClick={() => navigate('/app/resumes')} className="px-6 py-3 bg-blue-600 text-white font-bold rounded-2xl hover:bg-blue-500 transition-all flex items-center gap-2">
              Get Started <ArrowRight size={18} />
            </button>
          </div>
        </div>

        <div className="relative z-10 shrink-0 hidden md:block">
          <motion.div
            animate={{ y: [0, -15, 0] }}
            transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
          >
            <Rocket className="w-32 h-32 md:w-48 md:h-48 text-white fill-white drop-shadow-[0_0_50px_rgba(59,130,246,0.6)]" />
          </motion.div>
        </div>
      </motion.div>

      {/* Main Navigation Sections */}
      <div>
        <h2 className="text-xl font-bold text-white mb-4">Quick Access</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {mainSections.map((section, idx) => (
            <motion.div
              key={section.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.1 }}
              onClick={() => navigate(section.path)}
              whileHover={{ y: -4, scale: 1.02 }}
              className={`card-glass p-6 cursor-pointer hover:bg-white/10 transition-all group ${section.bgPattern}`}
            >
              <div className={`w-12 h-12 bg-linear-to-br ${section.color} rounded-xl flex items-center justify-center mb-4 shadow-lg`}>
                <section.icon size={24} className="text-white" />
              </div>
              <h3 className="text-lg font-bold text-white group-hover:text-blue-400 transition-colors">{section.title}</h3>
              <p className="text-sm text-slate-400 mt-2 line-clamp-2">{section.description}</p>
              <div className="mt-4 flex items-center text-blue-400 text-sm font-bold opacity-0 group-hover:opacity-100 transition-opacity">
                Go to section <ChevronRight size={16} />
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Recommended Jobs Preview */}
      <div className="space-y-4">
        <div className="flex items-center justify-between px-2">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Sparkles className="text-blue-400" size={20} />
            Recommended for You
          </h2>
          <button 
            onClick={() => navigate('/app/jobs/recommended')}
            className="text-sm font-bold text-blue-400 hover:text-blue-300 transition-colors flex items-center gap-1"
          >
            View All <ArrowRight size={16} />
          </button>
        </div>

        {loadingRecs ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[1, 2, 3].map(i => (
              <div key={i} className="card-glass p-6 animate-pulse space-y-4">
                <div className="flex gap-4">
                  <div className="w-12 h-12 bg-slate-800 rounded-xl shrink-0"></div>
                  <div className="flex-1 space-y-2">
                    <div className="h-4 bg-slate-800 rounded w-3/4"></div>
                    <div className="h-3 bg-slate-800 rounded w-1/2"></div>
                  </div>
                </div>
                <div className="h-3 bg-slate-800 rounded w-full mt-4"></div>
              </div>
            ))}
          </div>
        ) : recommendations.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {recommendations.map((match, idx) => (
              <motion.div
                key={match.job.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.2 + idx * 0.1 }}
                onClick={() => window.open(match.job.job_link, '_blank')}
                className="card-glass p-6 cursor-pointer hover:bg-white/10 transition-all border-white/5 group relative overflow-hidden"
              >
                <div className="absolute top-0 right-0 p-2">
                  <div className="bg-green-500/10 text-green-400 text-[10px] font-black px-2 py-0.5 rounded-lg border border-green-500/20">
                    {match.match_score}% MATCH
                  </div>
                </div>
                <div className="flex items-start gap-4 mb-4">
                  <div className="w-12 h-12 bg-white rounded-xl flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform shrink-0">
                    <Building2 size={24} className="text-slate-900" />
                  </div>
                  <div className="min-w-0">
                    <h4 className="font-bold text-white truncate group-hover:text-blue-400 transition-colors">{match.job.job_title}</h4>
                    <p className="text-xs text-slate-400 truncate">{match.job.company_name}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3 text-[10px] text-slate-500 font-bold uppercase tracking-wider">
                  <span className="flex items-center gap-1"><MapPin size={12} /> {match.job.location || 'Remote'}</span>
                  <span className="flex items-center gap-1"><Briefcase size={12} /> {match.job.job_type || 'Full-time'}</span>
                </div>
              </motion.div>
            ))}
          </div>
        ) : (
          <div className="card-glass p-8 text-center border-dashed border-white/10">
            <p className="text-slate-400 text-sm mb-4">
              {stats?.total_resumes > 0 
                ? "No personalized matches found yet. Try updating your resume details."
                : "Upload your resume to see personalized job matches here."}
            </p>
            <button 
              onClick={() => navigate(stats?.total_resumes > 0 ? '/app/resumes' : '/app/resumes/upload')}
              className="px-4 py-2 bg-blue-600/20 text-blue-400 border border-blue-500/30 rounded-xl text-xs font-bold hover:bg-blue-600/30 transition-all"
            >
              {stats?.total_resumes > 0 ? "Manage Resumes" : "Upload Resume"}
            </button>
          </div>
        )}
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {statsData.map((stat, i) => (
          <motion.div 
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 + i * 0.1 }}
            className="card-glass p-5 hover:-translate-y-0.5 transition-all"
          >
            <div className="flex items-center gap-3">
              <div className={`p-2.5 rounded-xl ${stat.bg} ${stat.color}`}>
                <stat.icon size={20} />
              </div>
              <div>
                <p className="text-xs text-slate-500 font-medium">{stat.label}</p>
                <p className="text-xl font-bold text-white">{stat.value}</p>
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="card-glass p-6">
        <h3 className="text-lg font-bold text-white mb-4">Quick Actions</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <button onClick={() => navigate('/app/resumes/upload')} className="p-4 bg-slate-900/50 border border-white/5 rounded-xl text-left hover:bg-blue-600/20 hover:border-blue-500/30 transition-all group">
            <FileText size={20} className="text-blue-400 mb-2 group-hover:text-blue-300" />
            <p className="text-sm font-bold text-white">Upload Resume</p>
          </button>
          <button onClick={() => navigate('/app/resumes')} className="p-4 bg-slate-900/50 border border-white/5 rounded-xl text-left hover:bg-amber-600/20 hover:border-amber-500/30 transition-all group">
            <Target size={20} className="text-amber-400 mb-2 group-hover:text-amber-300" />
            <p className="text-sm font-bold text-white">Check ATS Score</p>
          </button>
          <button onClick={() => navigate('/app/jobs')} className="p-4 bg-slate-900/50 border border-white/5 rounded-xl text-left hover:bg-green-600/20 hover:border-green-500/30 transition-all group">
            <Briefcase size={20} className="text-green-400 mb-2 group-hover:text-green-300" />
            <p className="text-sm font-bold text-white">Find Jobs</p>
          </button>
          <button onClick={() => navigate('/app/interview')} className="p-4 bg-slate-900/50 border border-white/5 rounded-xl text-left hover:bg-purple-600/20 hover:border-purple-500/30 transition-all group">
            <Zap size={20} className="text-purple-400 mb-2 group-hover:text-purple-300" />
            <p className="text-sm font-bold text-white">Practice Interview</p>
          </button>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
