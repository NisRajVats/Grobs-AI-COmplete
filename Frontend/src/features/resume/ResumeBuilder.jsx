   import React, { useState, useRef, useEffect } from "react";
import { resumeAPI } from "../../services/api";
import { useNavigate } from "react-router-dom";
import {
  FileText,
  User,
  Briefcase,
  GraduationCap,
  Wrench,
  Plus,
  Trash2,
  Download,
  Eye,
  Save,
  Sparkles,
  ChevronRight,
  ChevronLeft,
  Upload,
  FileCheck,
  AlertCircle,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

/* ─── ID generator ────────────────────────────────────────────────────────── */
let _idCounter = Date.now();
const genId = () => ++_idCounter;

/* ─── Print / A4 CSS ──────────────────────────────────────────────────────── */
const PRINT_STYLES = `
  @page { size: A4; margin: 0; }
  @media print {
    html, body {
      width: 210mm; height: 297mm;
      margin: 0; padding: 0;
      background: white !important;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }
    .no-print { display: none !important; }
    #resume-sheet {
      width: 210mm !important;
      min-height: 297mm !important;
      max-height: 297mm !important;
      margin: 0 !important;
      padding: 14mm 16mm !important;
      box-shadow: none !important;
      border-radius: 0 !important;
      overflow: hidden !important;
      page-break-after: avoid;
    }
  }
`;

/* ─── Section heading ─────────────────────────────────────────────────────── */
const SH = React.memo(({ children }) => (
  <div style={{ borderBottom: '1.5px solid #000', marginBottom: '10px', marginTop: '14px', width: '100%' }}>
    <h4 style={{
      fontSize: '13pt',
      fontWeight: 800,
      textTransform: 'uppercase',
      color: '#000',
      margin: '0 0 2px 0',
      fontFamily: '"Georgia", serif'  ,
      letterSpacing: '0.05em',
    }}>
      {children}
    </h4>
  </div>
));

/* ─── Bullet renderer ─────────────────────────────────────────────────────── */
const Bullets = React.memo(({ points, text }) => {
  if (points && points.length > 0) return (
    <ul style={{ listStyle: 'none', padding: 0, margin: '4px 0 0 0' }}>
      {points.map((pt, i) => (
        <li key={i} style={{ display: 'flex', gap: '8px', marginBottom: '2px', alignItems: 'flex-start' }}>
          <span style={{ color: '#000', fontWeight: 500, fontSize: '9pt', lineHeight: '1.4' }}>–</span>
          <span style={{ fontSize: '9pt', color: '#000', lineHeight: '1.4', fontFamily: '"Georgia", serif' }}>{pt}</span>
        </li>
      ))}
    </ul>
  );
  if (text) {
    const pts = text.split('\n').filter(p => p.trim());
    return (
       <ul style={{ listStyle: 'none', padding: 0, margin: '4px 0 0 0' }}>
        {pts.map((pt, j) => (
          <li key={j} style={{ display: 'flex', gap: '8px', marginBottom: '2px', alignItems: 'flex-start' }}>
            <span style={{ color: '#000', fontWeight: 500, fontSize: '9pt', lineHeight: '1.4' }}>–</span>
            <span style={{ fontSize: '9pt', color: '#000', lineHeight: '1.4', fontFamily: '"Georgia", serif' }}>{pt.replace(/^[•\-*▸]\s*/, '')}</span>
          </li>
        ))}
      </ul>
    );
  }
  return null;
});

/* ─── Live preview sub-component ─────────────────────────────────────────── */
const LiveResume = React.memo(({ data }) => {
  const contactItems = React.useMemo(() => [
    data.personal?.email,
    data.personal?.phone,
    data.personal?.location,
    data.personal?.linkedin ? data.personal.linkedin.replace(/^https?:\/\/(www\.)?/, "") : null
  ].filter(Boolean), [data.personal]);

  const groupedSkills = React.useMemo(() => (data.skills || []).reduce((acc, s) => {
    const cat  = typeof s === 'object' ? (s.category || 'Skills') : 'Skills';
    const name = typeof s === 'object' ? s.name : s;
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(name);
    return acc;
  }, {}), [data.skills]);

  return (
    <div
      id="resume-sheet"
      style={{
        background: 'white',
        width: '210mm',
        minHeight: '297mm',
        maxWidth: '100%',
        margin: '0 auto',
        padding: '14mm 16mm',
        boxSizing: 'border-box',
        fontFamily: '"Georgia", serif',
        color: '#1e293b',
        boxShadow: '0 8px 40px rgba(0,0,0,0.18)',
        borderRadius: '4px',
        fontSize: '9pt',
        lineHeight: '1.45',
        display: 'flex',
        flexDirection: 'column',
        gap: '9px',
      }}
    >
      {/* Header */}
      <div style={{ textAlign: 'center', paddingBottom: '7px', borderBottom: '2px solid #1e293b' }}>
        <h1 style={{ fontSize: '22pt', fontWeight: 900, letterSpacing: '0.04em', textTransform: 'uppercase', margin: 0, lineHeight: 1.1, color: '#0f172a' }}>
          {data.personal?.name || 'Your Name'}
        </h1>
        {data.personal?.title && (
          <p style={{ fontSize: '10pt', fontWeight: 600, color: '#2563eb', fontStyle: 'italic', margin: '3px 0 0' }}>
            {data.personal.title}
          </p>
        )}
        {contactItems.length > 0 && (
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '7px', marginTop: '5px', flexWrap: 'wrap' }}>
            {contactItems.map((item, i) => (
              <React.Fragment key={i}>
                {i > 0 && <span style={{ color: '#94a3b8', fontSize: '7pt' }}>●</span>}
                <span style={{ fontSize: '8.5pt', color: '#475569', fontFamily: 'sans-serif' }}>{item}</span>
              </React.Fragment>
            ))}
          </div>
        )}
      </div>

      {/* Summary */}
      {data.summary && (
        <div>
          <SH>Professional Summary</SH>
          <p style={{ fontSize: '8pt', color: '#374151', lineHeight: '1.55', margin: 0 }}>{data.summary}</p>
        </div>
      )}

      {/* Skills */}
      {Object.keys(groupedSkills).length > 0 && (
        <div>
          <SH>Skills</SH>
          {Object.entries(groupedSkills).map(([cat, skills], i) => (
            <div key={i} style={{ display: 'flex', gap: '6px', marginBottom: '2px', alignItems: 'flex-start' }}>
              {cat !== 'Skills' && (
                <span style={{ fontSize: '7.5pt', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em', whiteSpace: 'nowrap', minWidth: '70px', paddingTop: '1px' }}>
                  {cat}:
                </span>
              )}
              <span style={{ fontSize: '8pt', color: '#1e293b', lineHeight: '1.5' }}>{skills.join(' · ')}</span>
            </div>
          ))}
        </div>
      )}

      {/* Education */}
      {data.education?.length > 0 && (
        <div>
          <SH>Education</SH>
          {data.education.map((edu, i) => (
            <div key={edu.id || i} style={{ marginBottom: '6px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                <div style={{ fontWeight: 700, fontSize: '8.5pt', color: '#0f172a' }}>{edu.school}</div>
                <div style={{ fontSize: '7.5pt', color: '#64748b' }}>{edu.location}</div>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                <div style={{ fontSize: '8pt', color: '#475569', fontStyle: 'italic' }}>{edu.degree}{edu.major ? `, ${edu.major}` : ''}</div>
                <div style={{ fontSize: '7.5pt', color: '#64748b', fontStyle: 'italic', whiteSpace: 'nowrap', marginLeft: '8px' }}>{edu.duration || edu.year}</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Experience */}
      {data.experience?.length > 0 && (
        <div>
          <SH>Experience</SH>
          {data.experience.map((exp, i) => (
            <div key={exp.id || i} style={{ marginBottom: '6px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                <span style={{ fontWeight: 700, fontSize: '8.5pt', color: '#0f172a' }}>{exp.company}</span>
                <span style={{ fontSize: '7.5pt', color: '#64748b', whiteSpace: 'nowrap', marginLeft: '8px' }}>{exp.duration}</span>
              </div>
              <div style={{ fontSize: '8pt', color: '#2563eb', fontWeight: 600, fontStyle: 'italic', marginBottom: '3px' }}>{exp.role}</div>
              <Bullets points={exp.points} text={exp.desc} />
            </div>
          ))}
        </div>
      )}

      {/* Projects */}
      {data.projects?.length > 0 && (
        <div>
          <SH>KEY PROJECTS</SH>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {data.projects.map((proj, i) => {
                let name = proj.project_name;
                let status = proj.status || '';
                let subtitle = proj.subtitle || '';
                let technologies = Array.isArray(proj.technologies) ? proj.technologies.join(', ') : proj.technologies;

                if (!status) {
                   if (name.toLowerCase().includes('in progress')) {
                      status = 'In Progress';
                      name = name.replace(/[\s-]+In Progress/i, '');
                   } else if (name.toLowerCase().includes('completed')) {
                      status = 'Completed';
                      name = name.replace(/[\s-]+Completed/i, '');
                   }
                }

                if (!subtitle && technologies) {
                  const projectTypes = ['Front-End', 'Back-End', 'Full-Stack', 'Web Application', 'Static Web', 'Mobile App'];
                  for (const type of projectTypes) {
                    if (technologies.includes(type)) {
                       subtitle = technologies.split(type)[0] + type;
                       technologies = technologies.replace(subtitle, '').trim().replace(/^[, ]+/, '');
                       break;
                    }
                  }
                }

                // Filter out points that are redundant with title
                let filteredPoints = (proj.points || []).filter(p => {
                  const pNorm = p.trim().toLowerCase();
                  const nNorm = name.trim().toLowerCase();
                  return pNorm && pNorm !== nNorm && !nNorm.includes(pNorm) && !pNorm.includes(nNorm);
                });

                let desc = proj.desc || proj.description || '';
                if (desc.trim().toLowerCase() === name.trim().toLowerCase()) {
                  desc = '';
                }

                return (
                  <div key={proj.id || i} style={{ marginBottom: '8px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                      <span style={{ fontWeight: 800, fontSize: '11pt', color: '#000' }}>{name}</span>
                      {status && <span style={{ fontSize: '10pt', color: '#000', fontWeight: 500 }}>{status}</span>}
                    </div>
                    {(subtitle || technologies) && (
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginTop: '2px' }}>
                        <span style={{ fontSize: '10pt', fontStyle: 'italic', color: '#000' }}>{subtitle}</span>
                        <span style={{ fontSize: '10pt', fontStyle: 'italic', color: '#000', textAlign: 'right' }}>{technologies}</span>
                      </div>
                    )}
                    <Bullets points={filteredPoints} text={desc} />
                    {(proj.github_url || proj.github) && (
                       <div style={{ marginTop: '4px', fontSize: '9pt', color: '#000', fontStyle: 'italic' }}>
                         GitHub: <span style={{ fontFamily: 'sans-serif' }}>{(proj.github_url || proj.github).replace(/^https?:\/\//, '')}</span>
                       </div>
                    )}
                  </div>
                );
            })}
          </div>
        </div>
      )}
    </div>
  );
});

/* ═══ Main ResumeBuilder ═══════════════════════════════════════════════════ */
const ResumeBuilder = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("personal");
  const [saving, setSaving] = useState(false);
  const skillInputRef = useRef(null);
  const fileInputRef = useRef(null);

  const [resumeData, setResumeData] = useState({
    personal: { name: "", title: "", email: "", phone: "", location: "", linkedin: "", github: "" },
    summary: "",
    experience: [],
    education: [],
    projects: [],
    skills: [],
  });

  // Debounced data for live preview to prevent re-renders on every keystroke
  const [previewData, setPreviewData] = useState(resumeData);

  useEffect(() => {
    const timer = setTimeout(() => {
      setPreviewData(resumeData);
    }, 400); // 400ms debounce
    return () => clearTimeout(timer);
  }, [resumeData]);

  const handleSave = async () => {
    const { name, email, phone, title } = resumeData.personal;
    if (!name.trim()) return;
    if (!email.trim() || !/\S+@\S+\.\S+/.test(email)) return;

    setSaving(true);
    try {
      const payload = {
        full_name:  name.trim(),
        email:      email.trim(),
        phone:      phone.trim(),
        linkedin_url: resumeData.personal.linkedin.trim(),
        github_url:   resumeData.personal.github.trim(),
        title:      title.trim() || name.trim(),
        summary:    resumeData.summary,
        education:  resumeData.education.map(e => ({ school: e.school, degree: e.degree, location: e.location, duration: e.duration || e.year })),
        projects:   resumeData.projects.map(p => ({ project_name: p.project_name, technologies: p.technologies, desc: p.desc || p.description, points: p.points || [] })),
        experience: resumeData.experience.map(e => ({ company: e.company, role: e.role, duration: e.duration, desc: e.desc, points: e.points || [] })),
        skills:     resumeData.skills.map(s => ({ name: s })),
      };
      await resumeAPI.createResume(payload);
      navigate('/app/resumes');
    } catch (error) {
      console.error("Save error:", error);
    } finally {
      setSaving(false);
    }
  };

  const handleDownload = () => {
    window.print();
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const response = await resumeAPI.uploadResume(file, file.name, "");
      const data = response.data;
      if (data) {
        const parsed = data.parsed_data || data;
        
        // Ensure skills are handled correctly (might be array of strings or objects)
        const formattedSkills = (parsed.skills || data.skills || [])
          .map(s => typeof s === 'string' ? s : (s.name || s))
          .filter(Boolean);

        setResumeData({
          personal: {
            name:     parsed.full_name || data.full_name || parsed.name || data.name || "",
            title:    parsed.title     || data.title     || "",
            email:    parsed.email     || data.email     || "",
            phone:    parsed.phone     || data.phone     || "",
            location: parsed.location  || data.location  || "",
            linkedin: parsed.linkedin_url || data.linkedin_url || parsed.linkedin || data.linkedin || "",
            github:   parsed.github_url || data.github_url || parsed.github || data.github || "",
          },
          summary: parsed.summary || data.summary || "",
          experience: (parsed.experience || data.experience || [])?.map(exp => ({
            id:       genId(),
            company:  exp.company  || "",
            role:     exp.role     || "",
            duration: exp.duration || (exp.start_date && exp.end_date ? `${exp.start_date} – ${exp.end_date}` : exp.start_date || ""),
            desc:     exp.description || exp.desc || "",
            points:   exp.points || [],
          })),
          education: (parsed.education || data.education || [])?.map(edu => ({
            id:       genId(),
            school:   edu.school   || "",
            degree:   edu.degree   || "",
            major:    edu.major    || "",
            location: edu.location || "",
            duration: edu.duration || (edu.start_date && edu.end_date ? `${edu.start_date} – ${edu.end_date}` : edu.year || ""),
          })),
          projects: (parsed.projects || data.projects || [])?.map(proj => ({
            id:           genId(),
            project_name: proj.project_name || "",
            technologies: Array.isArray(proj.technologies) ? proj.technologies.join(", ") : proj.technologies || "",
            desc:         proj.description   || proj.desc || "",
            points:       proj.points || [],
          })),
          skills: formattedSkills,
        });
      }
    } catch (err) {
      console.error("Upload error:", err);
    } finally {
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handlePersonalChange = (e) => {
    const { name, value } = e.target;
    setResumeData(prev => ({ ...prev, personal: { ...prev.personal, [name]: value } }));
  };

  const addExperience  = () => setResumeData(prev => ({ ...prev, experience: [...prev.experience, { id: genId(), company: "", role: "", duration: "", desc: "", points: [] }] }));
  const updateExperience = (id, field, value) => setResumeData(prev => ({ ...prev, experience: prev.experience.map(e => e.id === id ? { ...e, [field]: value } : e) }));
  const removeExperience = (id) => setResumeData(prev => ({ ...prev, experience: prev.experience.filter(e => e.id !== id) }));

  const addEducation  = () => setResumeData(prev => ({ ...prev, education: [...prev.education, { id: genId(), school: "", degree: "", location: "", duration: "" }] }));
  const updateEducation = (id, field, value) => setResumeData(prev => ({ ...prev, education: prev.education.map(e => e.id === id ? { ...e, [field]: value } : e) }));
  const removeEducation = (id) => setResumeData(prev => ({ ...prev, education: prev.education.filter(e => e.id !== id) }));

  const addProject  = () => setResumeData(prev => ({ ...prev, projects: [...prev.projects, { id: genId(), project_name: "", technologies: "", desc: "", points: [] }] }));
  const updateProject = (id, field, value) => setResumeData(prev => ({ ...prev, projects: prev.projects.map(p => p.id === id ? { ...p, [field]: value } : p) }));
  const removeProject = (id) => setResumeData(prev => ({ ...prev, projects: prev.projects.filter(p => p.id !== id) }));

  const addSkill = (raw) => {
    const skill = raw.trim();
    if (!skill) return;
    if (!resumeData.skills.some(s => s.toLowerCase() === skill.toLowerCase())) {
      setResumeData(prev => ({ ...prev, skills: [...prev.skills, skill] }));
    }
    if (skillInputRef.current) skillInputRef.current.value = "";
  };
  const removeSkill = (s) => setResumeData(prev => ({ ...prev, skills: prev.skills.filter(sk => sk !== s) }));

  const tabs = [
    { id: "personal",    label: "Personal Info",  icon: User },
    { id: "summary",     label: "Summary",         icon: Sparkles },
    { id: "experience",  label: "Experience",      icon: Briefcase },
    { id: "education",   label: "Education",       icon: GraduationCap },
    { id: "projects",    label: "Projects",        icon: FileText },
    { id: "skills",      label: "Skills",          icon: Wrench },
  ];

  /* shared input class */
  const inp = "w-full bg-slate-900/50 border border-white/10 rounded-xl px-4 py-3 text-white focus:ring-2 focus:ring-blue-500/30 text-sm";
  const inpSm = "bg-transparent focus:outline-none w-full text-white";

  return (
    <div className="flex flex-col lg:flex-row h-[calc(100vh-160px)] gap-8">
      <style>{PRINT_STYLES}</style>

      {/* ── Sidebar ── */}
      <div className="w-full lg:w-112.5 flex flex-col gap-6 overflow-y-auto pr-2 custom-scrollbar no-print">
        {/* Sticky header + tabs */}
        <div className="card-glass p-6 sticky top-0 z-10">
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-2xl font-bold text-white flex items-center gap-3">
              <FileText className="text-blue-500" /> Resume Builder
            </h2>
            <div className="flex gap-2 items-center">
              <button onClick={handleSave} disabled={saving} className="p-2.5 bg-white/5 border border-white/10 rounded-xl hover:bg-white/10 text-slate-400 hover:text-white transition-all disabled:opacity-50 no-print">
                <Save size={18} />
              </button>
              <button onClick={handleDownload} className="p-2.5 bg-blue-600 text-white rounded-xl hover:bg-blue-500 transition-all shadow-lg shadow-blue-500/20 no-print">
                <Download size={18} />
              </button>
              <label className="p-2.5 bg-green-600/20 border border-green-600/30 rounded-xl hover:bg-green-600/30 text-green-400 hover:text-green-300 transition-all cursor-pointer no-print">
                <Upload size={18} />
                <input ref={fileInputRef} type="file" accept=".pdf,.doc,.docx" onChange={handleFileUpload} className="hidden" />
              </label>
            </div>
          </div>

          <div className="flex items-center gap-2 p-1 bg-slate-900/50 rounded-2xl border border-white/5">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex-1 flex flex-col items-center gap-1.5 py-3 rounded-xl transition-all ${
                  activeTab === tab.id ? "bg-blue-600 text-white shadow-lg" : "text-slate-500 hover:text-slate-300"
                }`}
              >
                <tab.icon size={18} />
                <span className="text-[10px] font-bold uppercase tracking-wider">{tab.label.split(" ")[0]}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Tab panels */}
        <div className="flex-1">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="card-glass p-8 space-y-8"
            >
              {/* ── Personal ── */}
              {activeTab === "personal" && (
                <div className="space-y-6">
                  <h3 className="text-lg font-bold text-white">Personal Information</h3>
                  <div className="grid grid-cols-1 gap-6">
                    <div className="space-y-2">
                      <label className="text-xs font-bold text-slate-500 uppercase">Full Name</label>
                      <input name="name" value={resumeData.personal.name || ''} onChange={handlePersonalChange} className={inp} />
                    </div>
                    <div className="space-y-2">
                      <label className="text-xs font-bold text-slate-500 uppercase">Professional Title</label>
                      <input name="title" value={resumeData.personal.title || ''} onChange={handlePersonalChange} className={inp} />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <label className="text-xs font-bold text-slate-500 uppercase">Email</label>
                        <input name="email" value={resumeData.personal.email || ''} onChange={handlePersonalChange} className={inp} />
                      </div>
                      <div className="space-y-2">
                        <label className="text-xs font-bold text-slate-500 uppercase">Phone</label>
                        <input name="phone" value={resumeData.personal.phone || ''} onChange={handlePersonalChange} className={inp} />
                      </div>
                    </div>
                    <div className="grid grid-cols-3 gap-4">
                      <div className="space-y-2">
                        <label className="text-xs font-bold text-slate-500 uppercase">Location</label>
                        <input name="location" value={resumeData.personal.location || ''} onChange={handlePersonalChange} className={inp} />
                      </div>
                      <div className="space-y-2">
                        <label className="text-xs font-bold text-slate-500 uppercase">LinkedIn URL</label>
                        <input name="linkedin" value={resumeData.personal.linkedin || ''} onChange={handlePersonalChange} className={inp} placeholder="linkedin.com/in/..." />
                      </div>
                      <div className="space-y-2">
                        <label className="text-xs font-bold text-slate-500 uppercase">GitHub URL</label>
                        <input name="github" value={resumeData.personal.github || ''} onChange={handlePersonalChange} className={inp} placeholder="github.com/..." />
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* ── Summary ── */}
              {activeTab === "summary" && (
                <div className="space-y-6">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-bold text-white">Professional Summary</h3>
                    <button className="flex items-center gap-2 text-xs font-bold text-blue-400 hover:text-blue-300">
                      <Sparkles size={14} /> AI Reword
                    </button>
                  </div>
                  <textarea
                    rows={8}
                    value={resumeData.summary || ''}
                    onChange={(e) => setResumeData(prev => ({ ...prev, summary: e.target.value }))}
                    className={`${inp} resize-none`}
                  />
                </div>
              )}

              {/* ── Experience ── */}
              {activeTab === "experience" && (
                <div className="space-y-6">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-bold text-white">Work Experience</h3>
                    <button onClick={addExperience} className="p-2 bg-blue-600/10 text-blue-400 rounded-lg hover:bg-blue-600/20 transition-all">
                      <Plus size={18} />
                    </button>
                  </div>
                  {resumeData.experience.map((exp) => (
                    <div key={exp.id} className="p-5 bg-white/5 border border-white/10 rounded-2xl space-y-4 group">
                      <div className="flex justify-between items-start">
                        <div className="space-y-1 w-full mr-4">
                          <input value={exp.company || ''} placeholder="Company" onChange={(e) => updateExperience(exp.id, "company", e.target.value)} className={`${inpSm} font-bold`} />
                          <input value={exp.role || ''} placeholder="Role" onChange={(e) => updateExperience(exp.id, "role", e.target.value)} className={`${inpSm} text-sm text-slate-400`} />
                          <input value={exp.duration || ''} placeholder="Duration (e.g. 2020 – Present)" onChange={(e) => updateExperience(exp.id, "duration", e.target.value)} className={`${inpSm} text-xs text-slate-500`} />
                        </div>
                        <button onClick={() => removeExperience(exp.id)} className="text-slate-600 hover:text-rose-500 transition-colors opacity-0 group-hover:opacity-100">
                          <Trash2 size={16} />
                        </button>
                      </div>
                      <textarea
                        value={exp.desc || ''}
                        placeholder="Description"
                        onChange={(e) => updateExperience(exp.id, "desc", e.target.value)}
                        className="w-full bg-slate-900/40 border border-white/5 rounded-xl p-3 text-xs text-slate-300 h-24 resize-none"
                      />
                    </div>
                  ))}
                </div>
              )}

              {/* ── Education ── */}
              {activeTab === "education" && (
                <div className="space-y-6">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-bold text-white">Education</h3>
                    <button onClick={addEducation} className="p-2 bg-blue-600/10 text-blue-400 rounded-lg hover:bg-blue-600/20 transition-all">
                      <Plus size={18} />
                    </button>
                  </div>
                  {resumeData.education.map((edu) => (
                    <div key={edu.id} className="p-5 bg-white/5 border border-white/10 rounded-2xl space-y-4 group">
                      <div className="flex justify-between items-start">
                        <div className="space-y-1 w-full mr-4">
                          <input value={edu.school || ''} placeholder="School/University" onChange={(e) => updateEducation(edu.id, "school", e.target.value)} className={`${inpSm} font-bold`} />
                          <input value={edu.degree || ''} placeholder="Degree" onChange={(e) => updateEducation(edu.id, "degree", e.target.value)} className={`${inpSm} text-sm text-slate-400`} />
                          <div className="grid grid-cols-2 gap-4 pt-1">
                            <input value={edu.location || ''} placeholder="Location" onChange={(e) => updateEducation(edu.id, "location", e.target.value)} className={`${inpSm} text-xs text-slate-500`} />
                            <input value={edu.duration || edu.year || ''} placeholder="Duration (e.g. 2021 – 2025)" onChange={(e) => updateEducation(edu.id, "duration", e.target.value)} className={`${inpSm} text-xs text-slate-500 text-right`} />
                          </div>
                        </div>
                        <button onClick={() => removeEducation(edu.id)} className="text-slate-600 hover:text-rose-500 transition-colors opacity-0 group-hover:opacity-100">
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* ── Projects ── */}
              {activeTab === "projects" && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-xl font-bold text-white px-2">Projects</h3>
                    <button onClick={addProject} className="flex items-center gap-2 px-3 py-1.5 bg-blue-600/20 text-blue-400 rounded-xl hover:bg-blue-600/30 transition-all text-xs font-bold">
                      <Plus size={16} /> Add Project
                    </button>
                  </div>
                  {resumeData.projects.map((proj) => (
                    <div key={proj.id} className="card-glass p-6 space-y-4 group relative">
                      <button onClick={() => removeProject(proj.id)} className="absolute top-4 right-4 text-slate-600 hover:text-rose-500 transition-colors opacity-0 group-hover:opacity-100">
                        <Trash2 size={18} />
                      </button>
                      <div className="space-y-1">
                        <label className="text-[10px] font-bold text-slate-500 uppercase px-1">Project Name</label>
                        <input value={proj.project_name || ''} onChange={(e) => updateProject(proj.id, 'project_name', e.target.value)} className="w-full bg-slate-900/40 border border-white/5 rounded-xl px-4 py-2.5 text-white focus:ring-2 focus:ring-blue-500/20 text-sm" />
                      </div>
                      <div className="space-y-1">
                        <label className="text-[10px] font-bold text-slate-500 uppercase px-1">Technologies</label>
                        <input value={proj.technologies || ''} onChange={(e) => updateProject(proj.id, 'technologies', e.target.value)} className="w-full bg-slate-900/40 border border-white/5 rounded-xl px-4 py-2.5 text-white focus:ring-2 focus:ring-blue-500/20 text-sm" />
                      </div>
                      <div className="space-y-1">
                        <label className="text-[10px] font-bold text-slate-500 uppercase px-1">Description</label>
                        <textarea value={proj.desc || proj.description || ''} onChange={(e) => updateProject(proj.id, 'desc', e.target.value)} className="w-full bg-slate-900/40 border border-white/5 rounded-xl p-4 text-sm text-slate-300 h-32 resize-none focus:ring-2 focus:ring-blue-500/20" />
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* ── Skills (Last Section) ── */}
              {activeTab === "skills" && (
                <div className="space-y-6">
                  <h3 className="text-lg font-bold text-white">Skills <span className="text-green-400 text-sm font-normal">(Last section - ready to save!)</span></h3>
                  <input
                    ref={skillInputRef}
                    placeholder="Type a skill and press Enter..."
                    className={inp}
                    onKeyDown={(e) => { if (e.key === "Enter") addSkill(e.target.value); }}
                  />
                  <div className="flex flex-wrap gap-2">
                    {resumeData.skills.map((skill) => (
                      <span key={skill} className="px-3 py-1.5 bg-blue-600/20 text-blue-400 border border-blue-600/30 rounded-lg text-xs font-bold flex items-center gap-2">
                        {skill}
                        <button onClick={() => removeSkill(skill)}><Trash2 size={12} className="hover:text-rose-500 transition-colors" /></button>
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Prev / Next */}
              <div className="pt-8 flex gap-4">
                <button
                  onClick={() => { const idx = tabs.findIndex(t => t.id === activeTab); if (idx > 0) setActiveTab(tabs[idx - 1].id); }}
                  disabled={activeTab === tabs[0].id}
                  className="flex-1 py-4 bg-slate-800 text-white font-bold rounded-2xl hover:bg-slate-700 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  <ChevronLeft size={20} /> Previous
                </button>
                {activeTab === "skills" ? (
                  <button
                    onClick={handleSave}
                    disabled={saving}
                    className="flex-1 py-4 bg-green-600 text-white font-bold rounded-2xl hover:bg-green-500 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    <Save size={20} className="ml-1" /> Save Resume
                  </button>
                ) : (
                  <button
                    onClick={() => { 
                      const idx = tabs.findIndex(t => t.id === activeTab); 
                      if (idx < tabs.length - 1) setActiveTab(tabs[idx + 1].id); 
                    }}
                    className="flex-1 py-4 bg-blue-600 text-white font-bold rounded-2xl hover:bg-blue-500 transition-all flex items-center justify-center gap-2"
                  >
                    Next <ChevronRight size={20} />
                  </button>
                )}
              </div>
            </motion.div>
          </AnimatePresence>
        </div>
      </div>

      {/* ── Live Preview Panel ── */}
      <div
        id="resume-preview-container"
        className="flex-1 bg-slate-900/40 border border-white/5 rounded-[40px] p-8 overflow-y-auto custom-scrollbar shadow-2xl relative"
      >
        {/* Template label */}
        <div className="absolute top-6 right-6 z-10 flex gap-2 no-print">
          <span className="px-4 py-2 bg-white/10 backdrop-blur-md rounded-full text-xs font-bold text-white border border-white/10">
            Classic · A4
          </span>
        </div>

        {/* Render the live resume */}
        <LiveResume data={previewData} />
      </div>
    </div>
  );
};

export default ResumeBuilder;
