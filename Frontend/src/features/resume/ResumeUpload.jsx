import React, { useState, useRef } from 'react';
import { Upload, FileText, CheckCircle2, AlertTriangle, Sparkles, ArrowRight } from 'lucide-react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { resumeAPI } from '../../services/api';

const ResumeUpload = () => {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadedResume, setUploadedResume] = useState(null);
  const [error, setError] = useState(null);

  const handleFileSelect = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (!file.type.includes('pdf') && !file.name.endsWith('.docx')) {
      setError('Only PDF and DOCX files are supported.');
      return;
    }

    setIsUploading(true);
    setError(null);
    setUploadProgress(0);

    try {
      const response = await resumeAPI.uploadResume(file, file.name, null);
      const resumeId = response.data.id;
      
      // Poll pipeline status
      let consecutiveErrors = 0;
      const interval = setInterval(async () => {
        try {
          const status = await resumeAPI.getPipelineStatus(resumeId);
          setUploadProgress(status.data.progress || 0);
          consecutiveErrors = 0; // Reset on success
          
          if (status.data.stages?.matched || status.data.progress >= 100 || status.data.status === 'complete') {
            clearInterval(interval);
            
            // Fetch the full resume data to show extracted info
            try {
              const resumeRes = await resumeAPI.getResume(resumeId);
              setUploadedResume(resumeRes.data);
            } catch (err) {
              console.error('Failed to fetch processed resume:', err);
              setUploadedResume({
                id: resumeId,
                filename: file.name,
                status: 'complete'
              });
            }
            setIsUploading(false);
          }
        } catch (e) {
          console.error('Status poll error:', e);
          consecutiveErrors++;
          
          // Stop polling if we get too many consecutive errors (e.g. 429 or network down)
          if (consecutiveErrors > 5) {
            clearInterval(interval);
            setIsUploading(false);
            setError('Lost connection to processing server. Please check your network or try again later.');
          }
        }
      }, 3000); // Slightly slower polling to be safer
    } catch (err) {
      console.error('Upload failed:', err);
      setError(err.response?.data?.detail || 'Failed to upload resume. Please try again.');
      setIsUploading(false);
    }
  };

  const triggerUpload = () => fileInputRef.current?.click();

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold text-white">Upload Your Resume</h1>
        <p className="text-slate-400 text-lg">We'll parse, analyze, and optimize it for job applications.</p>
      </div>

      <input type="file" ref={fileInputRef} onChange={handleFileSelect} className="hidden" accept=".pdf,.docx" />

      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-2xl flex items-center gap-3 text-rose-400">
          <AlertTriangle size={18} />
          <p>{error}</p>
        </div>
      )}

      {!uploadedResume ? (
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card-glass p-16 border-2 border-dashed border-white/10 hover:border-blue-500/30 transition-all text-center cursor-pointer"
          onClick={triggerUpload}
        >
          {isUploading ? (
            <div className="space-y-6">
              <div className="relative w-24 h-24 mx-auto">
                <div className="w-24 h-24 border-4 border-blue-600/20 border-t-blue-500 rounded-full animate-spin"></div>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-xl font-bold text-white">{uploadProgress}%</span>
                </div>
              </div>
              <div>
                <h3 className="text-2xl font-bold text-white">Processing Resume...</h3>
                <p className="text-slate-500 mt-2">Extracting skills, experience, and qualifications.</p>
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              <div className="w-24 h-24 bg-blue-600/10 rounded-full flex items-center justify-center mx-auto border border-blue-500/20">
                <Upload size={36} className="text-blue-400" />
              </div>
              <div>
                <h3 className="text-2xl font-bold text-white">Drop your resume here</h3>
                <p className="text-slate-400 mt-2">or click to browse files</p>
              </div>
              <div className="flex items-center justify-center gap-6 text-xs font-bold text-slate-500 uppercase tracking-widest">
                <span className="flex items-center gap-2"><CheckCircle2 size={14} className="text-green-500" /> PDF</span>
                <span className="flex items-center gap-2"><CheckCircle2 size={14} className="text-green-500" /> DOCX</span>
                <span className="flex items-center gap-2"><CheckCircle2 size={14} className="text-green-500" /> Private</span>
              </div>
            </div>
          )}
        </motion.div>
      ) : (
        <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="card-glass p-8 space-y-6">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-green-500/20 rounded-2xl flex items-center justify-center">
              <CheckCircle2 size={32} className="text-green-400" />
            </div>
            <div>
              <h3 className="text-2xl font-bold text-white">Resume Uploaded Successfully!</h3>
              <p className="text-slate-400">{uploadedResume.filename}</p>
            </div>
          </div>

          {uploadedResume.parsed_data && (
            <div className="p-6 bg-slate-900/50 rounded-2xl space-y-4">
              <h4 className="font-bold text-white flex items-center gap-2">
                <Sparkles size={18} className="text-blue-400" /> Extracted Information
              </h4>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div><span className="text-slate-500">Name:</span> <span className="text-white ml-2">{uploadedResume.parsed_data.full_name || uploadedResume.full_name}</span></div>
                <div><span className="text-slate-500">Email:</span> <span className="text-white ml-2">{uploadedResume.parsed_data.email || uploadedResume.email}</span></div>
              </div>
              <div>
                <span className="text-slate-500 text-sm">Skills Detected:</span>
                <div className="flex flex-wrap gap-2 mt-2">
                  {uploadedResume.parsed_data.skills?.map((skill, i) => (
                    <span key={i} className="px-3 py-1 bg-blue-500/20 border border-blue-500/30 rounded-full text-blue-400 text-sm">
                      {typeof skill === 'object' ? skill.name : skill}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}

          <div className="flex gap-4">
            <button onClick={() => navigate(`/app/resumes/${uploadedResume.id}`)} className="flex-1 py-4 bg-blue-600 text-white font-bold rounded-2xl hover:bg-blue-500 transition-all flex items-center justify-center gap-2">
              View Resume <ArrowRight size={20} />
            </button>
            <button onClick={() => navigate(`/app/resumes/${uploadedResume.id}/ats`)} className="flex-1 py-4 bg-slate-800 text-white font-bold rounded-2xl hover:bg-slate-700 transition-all">
              Run ATS Analysis
            </button>
          </div>
        </motion.div>
      )}
    </div>
  );
};

export default ResumeUpload;

