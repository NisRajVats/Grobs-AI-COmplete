import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { MessageSquare, Zap, ChevronRight, Sparkles, Target, BookOpen, Clock, BarChart3, ArrowRight } from 'lucide-react';
import { motion } from 'framer-motion';
import api from '../../services/api';

const InterviewPrep = () => {
  const navigate = useNavigate();
  const [recentSessions, setRecentSessions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchRecentSessions();
  }, []);

  const fetchRecentSessions = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/interview/sessions?limit=5');
      setRecentSessions(response.data);
    } catch (error) {
      console.error("Error fetching recent sessions:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleRoleClick = (role) => {
    // Navigate to mock interview with pre-filled role
    navigate('/app/interview/mock', { state: { target_role: role } });
  };

  const features = [
    { id: 'questions', icon: MessageSquare, title: 'Practice Questions', desc: 'Common interview questions with sample answers', path: '/app/interview/questions', color: 'bg-purple-600', shadow: 'shadow-purple-500/20' },
    { id: 'mock', icon: Zap, title: 'AI Mock Interview', desc: 'Practice with AI-powered mock interviews and get instant feedback', path: '/app/interview/mock', color: 'bg-green-600', shadow: 'shadow-green-500/20' },
    { id: 'analysis', icon: BarChart3, title: 'Performance Analysis', desc: 'Track your progress and identify areas for improvement', path: '/app/analytics', color: 'bg-blue-600', shadow: 'shadow-blue-500/20' },
  ];

  const popularRoles = [
    'Software Engineer', 'Frontend Developer', 'Backend Developer', 
    'Full Stack Developer', 'Product Manager', 'Data Scientist', 'UX Designer',
    'Mobile Developer', 'DevOps Engineer', 'AI Engineer'
  ];

  return (
    <div className="space-y-8 pb-12">
      <div className="relative overflow-hidden rounded-3xl bg-linear-to-br from-blue-600/20 via-slate-900 to-purple-600/20 border border-white/10 p-12 text-center">
        <div className="absolute -top-24 -left-24 w-64 h-64 bg-blue-500/10 rounded-full blur-3xl"></div>
        <div className="absolute -bottom-24 -right-24 w-64 h-64 bg-purple-500/10 rounded-full blur-3xl"></div>
        
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="relative z-10 space-y-4"
        >
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-bold uppercase tracking-wider mb-2">
            <Sparkles size={14} /> AI-Powered Preparation
          </div>
          <h1 className="text-5xl font-black text-white leading-tight">Master Your Next <br /> <span className="text-blue-500">Interview</span></h1>
          <p className="text-slate-400 text-lg max-w-2xl mx-auto">
            Prepare with confidence using our AI-driven interview platform. Get personalized questions based on your resume and real-time feedback on your performance.
          </p>
          <div className="pt-4 flex items-center justify-center gap-4">
            <button onClick={() => navigate('/app/interview/mock')} className="px-8 py-4 bg-blue-600 text-white font-bold rounded-2xl hover:bg-blue-500 transition-all shadow-lg shadow-blue-600/30 flex items-center gap-2">
              Start Mock Interview <ArrowRight size={20} />
            </button>
            <button onClick={() => navigate('/app/interview/questions')} className="px-8 py-4 bg-white/5 text-white font-bold rounded-2xl hover:bg-white/10 border border-white/10 transition-all">
              Practice Questions
            </button>
          </div>
        </motion.div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {features.map((feature, idx) => (
          <motion.div
            key={feature.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 + idx * 0.1 }}
            onClick={() => navigate(feature.path)}
            className="card-glass p-8 cursor-pointer hover:bg-white/10 transition-all group relative overflow-hidden"
          >
            <div className={`w-14 h-14 ${feature.color} rounded-2xl flex items-center justify-center mb-6 shadow-lg ${feature.shadow}`}>
              <feature.icon size={28} className="text-white" />
            </div>
            <h3 className="text-xl font-bold text-white group-hover:text-blue-400 transition-colors">{feature.title}</h3>
            <p className="text-slate-400 mt-2 text-sm leading-relaxed">{feature.desc}</p>
            <div className="mt-6 flex items-center text-blue-400 font-bold text-sm opacity-0 group-hover:opacity-100 transition-all translate-x-[-10px] group-hover:translate-x-0">
              Get Started <ChevronRight size={16} />
            </div>
          </motion.div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          <div className="card-glass p-8">
            <div className="flex items-center gap-4 mb-8">
              <div className="w-12 h-12 bg-blue-600/20 rounded-xl flex items-center justify-center">
                <Target size={24} className="text-blue-400" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-white">Select Your Target Role</h3>
                <p className="text-slate-400">Choose a role to generate specific interview questions</p>
              </div>
            </div>
            <div className="flex flex-wrap gap-3">
              {popularRoles.map((role, idx) => (
                <button 
                  key={idx} 
                  onClick={() => handleRoleClick(role)}
                  className="px-5 py-2.5 bg-slate-900/50 border border-white/10 rounded-full text-slate-300 hover:bg-blue-600 hover:text-white hover:border-blue-500 transition-all text-sm font-semibold"
                >
                  {role}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="card-glass p-6">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <Clock size={20} className="text-blue-400" />
                <h3 className="font-bold text-white">Recent Sessions</h3>
              </div>
              <button onClick={() => navigate('/app/analytics')} className="text-xs font-bold text-blue-400 hover:text-blue-300">View All</button>
            </div>
            
            <div className="space-y-4">
              {loading ? (
                Array(3).fill(0).map((_, i) => (
                  <div key={i} className="h-16 bg-white/5 animate-pulse rounded-xl"></div>
                ))
              ) : recentSessions.length > 0 ? (
                recentSessions.map((session) => (
                  <div 
                    key={session.id} 
                    onClick={() => navigate(`/app/interview/mock/${session.id}`)}
                    className="p-4 bg-white/5 border border-white/5 rounded-xl hover:bg-white/10 transition-all cursor-pointer group"
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <h4 className="font-bold text-white text-sm group-hover:text-blue-400 transition-colors truncate max-w-[150px]">
                          {session.job_title || 'General Interview'}
                        </h4>
                        <p className="text-xs text-slate-500 mt-1">
                          {new Date(session.started_at).toLocaleDateString()}
                        </p>
                      </div>
                      {session.overall_score && (
                        <div className="text-right">
                          <span className="text-sm font-black text-blue-400">{Math.round(session.overall_score)}%</span>
                          <div className="w-12 h-1 bg-slate-800 rounded-full mt-1 overflow-hidden">
                            <div className="h-full bg-blue-500" style={{ width: `${session.overall_score}%` }}></div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-8 px-4 border border-dashed border-white/10 rounded-2xl">
                  <BookOpen size={32} className="mx-auto text-slate-700 mb-3" />
                  <p className="text-slate-500 text-sm italic">No practice sessions yet. Start your first interview to see progress!</p>
                </div>
              )}
            </div>
          </div>

          <div className="card-glass p-6 bg-linear-to-br from-purple-600/10 to-blue-600/10">
            <h3 className="font-bold text-white mb-2">Pro Tip</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Use the <span className="text-white font-bold">STAR method</span> (Situation, Task, Action, Result) for behavioral questions to provide structured and impactful answers.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InterviewPrep;

