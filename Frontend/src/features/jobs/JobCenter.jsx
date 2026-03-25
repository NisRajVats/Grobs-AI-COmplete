import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Bookmark, ClipboardList, Calendar, ChevronRight, Sparkles, Target, Zap } from 'lucide-react';
import { motion } from 'framer-motion';

const JobCenter = () => {
  const navigate = useNavigate();

  const features = [
    { 
      id: 'search',
      icon: Search, 
      title: 'Job Search', 
      desc: 'Explore thousands of opportunities with AI matching',
      path: '/app/jobs/search',
      color: 'bg-blue-600'
    },
    { 
      id: 'recommended',
      icon: Sparkles, 
      title: 'Recommended Jobs', 
      desc: 'AI-tailored matches based on your unique profile',
      path: '/app/jobs/recommended',
      color: 'bg-indigo-600'
    },
    { 
      id: 'saved',
      icon: Bookmark, 
      title: 'Saved Jobs', 
      desc: 'Your curated list of potential opportunities',
      path: '/app/jobs/saved',
      color: 'bg-amber-600'
    },
    { 
      id: 'applications',
      icon: ClipboardList, 
      title: 'Application Tracker', 
      desc: 'Manage and track your pipeline in a smart Kanban view',
      path: '/app/jobs/applications',
      color: 'bg-emerald-600'
    },
  ];

  return (
    <div className="space-y-8">
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold text-white">Job Center</h1>
        <p className="text-slate-400 text-lg max-w-2xl mx-auto">
          Find your dream job, track applications, and manage your job search all in one place.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {features.map((feature, idx) => (
          <motion.div
            key={feature.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.1 }}
            onClick={() => navigate(feature.path)}
            className="card-glass p-8 cursor-pointer hover:bg-white/10 transition-all group border-white/5 hover:border-blue-500/30"
          >
            <div className="flex items-start gap-6">
              <div className={`w-16 h-16 ${feature.color} rounded-2xl flex items-center justify-center shadow-lg shrink-0`}>
                <feature.icon size={32} className="text-white" />
              </div>
              <div className="flex-1">
                <h3 className="text-xl font-bold text-white group-hover:text-blue-400 transition-colors flex items-center gap-2">
                  {feature.title}
                  <ChevronRight size={20} className="opacity-0 group-hover:opacity-100 transition-opacity -translate-x-2 group-hover:translate-x-0" />
                </h3>
                <p className="text-slate-400 mt-2">{feature.desc}</p>
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      <div className="card-glass p-8 border-blue-500/20">
        <div className="flex items-center gap-4 mb-6">
          <div className="w-12 h-12 bg-blue-600/20 rounded-xl flex items-center justify-center">
            <Sparkles size={24} className="text-blue-400" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-white">AI-Powered Job Matching</h3>
            <p className="text-slate-400">We analyze your resume to find the best matching jobs</p>
          </div>
        </div>
        <div className="flex gap-4">
          <button onClick={() => navigate('/app/resumes')} className="px-6 py-3 bg-slate-800 text-white font-bold rounded-xl hover:bg-slate-700 transition-all">
            Upload Resume
          </button>
          <button onClick={() => navigate('/app/jobs/recommended')} className="px-6 py-3 bg-blue-600 text-white font-bold rounded-xl hover:bg-blue-500 transition-all">
            Browse Jobs
          </button>
        </div>
      </div>
    </div>
  );
};

export default JobCenter;

