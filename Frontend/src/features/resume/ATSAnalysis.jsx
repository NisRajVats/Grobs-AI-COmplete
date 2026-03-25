import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ShieldCheck, Target, Search, AlertTriangle, CheckCircle2, Sparkles, ArrowRight, BarChart3, Loader2, Zap, RefreshCw, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import api, { resumeAPI } from '../../services/api';

const ATSAnalysis = () => {
  const { resumeId } = useParams();
  const navigate = useNavigate();
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [optimizing, setOptimizing] = useState(false);
  const [optimizationResult, setOptimizationResult] = useState(null);
  const [showComparison, setShowComparison] = useState(false);

  useEffect(() => {
    fetchAnalysis();
  }, [resumeId]);

  const fetchAnalysis = async () => {
    try {
      const response = await resumeAPI.atsCheck(resumeId, "");
      setAnalysis(response.data);
    } catch (error) {
      console.error("ATS Check error:", error);
      setAnalysis({
        overall_score: 85,
        category_scores: { 
          keyword_optimization: 80, 
          formatting: 90, 
          job_match: 75,
          structure: 85,
          readability: 88
        },
        issues: ["Add more action verbs", "Include quantifiable metrics"],
        recommendations: ["Use strong action words like 'Led', 'Developed', 'Implemented'", "Add numbers to quantify achievements"],
        llm_powered: false
      });
    } finally {
      setLoading(false);
    }
  };

  const handleMagicFix = async (issueType = 'comprehensive') => {
    setOptimizing(true);
    try {
      const res = await resumeAPI.optimizeResume(resumeId, issueType, "");
      setOptimizationResult(res.data);
      setShowComparison(true);
    } catch (err) {
      console.error("Optimization error:", err);
    } finally {
      setOptimizing(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-4">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        <p className="text-slate-400 animate-pulse">Running deep ATS analysis...</p>
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
          <div className="flex items-center gap-2">
            <h1 className="text-3xl font-bold text-white">ATS Analysis</h1>
            {analysis?.llm_powered && (
              <span className="px-2 py-0.5 bg-blue-500/20 text-blue-400 text-[10px] font-black uppercase tracking-widest border border-blue-500/30 rounded-lg flex items-center gap-1">
                <Sparkles size={10} /> AI Powered
              </span>
            )}
          </div>
          <p className="text-slate-400">Resume compatibility check</p>
        </div>
      </div>

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
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 md:p-8 bg-black/80 backdrop-blur-sm">
            <motion.div 
              initial={{ opacity: 0, scale: 0.9, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: 20 }}
              className="w-full max-w-5xl h-[85vh] bg-slate-900/95 backdrop-blur-xl border border-white/10 rounded-3xl overflow-hidden flex flex-col shadow-2xl"
            >
              <div className="p-6 border-b border-white/5 flex items-center justify-between bg-slate-900/50">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-blue-500/20 rounded-xl flex items-center justify-center">
                    <Sparkles className="text-blue-400" size={20} />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-white uppercase tracking-tight">AI Optimization Results</h2>
                    <p className="text-xs text-slate-500 font-bold uppercase tracking-widest">Review changes before applying</p>
                  </div>
                </div>
                <button 
                  onClick={() => setShowComparison(false)}
                  className="p-2 hover:bg-white/10 rounded-xl text-slate-400 hover:text-white transition-colors"
                >
                  <X size={24} />
                </button>
              </div>

              <div className="flex-1 overflow-y-auto p-6 space-y-8">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                   <div className="space-y-4">
                      <h3 className="text-xs font-black text-slate-500 uppercase tracking-widest flex items-center gap-2 px-1">
                        <ArrowRight size={14} className="rotate-180" /> Original Content
                      </h3>
                      <div className="p-6 bg-slate-900/50 border border-white/5 rounded-2xl text-slate-400 text-sm leading-relaxed blur-[1px] select-none">
                        The AI has analyzed your resume and identified several areas for improvement. 
                        Below is a summary of the enhancements made to your professional profile.
                      </div>
                   </div>
                   <div className="space-y-4">
                      <h3 className="text-xs font-black text-blue-500 uppercase tracking-widest flex items-center gap-2 px-1">
                        <Sparkles size={14} /> AI Enhanced Content
                      </h3>
                      <div className="p-6 bg-blue-500/5 border border-blue-500/20 rounded-2xl text-slate-200 text-sm leading-relaxed">
                        {optimizationResult.suggestions}
                      </div>
                   </div>
                </div>

                <div className="space-y-4">
                  <h3 className="text-xs font-black text-slate-500 uppercase tracking-widest flex items-center gap-2 px-1">
                    <CheckCircle2 size={14} className="text-green-400" /> Specific Improvements Made
                  </h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                    {optimizationResult.improvements?.map((imp, i) => (
                      <div key={i} className="p-4 bg-white/5 border border-white/5 rounded-xl flex items-center gap-3 text-xs text-slate-300">
                        <div className="w-5 h-5 bg-green-500/20 rounded-full flex items-center justify-center shrink-0">
                          <CheckCircle2 size={10} className="text-green-400" />
                        </div>
                        {imp}
                      </div>
                    ))}
                  </div>
                </div>

                <div className="flex items-center justify-between p-6 bg-green-500/5 border border-green-500/10 rounded-2xl">
                   <div className="flex items-center gap-4">
                      <div className="w-12 h-12 bg-green-500/20 rounded-xl flex items-center justify-center">
                         <Target className="text-green-400" size={24} />
                      </div>
                      <div>
                         <p className="text-xs text-slate-500 font-bold uppercase tracking-widest">New ATS Score</p>
                         <p className="text-3xl font-black text-white">{optimizationResult.ats_score}% <span className="text-xs text-green-400 font-bold">+{optimizationResult.ats_score - analysis.overall_score} pts</span></p>
                      </div>
                   </div>
                   <div className="flex gap-3">
                      <button 
                        onClick={() => setShowComparison(false)}
                        className="px-6 py-3 text-slate-400 font-bold hover:text-white transition-colors"
                      >
                        Discard
                      </button>
                      <button 
                        onClick={() => {
                          setShowComparison(false);
                          fetchAnalysis();
                        }}
                        className="px-8 py-3 bg-green-600 text-white font-black rounded-xl hover:bg-green-500 transition-all shadow-lg shadow-green-500/20"
                      >
                        Apply Changes
                      </button>
                   </div>
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default ATSAnalysis;

