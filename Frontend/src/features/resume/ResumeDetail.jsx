import React, { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  FileText,
  Eye,
  Edit3,
  Target,
  Sparkles,
  Download,
  Briefcase,
  Clock,
  ChevronRight,
  Trash2,
  MoreVertical,
  Link,
  Zap,
  Loader2,
  CheckCircle2,
  AlertCircle,
  X,
  RefreshCw,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { resumeAPI, jobsAPI } from "../../services/api";

const ResumeDetail = () => {
  const { resumeId } = useParams();
  const navigate = useNavigate();
  const [resume, setResume] = useState(null);
  const [loading, setLoading] = useState(true);

  // Recommendations states
  const [recommendations, setRecommendations] = useState([]);
  const [loadingRecs, setLoadingRecs] = useState(false);

  // Optimization states
  const [jobDescription, setJobDescription] = useState("");
  const [jobUrl, setJobUrl] = useState("");
  const [isTailoring, setIsTailoring] = useState(false);
  const [fetchingUrl, setFetchingUrl] = useState(false);
  const [saveAsNew, setSaveAsNew] = useState(true);
  const [optimizationResult, setOptimizationResult] = useState(null);
  const [showResult, setShowResult] = useState(false);
  const [error, setError] = useState(null);

  const fetchResume = useCallback(async () => {
    try {
      const response = await resumeAPI.getResume(resumeId);
      setResume(response.data);
    } catch (error) {
      console.error("Error fetching resume:", error);
    } finally {
      setLoading(false);
    }
  }, [resumeId]);

  const fetchRecommendations = useCallback(async () => {
    setLoadingRecs(true);
    try {
      const res = await jobsAPI.getJobRecommendations(resumeId, 3);
      setRecommendations(res.data.recommendations || []);
    } catch (err) {
      console.error("Error fetching recommendations:", err);
    } finally {
      setLoadingRecs(false);
    }
  }, [resumeId]);

  useEffect(() => {
    const fetchAll = async () => {
      await Promise.all([fetchResume(), fetchRecommendations()]);
    };
    fetchAll();
  }, [resumeId, fetchResume, fetchRecommendations]);

  const handleUrlFetch = async () => {
    if (!jobUrl) return;
    setFetchingUrl(true);
    setError(null);
    try {
      // Mocking URL fetch for now, in a real app this would call an API
      // that uses a scraper or AI to extract the JD from a link
      await new Promise((r) => setTimeout(r, 1500));
      setJobDescription(
        "Sample job description fetched from URL: " +
          jobUrl +
          "\n\nWe are looking for a Senior Software Engineer with 5+ years of experience in React and Node.js. The ideal candidate should have strong knowledge of AWS and CI/CD pipelines.",
      );
    } catch (err) {
      setError(
        "Failed to fetch job description from URL. Please paste it manually.",
      );
    } finally {
      setFetchingUrl(false);
    }
  };

  const handleTailor = async () => {
    if (!jobDescription.trim()) return;
    setIsTailoring(true);
    setError(null);
    try {
      const res = await resumeAPI.optimizeResume(
        resumeId,
        "job-specific",
        jobDescription,
        null,
        saveAsNew,
      );
      setOptimizationResult(res.data);
      setShowResult(true);
    } catch (err) {
      setError(
        err.response?.data?.detail || "Tailoring failed. Please try again.",
      );
    } finally {
      setIsTailoring(false);
    }
  };

  const actions = [
    {
      id: "preview",
      icon: Eye,
      label: "Preview",
      path: `/app/resumes/${resumeId}/preview`,
      color: "bg-blue-600",
    },
    {
      id: "edit",
      icon: Edit3,
      label: "Edit",
      path: `/app/resumes/${resumeId}/edit`,
      color: "bg-purple-600",
    },
    {
      id: "ats",
      icon: Target,
      label: "ATS Analysis",
      path: `/app/resumes/${resumeId}/ats`,
      color: "bg-amber-600",
    },
    {
      id: "jobs",
      icon: Briefcase,
      label: "Find Jobs",
      path: `/app/resumes/${resumeId}/jobs`,
      color: "bg-rose-600",
    },
    {
      id: "download",
      icon: Download,
      label: "Download",
      path: `/app/resumes/${resumeId}/download`,
      color: "bg-slate-600",
    },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8 pb-20">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate("/app/resumes")}
            className="p-2 hover:bg-white/10 rounded-xl transition-colors text-slate-400 hover:text-white"
          >
            <ChevronRight className="rotate-180" size={20} />
          </button>
          <div>
            <h1 className="text-3xl font-bold text-white">
              {resume?.filename}
            </h1>
            <p className="text-slate-400 flex items-center gap-2 mt-1">
              <Clock size={14} /> Created {resume?.created_at} • Version{" "}
              {resume?.version}
            </p>
          </div>
        </div>
        <button className="p-2 hover:bg-white/10 rounded-xl transition-colors text-slate-400 hover:text-rose-400">
          <Trash2 size={20} />
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-8">
          {/* ATS Quick View */}
          {resume?.latest_analysis && (
            <div className="card-glass p-6 border border-blue-500/20 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 bg-blue-600/20 rounded-2xl flex items-center justify-center">
                  <Target size={32} className="text-blue-400" />
                </div>
                <div>
                  <p className="text-sm text-slate-400 font-bold uppercase tracking-widest">
                    ATS Compatibility
                  </p>
                  <p className="text-3xl font-black text-white">
                    {resume.latest_analysis.score}%
                  </p>
                </div>
              </div>
              <button
                onClick={() => navigate(`/app/resumes/${resumeId}/ats`)}
                className="px-5 py-2.5 bg-blue-600/10 hover:bg-blue-600/20 text-blue-400 font-bold rounded-xl border border-blue-500/30 transition-all flex items-center gap-2"
              >
                <Target size={18} /> View Analysis
              </button>
            </div>
          )}

          {/* Quick Actions */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {actions.map((action) => (
              <motion.div
                key={action.id}
                whileHover={{ y: -4 }}
                onClick={() => navigate(action.path)}
                className="card-glass p-6 cursor-pointer hover:bg-white/10 transition-all group text-center"
              >
                <div
                  className={`w-12 h-12 ${action.color} rounded-xl flex items-center justify-center mx-auto mb-3 shadow-lg group-hover:scale-110 transition-transform`}
                >
                  <action.icon size={20} className="text-white" />
                </div>
                <p className="font-bold text-white group-hover:text-blue-400 transition-colors text-xs uppercase tracking-widest">
                  {action.label}
                </p>
              </motion.div>
            ))}
          </div>

          {/* Skills Section */}
          {(resume?.skills?.length > 0 ||
            resume?.parsed_data?.skills?.length > 0) && (
            <div className="card-glass p-8">
              <h3 className="font-bold text-white mb-6 flex items-center gap-2">
                <Zap className="text-amber-400" size={20} /> Detected Technical
                Skills
              </h3>
              <div className="flex flex-wrap gap-2">
                {(resume?.skills?.length > 0
                  ? resume.skills
                  : resume.parsed_data.skills
                ).map((skill, i) => (
                  <span
                    key={i}
                    className="px-4 py-2 bg-slate-900/50 border border-white/5 rounded-xl text-slate-300 text-sm hover:border-blue-500/30 transition-colors cursor-default"
                  >
                    {typeof skill === "string" ? skill : skill.name}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Tailoring Sidebar */}
        <div className="space-y-6">
          {/* AI Recommendations */}
          <div className="card-glass p-6 border border-blue-500/10">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-black text-white uppercase tracking-widest flex items-center gap-2">
                <Sparkles className="text-blue-400" size={16} /> Recommended For
                You
              </h3>
              <button
                onClick={fetchRecommendations}
                className="p-1.5 hover:bg-white/10 rounded-lg text-slate-500 hover:text-blue-400 transition-colors"
              >
                <RefreshCw
                  size={14}
                  className={loadingRecs ? "animate-spin" : ""}
                />
              </button>
            </div>

            {loadingRecs ? (
              <div className="space-y-3">
                {[1, 2].map((i) => (
                  <div
                    key={i}
                    className="h-16 bg-slate-800/50 rounded-xl animate-pulse"
                  />
                ))}
              </div>
            ) : recommendations.length > 0 ? (
              <div className="space-y-3">
                {recommendations.map((rec, i) => (
                  <div
                    key={i}
                    onClick={() => {
                      setJobDescription(rec.job.job_description || "");
                      setJobUrl(rec.job.job_link || "");
                    }}
                    className="p-3 bg-slate-900/50 border border-white/5 rounded-xl hover:border-blue-500/30 transition-all cursor-pointer group"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <p className="text-xs font-bold text-white truncate pr-2">
                        {rec.job.job_title}
                      </p>
                      <span className="text-[10px] font-black text-blue-400 bg-blue-500/10 px-1.5 py-0.5 rounded-md border border-blue-500/20">
                        {rec.match_score}% Match
                      </span>
                    </div>
                    <p className="text-[10px] text-slate-500 font-medium truncate">
                      {rec.job.company_name}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-4 bg-slate-900/30 rounded-xl border border-dashed border-white/5">
                <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">
                  No matching jobs found
                </p>
              </div>
            )}
          </div>

          {/* Tailoring Tool */}
          <div className="card-glass p-8 border border-green-500/20 relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity pointer-events-none">
              <Sparkles size={80} className="text-green-400" />
            </div>

            <div className="relative z-10 space-y-6">
              <div>
                <h3 className="text-xl font-black text-white flex items-center gap-2">
                  <Target className="text-green-400" /> Tailor for a Job
                </h3>
                <p className="text-xs text-slate-500 font-bold uppercase tracking-widest mt-1">
                  AI-Powered Optimization
                </p>
              </div>

              <div className="space-y-4">
                <div className="space-y-2">
                  <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest px-1">
                    Job Link (Auto-extract)
                  </label>
                  <div className="flex gap-2">
                    <div className="flex-1 relative">
                      <Link
                        className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500"
                        size={14}
                      />
                      <input
                        type="text"
                        value={jobUrl}
                        onChange={(e) => setJobUrl(e.target.value)}
                        placeholder="LinkedIn, Indeed, etc."
                        className="w-full bg-slate-900/50 border border-white/10 rounded-xl pl-9 pr-4 py-2.5 text-sm text-white focus:ring-1 focus:ring-green-500/30 outline-none transition-all"
                      />
                    </div>
                    <button
                      onClick={handleUrlFetch}
                      disabled={fetchingUrl || !jobUrl}
                      className="p-2.5 bg-slate-800 text-white rounded-xl hover:bg-slate-700 disabled:opacity-50 transition-all"
                    >
                      {fetchingUrl ? (
                        <Loader2 size={18} className="animate-spin" />
                      ) : (
                        <RefreshCw size={18} />
                      )}
                    </button>
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between px-1">
                    <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest">
                      Job Description
                    </label>
                    {jobDescription && (
                      <button
                        onClick={() => setJobDescription("")}
                        className="text-[10px] font-bold text-rose-400 hover:text-rose-300 transition-colors uppercase"
                      >
                        Clear
                      </button>
                    )}
                  </div>
                  <textarea
                    value={jobDescription}
                    onChange={(e) => setJobDescription(e.target.value)}
                    placeholder="Paste the job description details here or select a recommendation above..."
                    className="w-full h-40 bg-slate-900/50 border border-white/10 rounded-2xl px-4 py-3 text-sm text-white focus:ring-1 focus:ring-green-500/30 outline-none resize-none transition-all leading-relaxed"
                  />
                </div>

                <div className="flex items-center gap-3 px-1">
                  <button
                    onClick={() => setSaveAsNew(!saveAsNew)}
                    className={`w-5 h-5 rounded border flex items-center justify-center transition-all ${saveAsNew ? "bg-green-600 border-green-500" : "bg-slate-900 border-white/10"}`}
                  >
                    {saveAsNew && (
                      <CheckCircle2 size={12} className="text-white" />
                    )}
                  </button>
                  <span className="text-xs text-slate-400 font-medium">
                    Save as tailored version
                  </span>
                </div>

                {error && (
                  <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl flex items-start gap-2 text-rose-400 text-[10px] font-bold">
                    <AlertCircle size={14} className="shrink-0" />
                    <p>{error}</p>
                  </div>
                )}

                <button
                  onClick={handleTailor}
                  disabled={isTailoring || !jobDescription.trim()}
                  className="w-full py-4 bg-green-600 text-white font-black rounded-2xl hover:bg-green-500 transition-all shadow-lg shadow-green-500/20 flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  {isTailoring ? (
                    <Loader2 className="animate-spin" />
                  ) : (
                    <Sparkles size={20} />
                  )}
                  {isTailoring ? "AI is Tailoring..." : "Optimize for this Job"}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <AnimatePresence>
        {showResult && optimizationResult && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 md:p-8 bg-black/90 backdrop-blur-md">
            <motion.div
              initial={{ opacity: 0, scale: 0.9, y: 30 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: 30 }}
              className="w-full max-w-4xl h-[85vh] bg-slate-900/95 backdrop-blur-xl border border-white/10 rounded-4xl overflow-hidden flex flex-col shadow-2xl"
            >
              <div className="p-8 border-b border-white/5 flex items-center justify-between bg-slate-900/80">
                <div className="flex items-center gap-4">
                  <div className="w-14 h-14 bg-green-500/20 rounded-2xl flex items-center justify-center">
                    <Target className="text-green-400" size={28} />
                  </div>
                  <div>
                    <h2 className="text-2xl font-black text-white uppercase tracking-tight">
                      Tailored Success!
                    </h2>
                    <p className="text-xs text-slate-500 font-bold uppercase tracking-widest">
                      Job-specific optimization complete
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setShowResult(false)}
                  className="p-2 hover:bg-white/10 rounded-2xl text-slate-400 hover:text-white transition-colors"
                >
                  <X size={28} />
                </button>
              </div>

              <div className="flex-1 overflow-y-auto p-8 space-y-10">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  <div className="card-glass p-8 border-blue-500/20 space-y-4">
                    <div className="flex items-center justify-between">
                      <h4 className="text-xs font-black text-blue-400 uppercase tracking-widest flex items-center gap-2">
                        <Target size={14} /> Compatibility
                      </h4>
                      <span className="text-4xl font-black text-white">
                        {optimizationResult.compatibility_score}%
                      </span>
                    </div>
                    <p className="text-sm text-slate-400 leading-relaxed italic border-l-2 border-blue-500/30 pl-4">
                      "{optimizationResult.compatibility_feedback}"
                    </p>
                  </div>

                  <div className="card-glass p-8 border-green-500/20 space-y-4">
                    <div className="flex items-center justify-between">
                      <h4 className="text-xs font-black text-green-400 uppercase tracking-widest flex items-center gap-2">
                        <Target size={14} /> General ATS Score
                      </h4>
                      <span className="text-4xl font-black text-white">
                        {optimizationResult.ats_score}%
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-[10px] font-bold text-green-400 uppercase tracking-widest bg-green-500/10 w-fit px-3 py-1 rounded-full border border-green-500/20">
                      <Sparkles size={10} /> Improved Profile Strength
                    </div>
                  </div>
                </div>

                <div className="space-y-6">
                  <h4 className="text-sm font-black text-white uppercase tracking-widest flex items-center gap-2">
                    <Sparkles size={18} className="text-amber-400" /> Strategic
                    Tailoring Summary
                  </h4>
                  <div className="p-8 bg-slate-900/60 border border-white/5 rounded-3xl text-slate-300 text-sm leading-relaxed whitespace-pre-wrap">
                    {optimizationResult.suggestions}
                  </div>
                </div>

                <div className="space-y-6">
                  <h4 className="text-sm font-black text-white uppercase tracking-widest flex items-center gap-2">
                    <CheckCircle2 size={18} className="text-green-400" /> Target
                    Keyword Alignment
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                    {optimizationResult.improvements?.map((imp, i) => (
                      <div
                        key={i}
                        className="p-4 bg-white/5 border border-white/5 rounded-2xl flex items-center gap-3 text-[11px] font-bold text-slate-400 uppercase tracking-tight"
                      >
                        <div className="w-6 h-6 bg-green-500/10 rounded-full flex items-center justify-center border border-green-500/20">
                          <CheckCircle2 size={12} className="text-green-400" />
                        </div>
                        {imp}
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div className="p-8 bg-slate-900/80 border-t border-white/5 flex gap-4">
                <button
                  onClick={() => setShowResult(false)}
                  className="flex-1 py-4 bg-slate-800 text-white font-black rounded-2xl hover:bg-slate-700 transition-all uppercase tracking-widest text-sm"
                >
                  Back to Resume
                </button>
                <button
                  onClick={() => navigate(`/app/resumes/${resumeId}/preview`)}
                  className="flex-1 py-4 bg-blue-600 text-white font-black rounded-2xl hover:bg-blue-500 transition-all uppercase tracking-widest text-sm shadow-xl shadow-blue-500/20 flex items-center justify-center gap-2"
                >
                  Preview Optimized Version <ArrowRight size={18} />
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default ResumeDetail;
