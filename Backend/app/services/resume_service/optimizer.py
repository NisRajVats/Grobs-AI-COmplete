"""
Advanced Resume Optimization Service
────────────────────────────────────
AI-powered resume transformation engine with:
  • Job-specific tailoring & ATS optimization
  • Keyword injection & gap analysis
  • Versioning, rollback, and audit trail
  • Retry/back-off for LLM calls
  • Rich structured output with metrics
"""

from __future__ import annotations

import json
import logging
import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models import Job, Resume, ResumeAnalysis, ResumeVersion
from app.services.llm_service import llm_service
from app.services.resume_service.resume_manager import ResumeManager
from .parser import clean_experience_entry, clean_text

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Enums & Constants
# ──────────────────────────────────────────────

class OptimizationType(str, Enum):
    COMPREHENSIVE = "comprehensive"
    JOB_TAILORED  = "job_tailored"
    ATS_BOOST     = "ats_boost"
    TONE_POLISH   = "tone_polish"


class SeniorityLevel(str, Enum):
    INTERN     = "intern"
    JUNIOR     = "junior"
    MID        = "mid"
    SENIOR     = "senior"
    LEAD       = "lead"
    EXECUTIVE  = "executive"


_SENIORITY_KEYWORDS: Dict[SeniorityLevel, List[str]] = {
    SeniorityLevel.INTERN:    ["assisted", "supported", "learned", "contributed"],
    SeniorityLevel.JUNIOR:    ["developed", "implemented", "built", "collaborated"],
    SeniorityLevel.MID:       ["designed", "optimized", "led", "delivered"],
    SeniorityLevel.SENIOR:    ["architected", "spearheaded", "drove", "mentored"],
    SeniorityLevel.LEAD:      ["directed", "established", "transformed", "owned"],
    SeniorityLevel.EXECUTIVE: ["visioned", "championed", "scaled", "redefined"],
}

_MAX_LLM_RETRIES   = 3
_LLM_RETRY_DELAY   = 1.5   # seconds (exponential back-off base)
_MAX_EXPERIENCE_ROLES = 4   # focus on latest N roles


# ──────────────────────────────────────────────
# Data containers
# ──────────────────────────────────────────────

@dataclass
class OptimizationContext:
    """Immutable context bundle passed through the pipeline."""
    resume_id:         int
    user_id:           int
    optimization_type: OptimizationType = OptimizationType.COMPREHENSIVE
    job_description:   str              = ""
    job_id:            Optional[int]    = None
    save_as_new:       bool             = False
    target_seniority:  Optional[SeniorityLevel] = None


@dataclass
class OptimizationResult:
    """Structured result returned to callers."""
    success:                   bool
    resume_id:                 int
    original_resume:           Dict[str, Any]    = field(default_factory=dict)
    optimized_resume:          Dict[str, Any]    = field(default_factory=dict)
    suggestions:               str               = ""
    improvements:              List[str]         = field(default_factory=list)
    ats_score:                 int               = 0
    compatibility_score:       int               = 0
    compatibility_feedback:    str               = ""
    skill_gap:                 List[str]         = field(default_factory=list)
    matching_skills:           List[str]         = field(default_factory=list)
    skill_recommendations:     List[str]         = field(default_factory=list)
    certificate_recommendations: List[str]       = field(default_factory=list)
    error:                     Optional[str]     = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}


# ──────────────────────────────────────────────
# Core Service
# ──────────────────────────────────────────────

