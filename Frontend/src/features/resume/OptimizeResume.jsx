import React, { useState } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { Sparkles, ArrowRight, CheckCircle2, RefreshCw, AlertCircle, Loader2, Target, Zap, FileText } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { resumeAPI } from '../../services/api';

const OptimizeResume = () => {
  const { resumeId } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const initialTab = searchParams.get('tab') === 'job' ? 'job' : 'general';
  
  const [activeTab, setActiveTab] = useState(initialTab);
  const [optimizing, setOptimizing] = useState(false);
  const [jobDescription, setJobDescription] = useState('');
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleOptimize = async () => {
    setOptimizing(true); 
    setError(null);
    try {
      // If general tab is active, we don't send job description even if it was typed
      const jdToSend = activeTab === 'job' ? jobDescription : '';
      const res = await resumeAPI.optimizeResume(resumeId, 'comprehensive', jdToSend);
      setResult(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Optimization failed. Make sure your resume has content.');
    } finally { 
      setOptimizing(false); 
    }
  };

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <button onClick={() => navigate(`/app/resumes/${resumeId}`)} className="p-2 hover:bg-white/10 rounded-xl text-slate-400 hover:text-white transition-colors">
            <ArrowRight className="rotate-180" size={20} />
          </button>
          <div>
            <h1 className="text-3xl font-bold text-white">AI Resume Optimization</h1>
            <p className="text-slate-400">Improve your resume with AI-powered suggestions</p>
          </div>
        </div>

        {!result && (
          <div className="flex p-1 bg-slate-900/80 border border-white/5 rounded-2xl">
            <button
              onClick={() => setActiveTab('general')}
              className={`px-4 py-2 rounded-xl text-sm font-bold transition-all ${activeTab === 'general' ? 'bg-blue-600 text-white shadow-lg' : 'text-slate-400 hover:text-slate-200'}`}
            >
              General
            </button>
            <button
              onClick={() => setActiveTab('job')}
              className={`px-4 py-2 rounded-xl text-sm font-bold transition-all ${activeTab === 'job' ? 'bg-green-600 text-white shadow-lg' : 'text-slate-400 hover:text-slate-200'}`}
            >
              Job-Specific
            </button>
          </div>
        )}
      </div>

      {error && (
        <div className="flex items-center gap-3 p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400">
          <AlertCircle size={20} /><p className="text-sm">{error}</p>
        </div>
      )}

      {!result ? (
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="card-glass p-8 md:p-12 text-center space-y-8"
          >
            {activeTab === 'general' ? (
              <>
                <div className="w-20 h-20 bg-linear-to-br from-blue-500 to-indigo-600 rounded-2xl flex items-center justify-center mx-auto shadow-lg shadow-blue-500/30">
                  <Zap size={40} className="text-white" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-white">General ATS Optimization</h2>
                  <p className="text-slate-400 mt-2 max-w-lg mx-auto">
                    Enhance your resume for general industry standards. We'll improve your language, 
                    quantify achievements, and ensure maximum ATS readability.
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-left">
                  {[
                    { title: 'Action Verbs', desc: 'Stronger professional language', icon: Zap, color: 'text-blue-400' },
                    { title: 'Quantification', desc: 'Metric-driven achievements', icon: Target, color: 'text-indigo-400' },
                    { title: 'ATS Friendly', desc: 'Optimized for parsing engines', icon: CheckCircle2, color: 'text-cyan-400' }
                  ].map((item, i) => (
                    <div key={i} className="p-4 bg-white/5 border border-white/5 rounded-xl space-y-2">
                      <item.icon size={20} className={item.color} />
                      <h4 className="font-bold text-white text-sm">{item.title}</h4>
                      <p className="text-xs text-slate-500">{item.desc}</p>
                    </div>
                  ))}
                </div>

                <button 
                  onClick={handleOptimize} 
                  disabled={optimizing} 
                  className="w-full md:w-auto px-12 py-4 bg-blue-600 text-white font-bold rounded-2xl hover:bg-blue-500 transition-all flex items-center justify-center gap-3 mx-auto disabled:opacity-50"
                >
                  {optimizing ? <><Loader2 size={20} className="animate-spin" /> Optimizing...</> : <><Sparkles size={20} /> Improve My Resume</>}
                </button>
              </>
            ) : (
              <>
                <div className="w-20 h-20 bg-linear-to-br from-green-500 to-emerald-600 rounded-2xl flex items-center justify-center mx-auto shadow-lg shadow-green-500/30">
                  <Target size={40} className="text-white" />
                </div>
                <div className="space-y-4">
                  <h2 className="text-2xl font-bold text-white">Job-Specific Tailoring</h2>
                  <p className="text-slate-400 mt-2 max-w-lg mx-auto">
                    Paste a job description to tailor your resume specifically for that role. 
                    We'll match keywords and highlight your most relevant experience.
                  </p>
                </div>

                <div className="space-y-4 text-left">
                  <label className="text-xs font-bold text-slate-500 uppercase tracking-widest block px-1  items-center gap-2">
                    <FileText size={14} /> Job Description
                  </label>
                  <textarea
                    value={jobDescription}
                    onChange={(e) => setJobDescription(e.target.value)}
                    placeholder="Paste the job description here..."
                    className="w-full h-48 bg-slate-900/50 border border-white/10 rounded-2xl px-5 py-4 text-white focus:ring-2 focus:ring-green-500/30 resize-none transition-all outline-none"
                  />
                </div>

                <button 
                  onClick={handleOptimize} 
                  disabled={optimizing || !jobDescription.trim()} 
                  className="w-full md:w-auto px-12 py-4 bg-green-600 text-white font-bold rounded-2xl hover:bg-green-500 transition-all flex items-center justify-center gap-3 mx-auto disabled:opacity-50"
                >
                  {optimizing ? <><Loader2 size={20} className="animate-spin" /> Tailoring...</> : <><Sparkles size={20} /> Tailor for this Job</>}
                </button>
              </>
            )}
          </motion.div>
        </AnimatePresence>
      ) : (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
          <div className="flex items-center gap-3 text-green-400 font-bold p-4 bg-green-500/10 border border-green-500/20 rounded-xl">
            <CheckCircle2 size={20} /> Optimization complete!
          </div>

          {result.suggestions && (
            <div className="card-glass p-8 space-y-4">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <Sparkles size={18} className="text-blue-400" /> AI Optimization Summary
              </h3>
              <div className="text-slate-300 text-sm leading-relaxed whitespace-pre-wrap">{result.suggestions}</div>
            </div>
          )}

          {result.improvements && result.improvements.length > 0 && (
            <div className="card-glass p-8 space-y-4">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <CheckCircle2 size={18} className="text-green-400" /> Specific Improvements Made
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {result.improvements.map((imp, i) => (
                  <div key={i} className="p-3 bg-white/5 border border-white/5 rounded-xl flex items-center gap-2 text-xs text-slate-300">
                    <CheckCircle2 size={14} className="text-green-500 shrink-0" /> {imp}
                  </div>
                ))}
              </div>
            </div>
          )}

          {result.compatibility_score > 0 && (
            <div className="card-glass p-8 space-y-4 border-blue-500/20">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <Target size={18} className="text-blue-400" /> Job Compatibility Score
                </h3>
                <span className="text-3xl font-black text-blue-400">{result.compatibility_score}%</span>
              </div>
              {result.compatibility_feedback && (
                <div className="p-4 bg-blue-500/5 border border-blue-500/10 rounded-xl">
                  <p className="text-sm text-slate-300 leading-relaxed italic">
                    "{result.compatibility_feedback}"
                  </p>
                </div>
              )}
            </div>
          )}

          {result.ats_score !== undefined && (
            <div className="card-glass p-6 flex items-center justify-between">
              <span className="text-slate-400 font-medium">Updated General ATS Score</span>
              <span className="text-3xl font-black text-green-400">{result.ats_score}%</span>
            </div>
          )}

          <div className="flex gap-3">
            <button onClick={handleOptimize} className="flex-1 py-4 bg-slate-800 text-white font-bold rounded-2xl hover:bg-slate-700 transition-all flex items-center justify-center gap-2">
              <RefreshCw size={18} /> Re-optimize
            </button>
            <button onClick={() => navigate(`/app/resumes/${resumeId}`)} className="flex-1 py-4 bg-blue-600 text-white font-bold rounded-2xl hover:bg-blue-500 transition-all flex items-center justify-center gap-2">
              View Resume <ArrowRight size={18} />
            </button>
          </div>
        </motion.div>
      )}
    </div>
  );
};

export default OptimizeResume;
