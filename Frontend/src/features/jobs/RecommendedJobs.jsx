import React, { useState, useEffect, useCallback } from 'react';
import { 
  Search, 
  MapPin, 
  Briefcase, 
  Clock, 
  DollarSign, 
  ChevronRight, 
  Star, 
  Building2, 
  Bookmark, 
  BarChart3, 
  Loader2, 
  AlertCircle, 
  Sparkles,
  Target,
  FileText,
  RefreshCw
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { jobsAPI, resumeAPI } from '../../services/api';

const RecommendedJobs = () => {
  const navigate = useNavigate();
  const [resumes, setResumes] = useState([]);
  const [selectedResumeId, setSelectedResumeId] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [fetchingRecs, setFetchingRecs] = useState(false);
  const [error, setError] = useState(null);
  const [savedJobIds, setSavedJobIds] = useState(new Set());
  const [savingJobId, setSavingJobId] = useState(null);

  const fetchResumes = useCallback(async () => {
    try {
      const response = await resumeAPI.getResumes();
      setResumes(response.data || []);
      if (response.data && response.data.length > 0) {
        setSelectedResumeId(response.data[0].id);
      }
    } catch (err) {
      console.error("Error fetching resumes:", err);
      setError("Failed to load your resumes. Please try again.");
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchSavedJobs = useCallback(async () => {
    try {
      const res = await jobsAPI.getSavedJobs();
      setSavedJobIds(new Set((res.data || []).map(j => j.job_id || j.id)));
    } catch (err) {
      console.error("Error fetching saved jobs:", err);
    }
  }, []);

  const fetchRecommendations = useCallback(async (resumeId) => {
    if (!resumeId) return;
    
    setFetchingRecs(true);
    setError(null);
    try {
      const response = await jobsAPI.getJobRecommendations(resumeId, 15);
      setRecommendations(response.data.recommendations || []);
    } catch (err) {
      console.error("Error fetching recommendations:", err);
      setError("Failed to load job recommendations. The AI might still be processing your resume.");
    } finally {
      setFetchingRecs(false);
    }
  }, []);

  useEffect(() => {
    fetchResumes();
    fetchSavedJobs();
  }, [fetchResumes, fetchSavedJobs]);

  useEffect(() => {
    if (selectedResumeId) {
      fetchRecommendations(selectedResumeId);
    }
  }, [selectedResumeId, fetchRecommendations]);

  const handleSaveJob = async (jobId) => {
    setSavingJobId(jobId);
    try {
      if (savedJobIds.has(jobId)) {
        await jobsAPI.unsaveJob(jobId);
        setSavedJobIds(prev => {
          const s = new Set(prev);
          s.delete(jobId);
          return s;
        });
      } else {
        await jobsAPI.saveJob(jobId);
        setSavedJobIds(prev => new Set([...prev, jobId]));
      }
    } catch (err) {
      console.error("Error saving job:", err);
    } finally {
      setSavingJobId(null);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'Recently';
    try {
      const diff = Math.floor((Date.now() - new Date(dateStr).getTime()) / 86400000);
      if (diff === 0) return 'Today';
      if (diff === 1) return 'Yesterday';
      if (diff < 7) return `${diff} days ago`;
      return new Date(dateStr).toLocaleDateString();
    } catch {
      return 'Recently';
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] space-y-4">
        <Loader2 className="w-12 h-12 text-blue-500 animate-spin" />
        <p className="text-slate-400 animate-pulse">Analyzing your profile...</p>
      </div>
    );
  }

  if (resumes.length === 0) {
    return (
      <div className="space-y-8">
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold text-white">Recommended Jobs</h1>
          <p className="text-slate-400 text-lg max-w-2xl mx-auto">
            Get personalized job matches based on your skills and experience.
          </p>
        </div>

        <div className="card-glass p-12 text-center max-w-2xl mx-auto space-y-6">
          <div className="w-20 h-20 bg-blue-600/20 rounded-3xl flex items-center justify-center mx-auto mb-6">
            <FileText size={40} className="text-blue-400" />
          </div>
          <h2 className="text-2xl font-bold text-white">No Resume Found</h2>
          <p className="text-slate-400">
            To provide personalized job recommendations, we need to analyze your resume. 
            Upload your resume or create one using our builder to see jobs that match your profile.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
            <button 
              onClick={() => navigate('/app/resumes/upload')}
              className="w-full sm:w-auto px-8 py-4 bg-blue-600 text-white font-bold rounded-2xl shadow-xl shadow-blue-500/20 hover:bg-blue-500 transition-all flex items-center justify-center gap-2"
            >
              Upload Resume
            </button>
            <button 
              onClick={() => navigate('/app/resumes/create')}
              className="w-full sm:w-auto px-8 py-4 bg-slate-800 text-white font-bold rounded-2xl hover:bg-slate-700 transition-all"
            >
              Create from Scratch
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-col md:flex-row items-start md:items-end justify-between gap-6">
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-blue-400 mb-1">
            <Sparkles size={18} />
            <span className="text-sm font-bold uppercase tracking-wider">AI Powered Matches</span>
          </div>
          <h1 className="text-4xl font-bold text-white">Recommended Jobs</h1>
          <p className="text-slate-400">
            Based on your profile, we've found these opportunities for you.
          </p>
        </div>

        <div className="flex flex-col space-y-2 min-w-[240px]">
          <label className="text-xs font-bold text-slate-500 uppercase tracking-widest">Selected Resume</label>
          <div className="relative">
            <select 
              value={selectedResumeId || ''} 
              onChange={(e) => setSelectedResumeId(Number(e.target.value))}
              className="w-full bg-slate-900/60 border border-white/10 rounded-xl py-3 pl-4 pr-10 text-white focus:ring-2 focus:ring-blue-500/30 appearance-none transition-all cursor-pointer"
            >
              {resumes.map(resume => (
                <option key={resume.id} value={resume.id} className="bg-slate-900">
                  {resume.title || resume.full_name || `Resume #${resume.id}`}
                </option>
              ))}
            </select>
            <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-slate-400">
              <ChevronRight size={18} className="rotate-90" />
            </div>
          </div>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-3 p-4 bg-red-500/10 border border-red-500/20 rounded-2xl text-red-400">
          <AlertCircle size={20} />
          <p className="text-sm font-medium">{error}</p>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          <div className="flex items-center justify-between px-2">
            <h3 className="text-sm font-black text-slate-500 uppercase tracking-[0.2em]">
              {fetchingRecs ? 'Analyzing Market...' : `Top ${recommendations.length} AI Matches`}
            </h3>
            <button 
              onClick={() => fetchRecommendations(selectedResumeId)}
              disabled={fetchingRecs}
              className="text-xs font-bold text-blue-400 hover:text-blue-300 flex items-center gap-1.5 transition-colors disabled:opacity-50"
            >
              <RefreshCw size={14} className={fetchingRecs ? 'animate-spin' : ''} />
              Refresh
            </button>
          </div>

          <AnimatePresence mode="wait">
            {fetchingRecs ? (
              <motion.div 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="space-y-6"
              >
                {[1, 2, 3].map(i => (
                  <div key={i} className="card-glass p-8 border-white/5 animate-pulse">
                    <div className="flex gap-6">
                      <div className="w-16 h-16 bg-slate-800 rounded-2xl shrink-0"></div>
                      <div className="flex-1 space-y-4">
                        <div className="h-6 bg-slate-800 rounded-md w-3/4"></div>
                        <div className="h-4 bg-slate-800 rounded-md w-1/2"></div>
                        <div className="flex gap-4 pt-2">
                          <div className="h-4 bg-slate-800 rounded-md w-24"></div>
                          <div className="h-4 bg-slate-800 rounded-md w-24"></div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </motion.div>
            ) : recommendations.length === 0 ? (
              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="card-glass p-12 text-center space-y-4 border-dashed border-white/10"
              >
                <div className="w-16 h-16 bg-slate-800/50 rounded-2xl flex items-center justify-center mx-auto mb-2 text-slate-600">
                  <Briefcase size={32} />
                </div>
                <h3 className="text-xl font-bold text-white">No specific matches yet</h3>
                <p className="text-slate-400 max-w-md mx-auto">
                  We couldn't find highly relevant jobs for this resume. Make sure your resume is well-parsed and contains detailed skills.
                </p>
                <button 
                  onClick={() => navigate(`/app/resumes/${selectedResumeId}`)}
                  className="px-6 py-2 bg-blue-600/20 text-blue-400 border border-blue-500/30 rounded-xl font-bold hover:bg-blue-600/30 transition-all"
                >
                  Improve Resume
                </button>
              </motion.div>
            ) : (
              <motion.div 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="space-y-6"
              >
                {recommendations.map((match, idx) => {
                  const job = match.job;
                  return (
                    <motion.div 
                      key={job.id} 
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: idx * 0.05 }}
                      whileHover={{ y: -4 }} 
                      className="card-glass p-8 border-white/5 group cursor-pointer hover:bg-white/10 transition-all relative overflow-hidden"
                    >
                      {/* Match Score Indicator */}
                      <div className="absolute top-0 right-0 pt-4 pr-4">
                        <div className="flex flex-col items-end">
                          <div className={`px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest flex items-center gap-1.5 ${
                            match.match_score >= 80 ? 'bg-green-500/10 text-green-400 border border-green-500/20' :
                            match.match_score >= 60 ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20' :
                            'bg-slate-500/10 text-slate-400 border border-white/10'
                          }`}>
                            <Target size={12} />
                            {match.match_score}% Match
                          </div>
                        </div>
                      </div>

                      <div className="flex flex-col md:flex-row gap-6">
                        <div className="w-16 h-16 bg-white rounded-2xl p-3 flex items-center justify-center shadow-xl group-hover:scale-110 transition-transform shrink-0">
                          <Building2 size={32} className="text-slate-900" />
                        </div>
                        <div className="flex-1 space-y-4">
                          <div>
                            <h3 className="text-2xl font-bold text-white group-hover:text-blue-400 transition-colors pr-24">{job.job_title}</h3>
                            <div className="flex items-center gap-2 mt-1">
                              <span className="text-lg font-semibold text-slate-300">{job.company_name}</span>
                              {job.location && (
                                <>
                                  <span className="w-1.5 h-1.5 bg-slate-700 rounded-full"></span>
                                  <span className="text-slate-500 flex items-center gap-1.5 font-medium">
                                    <MapPin size={14} /> {job.location}
                                  </span>
                                </>
                              )}
                            </div>
                          </div>

                          <div className="flex flex-wrap gap-4 text-sm text-slate-400">
                            {job.job_type && <span className="flex items-center gap-1.5"><Briefcase size={14} className="text-blue-400" /> {job.job_type}</span>}
                            {job.salary_range && <span className="flex items-center gap-1.5"><DollarSign size={14} className="text-green-400" /> {job.salary_range}</span>}
                            <span className="flex items-center gap-1.5"><Clock size={14} className="text-slate-500" /> {formatDate(job.posted_date)}</span>
                          </div>

                          {match.missing_keywords && match.missing_keywords.length > 0 && (
                            <div className="p-3 bg-slate-900/40 border border-white/5 rounded-xl">
                              <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2 flex items-center gap-1.5">
                                <AlertCircle size={10} className="text-amber-500" /> Key Skills Missing
                              </p>
                              <div className="flex flex-wrap gap-2">
                                {match.missing_keywords.slice(0, 5).map(skill => (
                                  <span key={skill} className="px-2 py-0.5 bg-amber-500/10 text-amber-500/80 rounded-md text-[10px] font-bold">
                                    {skill}
                                  </span>
                                ))}
                                {match.missing_keywords.length > 5 && (
                                  <span className="text-[10px] text-slate-600 font-bold">+{match.missing_keywords.length - 5} more</span>
                                )}
                              </div>
                            </div>
                          )}

                          <div className="pt-4 flex items-center justify-between border-t border-white/5">
                            <div className="flex gap-2">
                              {job.source && (
                                <span className="px-3 py-1 bg-blue-500/10 border border-blue-500/20 rounded-lg text-blue-400 text-[10px] font-black tracking-wider uppercase">
                                  {job.source}
                                </span>
                              )}
                            </div>
                            <div className="flex items-center gap-3">
                              <button 
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleSaveJob(job.id);
                                }} 
                                disabled={savingJobId === job.id} 
                                className={`p-2.5 border rounded-xl transition-all ${
                                  savedJobIds.has(job.id) 
                                    ? 'bg-amber-400/10 border-amber-500/30 text-amber-400' 
                                    : 'bg-white/5 border-white/10 text-slate-500 hover:text-amber-400 hover:border-amber-500/30'
                                }`}
                                title={savedJobIds.has(job.id) ? "Remove from saved" : "Save for later"}
                              >
                                {savingJobId === job.id ? <Loader2 size={18} className="animate-spin" /> : <Bookmark size={18} fill={savedJobIds.has(job.id) ? 'currentColor' : 'none'} />}
                              </button>
                              {job.job_link ? (
                                <a 
                                  href={job.job_link} 
                                  target="_blank" 
                                  rel="noopener noreferrer" 
                                  onClick={(e) => e.stopPropagation()}
                                  className="px-6 py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-xl shadow-lg shadow-blue-500/20 transition-all flex items-center gap-2 group/btn"
                                >
                                  Apply Now 
                                  <ChevronRight size={16} className="group-hover/btn:translate-x-1 transition-transform" />
                                </a>
                              ) : (
                                <span className="text-slate-600 text-sm font-medium">No direct link</span>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  );
                })}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <div className="space-y-8">
          <div className="card-glass p-8 space-y-6 border-blue-500/10 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-blue-600/5 blur-2xl -z-10"></div>
            <div className="flex items-center gap-3 text-blue-400">
              <Star size={24} />
              <h3 className="text-xl font-bold text-white">Matching Logic</h3>
            </div>
            <div className="space-y-4">
              <p className="text-sm text-slate-400 leading-relaxed">
                Our AI compares your resume's skills, experience, and target roles against thousands of job listings to calculate a match score.
              </p>
              <div className="space-y-3">
                {[
                  { label: 'High Match (>80%)', color: 'bg-green-400' },
                  { label: 'Good Match (60-80%)', color: 'bg-blue-400' },
                  { label: 'Potential Match (<60%)', color: 'bg-slate-400' }
                ].map((item, i) => (
                  <div key={i} className="flex items-center gap-3">
                    <div className={`w-2 h-2 ${item.color} rounded-full`}></div>
                    <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">{item.label}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="card-glass p-8 space-y-6">
            <h3 className="text-lg font-bold text-white flex items-center gap-3">
              <Target className="text-purple-400" size={20} /> 
              Improve Recommendations
            </h3>
            <div className="space-y-4">
              <div className="p-4 bg-white/5 border border-white/5 rounded-xl space-y-2">
                <p className="text-xs font-bold text-slate-300">Update Your Resume</p>
                <p className="text-[11px] text-slate-500">More details about your skills lead to better AI matching.</p>
                <button 
                  onClick={() => navigate(`/app/resumes/${selectedResumeId}/edit`)}
                  className="text-xs font-bold text-blue-400 hover:text-blue-300 transition-colors"
                >
                  Edit Resume
                </button>
              </div>
              <div className="p-4 bg-white/5 border border-white/5 rounded-xl space-y-2">
                <p className="text-xs font-bold text-slate-300">Set Target Role</p>
                <p className="text-[11px] text-slate-500">Specify what you're looking for to narrow down results.</p>
                <button 
                  onClick={() => navigate('/app/profile/edit')}
                  className="text-xs font-bold text-blue-400 hover:text-blue-300 transition-colors"
                >
                  Update Profile
                </button>
              </div>
            </div>
          </div>

          <div className="card-glass p-8 space-y-4">
            <h3 className="text-lg font-bold text-white flex items-center gap-3">
              <BarChart3 className="text-amber-400" size={20} /> 
              Quick Stats
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">Perfect Matches</span>
                <span className="text-white font-bold">{recommendations.filter(m => m.match_score >= 80).length}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">Active Resumes</span>
                <span className="text-white font-bold">{resumes.length}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RecommendedJobs;
