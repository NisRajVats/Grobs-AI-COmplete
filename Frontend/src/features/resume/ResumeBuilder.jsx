import React, { useState } from "react";
import { resumeAPI } from "../../services/api";
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
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

const ResumeBuilder = () => {
  const [activeTab, setActiveTab] = useState("personal");
  const [saving, setSaving] = useState(false);
  const [saveMsg, setSaveMsg] = useState("");

  const handleSave = async () => {
    setSaving(true);
    try {
      const payload = {
        full_name: resumeData.personal.name,
        email: resumeData.personal.email,
        phone: resumeData.personal.phone,
        title:
          resumeData.personal.title ||
          `${resumeData.personal.name} - ${resumeData.personal.title}`,
        summary: resumeData.summary,
        education: resumeData.education.map((edu) => ({
          school: edu.school,
          degree: edu.degree,
          year: edu.year,
        })),
        experience: resumeData.experience.map((exp) => ({
          company: exp.company,
          role: exp.role,
          duration: exp.duration,
          desc: exp.desc,
        })),
        skills: resumeData.skills.map((s) => ({ name: s })),
      };
      await resumeAPI.createResume(payload);
      setSaveMsg("Saved!");
    } catch (error) {
      console.error("Save error:", error);
      setSaveMsg("Save failed");
    } finally {
      setSaving(false);
      setTimeout(() => setSaveMsg(""), 2000);
    }
  };

  const handleDownload = () => {
    window.print();
  };
  const [resumeData, setResumeData] = useState({
    personal: { name: "", title: "", email: "", phone: "", location: "" },
    summary: "",
    experience: [
      { id: Date.now(), company: "", role: "", duration: "", desc: "" },
    ],
    education: [{ id: Date.now() + 1, school: "", degree: "", year: "" }],
    skills: [],
  });

  const handlePersonalChange = (e) => {
    const { name, value } = e.target;
    setResumeData({
      ...resumeData,
      personal: { ...resumeData.personal, [name]: value },
    });
  };

  const addExperience = () => {
    setResumeData({
      ...resumeData,
      experience: [
        ...resumeData.experience,
        { id: Date.now(), company: "", role: "", duration: "", desc: "" },
      ],
    });
  };

  const updateExperience = (id, field, value) => {
    setResumeData({
      ...resumeData,
      experience: resumeData.experience.map((exp) =>
        exp.id === id ? { ...exp, [field]: value } : exp,
      ),
    });
  };

  const removeExperience = (id) => {
    setResumeData({
      ...resumeData,
      experience: resumeData.experience.filter((exp) => exp.id !== id),
    });
  };

  const addEducation = () => {
    setResumeData({
      ...resumeData,
      education: [
        ...resumeData.education,
        { id: Date.now(), school: "", degree: "", year: "" },
      ],
    });
  };

  const updateEducation = (id, field, value) => {
    setResumeData({
      ...resumeData,
      education: resumeData.education.map((edu) =>
        edu.id === id ? { ...edu, [field]: value } : edu,
      ),
    });
  };

  const removeEducation = (id) => {
    setResumeData({
      ...resumeData,
      education: resumeData.education.filter((edu) => edu.id !== id),
    });
  };

  const addSkill = (skill) => {
    if (skill && !resumeData.skills.includes(skill)) {
      setResumeData({ ...resumeData, skills: [...resumeData.skills, skill] });
    }
  };

  const removeSkill = (skillToRemove) => {
    setResumeData({
      ...resumeData,
      skills: resumeData.skills.filter((skill) => skill !== skillToRemove),
    });
  };

  const tabs = [
    { id: "personal", label: "Personal Info", icon: User },
    { id: "summary", label: "Summary", icon: Sparkles },
    { id: "experience", label: "Experience", icon: Briefcase },
    { id: "education", label: "Education", icon: GraduationCap },
    { id: "skills", label: "Skills", icon: Wrench },
  ];

  return (
    <div className="flex flex-col lg:flex-row h-[calc(100vh-160px)] gap-8">
      <style>
        {`
          @media print {
            body { 
              background: white !important;
              margin: 0;
              padding: 0;
            }
            .no-print, nav, sidebar, header { 
              display: none !important; 
            }
            .print-only {
              display: block !important;
              position: absolute;
              left: 0;
              top: 0;
              width: 100%;
              height: auto;
              margin: 0 !important;
              padding: 0 !important;
              border: none !important;
              box-shadow: none !important;
              background: white !important;
            }
            #resume-preview-container {
               padding: 0 !important;
               margin: 0 !important;
               border: none !important;
               background: white !important;
               overflow: visible !important;
               height: auto !important;
               width: 100% !important;
            }
            #resume-actual-content {
               box-shadow: none !important;
               margin: 0 auto !important;
               border: none !important;
            }
          }
        `}
      </style>
      {/* Sidebar Controls */}
      <div className="w-full lg:w-112.5 flex flex-col gap-6 overflow-y-auto pr-2 custom-scrollbar no-print">
        <div className="card-glass p-6 sticky top-0 z-10">
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-2xl font-bold text-white flex items-center gap-3">
              <FileText className="text-blue-500" /> Resume Builder
            </h2>
            <div className="flex gap-2 items-center">
              {saveMsg && (
                <span className="text-xs text-green-400 font-medium">
                  {saveMsg}
                </span>
              )}
              <button
                onClick={handleSave}
                disabled={saving}
                className="p-2.5 bg-white/5 border border-white/10 rounded-xl hover:bg-white/10 text-slate-400 hover:text-white transition-all disabled:opacity-50 no-print"
              >
                <Save size={18} />
              </button>
              <button
                onClick={handleDownload}
                className="p-2.5 bg-blue-600 text-white rounded-xl hover:bg-blue-500 transition-all shadow-lg shadow-blue-500/20 no-print"
              >
                <Download size={18} />
              </button>
            </div>
          </div>

          <div className="flex items-center gap-2 p-1 bg-slate-900/50 rounded-2xl border border-white/5">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex-1 flex flex-col items-center gap-1.5 py-3 rounded-xl transition-all ${activeTab === tab.id ? "bg-blue-600 text-white shadow-lg" : "text-slate-500 hover:text-slate-300"}`}
              >
                <tab.icon size={18} />
                <span className="text-[10px] font-bold uppercase tracking-wider">
                  {tab.label.split(" ")[0]}
                </span>
              </button>
            ))}
          </div>
        </div>

        <div className="flex-1">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className="card-glass p-8 space-y-8"
            >
              {activeTab === "personal" && (
                <div className="space-y-6">
                  <h3 className="text-lg font-bold text-white">
                    Personal Information
                  </h3>
                  <div className="grid grid-cols-1 gap-6">
                    <div className="space-y-2">
                      <label className="text-xs font-bold text-slate-500 uppercase">
                        Full Name
                      </label>
                      <input
                        name="name"
                        value={resumeData.personal.name}
                        onChange={handlePersonalChange}
                        className="w-full bg-slate-900/50 border border-white/10 rounded-xl px-4 py-3 text-white focus:ring-2 focus:ring-blue-500/30"
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-xs font-bold text-slate-500 uppercase">
                        Professional Title
                      </label>
                      <input
                        name="title"
                        value={resumeData.personal.title}
                        onChange={handlePersonalChange}
                        className="w-full bg-slate-900/50 border border-white/10 rounded-xl px-4 py-3 text-white focus:ring-2 focus:ring-blue-500/30"
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <label className="text-xs font-bold text-slate-500 uppercase">
                          Email
                        </label>
                        <input
                          name="email"
                          value={resumeData.personal.email}
                          onChange={handlePersonalChange}
                          className="w-full bg-slate-900/50 border border-white/10 rounded-xl px-4 py-3 text-sm text-white focus:ring-2 focus:ring-blue-500/30"
                        />
                      </div>
                      <div className="space-y-2">
                        <label className="text-xs font-bold text-slate-500 uppercase">
                          Phone
                        </label>
                        <input
                          name="phone"
                          value={resumeData.personal.phone}
                          onChange={handlePersonalChange}
                          className="w-full bg-slate-900/50 border border-white/10 rounded-xl px-4 py-3 text-sm text-white focus:ring-2 focus:ring-blue-500/30"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === "summary" && (
                <div className="space-y-6">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-bold text-white">
                      Professional Summary
                    </h3>
                    <button className="flex items-center gap-2 text-xs font-bold text-blue-400 hover:text-blue-300">
                      <Sparkles size={14} /> AI Reword
                    </button>
                  </div>
                  <textarea
                    rows={8}
                    value={resumeData.summary}
                    onChange={(e) =>
                      setResumeData({ ...resumeData, summary: e.target.value })
                    }
                    className="w-full bg-slate-900/50 border border-white/10 rounded-xl px-4 py-3 text-white focus:ring-2 focus:ring-blue-500/30 resize-none"
                  />
                </div>
              )}

              {activeTab === "experience" && (
                <div className="space-y-6">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-bold text-white">
                      Work Experience
                    </h3>
                    <button
                      onClick={addExperience}
                      className="p-2 bg-blue-600/10 text-blue-400 rounded-lg hover:bg-blue-600/20 transition-all"
                    >
                      <Plus size={18} />
                    </button>
                  </div>
                  {resumeData.experience.map((exp) => (
                    <div
                      key={exp.id}
                      className="p-5 bg-white/5 border border-white/10 rounded-2xl space-y-4 group"
                    >
                      <div className="flex justify-between items-start">
                        <div className="space-y-1 w-full mr-4">
                          <input
                            value={exp.company}
                            placeholder="Company"
                            onChange={(e) =>
                              updateExperience(
                                exp.id,
                                "company",
                                e.target.value,
                              )
                            }
                            className="bg-transparent font-bold text-white focus:outline-none w-full"
                          />
                          <input
                            value={exp.role}
                            placeholder="Role"
                            onChange={(e) =>
                              updateExperience(exp.id, "role", e.target.value)
                            }
                            className="bg-transparent text-sm text-slate-400 focus:outline-none block w-full"
                          />
                          <input
                            value={exp.duration}
                            placeholder="Duration (e.g. 2020 - Present)"
                            onChange={(e) =>
                              updateExperience(
                                exp.id,
                                "duration",
                                e.target.value,
                              )
                            }
                            className="bg-transparent text-xs text-slate-500 focus:outline-none block w-full"
                          />
                        </div>
                        <button
                          onClick={() => removeExperience(exp.id)}
                          className="text-slate-600 hover:text-rose-500 transition-colors opacity-0 group-hover:opacity-100"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                      <textarea
                        value={exp.desc}
                        placeholder="Description"
                        onChange={(e) =>
                          updateExperience(exp.id, "desc", e.target.value)
                        }
                        className="w-full bg-slate-900/40 border border-white/5 rounded-xl p-3 text-xs text-slate-300 h-24 resize-none"
                      />
                    </div>
                  ))}
                </div>
              )}

              {activeTab === "education" && (
                <div className="space-y-6">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-bold text-white">Education</h3>
                    <button
                      onClick={addEducation}
                      className="p-2 bg-blue-600/10 text-blue-400 rounded-lg hover:bg-blue-600/20 transition-all"
                    >
                      <Plus size={18} />
                    </button>
                  </div>
                  {resumeData.education.map((edu) => (
                    <div
                      key={edu.id}
                      className="p-5 bg-white/5 border border-white/10 rounded-2xl space-y-4 group"
                    >
                      <div className="flex justify-between items-start">
                        <div className="space-y-1 w-full mr-4">
                          <input
                            value={edu.school}
                            placeholder="School/University"
                            onChange={(e) =>
                              updateEducation(edu.id, "school", e.target.value)
                            }
                            className="bg-transparent font-bold text-white focus:outline-none w-full"
                          />
                          <input
                            value={edu.degree}
                            placeholder="Degree"
                            onChange={(e) =>
                              updateEducation(edu.id, "degree", e.target.value)
                            }
                            className="bg-transparent text-sm text-slate-400 focus:outline-none block w-full"
                          />
                          <input
                            value={edu.year}
                            placeholder="Year"
                            onChange={(e) =>
                              updateEducation(edu.id, "year", e.target.value)
                            }
                            className="bg-transparent text-xs text-slate-500 focus:outline-none block w-full"
                          />
                        </div>
                        <button
                          onClick={() => removeEducation(edu.id)}
                          className="text-slate-600 hover:text-rose-500 transition-colors opacity-0 group-hover:opacity-100"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {activeTab === "skills" && (
                <div className="space-y-6">
                  <h3 className="text-lg font-bold text-white">Skills</h3>
                  <div className="flex gap-2">
                    <input
                      placeholder="Add a skill..."
                      className="flex-1 bg-slate-900/50 border border-white/10 rounded-xl px-4 py-3 text-white focus:ring-2 focus:ring-blue-500/30"
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          addSkill(e.target.value);
                          e.target.value = "";
                        }
                      }}
                    />
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {resumeData.skills.map((skill) => (
                      <span
                        key={skill}
                        className="px-3 py-1.5 bg-blue-600/20 text-blue-400 border border-blue-600/30 rounded-lg text-xs font-bold flex items-center gap-2"
                      >
                        {skill}
                        <button onClick={() => removeSkill(skill)}>
                          <Trash2
                            size={12}
                            className="hover:text-rose-500 transition-colors"
                          />
                        </button>
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div className="pt-8 flex gap-4">
                <button
                  onClick={() => {
                    const idx = tabs.findIndex((t) => t.id === activeTab);
                    if (idx > 0) setActiveTab(tabs[idx - 1].id);
                  }}
                  disabled={activeTab === tabs[0].id}
                  className="flex-1 py-4 bg-slate-800 text-white font-bold rounded-2xl hover:bg-slate-700 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  <ChevronLeft size={20} /> Previous
                </button>
                <button
                  onClick={() => {
                    const idx = tabs.findIndex((t) => t.id === activeTab);
                    if (idx < tabs.length - 1) setActiveTab(tabs[idx + 1].id);
                  }}
                  disabled={activeTab === tabs[tabs.length - 1].id}
                  className="flex-1 py-4 bg-blue-600 text-white font-bold rounded-2xl hover:bg-blue-500 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  Next <ChevronRight size={20} />
                </button>
              </div>
            </motion.div>
          </AnimatePresence>
        </div>
      </div>

      {/* Live Preview */}
      <div
        id="resume-preview-container"
        className="flex-1 bg-slate-900/40 border border-white/5 rounded-[40px] p-12 overflow-y-auto custom-scrollbar shadow-2xl relative print-only"
      >
        <div className="absolute top-8 right-8 z-10 flex gap-2 no-print">
          <button className="px-4 py-2 bg-white/10 hover:bg-white/20 backdrop-blur-md rounded-full text-xs font-bold text-white transition-all border border-white/10">
            Modern Template
          </button>
          <button className="px-4 py-2 bg-white/10 hover:bg-white/20 backdrop-blur-md rounded-full text-xs font-bold text-white transition-all border border-white/10">
            A4 Preview
          </button>
        </div>

        <div
          id="resume-actual-content"
          className="max-w-200 mx-auto bg-white rounded-sm shadow-2xl p-16 min-h-275 text-slate-900 font-serif"
        >
          {/* Header */}
          <div className="text-center space-y-4 border-b-2 border-slate-900 pb-10 mb-10">
            <h1 className="text-5xl font-black tracking-tight uppercase">
              {resumeData.personal.name}
            </h1>
            <p className="text-xl font-bold text-blue-600 italic">
              {resumeData.personal.title}
            </p>
            <div className="flex items-center justify-center gap-6 text-sm font-medium text-slate-600">
              <span>{resumeData.personal.email}</span>
              <span className="w-1.5 h-1.5 bg-slate-300 rounded-full"></span>
              <span>{resumeData.personal.phone}</span>
              <span className="w-1.5 h-1.5 bg-slate-300 rounded-full"></span>
              <span>{resumeData.personal.location}</span>
            </div>
          </div>

          {/* Sections */}
          <div className="space-y-12">
            {/* Summary */}
            <div className="space-y-4">
              <h4 className="text-lg font-black uppercase tracking-widest border-b border-slate-200 pb-2">
                Professional Summary
              </h4>
              <p className="text-sm leading-relaxed text-slate-700">
                {resumeData.summary}
              </p>
            </div>

            {/* Experience */}
            <div className="space-y-6">
              <h4 className="text-lg font-black uppercase tracking-widest border-b border-slate-200 pb-2">
                Experience
              </h4>
              {resumeData.experience.map((exp) => (
                <div key={exp.id} className="space-y-2">
                  <div className="flex justify-between items-baseline">
                    <h5 className="font-bold text-lg">{exp.company}</h5>
                    <span className="text-sm italic text-slate-500">
                      {exp.duration}
                    </span>
                  </div>
                  <p className="text-sm font-bold text-blue-600 italic mb-2">
                    {exp.role}
                  </p>
                  <p className="text-sm text-slate-700 leading-relaxed">
                    {exp.desc}
                  </p>
                </div>
              ))}
            </div>

            {/* Education */}
            <div className="space-y-6">
              <h4 className="text-lg font-black uppercase tracking-widest border-b border-slate-200 pb-2">
                Education
              </h4>
              {resumeData.education.map((edu) => (
                <div key={edu.id} className="space-y-1">
                  <div className="flex justify-between items-baseline">
                    <h5 className="font-bold text-lg">{edu.school}</h5>
                    <span className="text-sm italic text-slate-500">
                      {edu.year}
                    </span>
                  </div>
                  <p className="text-sm font-bold text-blue-600 italic">
                    {edu.degree}
                  </p>
                </div>
              ))}
            </div>

            {/* Skills */}
            <div className="space-y-4">
              <h4 className="text-lg font-black uppercase tracking-widest border-b border-slate-200 pb-2">
                Expertise & Skills
              </h4>
              <div className="flex flex-wrap gap-x-8 gap-y-3">
                {resumeData.skills.map((skill) => (
                  <div
                    key={skill}
                    className="text-sm font-bold text-slate-800 flex items-center gap-2"
                  >
                    <div className="w-1.5 h-1.5 bg-blue-600 rounded-full"></div>
                    {skill}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResumeBuilder;
