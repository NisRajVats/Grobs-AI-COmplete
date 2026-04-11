import React, { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  FileText,
  Eye,
  Edit3,
  Target,
  Sparkles,
  Download,
  Briefcase,
  Clock,
  ChevronRight,
  Trash2,
  Zap,
  RefreshCw,
} from "lucide-react";
import { motion } from "framer-motion";
import { resumeAPI, jobsAPI } from "../../services/api";

const ResumeDetail = () => {
  const { resumeId } = useParams();
  const navigate = useNavigate();
  const [resume, setResume] = useState(null);
  const [loading, setLoading] = useState(true);

  // Recommendations states
  const [recommendations, setRecommendations] = useState([]);
  const [loadingRecs, setLoadingRecs] = useState(false);
  const [deleting, setDeleting] = useState(false);

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

  const fetchRecommendations = useCallback(async () => {
    setLoadingRecs(true);
    try {
      const res = await jobsAPI.getJobRecommendations(resumeId, 3);
      setRecommendations(res.data.recommendations || []);
    } catch (err) {
      console.error("Error fetching recommendations:", err);
    } finally {
      setLoadingRecs(false);
    }
  }, [resumeId]);

  const handleDelete = async () => {
    if (!window.confirm("Are you sure you want to delete this resume?")) return;
    setDeleting(true);
    try {
      await resumeAPI.deleteResume(resumeId);
      navigate("/app/resumes");
    } catch (err) {
      console.error("Error deleting resume:", err);
      alert("Failed to delete resume");
    } finally {
      setDeleting(false);
    }
  };

  useEffect(() => {
    const fetchAll = async () => {
      await Promise.all([fetchResume(), fetchRecommendations()]);
    };
    fetchAll();
  }, [resumeId, fetchResume, fetchRecommendations]);

  const actions = [
    {
      id: "preview",
      icon: Eye,
      label: "Preview",
      path: `/app/resumes/${resumeId}/preview`,
      color: "from-blue-600 to-blue-500",
      shadow: "shadow-blue-500/25",
    },
    {
      id: "edit",
      icon: Edit3,
      label: "Edit",
      path: `/app/resumes/${resumeId}/edit`,
      color: "from-violet-600 to-purple-500",
      shadow: "shadow-purple-500/25",
    },
    {
      id: "ats",
      icon: Target,
      label: "ATS Analysis",
      path: `/app/resumes/${resumeId}/ats`,
      color: "from-amber-500 to-orange-500",
      shadow: "shadow-amber-500/25",
    },
    {
      id: "optimize",
      icon: Sparkles,
      label: "Optimise",
      path: `/app/resumes/${resumeId}/job-optimization`,
      color: "from-emerald-600 to-teal-500",
      shadow: "shadow-emerald-500/25",
    },
    {
      id: "jobs",
      icon: Briefcase,
      label: "Find Jobs",
      path: `/app/resumes/${resumeId}/jobs`,
      color: "from-rose-600 to-pink-500",
      shadow: "shadow-rose-500/25",
    },
    {
      id: "download",
      icon: Download,
      label: "Download",
      path: `/app/resumes/${resumeId}/download`,
      color: "from-slate-600 to-slate-500",
      shadow: "shadow-slate-500/25",
    },
  ];

  const score = resume?.latest_analysis?.score || resume?.ats_score || 0;
  const circumference = 2 * Math.PI * 54;
  const offset = circumference - (circumference * score) / 100;

  const scoreColor =
    score >= 80
      ? "text-emerald-400"
      : score >= 60
      ? "text-amber-400"
      : "text-rose-400";
  const scoreStroke =
    score >= 80
      ? "#34d399"
      : score >= 60
      ? "#fbbf24"
      : "#f87171";

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-1 pb-20 space-y-7">

      {/* ── PAGE HEADER ── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-2">
        {/* Left – back + title */}
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate("/app/resumes")}
            className="shrink-0 w-10 h-10 grid place-items-center bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-slate-400 hover:text-white transition-all group"
            title="Back to My Resumes"
          >
            <ChevronRight
              className="rotate-180 group-hover:-translate-x-0.5 transition-transform"
              size={20}
            />
          </button>

          <div className="flex items-center gap-3 min-w-0">
            <div className="shrink-0 w-10 h-10 bg-blue-600/15 border border-blue-500/20 rounded-xl grid place-items-center">
              <FileText className="text-blue-400" size={18} />
            </div>
            <div className="min-w-0">
              <h1 className="text-xl font-bold text-white leading-tight truncate">
                {resume?.filename}
              </h1>
              <div className="flex items-center gap-3 mt-0.5">
                <span className="flex items-center gap-1.5 text-[11px] text-slate-500">
                  <Clock size={11} className="text-blue-500/70" />
                  {new Date(resume?.created_at).toLocaleDateString("en-GB", {
                    day: "numeric",
                    month: "short",
                    year: "numeric",
                  })}
                </span>
                <span className="w-1 h-1 rounded-full bg-slate-700" />
                <span className="text-[11px] text-slate-500">
                  v{resume?.version || "1.0"}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Right – actions */}
        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={() => navigate(`/app/resumes/${resumeId}/preview`)}
            className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold rounded-xl transition-all shadow-lg shadow-blue-600/20"
          >
            <Eye size={16} />
            Preview
          </button>
          <button
            onClick={handleDelete}
            disabled={deleting}
            className="w-10 h-10 grid place-items-center bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 hover:text-rose-300 rounded-xl border border-rose-500/20 transition-all disabled:opacity-50"
            title="Delete Resume"
          >
            {deleting ? (
              <RefreshCw size={16} className="animate-spin" />
            ) : (
              <Trash2 size={16} />
            )}
          </button>
        </div>
      </div>

      {/* ── BODY GRID ── */}
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_300px] gap-7">

        {/* ── LEFT COLUMN ── */}
        <div className="space-y-7 min-w-0">

          {/* HERO CARD */}
          <div className="relative overflow-hidden rounded-2xl border border-white/[0.07] bg-white/3 p-7">
            {/* decorative blobs */}
            <div className="pointer-events-none absolute -top-20 -right-20 w-56 h-56 rounded-full bg-blue-600/10 blur-3xl" />
            <div className="pointer-events-none absolute -bottom-20 -left-20 w-56 h-56 rounded-full bg-violet-600/8 blur-3xl" />

            <div className="relative flex flex-col md:flex-row md:items-center gap-8">

              {/* Score ring + copy */}
              <div className="flex items-center gap-7">
                {/* Ring */}
                <div className="relative shrink-0 w-30 h-30">
                  <svg
                    viewBox="0 0 120 120"
                    className="w-full h-full -rotate-90"
                  >
                    <circle
                      cx="60" cy="60" r="54"
                      stroke="currentColor"
                      strokeWidth="8"
                      fill="none"
                      className="text-white/5"
                    />
                    <circle
                      cx="60" cy="60" r="54"
                      stroke={scoreStroke}
                      strokeWidth="8"
                      fill="none"
                      strokeDasharray={circumference}
                      strokeDashoffset={offset}
                      strokeLinecap="round"
                      style={{ transition: "stroke-dashoffset 1s ease-out" }}
                    />
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className={`text-3xl font-black tabular-nums ${scoreColor}`}>
                      {score}
                    </span>
                    <span className="text-[9px] font-bold text-slate-500 uppercase tracking-widest mt-0.5">
                      ATS Score
                    </span>
                  </div>
                </div>

                {/* Copy */}
                <div>
                  <p className="text-[11px] font-bold text-slate-500 uppercase tracking-widest mb-1">
                    Resume Strength
                  </p>
                  <p className="text-white font-semibold text-base leading-snug mb-3 max-w-xs">
                    {score > 80
                      ? "Excellent — your profile is highly competitive."
                      : "A few improvements could significantly boost your visibility."}
                  </p>
                  <div className="flex items-center gap-4">
                    <button
                      onClick={() => navigate(`/app/resumes/${resumeId}/ats`)}
                      className="flex items-center gap-1 text-xs font-semibold text-blue-400 hover:text-blue-300 transition-colors"
                    >
                      Full Report <ChevronRight size={13} />
                    </button>
                    <span className="w-px h-3 bg-white/10" />
                    <button
                      onClick={() => navigate(`/app/resumes/${resumeId}/job-optimization`)}
                      className="flex items-center gap-1 text-xs font-semibold text-emerald-400 hover:text-emerald-300 transition-colors"
                    >
                      Optimise Now <ChevronRight size={13} />
                    </button>
                  </div>
                </div>
              </div>

              {/* Stats pills */}
              <div className="flex gap-4 md:ml-auto shrink-0">
                {[
                  {
                    value: (resume?.parsed_data?.experience?.length || (resume?.experience?.length || 0)),
                    label: "Experiences",
                  },

                  {
                    value: (resume?.parsed_data?.skills?.length || resume?.skills?.length || 0),
                    label: "Skills",
                  },
                ].map(({ value, label }) => (
                  <div
                    key={label}
                    className="flex flex-col items-center justify-center w-28 h-20 rounded-xl bg-white/4 border border-white/[0.07]"
                  >
                    <span className="text-2xl font-black text-white tabular-nums">
                      {value}
                    </span>
                    <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mt-0.5">
                      {label}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* ACTION TOOLS */}
          <div>
            <p className="flex items-center gap-2 text-[11px] font-bold text-slate-500 uppercase tracking-widest mb-4">
              <Zap size={13} className="text-amber-400" />
              Management Tools
            </p>
            <div className="grid grid-cols-3 sm:grid-cols-6 gap-3">
              {actions.map((action) => (
                <motion.button
                  key={action.id}
                  whileHover={{ y: -3 }}
                  whileTap={{ scale: 0.97 }}
                  onClick={() => navigate(action.path)}
                  className="flex flex-col items-center gap-3 py-5 px-2 rounded-2xl bg-white/3 border border-white/[0.07] hover:border-white/15 hover:bg-white/6 transition-all group"
                >
                  <div
                    className={`w-11 h-11 rounded-xl bg-linear-to-br ${action.color} ${action.shadow} shadow-lg grid place-items-center group-hover:scale-105 transition-transform duration-200`}
                  >
                    <action.icon size={20} className="text-white" />
                  </div>
                  <span className="text-[10px] font-semibold text-slate-400 group-hover:text-white transition-colors tracking-wide text-center leading-tight">
                    {action.label}
                  </span>
                </motion.button>
              ))}
            </div>
          </div>

          {/* CONTENT CARDS ROW */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">

            {/* Skills */}
            {(resume?.skills?.length > 0 || resume?.parsed_data?.skills?.length > 0) && (
            <div className="rounded-2xl border border-white/[0.07] bg-white/3 p-6">
              <div className="flex items-center gap-2.5 mb-5">
                <div className="w-8 h-8 rounded-lg bg-amber-500/15 border border-amber-500/20 grid place-items-center">
                  <Zap className="text-amber-400" size={15} />
                </div>
                <h3 className="text-sm font-semibold text-white">Technical Skills</h3>
              </div>
                <div className="flex flex-wrap gap-2">
                  {(resume?.skills?.length > 0
                    ? resume.skills
                    : resume.parsed_data.skills
                  ).map((skill, i) => (
                    <span
                      key={i}
                      className="px-3 py-1.5 rounded-lg bg-white/5 border border-white/8 text-slate-300 text-[11px] font-medium hover:border-blue-500/40 hover:text-white transition-all cursor-default"
                    >
                      {typeof skill === "string" ? skill : skill.name}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Quick Overview */}
            <div className="rounded-2xl border border-white/[0.07] bg-white/3 p-6">
              <div className="flex items-center gap-2.5 mb-5">
                <div className="w-8 h-8 rounded-lg bg-blue-500/15 border border-blue-500/20 grid place-items-center">
                  <FileText className="text-blue-400" size={15} />
                </div>
                <h3 className="text-sm font-semibold text-white">Quick Overview</h3>
              </div>
              {[
                {
                  icon: Target,
                  label: "Primary Role",
                  value: resume?.parsed_data?.title || resume?.title || "Not Specified",
                },
                  {
                    icon: Briefcase,
                    label: "Experience Level",
                    value:
                      (resume?.parsed_data?.experience?.length || resume?.experience?.length || 0) > 5
                        ? "Senior"
                        : (resume?.parsed_data?.experience?.length || resume?.experience?.length || 0) >= 2
                        ? "Mid-Level"
                        : "Entry-Level",
                  },
                  {
                    icon: Sparkles,
                    label: "Contact Email",
                    value: resume?.parsed_data?.email || resume?.email || "No email found",
                  },
                ].map(({ icon: Icon, label, value }) => (
                  <div key={label} className="flex items-center justify-between py-3.5 gap-4">
                    <div className="flex items-center gap-2.5">
                      <Icon size={13} className="text-slate-500 shrink-0" />
                      <span className="text-[11px] font-medium text-slate-500">{label}</span>
                    </div>
                    <span className="text-[12px] font-semibold text-slate-200 text-right truncate max-w-40">
                      {value}
                    </span>
                  </div>
                ))}
            </div>
          </div>
        </div>

        {/* ── RIGHT SIDEBAR ── */}
        <div className="space-y-5">

          {/* Smart Match */}
          <div className="rounded-2xl border border-blue-500/15 bg-white/2 overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between px-5 py-4 border-b border-white/5 bg-blue-600/[0.04]bg-blue-600/4">
              <div>
                <div className="flex items-center gap-2">
                  <Sparkles className="text-blue-400" size={14} />
                  <span className="text-xs font-bold text-white uppercase tracking-widest">
                    Smart Match
                  </span>
                </div>
                <p className="text-[10px] text-slate-500 mt-0.5">Top roles matching your profile</p>
              </div>
              <button
                onClick={fetchRecommendations}
                className="w-7 h-7 grid place-items-center rounded-lg hover:bg-white/10 text-slate-500 hover:text-blue-400 transition-colors"
              >
                <RefreshCw size={13} className={loadingRecs ? "animate-spin" : ""} />
              </button>
            </div>

            {/* Body */}
            <div className="p-4 space-y-3">
              {loadingRecs ? (
                [1, 2, 3].map((i) => (
                  <div key={i} className="flex gap-3 p-3 rounded-xl bg-white/3 animate-pulse">
                    <div className="w-9 h-9 rounded-lg bg-white/5 shrink-0" />
                    <div className="flex-1 space-y-2 py-1">
                      <div className="h-2.5 bg-white/5 rounded-full w-3/4" />
                      <div className="h-2 bg-white/5 rounded-full w-1/2" />
                    </div>
                  </div>
                ))
              ) : recommendations.length > 0 ? (
                <>
                  {recommendations.map((rec, i) => (
                    <div
                      key={i}
                      className="group p-4 rounded-xl border border-white/6 bg-white/3 hover:border-blue-500/30 hover:bg-white/6 transition-all cursor-pointer"
                    >
                      <div className="flex items-start justify-between gap-2 mb-3">
                        <div className="min-w-0">
                          <p className="text-[12px] font-semibold text-white leading-tight group-hover:text-blue-300 transition-colors truncate">
                            {rec.job.job_title}
                          </p>
                          <p className="text-[10px] text-slate-500 mt-0.5 truncate">
                            {rec.job.company_name}
                          </p>
                        </div>
                        <ChevronRight
                          size={13}
                          className="shrink-0 text-slate-600 group-hover:text-blue-400 group-hover:translate-x-0.5 transition-all mt-0.5"
                        />
                      </div>
                      <div className="flex items-center gap-2.5">
                        <div className="flex-1 h-1 rounded-full bg-white/6 overflow-hidden">
                          <div
                            className="h-full rounded-full bg-blue-500"
                            style={{ width: `${rec.match_score}%` }}
                          />
                        </div>
                        <span className="text-[10px] font-bold text-blue-400 tabular-nums shrink-0">
                          {rec.match_score}%
                        </span>
                      </div>
                    </div>
                  ))}
                  <button
                    onClick={() => navigate(`/app/resumes/${resumeId}/jobs`)}
                    className="w-full py-2.5 mt-1 rounded-xl bg-white/3 hover:bg-white/[0.07] border border-white/6 text-[10px] font-bold text-slate-400 hover:text-white uppercase tracking-widest transition-all"
                  >
                    View All Matches
                  </button>
                </>
              ) : (
                <div className="flex flex-col items-center justify-center py-10 px-4 text-center">
                  <div className="w-12 h-12 rounded-full bg-white/4 border border-white/6 grid place-items-center mb-3">
                    <Briefcase size={18} className="text-slate-600" />
                  </div>
                  <p className="text-[10px] font-bold text-slate-600 uppercase tracking-widest">
                    No matches found
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Storage Info */}
          <div className="rounded-2xl border border-white/7 bg-white/3 p-5">
            <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-4">
              File Info
            </p>
            <div className="space-y-0 divide-y divide-white/5">
              {[
                { label: "Last Activity", value: "Recently" },
                {
                  label: "File Type",
                  value: (resume?.filename?.split(".").pop() || "PDF").toUpperCase(),
                },
              ].map(({ label, value }) => (
                <div key={label} className="flex items-center justify-between py-3">
                  <span className="text-[11px] text-slate-500">{label}</span>
                  <span className="text-[11px] font-semibold text-slate-300">{value}</span>
                </div>  
              ))}
            </div>
            <button className="mt-4 w-full flex items-center justify-center gap-2 py-2.5 rounded-lg bg-white/4 hover:bg-white/8 border border-white/[0.07] text-[11px] font-semibold text-slate-400 hover:text-white transition-all">
              <Download size={13} />
              Download Backup
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResumeDetail;