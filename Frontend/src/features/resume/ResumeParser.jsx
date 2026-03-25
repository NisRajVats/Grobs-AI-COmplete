import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { FileText, ArrowRight, Loader2, CheckCircle2, User, Mail, Phone, Briefcase, GraduationCap, Wrench, AlertCircle, RefreshCw } from 'lucide-react';
import { motion } from 'framer-motion';
import { resumeAPI } from '../../services/api';

const ResumeParser = () => {
  const { resumeId } = useParams();
  const navigate = useNavigate();
  const [isParsing, setIsParsing] = useState(false);
  const [parsedData, setParsedData] = useState(null);
  const [resume, setResume] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      if (!resumeId) { setLoading(false); return; }
      try {
        const res = await resumeAPI.getResume(resumeId);
        setResume(res.data);
        // If already parsed, load preview
        if (res.data.full_name && res.data.full_name !== 'Uploaded Resume') {
          const previewRes = await resumeAPI.getResumePreview(resumeId);
          setParsedData(previewRes.data);
        }
      } catch { setError('Failed to load resume.'); }
      finally { setLoading(false); }
    };
    load();
  }, [resumeId]);

  const handleParse = async () => {
    setIsParsing(true); setError(null);
    try {
      await resumeAPI.parseResume(resumeId);
      const previewRes = await resumeAPI.getResumePreview(resumeId);
      setParsedData(previewRes.data);
    } catch (err) {
      setError('Failed to parse resume. Make sure it is a valid PDF with readable text.');
    } finally { setIsParsing(false); }
  };

  if (loading) return <div className="flex items-center justify-center py-20"><Loader2 className="animate-spin text-blue-400" size={40} /></div>;

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div className="flex items-center gap-4">
        <button onClick={() => navigate('/app/resumes')} className="p-2 hover:bg-white/10 rounded-xl text-slate-400 hover:text-white">
          <ArrowRight className="rotate-180" size={20} />
        </button>
        <div>
          <h1 className="text-3xl font-bold text-white">Resume Parser</h1>
          <p className="text-slate-400">Extract structured data from your uploaded resume PDF</p>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-3 p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400">
          <AlertCircle size={20} /> <p className="text-sm">{error}</p>
        </div>
      )}

      {!parsedData ? (
        <div className="card-glass p-12 text-center space-y-6">
          <div className="w-20 h-20 bg-blue-600/20 rounded-2xl flex items-center justify-center mx-auto">
            <FileText size={40} className="text-blue-400" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-white">{resume?.title || 'Your Resume'}</h2>
            <p className="text-slate-400 mt-2">Click below to extract structured data from your PDF</p>
          </div>
          <button onClick={handleParse} disabled={isParsing || !resumeId} className="px-8 py-4 bg-blue-600 text-white font-bold rounded-2xl hover:bg-blue-500 disabled:opacity-50 transition-all flex items-center gap-3 mx-auto">
            {isParsing ? <><Loader2 size={20} className="animate-spin" /> Parsing...</> : <><FileText size={20} /> Parse Resume</>}
          </button>
        </div>
      ) : (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-green-400 font-bold">
              <CheckCircle2 size={20} /> Resume parsed successfully
            </div>
            <button onClick={handleParse} disabled={isParsing} className="flex items-center gap-2 px-4 py-2 bg-slate-800 text-slate-300 rounded-xl hover:bg-slate-700 text-sm font-bold transition-all">
              <RefreshCw size={16} className={isParsing ? 'animate-spin' : ''} /> Re-parse
            </button>
          </div>

          {/* Contact Info */}
          <div className="card-glass p-6 space-y-4">
            <h3 className="text-lg font-bold text-white flex items-center gap-2"><User size={18} className="text-blue-400" /> Contact Information</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[
                { label: 'Name', value: parsedData.full_name, icon: User },
                { label: 'Email', value: parsedData.email, icon: Mail },
                { label: 'Phone', value: parsedData.phone, icon: Phone },
              ].map(f => f.value && (
                <div key={f.label} className="flex items-center gap-3 p-3 bg-white/5 rounded-xl">
                  <f.icon size={16} className="text-slate-400 shrink-0" />
                  <div><p className="text-xs text-slate-500">{f.label}</p><p className="text-white text-sm font-medium">{f.value}</p></div>
                </div>
              ))}
            </div>
          </div>

          {/* Experience */}
          {parsedData.experience?.length > 0 && (
            <div className="card-glass p-6 space-y-4">
              <h3 className="text-lg font-bold text-white flex items-center gap-2"><Briefcase size={18} className="text-green-400" /> Experience</h3>
              {parsedData.experience.map((e, i) => (
                <div key={i} className="p-4 bg-white/5 rounded-xl space-y-1">
                  <p className="text-white font-bold">{e.role}</p>
                  <p className="text-slate-400 text-sm">{e.company}</p>
                  {e.description && <p className="text-slate-500 text-sm line-clamp-2">{e.description}</p>}
                </div>
              ))}
            </div>
          )}

          {/* Education */}
          {parsedData.education?.length > 0 && (
            <div className="card-glass p-6 space-y-4">
              <h3 className="text-lg font-bold text-white flex items-center gap-2"><GraduationCap size={18} className="text-amber-400" /> Education</h3>
              {parsedData.education.map((e, i) => (
                <div key={i} className="p-4 bg-white/5 rounded-xl">
                  <p className="text-white font-bold">{e.degree}</p>
                  <p className="text-slate-400 text-sm">{e.school}</p>
                  {e.major && <p className="text-slate-500 text-sm">{e.major}</p>}
                </div>
              ))}
            </div>
          )}

          {/* Skills */}
          {parsedData.skills?.length > 0 && (
            <div className="card-glass p-6 space-y-4">
              <h3 className="text-lg font-bold text-white flex items-center gap-2"><Wrench size={18} className="text-purple-400" /> Skills</h3>
              <div className="flex flex-wrap gap-2">
                {parsedData.skills.map((s, i) => (
                  <span key={i} className="px-3 py-1.5 bg-purple-500/10 border border-purple-500/20 rounded-lg text-purple-300 text-sm font-medium">{s.name || s}</span>
                ))}
              </div>
            </div>
          )}

          <button onClick={() => navigate(`/app/resumes/${resumeId}`)} className="w-full py-4 bg-blue-600 text-white font-bold rounded-2xl hover:bg-blue-500 transition-all flex items-center justify-center gap-2">
            View Full Resume <ArrowRight size={20} />
          </button>
        </motion.div>
      )}
    </div>
  );
};

export default ResumeParser;
