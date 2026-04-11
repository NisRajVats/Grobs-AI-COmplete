import React, { useState, useEffect, useCallback } from 'react';
import { 
  FileText, 
  Plus, 
  Download, 
  Upload, 
  Search, 
  Edit3,
  Eye,
  Target,
  Sparkles,
  Clock,
  ChevronRight,
  Trash2,
  RefreshCw,
  CheckSquare,
  Square,
  Check
} from 'lucide-react';
import { motion } from 'framer-motion';
import { useNavigate, useLocation } from 'react-router-dom';
import { resumeAPI } from '../../services/api';

const MyResumes = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [resumes, setResumes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [successMsg, setSuccessMsg] = useState('');
  const [deletingResumeId, setDeletingResumeId] = useState(null);
  // Bulk select state
  const [selectedResumes, setSelectedResumes] = useState(new Set());
  const [selectAll, setSelectAll] = useState(false);
  const [bulkDeleting, setBulkDeleting] = useState(false);

  useEffect(() => {
    if (location.state?.success) {
      setSuccessMsg(location.state.success);
      setTimeout(() => setSuccessMsg(''), 5000);
    }
    fetchResumes();
  }, [location.state]);

  // Reset bulk selection when resumes change
  useEffect(() => {
    setSelectedResumes(new Set());
    setSelectAll(false);
  }, [resumes.length]);

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
      // Optimistic update - remove instantly for smooth UX
      const prevResumes = resumes;
      const prevSelected = new Set(selectedResumes);
      setResumes(prev => prev.filter(r => r.id !== id));
      prevSelected.delete(id);
      setSelectedResumes(prevSelected);
      setDeletingResumeId(id);

      try {
        await resumeAPI.deleteResume(id);
      } catch (error) {
        if (error.response?.status === 404) {
          console.log('Resume already deleted or removed');
        } else {
          // Revert optimistic update on real errors
          setResumes(prevResumes);
          setSelectedResumes(prevSelected);
          console.error("Delete failed:", error);
        }
      } finally {
        setDeletingResumeId(null);
      }
    }
  };

  const toggleSelectAll = useCallback(() => {
    if (selectAll || selectedResumes.size === resumes.length) {
      setSelectedResumes(new Set());
      setSelectAll(false);
    } else {
      setSelectedResumes(new Set(resumes.map(r => r.id)));
      setSelectAll(true);
    }
  }, [selectAll, selectedResumes, resumes]);

  const toggleResumeSelect = useCallback((id) => {
    setSelectedResumes(prev => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  }, []);

  const handleBulkDelete = async () => {
    const ids = Array.from(selectedResumes);
    if (ids.length === 0) return;
    
    if (window.confirm(`Delete ${ids.length} resume(s)? This cannot be undone.`)) {
      const prevResumes = resumes;
      setBulkDeleting(true);
      
      try {
        await resumeAPI.deleteResumes(ids);
        // Optimistic success - remove selected
        setResumes(prev => prev.filter(r => !ids.includes(r.id)));
        setSelectedResumes(new Set());
        setSelectAll(false);
      } catch (error) {
        console.error("Bulk delete failed:", error);
        setResumes(prevResumes); // Revert
        alert(`Failed to delete ${ids.length} resume(s). Please try again.`);
      } finally {
        setBulkDeleting(false);
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
      {successMsg && (
        <div className="p-4 bg-green-500/10 border border-green-500/20 rounded-2xl text-green-400 font-bold flex items-center gap-3 animate-in slide-in-from-top-2 fade-in">
          <Sparkles size={20} /> {successMsg}
        </div>
      )}
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
          <div className="flex items-center gap-3">
            <div className="relative">
              <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
              <input 
                placeholder="Search resumes..."
                className="bg-slate-900/50 border border-white/10 rounded-xl pl-10 pr-4 py-2 text-sm text-white focus:ring-2 focus:ring-blue-500/30"
              />
            </div>
            {resumes.length > 0 && (
              <motion.button
                whileTap={{ scale: 0.95 }}
                onClick={toggleSelectAll}
                className="p-2 hover:bg-white/10 rounded-xl text-slate-400 hover:text-blue-400 transition-all"
                title={selectAll ? 'Deselect all' : 'Select all'}
              >
                {selectAll || selectedResumes.size === resumes.length ? (
                  <Square size={18} />
                ) : (
                  <CheckSquare size={18} />
                )}
              </motion.button>
            )}
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
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {resumes.map((resume) => {
                const isSelected = selectedResumes.has(resume.id);
                return (
                  <motion.div
                    key={resume.id}
                    whileHover={{ y: -4 }}
                    className={`card-glass p-6 border-2 transition-all cursor-pointer group relative ${
                      isSelected 
                        ? 'border-blue-500/50 bg-blue-500/5 shadow-lg shadow-blue-500/20' 
                        : 'border-white/5 hover:border-blue-500/30'
                    }`}
                    onClick={(e) => {
                      if (e.target.closest('button') || e.target.closest('input')) return;
                      navigate(`/app/resumes/${resume.id}`);
                    }}
                  >
                    {/* Selection checkbox */}
                    <motion.button
                      whileTap={{ scale: 0.95 }}
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleResumeSelect(resume.id);
                      }}
                      className="absolute top-4 left-4 p-1.5 bg-white/10 hover:bg-white/20 rounded-lg opacity-0 group-hover:opacity-100 transition-all border border-white/20 hover:border-blue-400"
                      title="Toggle select"
                    >
                      {isSelected ? <Check size={16} className="text-blue-400" /> : <Square size={16} className="text-slate-400" />}
                    </motion.button>

                    {/* Download button */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        resumeAPI.downloadResume(resume.id).then(response => {
                          const blob = new Blob([response.data], { type: 'application/pdf' });
                          const url = window.URL.createObjectURL(blob);
                          const a = document.createElement('a');
                          a.href = url;
                          a.download = `${resume.title || resume.full_name || 'resume'}.pdf`;
                          a.click();
                          window.URL.revokeObjectURL(url);
                        }).catch(() => alert('Download failed'));
                      }}
                      className="absolute top-4 right-4 p-2 bg-white/10 hover:bg-white/20 rounded-xl opacity-0 group-hover:opacity-100 transition-all"
                      title="Download PDF"
                    >
                      <Download size={16} />
                    </button>
                    <div className="flex items-start justify-between mb-4">
                      <div className="w-12 h-12 bg-blue-600/20 rounded-xl flex items-center justify-center">
                        <FileText size={24} className="text-blue-400" />
                      </div>
                      <span className={`text-xs font-bold px-2 py-1 rounded-lg border ${ (resume.ats_score !== undefined && resume.ats_score !== null) ? 'text-green-400 bg-green-500/10 border-green-500/20' : 'text-slate-400 bg-slate-500/10 border-slate-500/20'}`}>
                        {(resume.ats_score !== undefined && resume.ats_score !== null) ? `ATS: ${resume.ats_score}%` : 'NEW'}
                      </span>
                    </div>
                    
                    <h3 className="font-bold text-white mb-1 group-hover:text-blue-400 transition-colors truncate">
                      {resume.title || resume.full_name || 'Untitled Resume'}
                    </h3>
                    <p className="text-sm text-slate-500 flex items-center gap-2 mb-4">
                      <Clock size={14} /> {new Date(resume.created_at).toLocaleDateString()}
                    </p>

                    {(resume.ats_score !== undefined && resume.ats_score !== null) && (
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
                        disabled={deletingResumeId === resume.id || bulkDeleting}
                        className="text-xs font-bold text-slate-500 hover:text-rose-400 transition-colors flex items-center gap-1 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {deletingResumeId === resume.id ? (
                          <RefreshCw size={14} className="animate-spin" />
                        ) : (
                          <Trash2 size={14} />
                        )}
                        {deletingResumeId === resume.id ? 'Deleting...' : 'Delete'}
                      </button>
                      <button className="text-xs font-bold text-blue-400 hover:text-blue-300 transition-colors flex items-center gap-1">
                        View <ChevronRight size={14} />
                      </button>
                    </div>
                  </motion.div>
                );
              })}
            </div>

            {/* Bulk Actions Toolbar */}
            {selectedResumes.size > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="card-glass p-4 border-t border-blue-500/30 bg-blue-500/5 backdrop-blur-sm sticky bottom-0 z-20 flex items-center justify-between gap-4"
              >
                <div className="text-sm font-bold text-slate-300">
                  {selectedResumes.size} {selectedResumes.size === 1 ? 'resume' : 'resumes'} selected
                </div>
                <div className="flex items-center gap-3">
                  <button
                    onClick={handleBulkDelete}
                    disabled={bulkDeleting}
                    className="flex items-center gap-2 px-5 py-2.5 bg-rose-600/90 text-white font-bold rounded-xl hover:bg-rose-500/90 transition-all shadow-lg shadow-rose-500/25 disabled:opacity-50 flex-1 sm:flex-none"
                  >
                    {bulkDeleting ? <RefreshCw size={16} className="animate-spin" /> : <Trash2 size={16} />}
                    {bulkDeleting ? 'Deleting...' : `Delete Selected`}
                  </button>
                  <button
                    onClick={toggleSelectAll}
                    className="p-2 hover:bg-white/10 rounded-xl text-slate-400 hover:text-white transition-all"
                  >
                    <Square size={18} />
                  </button>
                </div>
              </motion.div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default MyResumes;

