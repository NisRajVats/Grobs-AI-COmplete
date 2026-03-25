import React, { useState, useRef } from 'react';
import { 
  ShieldCheck, 
  Upload, 
  FileText, 
  Search, 
  AlertTriangle, 
  CheckCircle2, 
  Sparkles, 
  ArrowRight,
  Target,
  BarChart3,
  ChevronDown,
  Info
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../../services/api';

const ATSChecker = () => {
  const [isUploading, setIsUploading] = useState(false);
  const [jobDescription, setJobDescription] = useState('');
  const [analysis, setAnalysis] = useState(null);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileSelect = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    if (!file.type.includes('pdf')) {
      setError('Only PDF files are supported for deep ATS analysis.');
      return;
    }

    setIsUploading(true);
    setError(null);

    try {
      // 1. Upload and parse the resume
      const formData = new FormData();
      formData.append('file', file);
      
      const uploadResponse = await api.post('/api/resumes/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      const resumeId = uploadResponse.data.resume_id;

      // 2. Perform ATS Check
      const atsResponse = await api.post(`/api/resumes/${resumeId}/ats-check`, {
        job_description: jobDescription
      });

      const data = atsResponse.data;
      
      // Adapt backend response to frontend format
      setAnalysis({
        score: data.overall_score,
        matchRate: data.category_scores.job_match || 0,
        // Since backend doesn't return found/missing keywords specifically in the response 
        // (it uses them internally), we'll adapt from issues/recommendations or use defaults
        keywordsFound: data.category_scores.keyword_optimization > 50 ? ['Detected'] : [],
        missingKeywords: data.issues.filter(i => i.toLowerCase().includes('keyword')).length > 0 ? ['Technical Skills'] : [],
        issues: data.issues.map(issue => ({
          type: 'Analysis',
          message: issue,
          severity: issue.toLowerCase().includes('critical') || issue.toLowerCase().includes('missing') ? 'high' : 'medium'
        })),
        recommendations: data.recommendations
      });

    } catch (err) {
      console.error('ATS Check error:', err);
      setError(err.response?.data?.detail || 'Failed to analyze resume. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  const triggerUpload = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="max-w-5xl mx-auto space-y-12 pb-20">
      <div className="text-center space-y-6">
        <div className="inline-flex items-center gap-3 px-5 py-2.5 bg-blue-500/10 border border-blue-500/20 rounded-full text-blue-400 text-sm font-black shadow-lg shadow-blue-500/5">
          <ShieldCheck size={20} />
          <span>ATS SCORE OPTIMIZER</span>
        </div>
        <h1 className="text-5xl md:text-6xl font-black text-white tracking-tight">Be <span className="text-blue-500 italic">Unstoppable</span></h1>
        <p className="text-xl text-slate-400 max-w-2xl mx-auto leading-relaxed">
          Analyze your resume against any job description. Get deep insights on format, keywords, and overall match rate.
        </p>
      </div>

      <input 
        type="file" 
        ref={fileInputRef} 
        onChange={handleFileSelect} 
        className="hidden" 
        accept=".pdf"
      />

      {!analysis && (
        <div className="max-w-2xl mx-auto space-y-4">
          <div className="flex items-center justify-between px-1">
            <label className="text-xs font-bold text-slate-500 uppercase tracking-widest flex items-center gap-2">
              <Target size={14} className="text-blue-500" /> Job Description (Optional)
            </label>
            {jobDescription && (
              <button 
                onClick={() => setJobDescription('')}
                className="text-[10px] font-bold text-rose-400 hover:text-rose-300 uppercase tracking-tighter"
              >
                Clear
              </button>
            )}
          </div>
          <textarea
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            placeholder="Paste the job description here for a tailored compatibility analysis..."
            className="w-full h-32 bg-slate-900/50 border border-white/10 rounded-2xl px-5 py-4 text-white focus:ring-2 focus:ring-blue-500/30 resize-none transition-all outline-none text-sm leading-relaxed"
          />
        </div>
      )}

      {error && (
        <motion.div 
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-2xl flex items-center gap-3 text-rose-400 text-sm max-w-2xl mx-auto"
        >
          <AlertTriangle size={18} />
          <p>{error}</p>
        </motion.div>
      )}

      {!analysis ? (
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card-glass p-16 border-2 border-dashed border-white/10 hover:border-blue-500/30 transition-all text-center group cursor-pointer"
          onClick={triggerUpload}
        >
          {isUploading ? (
            <div className="space-y-8 py-10">
              <div className="relative inline-block">
                <div className="w-24 h-24 border-4 border-blue-600/20 border-t-blue-500 rounded-full animate-spin"></div>
                <div className="absolute inset-0 flex items-center justify-center">
                   <ShieldCheck size={32} className="text-blue-400 animate-pulse" />
                </div>
              </div>
              <div className="space-y-3">
                 <h3 className="text-2xl font-bold text-white">Deep Scanning Resume...</h3>
                 <p className="text-slate-500 font-medium">Applying AI heuristic models to analyze format and keywords.</p>
              </div>
            </div>
          ) : (
            <div className="space-y-8">
              <div className="w-24 h-24 bg-blue-600/10 rounded-full flex items-center justify-center mx-auto group-hover:scale-110 group-hover:bg-blue-600/20 transition-all duration-500 border border-blue-500/20 shadow-2xl">
                <Upload size={36} className="text-blue-400" />
              </div>
              <div className="space-y-4">
                <h3 className="text-3xl font-black text-white">Upload Your Resume</h3>
                <p className="text-slate-400 max-w-sm mx-auto text-lg">Drag and drop your PDF or Word file here to start the analysis.</p>
                <div className="flex items-center justify-center gap-6 pt-4 text-xs font-bold text-slate-500 uppercase tracking-widest">
                   <div className="flex items-center gap-2"><CheckCircle2 size={14} className="text-green-500" /> PDF SUPPORT</div>
                   <div className="flex items-center gap-2"><CheckCircle2 size={14} className="text-green-500" /> DOCX SUPPORT</div>
                   <div className="flex items-center gap-2"><CheckCircle2 size={14} className="text-green-500" /> 100% PRIVATE</div>
                </div>
              </div>
            </div>
          )}
        </motion.div>
      ) : (
        <motion.div 
           initial={{ opacity: 0, scale: 0.95 }}
           animate={{ opacity: 1, scale: 1 }}
           className="space-y-8"
        >
           {/* Score Header */}
           <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="card-glass p-10 flex flex-col items-center justify-center text-center space-y-4 border-2 border-blue-500/20 shadow-[0_32px_64px_-16px_rgba(59,130,246,0.3)]">
                  <div className="relative">
                    <svg className="w-40 h-40">
                      <circle cx="80" cy="80" r="70" stroke="currentColor" strokeWidth="12" fill="transparent" className="text-white/5" />
                      <circle cx="80" cy="80" r="70" stroke="currentColor" strokeWidth="12" fill="transparent" strokeDasharray={440} strokeDashoffset={440 - (440 * analysis.score) / 100} className="text-blue-500 drop-shadow-[0_0_10px_rgba(59,130,246,0.5)]" />
                    </svg>
                    <div className="absolute inset-0 flex flex-col items-center justify-center">
                       <span className="text-5xl font-black text-white">{analysis.score}</span>
                       <span className="text-xs font-black text-slate-500 tracking-widest uppercase">ATS SCORE</span>
                    </div>
                  </div>
              </div>

              <div className="md:col-span-2 card-glass p-10 space-y-8 border-white/5">
                 <div className="flex items-center justify-between">
                    <h3 className="text-2xl font-bold text-white flex items-center gap-3">
                       <Sparkles className="text-amber-400" /> AI Insights
                    </h3>
                    <button className="text-xs font-bold text-blue-400 hover:text-white transition-colors flex items-center gap-2">
                       Full Report <ArrowRight size={14} />
                    </button>
                 </div>
                 
                 <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                    <div className="p-6 bg-slate-900/60 rounded-2xl border border-white/5 space-y-3">
                       <div className="flex items-center gap-2 text-green-400">
                          <CheckCircle2 size={18} />
                          <h4 className="font-bold">Match Rate</h4>
                       </div>
                       <p className="text-3xl font-black text-white">{analysis.matchRate}%</p>
                       <p className="text-sm text-slate-400">Strong alignment with the role.</p>
                    </div>
                    <div className="p-6 bg-slate-900/60 rounded-2xl border border-white/5 space-y-3">
                       <div className="flex items-center gap-2 text-rose-400">
                          <AlertTriangle size={18} />
                          <h4 className="font-bold">Critical Issues</h4>
                       </div>
                       <p className="text-3xl font-black text-white">{analysis.issues.length}</p>
                       <p className="text-sm text-slate-400">Requires immediate attention.</p>
                    </div>
                 </div>
              </div>
           </div>

           <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Recommendations */}
              <div className="card-glass p-8 space-y-8">
                 <h3 className="text-xl font-bold text-white flex items-center gap-2">
                    <Info size={20} className="text-blue-400" /> Recommendations
                 </h3>
                 <div className="space-y-4">
                    {analysis.recommendations.map((rec, idx) => (
                       <div key={idx} className="p-4 bg-white/5 border border-white/5 rounded-xl text-sm text-slate-300 flex gap-3">
                          <span className="text-blue-400 font-bold">•</span>
                          {rec}
                       </div>
                    ))}
                 </div>
              </div>

              {/* Fix Suggestions / Issues */}
              <div className="card-glass p-8 space-y-8">
                 <h3 className="text-xl font-bold text-white">Issues Found</h3>
                 <div className="space-y-4">
                    {analysis.issues.map((issue, idx) => (
                       <div key={idx} className="p-5 bg-white/5 border border-white/5 rounded-2xl flex gap-4 group hover:bg-white/10 transition-all cursor-default">
                          <div className={`p-3 h-fit rounded-xl ${issue.severity === 'high' ? 'bg-rose-500/10 text-rose-400' : 'bg-amber-500/10 text-amber-400'}`}>
                             <AlertTriangle size={20} />
                          </div>
                          <div className="space-y-1">
                             <div className="flex items-center gap-2">
                                <span className="font-bold text-white text-sm">{issue.type}</span>
                                <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-widest ${issue.severity === 'high' ? 'bg-rose-500/20 text-rose-400' : 'bg-amber-500/20 text-amber-400'}`}>{issue.severity}</span>
                             </div>
                             <p className="text-sm text-slate-400 leading-relaxed">{issue.message}</p>
                          </div>
                       </div>
                    ))}
                    <button 
                       onClick={() => setAnalysis(null)}
                       className="w-full py-4 mt-4 bg-slate-800 hover:bg-slate-700 text-white font-black rounded-2xl transition-all"
                    >
                       Analyze Another Resume
                    </button>
                 </div>
              </div>
           </div>
        </motion.div>
      )}
    </div>
  );
};

export default ATSChecker;
