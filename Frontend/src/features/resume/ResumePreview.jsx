import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowRight, Download, Printer, Edit3 } from 'lucide-react';
import { motion } from 'framer-motion';
import { resumeAPI } from '../../services/api';

const ResumePreview = () => {
  const { resumeId } = useParams();
  const navigate = useNavigate();
  const [resume, setResume] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchResume();
  }, [resumeId]);

  const fetchResume = async () => {
    try {
      // Use the preview endpoint which returns formatted data for display
      const response = await resumeAPI.getResumePreview(resumeId);
      setResume({ parsed_data: response.data });
    } catch (error) {
      console.error("Error fetching resume preview:", error);
      setResume({
        filename: "Resume Preview",
        parsed_data: {
          name: "",
          title: "",
          email: "",
          phone: "",
          location: "",
          summary: "",
          experience: [],
          education: [],
          skills: []
        }
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    window.print();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  const data = resume?.parsed_data || {};

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between no-print">
        <div className="flex items-center gap-4">
          <button onClick={() => navigate(`/app/resumes/${resumeId}`)} className="p-2 hover:bg-white/10 rounded-xl text-slate-400 hover:text-white">
            <ArrowRight className="rotate-180" size={20} />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-white">Resume Preview</h1>
            <p className="text-slate-400">{resume?.filename}</p>
          </div>
        </div>
        <div className="flex gap-3">
          <button onClick={() => navigate(`/app/resumes/${resumeId}/edit`)} className="flex items-center gap-2 px-4 py-2 bg-slate-800 text-white font-bold rounded-xl hover:bg-slate-700 transition-all">
            <Edit3 size={18} /> Edit
          </button>
          <button onClick={handleDownload} className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white font-bold rounded-xl hover:bg-blue-500 transition-all">
            <Download size={18} /> Download
          </button>
        </div>
      </div>

      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="bg-white rounded-sm shadow-2xl p-16 min-h-275 text-slate-900 font-serif print-only">
        <div className="text-center space-y-4 border-b-2 border-slate-900 pb-10 mb-10">
          <h1 className="text-5xl font-black tracking-tight uppercase">{data.name || "Your Name"}</h1>
          <p className="text-xl font-bold text-blue-600 italic">{data.title || "Professional Title"}</p>
          <div className="flex items-center justify-center gap-6 text-sm font-medium text-slate-600">
            <span>{data.email}</span>
            <span className="w-1.5 h-1.5 bg-slate-300 rounded-full"></span>
            <span>{data.phone}</span>
            <span className="w-1.5 h-1.5 bg-slate-300 rounded-full"></span>
            <span>{data.location}</span>
          </div>
        </div>

        <div className="space-y-12">
          {data.summary && (
            <div className="space-y-4">
              <h4 className="text-lg font-black uppercase tracking-widest border-b border-slate-200 pb-2">Professional Summary</h4>
              <p className="text-sm leading-relaxed text-slate-700">{data.summary}</p>
            </div>
          )}

          {data.experience?.length > 0 && (
            <div className="space-y-6">
              <h4 className="text-lg font-black uppercase tracking-widest border-b border-slate-200 pb-2">Experience</h4>
              {data.experience.map((exp, i) => (
                <div key={i} className="space-y-2">
                  <div className="flex justify-between items-baseline">
                    <h5 className="font-bold text-lg">{exp.company}</h5>
                    <span className="text-sm italic text-slate-500">{exp.duration}</span>
                  </div>
                  <p className="text-sm font-bold text-blue-600 italic mb-2">{exp.role}</p>
                  <p className="text-sm text-slate-700 leading-relaxed">{exp.desc}</p>
                </div>
              ))}
            </div>
          )}

          {data.education?.length > 0 && (
            <div className="space-y-4">
              <h4 className="text-lg font-black uppercase tracking-widest border-b border-slate-200 pb-2">Education</h4>
              {data.education.map((edu, i) => (
                <div key={i} className="flex justify-between">
                  <div>
                    <h5 className="font-bold text-slate-900">{edu.school}</h5>
                    <p className="text-sm text-slate-600">{edu.degree}</p>
                  </div>
                  <span className="text-sm italic text-slate-500">{edu.year}</span>
                </div>
              ))}
            </div>
          )}

          {data.projects?.length > 0 && (
            <div className="space-y-6">
              <h4 className="text-lg font-black uppercase tracking-widest border-b border-slate-200 pb-2">Key Projects</h4>
              {data.projects.map((proj, i) => (
                <div key={i} className="space-y-2">
                  <h5 className="font-bold text-lg">{proj.project_name}</h5>
                  <p className="text-sm text-slate-700 leading-relaxed">{proj.desc || proj.description}</p>
                </div>
              ))}
            </div>
          )}

          {data.skills?.length > 0 && (
            <div className="space-y-4">
              <h4 className="text-lg font-black uppercase tracking-widest border-b border-slate-200 pb-2">Expertise & Skills</h4>
              <div className="flex flex-wrap gap-x-8 gap-y-3">
                {data.skills.map((skill, i) => (
                  <div key={i} className="text-sm font-bold text-slate-800 flex items-center gap-2">
                    <div className="w-1.5 h-1.5 bg-blue-600 rounded-full"></div>
                    {skill}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </motion.div>
    </div>
  );
};

export default ResumePreview;

