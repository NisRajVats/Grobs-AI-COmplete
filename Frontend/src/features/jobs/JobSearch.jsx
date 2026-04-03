import React, { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { Search, MapPin, Briefcase, Clock, DollarSign, ChevronRight, Star, Globe, Building2, Bookmark, BarChart3, Loader2, AlertCircle, Sparkles } from 'lucide-react';
import { motion } from 'framer-motion';
import { jobsAPI, resumeAPI } from '../../services/api';

const JobSearch = () => {
  const { resumeId } = useParams();
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [totalJobs, setTotalJobs] = useState(0);
  const [savingJobId, setSavingJobId] = useState(null);
  const [savedJobIds, setSavedJobIds] = useState(new Set());
  const [isMatching, setIsMatching] = useState(false);
  const [resume, setResume] = useState(null);

  const fetchJobs = useCallback(async (query = '') => {
    setLoading(true);
    setError(null);
    try {
      let response;
      if (resumeId && !query.trim()) {
        setIsMatching(true);
        response = await jobsAPI.getJobRecommendations(resumeId, 50);
        // Transform recommendation response to match standard job response structure if needed
        const matchedJobs = response.data.recommendations || [];
        setJobs(matchedJobs.map(m => ({ ...m.job, match_score: m.match_score })));
        setTotalJobs(response.data.total || matchedJobs.length);
      } else {
        setIsMatching(false);
        response = query.trim() ? await jobsAPI.searchJobs(query, 50) : await jobsAPI.getJobs(0, 50);
        setJobs(response.data.jobs || []);
        setTotalJobs(response.data.total || 0);
      }
    } catch (err) {
      console.error("Error fetching jobs:", err);
      setError('Failed to load jobs. Make sure the backend is running.');
    } finally {
      setLoading(false);
    }
  }, [resumeId]);

  const fetchResumeInfo = useCallback(async () => {
    if (!resumeId) return;
    try {
      const res = await resumeAPI.getResume(resumeId);
      setResume(res.data);
    } catch (err) {
      console.error("Error fetching resume info:", err);
    }
  }, [resumeId]);

  const fetchSavedJobs = useCallback(async () => {
    try {
      const res = await jobsAPI.getSavedJobs();
      setSavedJobIds(new Set((res.data || []).map(j => j.job_id || j.id)));
    } catch { /* ignore */ }
  }, []);

  useEffect(() => { 
    fetchJobs(); 
    fetchSavedJobs();
    fetchResumeInfo();
  }, [fetchJobs, fetchSavedJobs, fetchResumeInfo]);

  const handleSearch = (e) => { e.preventDefault(); fetchJobs(searchQuery); };

  const handleSaveJob = async (jobId) => {
    setSavingJobId(jobId);
    try {
      if (savedJobIds.has(jobId)) {
        await jobsAPI.unsaveJob(jobId);
        setSavedJobIds(prev => { const s = new Set(prev); s.delete(jobId); return s; });
      } else {
        await jobsAPI.saveJob(jobId);
        setSavedJobIds(prev => new Set([...prev, jobId]));
      }
    } catch { /* ignore */ } finally { setSavingJobId(null); }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'Recently';
    try {
      const diff = Math.floor((Date.now() - new Date(dateStr).getTime()) / 86400000);
      return diff === 0 ? 'Today' : diff === 1 ? '1 day ago' : `${diff} days ago`;
    } catch { return dateStr; }
  };

  return (
    <div className="space-y-8">
      <div className="card-glass p-8 md:p-10 space-y-8 border-white/5 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-blue-600/10 blur-3xl -z-10"></div>
        <div className="space-y-2">
          <h1 className="text-4xl font-bold text-white tracking-tight">
            {isMatching ? (
              <>Jobs Matched for <span className="text-blue-500 italic">{resume?.filename || 'Your Resume'}</span></>
            ) : (
              <>Discover Your <span className="text-blue-500 italic">Next Big Role</span></>
            )}
          </h1>
          <p className="text-slate-400">
            {isMatching 
              ? "AI-matched opportunities based on your skills and experience."
              : "AI-curated job opportunities from top companies."}
          </p>
        </div>
        <form onSubmit={handleSearch} className="grid grid-cols-1 md:grid-cols-12 gap-4">
          <div className="md:col-span-9 relative group">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-blue-400 transition-colors" size={20} />
            <input value={searchQuery} onChange={e => setSearchQuery(e.target.value)} placeholder="Job title, keywords, or company" className="w-full bg-slate-900/60 border border-white/10 rounded-2xl py-4 pl-12 pr-4 text-white focus:ring-2 focus:ring-blue-500/30 transition-all" />
          </div>
          <div className="md:col-span-3">
            <button type="submit" className="w-full h-full bg-blue-600 hover:bg-blue-500 text-white font-black rounded-2xl shadow-xl shadow-blue-500/20 transition-all flex items-center justify-center gap-3">Search <ChevronRight size={20} /></button>
          </div>
        </form>
        <div className="flex flex-wrap gap-3">
          {['Software Engineer','Frontend','Backend','Data Science','Product Manager'].map(tag => (
            <button key={tag} onClick={() => { setSearchQuery(tag); fetchJobs(tag); }} className="px-4 py-2 bg-slate-900/40 border border-white/5 rounded-xl text-xs font-bold text-slate-500 hover:text-blue-400 hover:border-blue-500/30 transition-all uppercase tracking-widest">{tag}</button>
          ))}
        </div>
      </div>

      {error && <div className="flex items-center gap-3 p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400"><AlertCircle size={20} /><p className="text-sm">{error}</p></div>}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          <div className="flex items-center justify-between px-2">
            <h3 className="text-sm font-black text-slate-500 uppercase tracking-[0.2em]">{loading ? 'Loading...' : `Showing ${jobs.length} of ${totalJobs} Results`}</h3>
          </div>
          {loading ? (
            <div className="flex items-center justify-center py-20"><Loader2 className="animate-spin text-blue-400" size={40} /></div>
          ) : jobs.length === 0 ? (
            <div className="card-glass p-12 text-center space-y-4">
              <Building2 size={48} className="text-slate-600 mx-auto" />
              <p className="text-slate-400 text-lg">No jobs found</p>
              <p className="text-slate-600 text-sm">Try a different search. Admins can ingest jobs via the API.</p>
            </div>
          ) : (
            <div className="space-y-6">
              {jobs.map((job) => (
                <motion.div key={job.id} whileHover={{ y: -4 }} className="card-glass p-8 border-white/5 group cursor-pointer hover:bg-white/10 transition-all">
                  <div className="flex flex-col md:flex-row gap-6">
                    <div className="w-16 h-16 bg-white rounded-2xl p-3 flex items-center justify-center shadow-xl group-hover:scale-110 transition-transform">
                      <Building2 size={32} className="text-slate-900" />
                    </div>
                    <div className="flex-1 space-y-4">
                      <div className="flex items-start justify-between">
                        <div className="min-w-0">
                          <div className="flex flex-col sm:flex-row sm:items-center gap-3">
                            <h3 className="text-2xl font-bold text-white group-hover:text-blue-400 transition-colors truncate">{job.job_title}</h3>
                            {job.match_score && (
                              <div className="shrink-0 inline-flex items-center gap-1 px-2.5 py-1 bg-green-500/10 border border-green-500/20 rounded-lg text-green-400 text-xs font-black uppercase tracking-wider">
                                <Sparkles size={10} /> {job.match_score}% Match
                              </div>
                            )}
                          </div>
                          <div className="flex items-center gap-2 mt-1">
                            <span className="text-lg font-semibold text-slate-300">{job.company_name}</span>
                            {job.location && (
                              <>
                                <span className="w-1.5 h-1.5 bg-slate-700 rounded-full"></span>
                                <span className="text-slate-500 flex items-center gap-1.5"><MapPin size={14} /> {job.location}</span>
                              </>
                            )}
                          </div>
                        </div>
                        <button onClick={() => handleSaveJob(job.id)} disabled={savingJobId === job.id} className={`p-3 border rounded-xl transition-all ${savedJobIds.has(job.id) ? 'bg-amber-400/10 border-amber-500/30 text-amber-400' : 'bg-white/5 border-white/10 text-slate-500 hover:text-amber-400'}`}>
                          {savingJobId === job.id ? <Loader2 size={20} className="animate-spin" /> : <Bookmark size={20} fill={savedJobIds.has(job.id) ? 'currentColor' : 'none'} />}
                        </button>
                      </div>
                      <div className="flex flex-wrap gap-4 text-sm text-slate-400">
                        {job.job_type && <span className="flex items-center gap-1"><Briefcase size={14} /> {job.job_type}</span>}
                        {job.salary_range && <span className="flex items-center gap-1"><DollarSign size={14} /> {job.salary_range}</span>}
                        <span className="flex items-center gap-1"><Clock size={14} /> {formatDate(job.posted_date)}</span>
                        {job.source && <span className="flex items-center gap-1"><Globe size={14} /> {job.source}</span>}
                      </div>
                      {job.job_description && <p className="text-slate-500 text-sm line-clamp-2">{job.job_description.replace(/<[^>]*>/g, '').slice(0, 200)}</p>}
                      <div className="pt-4 flex items-center justify-between border-t border-white/5">
                        <div className="flex gap-2">
                          {job.source && <span className="px-3 py-1 bg-blue-500/10 border border-blue-500/20 rounded-lg text-blue-400 text-xs font-black">{job.source.toUpperCase()}</span>}
                        </div>
                        {job.job_link ? (
                          <a href={job.job_link} target="_blank" rel="noopener noreferrer" className="text-blue-400 font-bold text-sm flex items-center gap-2 group-hover:translate-x-1 transition-transform">Apply Now <ChevronRight size={16} /></a>
                        ) : <span className="text-slate-600 text-sm">No link available</span>}
                      </div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </div>

        <div className="space-y-8">
          <div className="card-glass p-8 space-y-6 border-blue-500/10">
            <div className="flex items-center gap-3 text-blue-400"><Star size={24} /><h3 className="text-xl font-bold text-white">Job Board Tips</h3></div>
            <div className="space-y-4">
              {['Upload your resume for AI-matched recommendations','Check ATS score before applying','Practice mock interviews for your target role'].map((tip, i) => (
                <div key={i} className="p-4 bg-white/5 border border-white/5 rounded-xl"><p className="text-sm text-slate-400">{tip}</p></div>
              ))}
            </div>
          </div>
          <div className="card-glass p-8 space-y-4">
            <h3 className="text-lg font-bold text-white flex items-center gap-3"><BarChart3 className="text-purple-400" size={20} /> Market Stats</h3>
            <div className="flex justify-between text-sm"><span className="text-slate-400">Total Available</span><span className="text-white font-bold">{totalJobs}</span></div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default JobSearch;
