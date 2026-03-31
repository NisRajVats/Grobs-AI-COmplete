import React, { useState, useEffect, useRef, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  Briefcase,
  FileText,
  Target,
  Sparkles,
  Zap,
  CheckCircle2,
  AlertCircle,
  Award,
  BarChart3,
  Loader2,
  Send,
  Upload,
  Edit3,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { resumeAPI } from "../../services/api";

const JobOptimization = () => {
  const { resumeId } = useParams();
  const navigate = useNavigate();
  const [resume, setResume] = useState(null);
  const [loading, setLoading] = useState(true);
  const [jobDescription, setJobDescription] = useState("");
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [error, setError] = useState(null);
  const resultsRef = useRef(null);

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

  useEffect(() => {
    fetchResume();
  }, [fetchResume]);

  const handleAnalyze = async () => {
    if (!jobDescription.trim()) return;
    setAnalyzing(true);
    setError(null);
    try {
      // Calling the backend optimize endpoint
      const response = await resumeAPI.optimizeResume(
        resumeId,
        "job-specific",
        jobDescription,
        null,
        false
      );
      
      const result = response.data;
      
      if (result.success) {
        setAnalysisResult({
          selectionChance: result.compatibility_score || 0,
          skillGap: result.skill_gap || [],
          matchingSkills: result.matching_skills || [],
          skillRecommendations: result.skill_recommendations || [],
          certificateRecommendations: result.certificate_recommendations || [],
          comparison: result.compatibility_feedback || result.suggestions || "No detailed comparison available."
        });

        // Smooth scroll to results
        setTimeout(() => {
          resultsRef.current?.scrollIntoView({ behavior: "smooth" });
        }, 100);
      } else {
        setError(result.error || "Analysis failed. Please try again.");
      }

    } catch (err) {
      console.error("Analysis failed:", err);
      setError("Failed to connect to the analysis service. Please check your connection.");
    } finally {
      setAnalyzing(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate(`/app/resumes/${resumeId}`)}
          className="p-2 hover:bg-white/10 rounded-xl text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft size={20} />
        </button>
        <div>
          <h1 className="text-3xl font-bold text-white">Job Optimisation</h1>
          <p className="text-slate-400">Compare your resume with a specific job description</p>
        </div>
      </div>

      {/* Main Content - Two Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left Section: Resume Preview */}
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-white font-bold mb-2">
            <FileText className="text-blue-400" size={20} />
            Current Resume Preview
          </div>
          <div className="card-glass h-150 overflow-y-auto p-8 bg-white text-slate-900 rounded-2xl shadow-2xl">
            {resume?.parsed_data ? (
              <div className="space-y-6 text-sm">
                <div className="text-center border-b pb-4">
                  <h2 className="text-2xl font-bold uppercase">{resume.parsed_data.full_name || resume.filename}</h2>
                  <p className="text-slate-600 font-medium">{resume.parsed_data.title}</p>
                </div>
                
                {resume.parsed_data.summary && (
                  <div>
                    <h3 className="font-bold border-b mb-2 uppercase tracking-wide">Professional Summary</h3>
                    <p className="leading-relaxed">{resume.parsed_data.summary}</p>
                  </div>
                )}

                <div>
                  <h3 className="font-bold border-b mb-2 uppercase tracking-wide">Experience</h3>
                  <div className="space-y-4">
                    {(resume.parsed_data.experience || []).map((exp, i) => (
                      <div key={i}>
                        <div className="flex justify-between font-bold">
                          <span>{exp.role}</span>
                          <span className="text-slate-500 text-xs">{exp.duration || (exp.start_date + " - " + exp.end_date)}</span>
                        </div>
                        <p className="text-slate-700 italic">{exp.company}</p>
                        <p className="mt-1 text-xs">{exp.description || exp.desc}</p>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <h3 className="font-bold border-b mb-2 uppercase tracking-wide">Skills</h3>
                  <div className="flex flex-wrap gap-2">
                    {(resume.parsed_data.skills || []).map((skill, i) => (
                      <span key={i} className="px-2 py-1 bg-slate-100 rounded border text-xs">
                        {typeof skill === 'string' ? skill : skill.name}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-slate-400 space-y-4">
                <FileText size={48} className="opacity-20" />
                <p>No preview available</p>
              </div>
            )}
          </div>
        </div>

        {/* Right Section: Job Description Input */}
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-white font-bold mb-2">
            <Briefcase className="text-green-400" size={20} />
            Target Job Description
          </div>
          <div className="card-glass h-150 flex flex-col p-6 space-y-4">
            <div className="flex-1 flex flex-col space-y-2">
              <label className="text-xs font-bold text-slate-400 uppercase tracking-widest">
                Paste Job Description
              </label>
              <textarea
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                placeholder="Paste the full job description here..."
                className="flex-1 w-full bg-slate-900/50 border border-white/10 rounded-2xl p-4 text-sm text-white focus:ring-1 focus:ring-green-500/30 outline-none resize-none transition-all leading-relaxed"
              />
            </div>
            
            <div className="p-4 bg-blue-500/5 border border-blue-500/10 rounded-xl space-y-2">
              <p className="text-xs text-blue-400 font-bold flex items-center gap-2">
                <Upload size={14} /> Quick Tips
              </p>
              <ul className="text-[11px] text-slate-400 space-y-1 list-disc pl-4">
                <li>Include the Job Title and Key Responsibilities</li>
                <li>Paste the required Skills and Qualifications</li>
                <li>Mention the Company's culture if available</li>
              </ul>
            </div>

            {error && (
              <motion.div 
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl flex items-center gap-3 text-rose-400 text-sm"
              >
                <AlertCircle size={18} />
                {error}
              </motion.div>
            )}

            <button
              onClick={handleAnalyze}
              disabled={analyzing || !jobDescription.trim()}
              className="w-full py-4 bg-linear-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-black rounded-2xl shadow-xl shadow-blue-900/20 transition-all flex items-center justify-center gap-3 disabled:opacity-50 group"
            >
              {analyzing ? (
                <>
                  <Loader2 className="animate-spin" size={20} />
                  <span>Analyzing...</span>
                </>
              ) : (
                <>
                  <Sparkles size={20} className="group-hover:scale-125 transition-transform" />
                  <span>Analyse</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Analysis Results Section */}
      <AnimatePresence>
        {analysisResult && (
          <motion.div
            ref={resultsRef}
            initial={{ opacity: 0, y: 100 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 50 }}
            transition={{ type: "spring", damping: 20, stiffness: 100 }}
            className="space-y-8 pt-8"
          >
            <div className="text-center space-y-2">
              <h2 className="text-4xl font-black text-white">Analysis Results</h2>
              <p className="text-slate-400">Here's how your resume stacks up against the job</p>
            </div>

            <div className="flex flex-col gap-8">
              {/* 1. Optimisation Recommendation */}
              <div className="card-glass p-8 space-y-4">
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <BarChart3 className="text-indigo-400" size={20} /> Optimisation Recommendation
                </h3>
                <div className="p-6 bg-slate-900/50 rounded-2xl border border-white/5">
                  <p className="text-slate-300 leading-relaxed text-sm italic">
                    "{analysisResult.comparison}"
                  </p>
                </div>
              </div>

              {/* 2. Button to "optimise my resume" */}
              <div className="flex justify-center">
                 <button 
                   onClick={() => navigate(`/app/resumes/${resumeId}/edit`)}
                   className="w-full md:w-auto px-12 py-4 bg-white text-slate-900 font-black rounded-2xl hover:bg-slate-100 transition-all flex items-center justify-center gap-2 shadow-xl shadow-white/5"
                 >
                   <Edit3 size={20} /> Optimise my resume
                 </button>
              </div>

              {/* 3. Skill Gap Analysis & 4. Selection Chance */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div className="md:col-span-3 card-glass p-8 space-y-6">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-bold text-white flex items-center gap-2">
                      <Zap className="text-amber-400" size={20} /> Skill Gap Analysis
                    </h3>
                    <span className="px-3 py-1 bg-amber-500/10 text-amber-400 text-[10px] font-black uppercase rounded-full border border-amber-500/20">
                      High Impact
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <div className="space-y-4">
                      <p className="text-xs font-bold text-slate-400 uppercase tracking-widest">Matching Skills</p>
                      <div className="flex flex-wrap gap-2">
                        {analysisResult.matchingSkills.map((skill, i) => (
                          <span key={i} className="px-3 py-1.5 bg-green-500/10 text-green-400 text-xs font-medium rounded-lg border border-green-500/20 flex items-center gap-2">
                            <CheckCircle2 size={12} /> {skill}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div className="space-y-4">
                      <p className="text-xs font-bold text-rose-400 uppercase tracking-widest">Missing Skills</p>
                      <div className="flex flex-wrap gap-2">
                        {analysisResult.skillGap.map((skill, i) => (
                          <span key={i} className="px-3 py-1.5 bg-rose-500/10 text-rose-400 text-xs font-medium rounded-lg border border-rose-500/20 flex items-center gap-2">
                            <AlertCircle size={12} /> {skill}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="card-glass p-6 flex flex-col items-center justify-center text-center space-y-3 border-blue-500/20">
                  <div className="w-20 h-20 rounded-full border-4 border-blue-500/20 flex items-center justify-center relative">
                     <div 
                       className="absolute inset-0 rounded-full border-4 border-blue-500" 
                       style={{ clipPath: `inset(${100 - analysisResult.selectionChance}% 0 0 0)` }}
                     />
                     <span className="text-2xl font-black text-white">{analysisResult.selectionChance}%</span>
                  </div>
                  <div>
                    <h4 className="font-bold text-white uppercase text-xs tracking-widest">Selection Chance</h4>
                    <p className="text-[10px] text-slate-400 mt-1">Based on AI analysis</p>
                  </div>
                </div>

                {/* 5. Skill Recommendation */}
                <div className="md:col-span-2 card-glass p-8 space-y-6">
                   <h3 className="text-lg font-bold text-white flex items-center gap-2">
                      <Sparkles className="text-blue-400" size={20} /> Skill Recommendation
                    </h3>
                    <div className="space-y-4">
                      {analysisResult.skillRecommendations.map((rec, i) => (
                        <div key={i} className="p-4 bg-slate-900/50 rounded-xl border border-white/5 flex gap-3">
                          <div className="w-6 h-6 rounded-full bg-blue-500/20 flex items-center justify-center shrink-0">
                            <span className="text-[10px] font-black text-blue-400">{i + 1}</span>
                          </div>
                          <p className="text-sm text-slate-300 leading-relaxed">{rec}</p>
                        </div>
                      ))}
                    </div>
                </div>

                {/* 6. Certificate Recommendation */}
                <div className="md:col-span-2 card-glass p-8 space-y-6">
                   <h3 className="text-lg font-bold text-white flex items-center gap-2">
                      <Award className="text-purple-400" size={20} /> Certificate Recommendation
                    </h3>
                    <div className="space-y-4">
                      {analysisResult.certificateRecommendations.map((cert, i) => (
                        <div key={i} className="p-4 bg-slate-900/50 rounded-xl border border-white/5 flex items-center justify-between group hover:border-purple-500/30 transition-all cursor-pointer">
                          <div className="flex items-center gap-3">
                            <div className="p-2 bg-purple-500/10 rounded-lg text-purple-400">
                              <Award size={16} />
                            </div>
                            <span className="text-sm font-medium text-slate-300">{cert}</span>
                          </div>
                          <Send size={14} className="text-slate-600 group-hover:text-purple-400 transition-colors" />
                        </div>
                      ))}
                    </div>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default JobOptimization;
