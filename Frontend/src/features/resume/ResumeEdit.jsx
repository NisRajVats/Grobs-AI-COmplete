import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { resumeAPI } from '../../services/api';
import { 
  FileText, 
  User, 
  Briefcase, 
  GraduationCap, 
  Wrench, 
  Plus, 
  Trash2, 
  Save, 
  Sparkles,
  ChevronRight,
  ChevronLeft,
  ArrowLeft,
  Link as LinkIcon,
  Github,
  X
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const ResumeEdit = () => {
  const { resumeId } = useParams();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('personal');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveMsg, setSaveMsg] = useState('');
  
  const [resumeData, setResumeData] = useState({
    personal: { name: '', title: '', email: '', phone: '', location: '' },
    summary: '',
    experience: [],
    education: [],
    projects: [],
    skills: []
  });

  const tabs = [
    { id: 'personal', label: 'Personal Info', icon: User },
    { id: 'summary', label: 'Summary', icon: Sparkles },
    { id: 'experience', label: 'Experience', icon: Briefcase },
    { id: 'education', label: 'Education', icon: GraduationCap },
    { id: 'skills', label: 'Skills', icon: Wrench },
  ];

  const tabOrder = ['personal', 'summary', 'experience', 'education', 'skills'];

  useEffect(() => {
    fetchResume();
  }, [resumeId]);

  const fetchResume = async () => {
    try {
      const response = await resumeAPI.getResumePreview(resumeId);
      const data = response.data;
      
      setResumeData({
        personal: { 
          name: data.full_name || data.name || '', 
          title: data.title || '', 
          email: data.email || '', 
          phone: data.phone || '', 
          location: data.location || '' 
        },
        summary: data.summary || '',
        experience: data.experience || [],
        education: data.education || [],
        projects: data.projects || [],
        skills: data.skills || []
      });
    } catch (error) {
      console.error("Error fetching resume:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const updateData = {
        full_name: resumeData.personal.name,
        title: resumeData.personal.title,
        email: resumeData.personal.email,
        phone: resumeData.personal.phone,
        summary: resumeData.summary,
        experience: resumeData.experience,
        education: resumeData.education,
        projects: resumeData.projects,
        skills: resumeData.skills.map(s => typeof s === 'string' ? { name: s } : s)
      };
      
      await resumeAPI.updateResume(resumeId, updateData);
      setSaveMsg('Saved Successfully!');
    } catch (error) {
      console.error("Save failed:", error);
      setSaveMsg('Save failed');
    } finally {
      setSaving(false);
      setTimeout(() => setSaveMsg(''), 3000);
    }
  };

  const handleNext = () => {
    const currentIndex = tabOrder.indexOf(activeTab);
    if (currentIndex < tabOrder.length - 1) {
      setActiveTab(tabOrder[currentIndex + 1]);
    }
  };

  const handleBack = () => {
    const currentIndex = tabOrder.indexOf(activeTab);
    if (currentIndex > 0) {
      setActiveTab(tabOrder[currentIndex - 1]);
    }
  };

  const handlePersonalChange = (e) => {
    const { name, value } = e.target;
    setResumeData({ ...resumeData, personal: { ...resumeData.personal, [name]: value } });
  };

  // State Updaters for Lists
  const updateListField = (type, index, field, value) => {
    const newList = [...resumeData[type]];
    newList[index][field] = value;
    setResumeData({ ...resumeData, [type]: newList });
  };

  const addListItem = (type, template) => {
    setResumeData({ ...resumeData, [type]: [...resumeData[type], template] });
  };

  const removeListItem = (type, index) => {
    const newList = resumeData[type].filter((_, i) => i !== index);
    setResumeData({ ...resumeData, [type]: newList });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="flex flex-col lg:flex-row h-[calc(100vh-160px)] gap-8">
      {/* Sidebar Controls */}
      <div className="w-full lg:w-[450px] flex flex-col gap-6 overflow-y-auto pr-2 custom-scrollbar">
        <div className="card-glass p-6 sticky top-0 z-20">
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-3">
              <button onClick={() => navigate(-1)} className="p-2 hover:bg-white/10 rounded-xl text-slate-400 transition-colors">
                <ArrowLeft size={18} />
              </button>
              <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                <FileText className="text-blue-500" /> Edit Resume
              </h2>
            </div>
            <div className="flex gap-2 items-center">
              {saveMsg && <span className={`text-xs font-bold ${saveMsg.includes('failed') ? 'text-rose-400' : 'text-green-400'}`}>{saveMsg}</span>}
              <button 
                onClick={handleSave} 
                disabled={saving} 
                className="p-3 bg-blue-600 text-white rounded-xl hover:bg-blue-500 transition-all disabled:opacity-50 shadow-lg shadow-blue-500/20"
              >
                <Save size={18} />
              </button>
            </div>
          </div>

          <div className="flex items-center gap-2 p-1 bg-slate-900/50 rounded-2xl border border-white/5">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex-1 flex flex-col items-center gap-1.5 py-3 rounded-xl transition-all ${activeTab === tab.id ? 'bg-blue-600 text-white shadow-lg' : 'text-slate-500 hover:text-slate-300'}`}
              >
                <tab.icon size={18} />
                <span className="text-[10px] font-bold uppercase tracking-wider">{tab.label.split(' ')[0]}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="flex-1">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="space-y-6"
            >
              {activeTab === 'personal' && (
                <div className="card-glass p-8 space-y-6">
                  <h3 className="text-xl font-bold text-white border-b border-white/5 pb-4">Personal Information</h3>
                  <div className="grid grid-cols-1 gap-6">
                    <div className="space-y-2">
                      <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">Full Name</label>
                      <input name="name" value={resumeData.personal.name} onChange={handlePersonalChange} className="w-full bg-slate-900/50 border border-white/10 rounded-xl px-4 py-3 text-white focus:ring-2 focus:ring-blue-500/30 transition-all" />
                    </div>
                    <div className="space-y-2">
                      <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">Professional Title</label>
                      <input name="title" value={resumeData.personal.title} onChange={handlePersonalChange} className="w-full bg-slate-900/50 border border-white/10 rounded-xl px-4 py-3 text-white focus:ring-2 focus:ring-blue-500/30 transition-all" />
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">Email Address</label>
                        <input name="email" value={resumeData.personal.email} onChange={handlePersonalChange} className="w-full bg-slate-900/50 border border-white/10 rounded-xl px-4 py-3 text-sm text-white focus:ring-2 focus:ring-blue-500/30" />
                      </div>
                      <div className="space-y-2">
                        <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">Phone Number</label>
                        <input name="phone" value={resumeData.personal.phone} onChange={handlePersonalChange} className="w-full bg-slate-900/50 border border-white/10 rounded-xl px-4 py-3 text-sm text-white focus:ring-2 focus:ring-blue-500/30" />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">Location</label>
                      <input name="location" value={resumeData.personal.location} onChange={handlePersonalChange} className="w-full bg-slate-900/50 border border-white/10 rounded-xl px-4 py-3 text-white focus:ring-2 focus:ring-blue-500/30" />
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'summary' && (
                <div className="card-glass p-8 space-y-6">
                   <div className="flex items-center justify-between border-b border-white/5 pb-4">
                    <h3 className="text-xl font-bold text-white">Professional Summary</h3>
                    <button className="flex items-center gap-2 text-xs font-bold text-blue-400 hover:text-blue-300 transition-colors">
                      <Sparkles size={14} /> AI Reword
                    </button>
                  </div>
                  <textarea 
                    rows={12} 
                    value={resumeData.summary} 
                    onChange={(e) => setResumeData({...resumeData, summary: e.target.value})}
                    className="w-full bg-slate-900/50 border border-white/10 rounded-2xl px-5 py-4 text-white focus:ring-2 focus:ring-blue-500/30 resize-none leading-relaxed transition-all" 
                    placeholder="Describe your professional background and key strengths..."
                  />
                </div>
              )}

              {activeTab === 'experience' && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-xl font-bold text-white px-2">Work Experience</h3>
                    <button 
                      onClick={() => addListItem('experience', { company: '', role: '', duration: '', desc: '', description: '' })}
                      className="flex items-center gap-2 px-3 py-1.5 bg-blue-600/20 text-blue-400 rounded-xl hover:bg-blue-600/30 transition-all text-xs font-bold"
                    >
                      <Plus size={16} /> Add Position
                    </button>
                  </div>
                  {resumeData.experience.map((exp, index) => (
                    <div key={index} className="card-glass p-6 space-y-4 group relative">
                      <button 
                        onClick={() => removeListItem('experience', index)}
                        className="absolute top-4 right-4 text-slate-600 hover:text-rose-500 transition-colors opacity-0 group-hover:opacity-100"
                      >
                        <Trash2 size={18} />
                      </button>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-1">
                          <label className="text-[10px] font-bold text-slate-500 uppercase px-1">Company</label>
                          <input 
                            value={exp.company} 
                            onChange={(e) => updateListField('experience', index, 'company', e.target.value)}
                            className="w-full bg-slate-900/40 border border-white/5 rounded-xl px-4 py-2.5 text-white focus:ring-2 focus:ring-blue-500/20" 
                          />
                        </div>
                        <div className="space-y-1">
                          <label className="text-[10px] font-bold text-slate-500 uppercase px-1">Role</label>
                          <input 
                            value={exp.role} 
                            onChange={(e) => updateListField('experience', index, 'role', e.target.value)}
                            className="w-full bg-slate-900/40 border border-white/5 rounded-xl px-4 py-2.5 text-white focus:ring-2 focus:ring-blue-500/20" 
                          />
                        </div>
                      </div>
                      <div className="space-y-1">
                        <label className="text-[10px] font-bold text-slate-500 uppercase px-1">Duration (e.g., 2020 - Present)</label>
                        <input 
                          value={exp.duration} 
                          onChange={(e) => updateListField('experience', index, 'duration', e.target.value)}
                          className="w-full bg-slate-900/40 border border-white/5 rounded-xl px-4 py-2.5 text-white focus:ring-2 focus:ring-blue-500/20" 
                        />
                      </div>
                      <div className="space-y-1">
                        <label className="text-[10px] font-bold text-slate-500 uppercase px-1">Description</label>
                        <textarea 
                          value={exp.desc || exp.description} 
                          onChange={(e) => {
                            updateListField('experience', index, 'desc', e.target.value);
                            updateListField('experience', index, 'description', e.target.value);
                          }}
                          className="w-full bg-slate-900/40 border border-white/5 rounded-xl p-4 text-sm text-slate-300 h-32 resize-none transition-all focus:ring-2 focus:ring-blue-500/20" 
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {activeTab === 'education' && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-xl font-bold text-white px-2">Education</h3>
                    <button 
                      onClick={() => addListItem('education', { school: '', degree: '', year: '' })}
                      className="flex items-center gap-2 px-3 py-1.5 bg-blue-600/20 text-blue-400 rounded-xl hover:bg-blue-600/30 transition-all text-xs font-bold"
                    >
                      <Plus size={16} /> Add Education
                    </button>
                  </div>
                  {resumeData.education.map((edu, index) => (
                    <div key={index} className="card-glass p-6 space-y-4 group relative">
                      <button 
                        onClick={() => removeListItem('education', index)}
                        className="absolute top-4 right-4 text-slate-600 hover:text-rose-500 transition-colors opacity-0 group-hover:opacity-100"
                      >
                        <Trash2 size={18} />
                      </button>
                      <div className="space-y-1">
                        <label className="text-[10px] font-bold text-slate-500 uppercase px-1">School / University</label>
                        <input 
                          value={edu.school} 
                          onChange={(e) => updateListField('education', index, 'school', e.target.value)}
                          className="w-full bg-slate-900/40 border border-white/5 rounded-xl px-4 py-2.5 text-white focus:ring-2 focus:ring-blue-500/20" 
                        />
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-1">
                          <label className="text-[10px] font-bold text-slate-500 uppercase px-1">Degree</label>
                          <input 
                            value={edu.degree} 
                            onChange={(e) => updateListField('education', index, 'degree', e.target.value)}
                            className="w-full bg-slate-900/40 border border-white/5 rounded-xl px-4 py-2.5 text-white focus:ring-2 focus:ring-blue-500/20" 
                          />
                        </div>
                        <div className="space-y-1">
                          <label className="text-[10px] font-bold text-slate-500 uppercase px-1">Year / Period</label>
                          <input 
                            value={edu.year} 
                            onChange={(e) => updateListField('education', index, 'year', e.target.value)}
                            className="w-full bg-slate-900/40 border border-white/5 rounded-xl px-4 py-2.5 text-white focus:ring-2 focus:ring-blue-500/20" 
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {activeTab === 'skills' && (
                <div className="card-glass p-8 space-y-6">
                  <div className="flex items-center justify-between border-b border-white/5 pb-4">
                    <h3 className="text-xl font-bold text-white">Expertise & Skills</h3>
                  </div>
                  
                  <div className="space-y-4">
                    <div className="flex gap-2">
                      <input 
                        id="new-skill"
                        placeholder="Add a skill (e.g. React, Python)" 
                        className="flex-1 bg-slate-900/50 border border-white/10 rounded-xl px-4 py-2.5 text-white focus:ring-2 focus:ring-blue-500/30"
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            const val = e.currentTarget.value.trim();
                            if (val) {
                              setResumeData({ ...resumeData, skills: [...resumeData.skills, val] });
                              e.currentTarget.value = '';
                            }
                          }
                        }}
                      />
                      <button 
                        onClick={() => {
                          const input = document.getElementById('new-skill');
                          const val = input.value.trim();
                          if (val) {
                            setResumeData({ ...resumeData, skills: [...resumeData.skills, val] });
                            input.value = '';
                          }
                        }}
                        className="p-2.5 bg-blue-600 text-white rounded-xl hover:bg-blue-500 transition-all"
                      >
                        <Plus size={20} />
                      </button>
                    </div>

                    <div className="flex flex-wrap gap-2 pt-2">
                      {resumeData.skills.map((skill, index) => (
                        <div key={index} className="flex items-center gap-2 px-3 py-1.5 bg-blue-600/10 border border-blue-500/20 rounded-lg text-blue-400 font-bold text-sm">
                          {typeof skill === 'string' ? skill : skill.name}
                          <button 
                            onClick={() => removeListItem('skills', index)}
                            className="text-blue-400/50 hover:text-rose-400 transition-colors"
                          >
                            <X size={14} />
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Navigation Buttons */}
              <div className="pt-6 flex gap-4">
                 <button 
                    onClick={handleBack}
                    disabled={activeTab === 'personal'}
                    className="flex-1 py-4 bg-slate-800 text-white font-bold rounded-2xl hover:bg-slate-700 transition-all flex items-center justify-center gap-2 disabled:opacity-30 disabled:cursor-not-allowed"
                 >
                    <ChevronLeft size={20} /> Previous
                 </button>
                 <button 
                    onClick={handleNext}
                    disabled={activeTab === 'skills'}
                    className="flex-1 py-4 bg-blue-600 text-white font-bold rounded-2xl hover:bg-blue-500 transition-all flex items-center justify-center gap-2 disabled:opacity-30 disabled:cursor-not-allowed shadow-lg shadow-blue-500/20"
                 >
                    Next <ChevronRight size={20} />
                 </button>
              </div>
            </motion.div>
          </AnimatePresence>
        </div>
      </div>

      {/* Live Preview */}
      <div className="flex-1 bg-slate-900/40 border border-white/5 rounded-[40px] p-12 overflow-y-auto custom-scrollbar shadow-2xl relative">
        <div className="max-w-[800px] mx-auto bg-white rounded-sm shadow-2xl p-16 min-h-[1100px] text-slate-900 font-serif">
          {/* Header */}
          <div className="text-center space-y-4 border-b-2 border-slate-900 pb-10 mb-10">
             <h1 className="text-5xl font-black tracking-tight uppercase leading-tight">{resumeData.personal.name || "Your Name"}</h1>
             <p className="text-xl font-bold text-blue-600 italic">{resumeData.personal.title || "Professional Title"}</p>
             <div className="flex items-center justify-center gap-6 text-sm font-medium text-slate-600">
                <span>{resumeData.personal.email}</span>
                {resumeData.personal.phone && (
                  <>
                    <span className="w-1.5 h-1.5 bg-slate-300 rounded-full"></span>
                    <span>{resumeData.personal.phone}</span>
                  </>
                )}
                {resumeData.personal.location && (
                  <>
                    <span className="w-1.5 h-1.5 bg-slate-300 rounded-full"></span>
                    <span>{resumeData.personal.location}</span>
                  </>
                )}
             </div>
          </div>

          {/* Sections */}
          <div className="space-y-12">
            {/* Summary */}
            {resumeData.summary && (
              <div className="space-y-4">
                 <h4 className="text-lg font-black uppercase tracking-widest border-b border-slate-200 pb-2">Professional Summary</h4>
                 <p className="text-sm leading-relaxed text-slate-700">{resumeData.summary}</p>
              </div>
            )}

            {/* Experience */}
            {resumeData.experience.length > 0 && (
              <div className="space-y-6">
                 <h4 className="text-lg font-black uppercase tracking-widest border-b border-slate-200 pb-2">Experience</h4>
                 {resumeData.experience.map((exp, i) => (
                   <div key={i} className="space-y-2">
                      <div className="flex justify-between items-baseline">
                         <h5 className="font-bold text-lg">{exp.company}</h5>
                         <span className="text-sm italic text-slate-500">{exp.duration}</span>
                      </div>
                      <p className="text-sm font-bold text-blue-600 italic mb-2">{exp.role}</p>
                      <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">{exp.desc || exp.description}</p>
                   </div>
                 ))}
              </div>
            )}

            {/* Education */}
            {resumeData.education.length > 0 && (
              <div className="space-y-6">
                 <h4 className="text-lg font-black uppercase tracking-widest border-b border-slate-200 pb-2">Education</h4>
                 {resumeData.education.map((edu, i) => (
                   <div key={i} className="flex justify-between items-start">
                      <div>
                         <h5 className="font-bold text-lg">{edu.school}</h5>
                         <p className="text-sm font-bold text-blue-600 italic">{edu.degree}</p>
                      </div>
                      <span className="text-sm italic text-slate-500">{edu.year}</span>
                   </div>
                 ))}
              </div>
            )}

            {/* Skills */}
            {resumeData.skills.length > 0 && (
              <div className="space-y-4">
                 <h4 className="text-lg font-black uppercase tracking-widest border-b border-slate-200 pb-2">Expertise & Skills</h4>
                 <div className="flex flex-wrap gap-x-8 gap-y-3">
                    {resumeData.skills.map((skill, i) => (
                      <div key={i} className="text-sm font-bold text-slate-800 flex items-center gap-2">
                         <div className="w-1.5 h-1.5 bg-blue-600 rounded-full"></div>
                         {typeof skill === 'string' ? skill : skill.name}
                      </div>
                    ))}
                 </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResumeEdit;