class ResumeOptimizer:
    """
    AI-powered resume optimization pipeline.

    Responsibilities
    ----------------
    1. Resolve context  – fetch resume + optional job description
    2. Prepare payload  – serialise resume to LLM-friendly dict
    3. Optimize         – call LLM with structured schema + retry logic
    4. Post-process     – clean artifacts, validate completeness
    5. Persist          – create version record + analysis log
    6. Return           – typed OptimizationResult
    """

    def __init__(self, db: Session) -> None:
        self.db             = db
        self.resume_manager = ResumeManager(db)

    # ─── Public API ────────────────────────────

    async def optimize_resume(
        self,
        resume_id:         int,
        user_id:           int,
        optimization_type: str           = OptimizationType.COMPREHENSIVE,
        job_description:   str           = "",
        job_id:            Optional[int] = None,
        save_as_new:       bool          = False,
        target_seniority:  Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Entry point for resume optimization.
        Returns a dict-serialised OptimizationResult.
        """
        # Validate optimization type
        valid_types = [t.value for t in OptimizationType]
        if optimization_type not in valid_types:
            logger.warning(f"Invalid optimization type: {optimization_type}. Using comprehensive.")
            optimization_type = OptimizationType.COMPREHENSIVE.value
        
        llm_service.refresh_config()

        try:
            opt_type = OptimizationType(optimization_type)
        except ValueError:
            opt_type = OptimizationType.COMPREHENSIVE

        ctx = OptimizationContext(
            resume_id         = resume_id,
            user_id           = user_id,
            optimization_type = opt_type,
            job_description   = job_description or "",
            job_id            = job_id,
            save_as_new       = save_as_new,
            target_seniority  = SeniorityLevel(target_seniority) if target_seniority else None,
        )

        try:
            result = await self._run_pipeline(ctx)
        except ValueError as exc:
            logger.warning("Optimization rejected: %s", exc)
            return OptimizationResult(success=False, resume_id=resume_id, error=str(exc)).to_dict()
        except Exception as exc:
            logger.exception("Unexpected error optimizing resume %d", resume_id)
            return OptimizationResult(success=False, resume_id=resume_id, error="Internal error during optimization").to_dict()

        return result.to_dict()

    # ─── Pipeline ──────────────────────────────

    async def _run_pipeline(self, ctx: OptimizationContext) -> OptimizationResult:
        # 1. Resolve context
        resume, ctx = await self._resolve_context(ctx)

        # 2. Prepare payload
        resume_data = self._serialize_resume(resume)

        # 3. Optimize (with retry)
        llm_output = await self._optimize_with_retry(resume_data, ctx)
        if not llm_output:
            raise ValueError("LLM returned no usable output after retries")

        # 4. Post-process
        optimized_resume = self._post_process(llm_output["optimized_resume"])

        # 5. Persist
        target_id = await self._persist(resume, ctx, optimized_resume, llm_output)

        # 6. Build & return result
        manager_ready = self._to_manager_format(optimized_resume)
        return OptimizationResult(
            success                    = True,
            resume_id                  = target_id,
            original_resume            = resume_data,
            optimized_resume           = manager_ready,
            suggestions                = llm_output.get("optimization_summary", ""),
            improvements               = llm_output.get("improvements_made", []),
            ats_score                  = llm_output.get("projected_ats_score", 0),
            compatibility_score        = llm_output.get("compatibility_score", 0),
            compatibility_feedback     = llm_output.get("compatibility_feedback", ""),
            skill_gap                  = llm_output.get("skill_gap", []),
            matching_skills            = llm_output.get("matching_skills", []),
            skill_recommendations      = llm_output.get("skill_recommendations", []),
            certificate_recommendations= llm_output.get("certificate_recommendations", []),
        )

    # ─── Step 1: Resolve context ───────────────

    async def _resolve_context(
        self, ctx: OptimizationContext
    ) -> tuple[Resume, OptimizationContext]:
        """Fetch resume and optionally enrich job description from DB."""
        if ctx.job_id and not ctx.job_description:
            job = self.db.query(Job).filter(Job.id == ctx.job_id).first()
            if job and job.job_description:
                ctx = OptimizationContext(**{**ctx.__dict__, "job_description": job.job_description})
                logger.info("Enriched context with job_id=%d description", ctx.job_id)

        resume = self.resume_manager.get_resume(ctx.resume_id, ctx.user_id)
        if not resume:
            raise ValueError(f"Resume {ctx.resume_id} not found or access denied for user {ctx.user_id}")

        return resume, ctx

    # ─── Step 2: Serialize resume ──────────────

    def _serialize_resume(self, resume: Resume) -> Dict[str, Any]:
        """Convert ORM model → clean dict for LLM consumption."""
        summary = ""
        if resume.parsed_data:
            try:
                summary = json.loads(resume.parsed_data).get("summary", "")
            except json.JSONDecodeError:
                logger.warning("Failed to parse resume.parsed_data for resume %d", resume.id)

        # Cap experience to latest N roles to keep prompt focused
        sorted_experience = sorted(
            resume.experience,
            key=lambda e: e.start_date or "",
            reverse=True,
        )[:_MAX_EXPERIENCE_ROLES]

        return {
            "full_name":   resume.full_name,
            "title":       resume.title,
            "summary":     summary,
            "target_role": resume.target_role,
            "education": [
                {
                    "school":     e.school,
                    "degree":     e.degree,
                    "major":      e.major,
                    "start_date": e.start_date,
                    "end_date":   e.end_date,
                    "description":e.description,
                }
                for e in resume.education
            ],
            "experience": [
                {
                    "company":    e.company,
                    "role":       e.role,
                    "location":   e.location,
                    "start_date": e.start_date,
                    "end_date":   e.end_date,
                    "current":    e.current,
                    "description":e.description,
                }
                for e in sorted_experience
            ],
            "projects": [
                {
                    "project_name": p.project_name,
                    "description":  p.description,
                    "technologies": p.technologies,
                }
                for p in resume.projects
            ],
            "skills": [s.name for s in resume.skills],
        }

    # ─── Step 3: LLM call with retry ──────────

    async def _optimize_with_retry(
        self, resume_data: Dict[str, Any], ctx: OptimizationContext
    ) -> Optional[Dict[str, Any]]:
        """Call LLM with exponential back-off and structured schema enforcement."""
        prompt = self._build_prompt(resume_data, ctx)
        schema = self._build_response_schema()

        for attempt in range(1, _MAX_LLM_RETRIES + 1):
            try:
                result = await llm_service.generate_structured_output_async(prompt, schema)
                if result and "optimized_resume" in result:
                    logger.info(
                        "LLM optimization succeeded on attempt %d for resume %d",
                        attempt, ctx.resume_id,
                    )
                    return result

                logger.warning(
                    "Attempt %d/%d: LLM returned incomplete output for resume %d",
                    attempt, _MAX_LLM_RETRIES, ctx.resume_id,
                )
            except Exception as exc:
                logger.error(
                    "Attempt %d/%d: LLM call failed for resume %d – %s",
                    attempt, _MAX_LLM_RETRIES, ctx.resume_id, exc,
                )

            if attempt < _MAX_LLM_RETRIES:
                await asyncio.sleep(_LLM_RETRY_DELAY * (2 ** (attempt - 1)))

        return None

    # ─── Step 4: Post-process ─────────────────

    def _post_process(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """Clean LLM artifacts and validate structural completeness."""
        processed = dict(raw)

        # Clean text fields
        for field_name in ("title", "target_role", "summary"):
            if processed.get(field_name):
                processed[field_name] = clean_text(processed[field_name])

        # Clean experience descriptions
        if "experience" in processed:
            processed["experience"] = [
                clean_experience_entry(exp) for exp in processed["experience"]
            ]

        # Sanitize skills — ensure list of strings, deduplicate, sort
        if "skills" in processed and isinstance(processed["skills"], list):
            seen = set()
            cleaned_skills = []
            for s in processed["skills"]:
                name = (s.get("name") if isinstance(s, dict) else str(s)).strip()
                if name and name.lower() not in seen:
                    seen.add(name.lower())
                    cleaned_skills.append(name)
            processed["skills"] = sorted(cleaned_skills, key=str.lower)

        return processed

    # ─── Step 5: Persist ──────────────────────

    async def _persist(
        self,
        resume:          Resume,
        ctx:             OptimizationContext,
        optimized_resume:Dict[str, Any],
        llm_output:      Dict[str, Any],
    ) -> int:
        """Save version record + analysis log; return target resume id."""
        if ctx.save_as_new:
            return self._create_new_resume(resume, ctx, optimized_resume)
        else:
            self._create_version_and_analysis(resume, optimized_resume, llm_output, ctx.job_description)
            return resume.id

    def _create_new_resume(
        self,
        source_resume:   Resume,
        ctx:             OptimizationContext,
        optimized_data:  Dict[str, Any],
    ) -> int:
        label = datetime.now().strftime("%b %d")
        new_title = (
            f"{source_resume.title or 'Resume'} – Tailored {label}"
            if ctx.job_description
            else f"{source_resume.title or 'Resume'} (Optimized)"
        )

        manager_data = self._to_manager_format(optimized_data)
        new_resume = self.resume_manager.create_resume(
            user=source_resume.user,
            resume_data={
                **manager_data,
                "title":       new_title,
                "target_role": manager_data.get("target_role", source_resume.target_role),
            },
        )

        # Carry over file attachment if present
        if source_resume.resume_file_url:
            new_resume.resume_file_url = source_resume.resume_file_url
            self.db.commit()

        logger.info("Created new tailored resume id=%d from source id=%d", new_resume.id, source_resume.id)
        return new_resume.id

    def _create_version_and_analysis(
        self,
        resume:          Resume,
        optimized_data:  Dict[str, Any],
        llm_output:      Dict[str, Any],
        job_description: str,
    ) -> None:
        version_number = len(resume.versions) + 1
        now = datetime.utcnow()

        version = ResumeVersion(
            resume_id      = resume.id,
            version_number = version_number,
            version_label  = f"AI Optimized · {now.strftime('%Y-%m-%d %H:%M')}",
            optimized_flag = True,
            parsed_data    = json.dumps(optimized_data),
            ats_score      = llm_output.get("projected_ats_score", 0),
            created_at     = now,
        )

        analysis = ResumeAnalysis(
            resume_id       = resume.id,
            analysis_type   = "optimization",
            score           = llm_output.get("projected_ats_score", 0),
            feedback        = json.dumps({
                "summary":               llm_output.get("optimization_summary", ""),
                "improvements":          llm_output.get("improvements_made", []),
                "compatibility_score":   llm_output.get("compatibility_score", 0),
                "compatibility_feedback":llm_output.get("compatibility_feedback", ""),
                "skill_gap":             llm_output.get("skill_gap", []),
                "matching_skills":       llm_output.get("matching_skills", []),
            }),
            job_description = job_description,
            created_at      = now,
        )

        self.db.add_all([version, analysis])
        self.db.commit()
        logger.info("Persisted version #%d and analysis for resume id=%d", version_number, resume.id)

    # ─── Prompt builder ───────────────────────

    def _build_prompt(self, resume_data: Dict[str, Any], ctx: OptimizationContext) -> str:
        seniority_hint = ""
        if ctx.target_seniority:
            power_verbs = ", ".join(_SENIORITY_KEYWORDS[ctx.target_seniority])
            seniority_hint = (
                f"\nSENIORITY TARGET: {ctx.target_seniority.value.upper()}\n"
                f"Preferred action verbs for this level: {power_verbs}.\n"
            )

        if ctx.job_description:
            mode_block = (
                "═══ MODE: JOB-SPECIFIC TAILORING (MAX PRECISION) ═══\n"
                f"TARGET JOB DESCRIPTION:\n{ctx.job_description}\n\n"
                "GOALS:\n"
                "1. ALIGNMENT     – Re-engineer every bullet to speak directly to JD requirements.\n"
                "2. KEYWORD INJECTION – Naturally embed the top 12–15 mission-critical keywords.\n"
                "3. IMPACT QUANTIFICATION – Use the XYZ formula: 'Accomplished [X] measured by [Y], by doing [Z]'.\n"
                "4. SENIORITY MATCH – Align tone and responsibilities to the seniority expected in the JD.\n"
                "5. GAP BRIDGING – Surface transferable skills that bridge any visible experience gaps.\n"
            )
        else:
            target = resume_data.get("target_role", "Professional")
            mode_block = (
                "═══ MODE: UNIVERSAL ATS EXCELLENCE & PROFESSIONAL BRANDING ═══\n\n"
                "GOALS:\n"
                "1. ATS READABILITY   – Standard section headers; zero fancy formatting.\n"
                "2. VERB DYNAMISM     – Replace generic verbs with high-octane action verbs.\n"
                "3. METRIC INJECTION  – Add numbers, percentages, or dollar figures to every role.\n"
                f"4. VALUE PROPOSITION – Rewrite summary as a keyword-dense elevator pitch for: {target}.\n"
                "5. BREVITY           – Remove fluff; every word must earn its place.\n"
            )

        compliance = (
            "COMPLIANCE RULES:\n"
            "• Return 'optimized_resume' with the EXACT SAME structure as the input JSON.\n"
            "• Focus on the latest 3–4 roles; make them the most detailed.\n"
            "• NEVER fabricate titles, dates, companies, or degrees.\n"
            "• Use standard bullet points (–). Avoid Markdown bold/italic inside text fields.\n"
            "• All dates must remain in their original format.\n"
        )

        return (
            "You are the world's most advanced Resume Optimization AI — "
            "a hybrid of a Stanford-trained NLP engineer and a Fortune 500 talent partner.\n"
            "Your mission: transform the resume below into a 99th-percentile document.\n\n"
            f"{mode_block}\n"
            f"{seniority_hint}\n"
            f"{compliance}\n"
            f"RESUME JSON:\n{json.dumps(resume_data, indent=2)}\n\n"
            "Respond ONLY with a valid JSON object matching the specified schema. No prose outside JSON."
        )

    # ─── Response schema ──────────────────────

    @staticmethod
    def _build_response_schema() -> Dict[str, Any]:
        experience_item = {
            "type": "object",
            "properties": {
                "company":     {"type": "string"},
                "role":        {"type": "string"},
                "location":    {"type": "string"},
                "start_date":  {"type": "string"},
                "end_date":    {"type": "string"},
                "current":     {"type": "boolean"},
                "description": {"type": "string"},
            },
        }
        education_item = {
            "type": "object",
            "properties": {
                "school":      {"type": "string"},
                "degree":      {"type": "string"},
                "major":       {"type": "string"},
                "start_date":  {"type": "string"},
                "end_date":    {"type": "string"},
                "description": {"type": "string"},
            },
        }
        project_item = {
            "type": "object",
            "properties": {
                "project_name": {"type": "string"},
                "description":  {"type": "string"},
                "technologies": {"type": "string"},
            },
        }
        return {
            "type": "object",
            "required": ["optimized_resume", "optimization_summary", "improvements_made", "projected_ats_score"],
            "properties": {
                "optimized_resume": {
                    "type": "object",
                    "required": ["title", "summary", "experience", "skills"],
                    "properties": {
                        "title":       {"type": "string"},
                        "target_role": {"type": "string"},
                        "summary":     {"type": "string"},
                        "education":   {"type": "array", "items": education_item},
                        "experience":  {"type": "array", "items": experience_item},
                        "projects":    {"type": "array", "items": project_item},
                        "skills":      {"type": "array", "items": {"type": "string"}},
                    },
                },
                "optimization_summary":        {"type": "string"},
                "improvements_made":           {"type": "array",  "items": {"type": "string"}, "minItems": 3, "maxItems": 10},
                "projected_ats_score":         {"type": "integer", "minimum": 0,  "maximum": 100},
                "compatibility_score":         {"type": "integer", "minimum": 0,  "maximum": 100},
                "compatibility_feedback":      {"type": "string"},
                "skill_gap":                   {"type": "array",  "items": {"type": "string"}},
                "matching_skills":             {"type": "array",  "items": {"type": "string"}},
                "skill_recommendations":       {"type": "array",  "items": {"type": "string"}, "maxItems": 5},
                "certificate_recommendations": {"type": "array",  "items": {"type": "string"}, "maxItems": 3},
            },
        }

    # ─── Helpers ──────────────────────────────

    @staticmethod
    def _to_manager_format(resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert LLM skills list[str] → list[dict] expected by ResumeManager."""
        data = resume_data.copy()
        if "skills" in data and isinstance(data["skills"], list):
            data["skills"] = [
                {"name": s} if isinstance(s, str) else s
                for s in data["skills"]
            ]
        return data

    def build_resume_text(self, resume: Resume) -> str:
        """
        Plain-text representation of a resume (useful for keyword extraction,
        diff-views, and non-LLM ATS scanners).
        """
        lines: List[str] = []

        def _add(label: str, value: Optional[str]) -> None:
            if value:
                lines.append(f"{label}: {value}")

        _add("Name",     resume.full_name)
        _add("Email",    resume.email)
        _add("Phone",    resume.phone)
        _add("LinkedIn", resume.linkedin_url)
        _add("Title",    resume.title or resume.target_role)

        if resume.education:
            lines.append("\nEDUCATION")
            for e in resume.education:
                parts = [f"{e.degree} — {e.school}"]
                if e.major:      parts.append(f"Major: {e.major}")
                if e.gpa:        parts.append(f"GPA: {e.gpa}")
                date_range = _format_date_range(e.start_date, e.end_date)
                if date_range:   parts.append(date_range)
                lines.append("  • " + " | ".join(parts))
                if e.description:
                    lines.append(f"    {e.description}")

        if resume.experience:
            lines.append("\nEXPERIENCE")
            for e in resume.experience:
                date_range = _format_date_range(e.start_date, e.end_date, e.current)
                header = f"{e.role} @ {e.company}"
                if e.location:  header += f", {e.location}"
                if date_range:  header += f"  ({date_range})"
                lines.append(f"  • {header}")
                if e.description:
                    lines.append(f"    {e.description}")

        if resume.projects:
            lines.append("\nPROJECTS")
            for p in resume.projects:
                lines.append(f"  • {p.project_name}")
                if p.description:   lines.append(f"    {p.description}")
                if p.technologies:  lines.append(f"    Tech: {p.technologies}")

        if resume.skills:
            lines.append("\nSKILLS")
            lines.append("  " + " · ".join(s.name for s in resume.skills))

        return "\n".join(lines)


# ──────────────────────────────────────────────
# Utility helpers (module-level)
# ──────────────────────────────────────────────

def _format_date_range(
    start: Optional[str],
    end:   Optional[str],
    current: bool = False,
) -> str:
    if not start:
        return ""
    end_label = "Present" if current or not end else end
    return f"{start} – {end_label}"