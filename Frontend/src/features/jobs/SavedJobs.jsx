import React, { useState, useEffect } from 'react';
import { 
  Search, 
  MapPin, 
  Briefcase, 
  Clock, 
  DollarSign, 
  Filter, 
  ChevronRight, 
  Bookmark, 
  Building2, 
  Trash2,
  ArrowLeft,
  ExternalLink,
  Target,
  Sparkles
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { jobsAPI } from '../../services/api';

// UI Components
import Button from '../../components/ui/Button';
import Card from '../../components/ui/Card';
import Badge from '../../components/ui/Badge';
import EmptyState from '../../components/ui/EmptyState';

const SavedJobs = () => {
  const navigate = useNavigate();
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [removingId, setRemovingId] = useState(null);

  useEffect(() => {
    fetchSavedJobs();
  }, []);

  const fetchSavedJobs = async () => {
    try {
      setLoading(true);
      const response = await jobsAPI.getSavedJobs();
      setJobs(response.data || []);
    } catch (error) {
      console.error("Error fetching saved jobs:", error);
    } finally {
      setLoading(false);
    }
  };

  const removeJob = async (jobId, e) => {
    e.stopPropagation();
    setRemovingId(jobId);
    try {
      await jobsAPI.unsaveJob(jobId);
      setJobs(prev => prev.filter(j => (j.job_id || j.id) !== jobId));
    } catch (error) {
      console.error("Error removing job:", error);
    } finally {
      setRemovingId(null);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'Recently';
    try {
      return new Date(dateStr).toLocaleDateString(undefined, { 
        month: 'short', 
        day: 'numeric',
        year: 'numeric'
      });
    } catch { return 'Recently'; }
  };

  return (
    <div className="space-y-10 max-w-[1200px] mx-auto pb-20 px-2 md:px-6">
      {/* Header Section */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-amber-500/10 rounded-xl">
              <Bookmark className="text-amber-500" size={24} fill="currentColor" />
            </div>
            <h1 className="text-4xl font-black text-white tracking-tight">Saved Jobs</h1>
          </div>
          <p className="text-slate-400 font-medium text-lg ml-12">Manage your bookmarked opportunities</p>
        </div>
        
        <Button 
          variant="ghost" 
          leftIcon={ArrowLeft} 
          onClick={() => navigate('/app/jobs')}
          className="text-slate-400 hover:text-white font-black uppercase tracking-widest text-xs"
        >
          Job Center
        </Button>
      </div>

      {loading ? (
        <div className="flex flex-col items-center justify-center h-96 gap-4">
          <div className="w-16 h-16 border-4 border-blue-500/10 border-t-blue-500 rounded-full animate-spin"></div>
          <p className="text-slate-500 font-bold uppercase tracking-widest text-xs animate-pulse">Retrieving your collection...</p>
        </div>
      ) : jobs.length === 0 ? (
        <EmptyState 
          icon={Bookmark}
          title="Your collection is empty"
          description="Browse thousands of jobs and save the ones that catch your eye for later review."
          actionText="Explore Jobs"
          onAction={() => navigate('/app/jobs/search')}
        />
      ) : (
        <div className="grid grid-cols-1 gap-6">
          <AnimatePresence mode="popLayout">
            {jobs.map((job, idx) => {
              const jobId = job.job_id || job.id;
              return (
                <motion.div
                  key={job.id}
                  layout
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ delay: idx * 0.05 }}
                >
                  <Card padding="none" className="group border-white/5 hover:border-blue-500/30 hover:bg-slate-900/60 overflow-hidden shadow-xl transition-all duration-300">
                    <div className="p-6 md:p-8 flex flex-col md:flex-row items-center gap-8">
                      {/* Company Logo/Icon */}
                      <div className="w-20 h-20 bg-white rounded-2xl p-4 flex items-center justify-center shadow-2xl group-hover:scale-105 transition-transform shrink-0">
                        <Building2 size={40} className="text-slate-900" />
                      </div>

                      {/* Job Info */}
                      <div className="flex-1 min-w-0 space-y-4 text-center md:text-left">
                        <div className="space-y-1">
                          <h3 className="text-2xl font-black text-white group-hover:text-blue-400 transition-colors tracking-tight leading-tight">
                            {job.job_title}
                          </h3>
                          <div className="flex flex-wrap items-center justify-center md:justify-start gap-3">
                            <span className="text-lg font-bold text-slate-300">{job.company_name || job.company}</span>
                            {(job.location) && (
                              <>
                                <span className="w-1 h-1 bg-slate-700 rounded-full hidden md:block"></span>
                                <div className="flex items-center gap-1.5 text-slate-500 text-xs font-black uppercase tracking-widest">
                                  <MapPin size={12} className="text-blue-500" />
                                  {job.location}
                                </div>
                              </>
                            )}
                          </div>
                        </div>

                        <div className="flex flex-wrap items-center justify-center md:justify-start gap-6 text-[11px] font-black uppercase tracking-[0.15em] text-slate-500">
                          {job.job_type && (
                            <span className="flex items-center gap-2 text-blue-400 bg-blue-500/5 px-2.5 py-1 rounded-md border border-blue-500/10">
                              <Briefcase size={12} /> {job.job_type}
                            </span>
                          )}
                          <span className="flex items-center gap-2">
                            <Clock size={12} /> Saved {formatDate(job.saved_date || job.created_at)}
                          </span>
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="flex flex-row md:flex-col items-center gap-3 w-full md:w-auto border-t md:border-t-0 md:border-l border-white/5 pt-6 md:pt-0 md:pl-8">
                        {job.match_score && (
                          <div className="hidden md:flex flex-col items-center gap-1 mb-2">
                            <span className="text-[10px] font-black text-slate-600 uppercase tracking-widest">Match Score</span>
                            <Badge variant="success" className="font-black px-3 py-1 text-sm bg-emerald-500/10 border-emerald-500/20">
                              {job.match_score}%
                            </Badge>
                          </div>
                        )}
                        
                        <div className="flex gap-2 w-full">
                          {job.job_link && (
                            <a 
                              href={job.job_link} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white font-black uppercase tracking-widest text-xs rounded-xl transition-all shadow-lg shadow-blue-500/20"
                            >
                              Apply <ExternalLink size={14} />
                            </a>
                          )}
                          <Button 
                            variant="ghost" 
                            size="icon" 
                            onClick={(e) => removeJob(jobId, e)}
                            loading={removingId === jobId}
                            className="w-12 h-12 rounded-xl text-slate-600 hover:text-rose-400 hover:bg-rose-500/10 border border-transparent hover:border-rose-500/20"
                          >
                            <Trash2 size={20} />
                          </Button>
                        </div>
                      </div>
                    </div>
                  </Card>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>
      )}
      
      {/* Footer Insight */}
      {!loading && jobs.length > 0 && (
        <Card className="p-8 border-dashed border-white/10 bg-white/[0.02] flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-indigo-500/10 rounded-2xl">
              <Sparkles size={24} className="text-indigo-400" />
            </div>
            <div>
              <p className="text-white font-bold">Ready to take the next step?</p>
              <p className="text-slate-500 text-sm font-medium">Use our Interview Prep tool to practice for these roles.</p>
            </div>
          </div>
          <Button 
            onClick={() => navigate('/app/interview')}
            className="w-full md:w-auto bg-indigo-600 hover:bg-indigo-500 font-black uppercase tracking-widest text-xs h-12 px-8 rounded-xl"
          >
            Start Prep Session
          </Button>
        </Card>
      )}
    </div>
  );
};

export default SavedJobs;

