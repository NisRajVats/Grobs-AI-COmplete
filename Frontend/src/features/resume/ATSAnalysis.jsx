import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ShieldCheck, Target, Search, AlertTriangle, CheckCircle2, Sparkles, ArrowRight, BarChart3, Loader2, Zap, RefreshCw, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import api, { resumeAPI } from '../../services/api';

const ATSAnalysis = () => {
  const { resumeId } = useParams();
  const navigate = useNavigate();
  const resultsRef = useRef(null);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [optimizing, setOptimizing] = useState(false);
  const [error, setError] = useState(null);
  const [optimizationResult, setOptimizationResult] = useState(null);
  const [showComparison, setShowComparison] = useState(false);

  const fetchAnalysis = useCallback(async (isRefresh = false) => {
    if (isRefresh) setLoading(true);
    setError(null);
    try {
      const response = await resumeAPI.atsCheck(resumeId, "");
      setAnalysis(response.data);
    } catch (_error) {
      console.error("ATS Check error:", _error);
      setError("Failed to load ATS analysis. Please try again.");
      setAnalysis(null);
    } finally {
      setLoading(false);
    }
  }, [resumeId]);

  useEffect(() => {
    fetchAnalysis();
  }, [fetchAnalysis]);

  useEffect(() => {
    if (showComparison && resultsRef.current) {
      setTimeout(() => {
        resultsRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);
    }
  }, [showComparison]);

  const handleRefresh = () => {
    fetchAnalysis(true);
  };

  const handleMagicFix = async (issueType = 'comprehensive') => {
    setOptimizing(true);
    setError(null);
    try {
      const res = await resumeAPI.optimizeResume(resumeId, issueType, "");
      if (res.data.success) {
        setOptimizationResult(res.data);
        setShowComparison(true);
      } else {
        setError(res.data.error || "Optimization failed.");
      }
    } catch (err) {
      console.error("Optimization error:", err);
      // Provide more specific error messages
      let errorMessage = "An error occurred during AI optimization.";
      if (err.response?.status === 404) {
        errorMessage = "Resume not found. Please refresh the page and try again.";
      } else if (err.response?.status === 400) {
        errorMessage = err.response.data?.detail || "Resume has insufficient data for optimization. Please add more content to your resume first.";
      } else if (err.response?.status === 500) {
        errorMessage = "The optimization service is temporarily unavailable. Please try again in a few moments.";
      } else if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      }
      setError(errorMessage);
    } finally {
      setOptimizing(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-4">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        <p className="text-slate-400 animate-pulse font-bold tracking-widest uppercase text-xs">Running deep ATS analysis...</p>
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-6 text-center max-w-md mx-auto">
        <div className="w-20 h-20 bg-red-500/10 rounded-3xl flex items-center justify-center border border-red-500/20">
          <AlertTriangle className="text-red-400" size={40} />
        </div>
        <div className="space-y-2">
          <h2 className="text-2xl font-bold text-white">Analysis Failed</h2>
          <p className="text-slate-400">We couldn't analyze your resume at this moment. This might be due to a connection issue or an error with our AI provider.</p>
        </div>
        <button 
          onClick={handleRefresh}
          className="px-8 py-3 bg-blue-600 text-white font-bold rounded-xl hover:bg-blue-500 transition-all shadow-lg shadow-blue-500/20 flex items-center gap-2"
        >
          <RefreshCw size={18} /> Try Again
        </button>
      </div>
    );
  }

  const categoryLabels = {
    keyword_optimization: 'Keyword Optimization',
    formatting: 'Formatting Compatibility',
    job_match: 'Job Match Rate',
    structure: 'Resume Structure',
    readability: 'ATS Readability',
    contact_info: 'Contact Information',
    semantic_relevance: 'Semantic Relevance'
  };

  const getCategoryColor = (name) => {
    const colors = {
      keyword_optimization: 'bg-blue-500',
      formatting: 'bg-green-500',
      job_match: 'bg-purple-500',
      structure: 'bg-amber-500',
      readability: 'bg-cyan-500',
      contact_info: 'bg-rose-500',
      semantic_relevance: 'bg-indigo-500'
    };
    return colors[name] || 'bg-slate-500';
  };

  const categories = analysis?.category_scores 
    ? Object.entries(analysis.category_scores).map(([key, score]) => ({
        name: categoryLabels[key] || key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
        score,
        color: getCategoryColor(key)
      }))
    : [];

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      <div className="flex items-center gap-4">
        <button onClick={() => navigate(`/app/resumes/${resumeId}`)} className="p-2 hover:bg-white/10 rounded-xl text-slate-400 hover:text-white">
          <ArrowRight className="rotate-180" size={20} />
        </button>
        <div>
          <div className="flex items-center gap-4">
            <h1 className="text-3xl font-bold text-white">ATS Analysis</h1>
            {analysis?.llm_powered && (
              <span className="px-2 py-0.5 bg-blue-500/20 text-blue-400 text-[10px] font-black uppercase tracking-widest border border-blue-500/30 rounded-lg flex items-center gap-1">
                <Sparkles size={10} /> AI Powered
              </span>
            )}
            <button 
              onClick={handleRefresh}
              className="p-2 hover:bg-white/10 rounded-xl text-slate-400 hover:text-white transition-all flex items-center gap-2 text-xs font-bold uppercase tracking-wider"
              title="Recalculate ATS Score"
            >
              <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
              {loading ? "Recalculating..." : "Refresh"}
            </button>
          </div>
          <p className="text-slate-400">Resume compatibility check</p>
        </div>
      </div>

      {error && (
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="p-4 bg-red-500/10 border border-red-500/20 rounded-2xl text-red-400 text-sm flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <AlertTriangle size={18} />
            {error}
          </div>
          <button onClick={() => setError(null)} className="p-1 hover:bg-white/10 rounded-lg">
            <X size={16} />
          </button>
        </motion.div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="card-glass p-8 flex flex-col items-center justify-center border-2 border-blue-500/20">
          <div className="relative w-32 h-32">
            <svg className="w-32 h-32 transform -rotate-90">
              <circle cx="64" cy="64" r="56" stroke="currentColor" strokeWidth="12" fill="transparent" className="text-white/5" />
              <circle cx="64" cy="64" r="56" stroke="currentColor" strokeWidth="12" fill="transparent" strokeDasharray={352} strokeDashoffset={352 - (352 * analysis.overall_score) / 100} className="text-blue-500" />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-4xl font-black text-white">{analysis.overall_score}</span>
              <span className="text-xs text-slate-500 font-bold uppercase">Score</span>
            </div>
          </div>
        </motion.div>

        <div className="md:col-span-2 card-glass p-8 space-y-6">
          <h3 className="text-xl font-bold text-white flex items-center gap-2">
            <BarChart3 className="text-blue-400" /> Category Breakdown
          </h3>
          <div className="space-y-4">
            {categories.map((cat) => (
              <div key={cat.name} className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">{cat.name}</span>
                  <span className="font-bold text-white">{cat.score}%</span>
                </div>
                <div className="h-3 bg-slate-900 rounded-full overflow-hidden">
                  <div className={`h-full ${cat.color} rounded-full`} style={{ width: `${cat.score}%` }}></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card-glass p-6">
          <h3 className="font-bold text-white mb-4 flex items-center justify-between">
            <span className="flex items-center gap-2">
              <AlertTriangle className="text-amber-400" /> Issues Found
            </span>
            <button 
              onClick={() => handleMagicFix()}
              disabled={optimizing}
              className="text-[10px] font-black uppercase tracking-tighter px-3 py-1 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 rounded-lg border border-blue-500/20 transition-all flex items-center gap-1"
            >
              {optimizing ? <Loader2 size={10} className="animate-spin" /> : <Sparkles size={10} />} Fix All
            </button>
          </h3>
          <div className="space-y-3">
            {analysis?.issues?.map((issue, i) => (
              <div key={i} className="p-4 bg-amber-500/10 border border-amber-500/20 rounded-xl text-slate-300 text-sm flex items-start justify-between gap-4 group">
                <span>{issue}</span>
                <button 
                  onClick={() => handleMagicFix()} 
                  className="shrink-0 p-1.5 bg-blue-500/20 text-blue-400 rounded-lg opacity-0 group-hover:opacity-100 transition-all hover:scale-110"
                  title="Apply AI Magic Fix"
                >
                  <Zap size={14} fill="currentColor" />
                </button>
              </div>
            ))}
          </div>
        </div>

        <div className="card-glass p-6">
          <h3 className="font-bold text-white mb-4 flex items-center gap-2">
            <Sparkles className="text-green-400" /> Recommendations
          </h3>
          <div className="space-y-3">
            {analysis?.recommendations?.map((rec, i) => (
              <div key={i} className="p-4 bg-green-500/10 border border-green-500/20 rounded-xl text-slate-300 text-sm flex gap-3">
                <CheckCircle2 size={18} className="text-green-400 shrink-0 mt-0.5" />
                {rec}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* New: Skill Extraction Section */}
      {analysis?.skill_analysis && (
        <div className="card-glass p-8 space-y-6">
          <h3 className="text-xl font-bold text-white flex items-center gap-2">
            <Target className="text-blue-400" /> Advanced Skill Extraction
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="space-y-3">
              <h4 className="text-xs font-black text-slate-500 uppercase tracking-widest px-1">Hard Skills</h4>
              <div className="flex flex-wrap gap-2">
                {analysis.skill_analysis.hard_skills?.map((skill, i) => (
                  <span key={i} className="px-3 py-1.5 bg-blue-500/10 border border-blue-500/20 rounded-lg text-blue-400 text-xs font-bold">{skill}</span>
                ))}
              </div>
            </div>
            <div className="space-y-3">
              <h4 className="text-xs font-black text-slate-500 uppercase tracking-widest px-1">Soft Skills</h4>
              <div className="flex flex-wrap gap-2">
                {analysis.skill_analysis.soft_skills?.map((skill, i) => (
                  <span key={i} className="px-3 py-1.5 bg-green-500/10 border border-green-500/20 rounded-lg text-green-400 text-xs font-bold">{skill}</span>
                ))}
              </div>
            </div>
            <div className="space-y-3">
              <h4 className="text-xs font-black text-slate-500 uppercase tracking-widest px-1">Tools & Platforms</h4>
              <div className="flex flex-wrap gap-2">
                {analysis.skill_analysis.tools?.map((skill, i) => (
                  <span key={i} className="px-3 py-1.5 bg-purple-500/10 border border-purple-500/20 rounded-lg text-purple-400 text-xs font-bold">{skill}</span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* New: Keyword Gap Analysis */}
      {analysis?.keyword_gap && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="card-glass p-6 space-y-4">
            <h3 className="font-bold text-white flex items-center gap-2">
              <CheckCircle2 className="text-green-400" /> Matched Keywords
            </h3>
            <div className="flex flex-wrap gap-2">
              {analysis.keyword_gap.matched?.map((keyword, i) => (
                <span key={i} className="px-3 py-1.5 bg-green-500/10 border border-green-500/20 rounded-lg text-green-400 text-xs font-medium">{keyword}</span>
              ))}
            </div>
          </div>
          <div className="card-glass p-6 space-y-4">
            <h3 className="font-bold text-white flex items-center gap-2">
              <AlertTriangle className="text-rose-400" /> Missing Keywords
            </h3>
            <div className="flex flex-wrap gap-2">
              {analysis.keyword_gap.missing?.map((keyword, i) => (
                <span key={i} className="px-3 py-1.5 bg-rose-500/10 border border-rose-500/20 rounded-lg text-rose-400 text-xs font-medium">{keyword}</span>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* New: Industry Optimization Section */}
      {analysis?.industry_tips && analysis.industry_tips.length > 0 && (
        <div className="card-glass p-8 bg-linear-to-r from-blue-600/5 to-indigo-600/5 border-blue-500/20">
          <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
            <Zap className="text-amber-400" /> Industry-Specific Optimization
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {analysis.industry_tips.map((tip, i) => (
              <div key={i} className="p-4 bg-white/5 border border-white/5 rounded-2xl text-slate-300 text-sm flex gap-3 hover:bg-white/10 transition-colors">
                <span className="text-blue-500 font-bold">•</span>
                {tip}
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="flex gap-4">
        <button 
          onClick={() => handleMagicFix()} 
          disabled={optimizing}
          className="flex-1 py-4 bg-linear-to-r from-blue-600 to-indigo-600 text-white font-black rounded-2xl hover:from-blue-500 hover:to-indigo-500 transition-all flex items-center justify-center gap-2 shadow-lg shadow-blue-500/20 disabled:opacity-50"
        >
          {optimizing ? <Loader2 className="animate-spin" /> : <Sparkles size={20} />} 
          {optimizing ? 'Analyzing & Fixing...' : 'Deep AI Optimization'}
        </button>
        <button onClick={() => navigate(`/app/resumes/${resumeId}/jobs`)} className="flex-1 py-4 bg-slate-800 text-white font-bold rounded-2xl hover:bg-slate-700 transition-all flex items-center justify-center gap-2">
          <Search size={20} /> Find Matching Jobs
        </button>
      </div>

      <AnimatePresence>
        {showComparison && optimizationResult && (
          <motion.div 
            ref={resultsRef}
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="w-full bg-slate-900/40 backdrop-blur-xl border-2 border-blue-500/20 rounded-3xl overflow-hidden flex flex-col shadow-2xl mt-12 mb-20 scroll-mt-10"
          >
            <div className="p-8 border-b border-white/5 flex items-center justify-between bg-blue-500/5">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-blue-500/20 rounded-2xl flex items-center justify-center">
                  <Sparkles className="text-blue-400" size={24} />
                </div>
                <div>
                  <h2 className="text-2xl font-black text-white uppercase tracking-tight">AI Optimization Results</h2>
                  <p className="text-sm text-slate-400 font-bold uppercase tracking-widest">Review enhancements before applying</p>
                </div>
              </div>
              <button 
                onClick={() => setShowComparison(false)}
                className="p-2 hover:bg-white/10 rounded-xl text-slate-400 hover:text-white transition-colors"
              >
                <X size={28} />
              </button>
            </div>

            <div className="p-8 space-y-10">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                 <div className="space-y-4">
                    <h3 className="text-sm font-black text-slate-500 uppercase tracking-widest flex items-center gap-2 px-1">
                      <ArrowRight size={16} className="rotate-180" /> Original Content
                    </h3>
                    <div className="p-8 bg-slate-900/50 border border-white/5 rounded-3xl text-slate-400 text-base leading-relaxed">
                      {optimizationResult.original_resume?.summary || "No summary provided in original resume."}
                    </div>
                 </div>
                 <div className="space-y-4">
                    <h3 className="text-sm font-black text-blue-500 uppercase tracking-widest flex items-center gap-2 px-1">
                      <Sparkles size={16} /> AI Enhanced Content
                    </h3>
                    <div className="p-8 bg-blue-500/5 border border-blue-500/20 rounded-3xl text-slate-100 text-base leading-relaxed font-medium">
                      {optimizationResult.optimized_resume?.summary || optimizationResult.suggestions}
                    </div>
                 </div>
              </div>

              <div className="space-y-4">
                <h3 className="text-sm font-black text-slate-500 uppercase tracking-widest flex items-center gap-2 px-1">
                  <CheckCircle2 size={16} className="text-green-400" /> Key Improvements
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {optimizationResult.improvements?.map((imp, i) => (
                    <div key={i} className="p-5 bg-white/5 border border-white/5 rounded-2xl flex items-center gap-4 text-sm text-slate-200 hover:bg-white/10 transition-colors">
                      <div className="w-6 h-6 bg-green-500/20 rounded-full flex items-center justify-center shrink-0">
                        <CheckCircle2 size={12} className="text-green-400" />
                      </div>
                      {imp}
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex flex-col md:flex-row items-center justify-between p-8 bg-green-500/5 border border-green-500/10 rounded-3xl gap-6">
                 <div className="flex items-center gap-6">
                    <div className="w-16 h-16 bg-green-500/20 rounded-2xl flex items-center justify-center">
                       <Target className="text-green-400" size={32} />
                    </div>
                    <div>
                       <p className="text-sm text-slate-400 font-bold uppercase tracking-widest">Projected ATS Score</p>
                       <p className="text-5xl font-black text-white">{optimizationResult.ats_score}% <span className="text-base text-green-400 font-black ml-2">+{optimizationResult.ats_score - analysis.overall_score} pts</span></p>
                    </div>
                 </div>
                 <div className="flex gap-4 w-full md:w-auto">
                    <button 
                      onClick={() => setShowComparison(false)}
                      className="flex-1 md:flex-none px-8 py-4 text-slate-400 font-black hover:text-white transition-colors uppercase tracking-widest text-sm"
                    >
                      Discard Changes
                    </button>
                    <button 
                      onClick={async () => {
                        try {
                          setOptimizing(true);
                          // Apply changes to the original resume
                          await resumeAPI.updateResume(resumeId, optimizationResult.optimized_resume);
                          setShowComparison(false);
                          // Refresh analysis to show the new ATS score
                          fetchAnalysis();
                        } catch (err) {
                          console.error("Apply error:", err);
                          setError("Failed to apply enhancements.");
                        } finally {
                          setOptimizing(false);
                        }
                      }}
                      disabled={optimizing}
                      className="flex-1 md:flex-none px-12 py-4 bg-green-600 text-white font-black rounded-2xl hover:bg-green-500 transition-all shadow-xl shadow-green-500/20 uppercase tracking-widest text-sm disabled:opacity-50"
                    >
                      {optimizing ? 'Applying...' : 'Apply Enhancements'}
                    </button>
                 </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default ATSAnalysis;

