import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  Plus, 
  Upload, 
  Search, 
  Edit3,
  Eye,
  Target,
  Sparkles,
  Clock,
  ChevronRight,
  Trash2
} from 'lucide-react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { resumeAPI } from '../../services/api';

const MyResumes = () => {
  const navigate = useNavigate();
  const [resumes, setResumes] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchResumes();
  }, []);

  const fetchResumes = async () => {
    try {
      const response = await resumeAPI.getResumes();
      setResumes(response.data);
    } catch (error) {
      console.error("Error fetching resumes:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteResume = async (id, e) => {
    e.stopPropagation();
    if (window.confirm('Are you sure you want to delete this resume?')) {
      try {
        await resumeAPI.deleteResume(id);
        setResumes(resumes.filter(r => r.id !== id));
      } catch (error) {
        console.error("Error deleting resume:", error);
      }
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'text-green-400 bg-green-500/10 border-green-500/20';
      case 'optimized': return 'text-blue-400 bg-blue-500/10 border-blue-500/20';
      case 'archived': return 'text-slate-400 bg-slate-500/10 border-slate-500/20';
      default: return 'text-slate-400 bg-slate-500/10 border-slate-500/20';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  const latestResumeId = resumes.length > 0 ? resumes[0].id : null;

  return (
    <div className="space-y-8">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div className="space-y-2">
          <h1 className="text-3xl font-bold text-white">Resume Center</h1>
          <p className="text-slate-400">Manage your resumes, analyze ATS scores, and find matching jobs.</p>
        </div>
        <div className="flex items-center gap-3">
          <button 
            onClick={() => navigate('/app/resumes/create')}
            className="flex items-center gap-2 px-5 py-3 bg-slate-800 text-white font-bold rounded-2xl hover:bg-slate-700 transition-all"
          >
            <Plus size={20} /> Create New
          </button>
          <button 
            onClick={() => navigate('/app/resumes/upload')}
            className="flex items-center gap-2 px-5 py-3 bg-blue-600 text-white font-bold rounded-2xl shadow-lg shadow-blue-500/20 hover:bg-blue-500 transition-all"
          >
            <Upload size={20} /> Upload Resume
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[
          { icon: Plus, label: 'Create Resume', path: '/app/resumes/create', color: 'bg-blue-600' },
          { icon: Upload, label: 'Upload Resume', path: '/app/resumes/upload', color: 'bg-purple-600' },
          { 
            icon: Target, 
            label: 'General Optimize', 
            desc: 'Boost ATS Score', 
            color: 'bg-amber-600', 
            path: latestResumeId ? `/app/resumes/${latestResumeId}/optimize?tab=general` : '/app/resumes/upload' 
          },
          { 
            icon: Sparkles, 
            label: 'Job-Specific Tailor', 
            desc: 'Match a Job Description', 
            color: 'bg-green-600', 
            path: latestResumeId ? `/app/resumes/${latestResumeId}/optimize?tab=job` : '/app/resumes/upload' 
          }
        ].map((action, idx) => (
          <motion.div
            key={idx}
            whileHover={latestResumeId || idx < 2 ? { y: -4 } : {}}
            onClick={() => navigate(action.path)}
            className={`card-glass p-6 cursor-pointer hover:bg-white/10 transition-all group ${(!latestResumeId && idx >= 2) ? 'opacity-50 grayscale' : ''}`}
          >
            <div className={`w-12 h-12 ${action.color} rounded-xl flex items-center justify-center mb-4 shadow-lg`}>
              <action.icon size={24} className="text-white" />
            </div>
            <h3 className="font-bold text-white group-hover:text-blue-400 transition-colors">{action.label}</h3>
            {action.desc && <p className="text-sm text-slate-500 mt-1">{action.desc}</p>}
          </motion.div>
        ))}
      </div>

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-white">My Resumes</h2>
          <div className="relative">
            <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input 
              placeholder="Search resumes..."
              className="bg-slate-900/50 border border-white/10 rounded-xl pl-10 pr-4 py-2 text-sm text-white focus:ring-2 focus:ring-blue-500/30"
            />
          </div>
        </div>

        {resumes.length === 0 ? (
          <div className="card-glass p-16 text-center">
            <FileText size={48} className="text-slate-600 mx-auto mb-4" />
            <h3 className="text-xl font-bold text-white mb-2">No Resumes Yet</h3>
            <p className="text-slate-400 mb-6">Upload your first resume or create one from scratch.</p>
            <div className="flex items-center justify-center gap-4">
              <button onClick={() => navigate('/app/resumes/create')} className="px-6 py-3 bg-slate-800 text-white font-bold rounded-xl hover:bg-slate-700 transition-all">Create Resume</button>
              <button onClick={() => navigate('/app/resumes/upload')} className="px-6 py-3 bg-blue-600 text-white font-bold rounded-xl hover:bg-blue-500 transition-all">Upload Resume</button>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {resumes.map((resume) => (
              <motion.div
                key={resume.id}
                whileHover={{ y: -4 }}
                className="card-glass p-6 border-white/5 hover:border-blue-500/30 transition-all cursor-pointer group"
                onClick={() => navigate(`/app/resumes/${resume.id}`)}
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="w-12 h-12 bg-blue-600/20 rounded-xl flex items-center justify-center">
                    <FileText size={24} className="text-blue-400" />
                  </div>
                  <span className={`text-xs font-bold px-2 py-1 rounded-lg border ${resume.ats_score ? 'text-green-400 bg-green-500/10 border-green-500/20' : 'text-slate-400 bg-slate-500/10 border-slate-500/20'}`}>
                    {resume.ats_score ? `ATS: ${resume.ats_score}%` : 'NEW'}
                  </span>
                </div>
                
                <h3 className="font-bold text-white mb-1 group-hover:text-blue-400 transition-colors truncate">
                  {resume.title || resume.full_name || 'Untitled Resume'}
                </h3>
                <p className="text-sm text-slate-500 flex items-center gap-2 mb-4">
                  <Clock size={14} /> {new Date(resume.created_at).toLocaleDateString()}
                </p>

                {resume.ats_score && (
                  <div className="flex items-center gap-3 p-3 bg-slate-900/50 rounded-xl">
                    <Target size={18} className="text-green-400" />
                    <div className="flex-1">
                      <p className="text-xs text-slate-500">ATS Score</p>
                      <p className="font-bold text-white">{resume.ats_score}%</p>
                    </div>
                    <div className="w-16 h-2 bg-slate-800 rounded-full overflow-hidden">
                      <div className="h-full bg-green-500 rounded-full" style={{ width: `${resume.ats_score}%` }}></div>
                    </div>
                  </div>
                )}

                <div className="mt-4 pt-4 border-t border-white/5 flex items-center justify-between opacity-0 group-hover:opacity-100 transition-opacity">
                  <button 
                    onClick={(e) => handleDeleteResume(resume.id, e)}
                    className="text-xs font-bold text-slate-500 hover:text-rose-400 transition-colors flex items-center gap-1"
                  >
                    <Trash2 size={14} /> Delete
                  </button>
                  <button className="text-xs font-bold text-blue-400 hover:text-blue-300 transition-colors flex items-center gap-1">
                    View <ChevronRight size={14} />
                  </button>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default MyResumes;

