import React, { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowRight,
  Download,
  Edit3,
  Phone,
  Mail,
  Linkedin,
  Github,
} from "lucide-react";
import { motion } from "framer-motion";
import { resumeAPI } from "../../services/api";

/* ─── Print & A4 styles ──────────────────────────────────────────────────── */
const printStyles = `
  @page {
    size: A4;
    margin: 0;
  }
  @media print {
    html, body {
      width: 210mm;
      height: 297mm;
      margin: 0;
      padding: 0;
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

/* ─── Reusable section heading ───────────────────────────────────────────── */
const SectionHeading = ({ children }) => (
  <div
    style={{
      borderBottom: "1.5px solid #000",
      marginBottom: "10px",
      marginTop: "14px",
      width: "100%",
    }}
  >
    <h4
      style={{
        fontSize: "13pt",
        fontWeight: 800,
        textTransform: "uppercase",
        color: "#000",
        margin: "0 0 2px 0",
        fontFamily: '"Georgia", serif',
        letterSpacing: "0.05em",
      }}
    >
      {children}
    </h4>
  </div>
);

/* ─── Bullet list helper ─────────────────────────────────────────────────── */
const BulletList = ({ items, text }) => {
  if (items && items.length > 0) {
    return (
      <ul style={{ listStyle: "none", padding: 0, margin: "4px 0 0 0" }}>
        {items.map((pt, j) => (
          <li
            key={j}
            style={{
              display: "flex",
              gap: "8px",
              marginBottom: "2px",
              alignItems: "flex-start",
            }}
          >
            <span
              style={{
                color: "#000",
                fontWeight: 500,
                fontSize: "9pt",
                lineHeight: "1.4",
              }}
            >
              –
            </span>
            <span
              style={{
                fontSize: "9pt",
                color: "#000",
                lineHeight: "1.4",
                fontFamily: '"Georgia", serif',
              }}
            >
              {pt}
            </span>
          </li>
        ))}
      </ul>
    );
  }
  if (text) {
    const points = text.split("\n").filter((p) => p.trim());
    return (
      <ul style={{ listStyle: "none", padding: 0, margin: "4px 0 0 0" }}>
        {points.map((pt, j) => (
          <li
            key={j}
            style={{
              display: "flex",
              gap: "8px",
              marginBottom: "2px",
              alignItems: "flex-start",
            }}
          >
            <span
              style={{
                color: "#000",
                fontWeight: 500,
                fontSize: "9pt",
                lineHeight: "1.4",
              }}
            >
              –
            </span>
            <span
              style={{
                fontSize: "9pt",
                color: "#000",
                lineHeight: "1.4",
                fontFamily: '"Georgia", serif',
              }}
            >
              {pt.replace(/^[•\-*▸]\s*/, "")}
            </span>
          </li>
        ))}
      </ul>
    );
  }
  return null;
};

/* ─── Main component ─────────────────────────────────────────────────────── */
const ResumePreview = () => {
  const { resumeId } = useParams();
  const navigate = useNavigate();
  const [resume, setResume] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchResume = useCallback(async () => {
    try {
      const response = await resumeAPI.getResume(resumeId);
      const resumeData = response.data;
      const raw = resumeData.parsed_data || {};

      const formattedData = {
        name: raw.full_name || resumeData.full_name || "",
        title: raw.title || resumeData.title || "",
        email: raw.email || resumeData.email || "",
        phone: raw.phone || resumeData.phone || "",
        linkedin: raw.linkedin_url || resumeData.linkedin_url || "",
        github: raw.github_url || "",
        location: raw.location || "",
        summary: raw.summary || "",
        experience: (raw.experience || resumeData.experience || []).map(
          (exp) => ({
            company: exp.company || "",
            role: exp.role || "",
            duration:
              exp.duration ||
              (exp.start_date && exp.end_date
                ? `${exp.start_date} – ${exp.end_date}`
                : exp.start_date || ""),
            desc: exp.description || exp.desc || "",
            points: exp.points || [],
          }),
        ),
        education: (raw.education || resumeData.education || []).map((edu) => {
          // Format duration: check for duration field or combine start/end dates
          let duration = edu.duration || "";
          if (!duration) {
            const start = edu.start_date || "";
            const end = edu.end_date || "";
            if (start && end) {
              duration = `${start} – ${end}`;
            } else {
              duration = edu.year || end || start || "";
            }
          }

          return {
            school: edu.school || "",
            degree: edu.degree || "",
            major: edu.major || "",
            duration: duration,
            location: edu.location || "",
          };
        }),
        projects: (raw.projects || resumeData.projects || []).map((proj) => ({
          project_name: proj.project_name || "",
          desc: proj.description || proj.desc || "",
          points: proj.points || [],
          technologies: proj.technologies || [],
          github_url: proj.github_url || proj.github || "",
          status: proj.status || "",
          subtitle: proj.subtitle || "",
        })),
        skills: raw.skills || resumeData.skills || [],
        achievements: raw.achievements || resumeData.achievements || [],
        certifications: raw.certifications || resumeData.certifications || [],
      };

      setResume({ ...resumeData, parsed_data: formattedData });
    } catch (_error) {
      console.error("Error fetching resume preview:", _error);
    } finally {
      setLoading(false);
    }
  }, [resumeId]);

  useEffect(() => {
    fetchResume();
  }, [fetchResume]);

  const handleDownload = () => window.print();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500" />
      </div>
    );
  }

  const data = resume?.parsed_data || {};

  /* Group skills by category */
  const groupedSkills = (data.skills || []).reduce((acc, skill) => {
    const category =
      typeof skill === "object" ? skill.category || "Skills" : "Skills";
    const name = typeof skill === "object" ? skill.name : skill;
    if (!acc[category]) acc[category] = [];
    acc[category].push(name);
    return acc;
  }, {});

  /* ── Contact Info with Icons ── */
  const contactInfo = [
    { icon: Phone, value: data.phone },
    { icon: Mail, value: data.email },
    { icon: Linkedin, value: data.linkedin },
    { icon: Github, value: data.github },
  ].filter((item) => item.value);

  return (
    <div className="space-y-6">
      <style>{printStyles}</style>

      {/* ── Toolbar ── */}
      <div className="flex items-center justify-between no-print">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate(`/app/resumes/${resumeId}`)}
            className="p-2 hover:bg-white/10 rounded-xl text-slate-400 hover:text-white"
          >
            <ArrowRight className="rotate-180" size={20} />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-white">Resume Preview</h1>
            <p className="text-slate-400">{resume?.filename}</p>
          </div>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => navigate(`/app/resumes/${resumeId}/edit`)}
            className="flex items-center gap-2 px-4 py-2 bg-slate-800 text-white font-bold rounded-xl hover:bg-slate-700 transition-all"
          >
            <Edit3 size={18} /> Edit
          </button>
          <button
            onClick={handleDownload}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white font-bold rounded-xl hover:bg-blue-500 transition-all"
          >
            <Download size={18} /> Download PDF
          </button>
        </div>
      </div>

      {/* ── A4 Sheet ── */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        id="resume-sheet"
        style={{
          background: "white",
          width: "210mm",
          minHeight: "297mm",
          maxWidth: "100%",
          margin: "0 auto",
          padding: "14mm 16mm",
          boxSizing: "border-box",
          fontFamily: '"Georgia", serif',
          color: "#1e293b",
          boxShadow: "0 8px 40px rgba(0,0,0,0.18)",
          borderRadius: "4px",
          fontSize: "9pt",
          lineHeight: "1.45",
          display: "flex",
          flexDirection: "column",
          gap: "10px",
        }}
      >
        {/* ═══ HEADER ═══ */}
        <div
          style={{
            textAlign: "center",
            paddingBottom: "12px",
            borderBottom: "1px solid #e2e8f0",
          }}
        >
          <h1
            style={{
              fontSize: "28pt",
              fontWeight: 500,
              margin: 0,
              lineHeight: 1.1,
              color: "#000",
              fontFamily: '"Georgia", serif',
              textTransform: "capitalize",
            }}
          >
            {data.name?.toLowerCase() || "Your Name"}
          </h1>
          {data.title && (
            <p
              style={{
                fontSize: "11pt",
                fontWeight: 700,
                color: "#000",
                margin: "4px 0",
              }}
            >
              {data.title}
            </p>
          )}
          {contactInfo.length > 0 && (
            <div
              style={{
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
                gap: "10px",
                marginTop: "6px",
                flexWrap: "wrap",
              }}
            >
              {contactInfo.map((item, i) => (
                <React.Fragment key={i}>
                  {i > 0 && (
                    <span style={{ color: "#94a3b8", fontSize: "10pt" }}>
                      |
                    </span>
                  )}
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "4px",
                    }}
                  >
                    <item.icon size={12} strokeWidth={2.5} color="#000" />
                    <span
                      style={{
                        fontSize: "8.5pt",
                        color: "#000",
                        fontFamily: "sans-serif",
                      }}
                    >
                      {item.value.replace(/^https?:\/\//, "")}
                    </span>
                  </div>
                </React.Fragment>
              ))}
            </div>
          )}
        </div>

        {/* ═══ SUMMARY ═══ */}
        {data.summary && (
          <div>
            <SectionHeading>Professional Summary</SectionHeading>
            <p
              style={{
                fontSize: "8pt",
                color: "#374151",
                lineHeight: "1.55",
                margin: 0,
              }}
            >
              {data.summary}
            </p>
          </div>
        )}

        {/* ═══ SKILLS ═══ */}
        {Object.keys(groupedSkills).length > 0 && (
          <div>
            <SectionHeading>Skills</SectionHeading>
            <div
              style={{ display: "flex", flexDirection: "column", gap: "3px" }}
            >
              {Object.entries(groupedSkills).map(([category, skills], i) => (
                <div
                  key={i}
                  style={{
                    display: "flex",
                    gap: "6px",
                    alignItems: "flex-start",
                  }}
                >
                  {category !== "Skills" && (
                    <span
                      style={{
                        fontSize: "7.5pt",
                        fontWeight: 700,
                        color: "#64748b",
                        textTransform: "uppercase",
                        letterSpacing: "0.05em",
                        whiteSpace: "nowrap",
                        minWidth: "70px",
                        paddingTop: "1px",
                      }}
                    >
                      {category}:
                    </span>
                  )}
                  <span
                    style={{
                      fontSize: "8pt",
                      color: "#1e293b",
                      lineHeight: "1.5",
                    }}
                  >
                    {skills.join(" · ")}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ═══ EDUCATION ═══ */}
        {data.education?.length > 0 && (
          <div>
            <SectionHeading>Education</SectionHeading>
            <div
              style={{ display: "flex", flexDirection: "column", gap: "2px" }}
            >
              {data.education.map((edu, i) => (
                <div key={i} style={{ marginBottom: "6px" }}>
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "baseline",
                    }}
                  >
                    <span
                      style={{
                        fontWeight: 700,
                        fontSize: "10.5pt",
                        color: "#000",
                      }}
                    >
                      {edu.school}
                    </span>
                    <span style={{ fontSize: "10pt", color: "#000" }}>
                      {edu.location}
                    </span>
                  </div>
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "baseline",
                    }}
                  >
                    <span
                      style={{
                        fontSize: "10pt",
                        color: "#000",
                        fontStyle: "italic",
                      }}
                    >
                      {edu.degree}
                      {edu.major ? `, ${edu.major}` : ""}
                    </span>
                    <span
                      style={{
                        fontSize: "10pt",
                        color: "#000",
                        fontStyle: "italic",
                      }}
                    >
                      {edu.duration}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ═══ EXPERIENCE ═══ */}
        {data.experience?.length > 0 && (
          <div>
            <SectionHeading>Experience</SectionHeading>
            <div
              style={{ display: "flex", flexDirection: "column", gap: "7px" }}
            >
              {data.experience.map((exp, i) => (
                <div key={i}>
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "baseline",
                    }}
                  >
                    <span
                      style={{
                        fontWeight: 700,
                        fontSize: "8.5pt",
                        color: "#0f172a",
                      }}
                    >
                      {exp.company}
                    </span>
                    <span
                      style={{
                        fontSize: "7.5pt",
                        color: "#64748b",
                        whiteSpace: "nowrap",
                        marginLeft: "8px",
                      }}
                    >
                      {exp.duration}
                    </span>
                  </div>
                  <div
                    style={{
                      fontSize: "8pt",
                      color: "#2563eb",
                      fontWeight: 600,
                      fontStyle: "italic",
                      marginBottom: "3px",
                    }}
                  >
                    {exp.role}
                  </div>
                  <BulletList items={exp.points} text={exp.desc} />
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ═══ PROJECTS ═══ */}
        {data.projects?.length > 0 && (
          <div>
            <SectionHeading>KEY PROJECTS</SectionHeading>
            <div
              style={{ display: "flex", flexDirection: "column", gap: "10px" }}
            >
              {data.projects.map((proj, i) => {
                // Try to extract status and subtitle if missing
                let name = proj.project_name;
                let status = proj.status;
                let subtitle = proj.subtitle;
                let technologies = Array.isArray(proj.technologies)
                  ? proj.technologies.join(", ")
                  : proj.technologies;

                if (!status) {
                  if (name.toLowerCase().includes("in progress")) {
                    status = "In Progress";
                    name = name.replace(/[\s-]+In Progress/i, "");
                  } else if (name.toLowerCase().includes("completed")) {
                    status = "Completed";
                    name = name.replace(/[\s-]+Completed/i, "");
                  }
                }

                // If subtitle is missing, try to see if technologies starts with project type
                if (!subtitle && technologies) {
                  const projectTypes = [
                    "Front-End",
                    "Back-End",
                    "Full-Stack",
                    "Web Application",
                    "Static Web",
                    "Mobile App",
                  ];
                  for (const type of projectTypes) {
                    if (technologies.includes(type)) {
                      subtitle = technologies.split(type)[0] + type;
                      technologies = technologies
                        .replace(subtitle, "")
                        .trim()
                        .replace(/^[, ]+/, "");
                      break;
                    }
                  }
                }

                // Filter out points that are redundant with title or other points
                let filteredPoints = (proj.points || []).filter((p) => {
                  const pNorm = p.trim().toLowerCase();
                  const nNorm = name.trim().toLowerCase();
                  return (
                    pNorm &&
                    pNorm !== nNorm &&
                    !nNorm.includes(pNorm) &&
                    !pNorm.includes(nNorm)
                  );
                });

                // If description is same as title, clear it
                let desc = proj.desc || "";
                if (desc.trim().toLowerCase() === name.trim().toLowerCase()) {
                  desc = "";
                }

                return (
                  <div key={i} style={{ marginBottom: "8px" }}>
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "baseline",
                      }}
                    >
                      <span
                        style={{
                          fontWeight: 800,
                          fontSize: "11pt",
                          color: "#000",
                        }}
                      >
                        {name}
                      </span>
                      {status && (
                        <span
                          style={{
                            fontSize: "10pt",
                            color: "#000",
                            fontWeight: 500,
                          }}
                        >
                          {status}
                        </span>
                      )}
                    </div>
                    {(subtitle || technologies) && (
                      <div
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "baseline",
                          marginTop: "2px",
                        }}
                      >
                        <span
                          style={{
                            fontSize: "10pt",
                            fontStyle: "italic",
                            color: "#000",
                          }}
                        >
                          {subtitle}
                        </span>
                        <span
                          style={{
                            fontSize: "10pt",
                            fontStyle: "italic",
                            color: "#000",
                            textAlign: "right",
                          }}
                        >
                          {technologies}
                        </span>
                      </div>
                    )}
                    <BulletList items={filteredPoints} text={desc} />
                    {proj.github_url && (
                      <div
                        style={{
                          marginTop: "4px",
                          fontSize: "9pt",
                          color: "#000",
                          fontStyle: "italic",
                        }}
                      >
                        GitHub:{" "}
                        <span style={{ fontFamily: "sans-serif" }}>
                          {proj.github_url.replace(/^https?:\/\//, "")}
                        </span>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* ═══ ACHIEVEMENTS & CERTIFICATIONS ═══ */}
        {(data.achievements?.length > 0 || data.certifications?.length > 0) && (
          <div
            style={{
              display: "grid",
              gridTemplateColumns:
                data.achievements?.length > 0 && data.certifications?.length > 0
                  ? "1fr 1fr"
                  : "1fr",
              gap: "12px",
            }}
          >
            {data.achievements?.length > 0 && (
              <div>
                <SectionHeading>Achievements</SectionHeading>
                <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
                  {data.achievements.map((item, i) => (
                    <li
                      key={i}
                      style={{
                        display: "flex",
                        gap: "6px",
                        marginBottom: "2px",
                      }}
                    >
                      <span
                        style={{
                          color: "#2563eb",
                          fontWeight: 700,
                          flexShrink: 0,
                        }}
                      >
                        ▸
                      </span>
                      <span
                        style={{
                          fontSize: "8pt",
                          color: "#374151",
                          lineHeight: "1.5",
                        }}
                      >
                        {item}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {data.certifications?.length > 0 && (
              <div>
                <SectionHeading>Certifications</SectionHeading>
                <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
                  {data.certifications.map((item, i) => (
                    <li
                      key={i}
                      style={{
                        display: "flex",
                        gap: "6px",
                        marginBottom: "2px",
                      }}
                    >
                      <span
                        style={{
                          color: "#2563eb",
                          fontWeight: 700,
                          flexShrink: 0,
                        }}
                      >
                        ▸
                      </span>
                      <span
                        style={{
                          fontSize: "8pt",
                          color: "#374151",
                          lineHeight: "1.5",
                        }}
                      >
                        {item}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </motion.div>
    </div>
  );
};

export default ResumePreview;
