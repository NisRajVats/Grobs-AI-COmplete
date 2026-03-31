"""
Resume optimization service for AI-powered resume improvements.
"""
import json
import logging
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from datetime import datetime

from app.models import Resume, ResumeVersion, ResumeAnalysis, Job
from rapidfuzz import fuzz
from app.services.llm_service import llm_service
from app.services.resume_service.resume_manager import ResumeManager
from .parser import clean_text, clean_experience_entry  # Reuse parser utils

logger = logging.getLogger(__name__)


class ResumeOptimizer:
    """AI-powered resume optimization service."""
    
    def __init__(self, db: Session):
        self.db = db
        self.resume_manager = ResumeManager(db)
    
    def optimize_resume(
        self,
        resume_id: int,
        user_id: int,
        optimization_type: str = "comprehensive",
        job_description: str = "",
        job_id: Optional[int] = None,
        save_as_new: bool = False
    ) -> Dict[str, Any]:
        """
        Optimize a resume using AI for language, tone, ATS score, and grammar.
        """
        # Ensure latest API keys from .env are loaded
        llm_service.refresh_config()
        
        # If job_id is provided, fetch job description
        if job_id and not job_description:
            job = self.db.query(Job).filter(Job.id == job_id).first()
            if job:
                job_description = job.job_description or ""
                logger.info(f"Fetched job description from job_id {job_id}")
        
        # Get resume using manager to ensure decryption of sensitive fields
        resume = self.resume_manager.get_resume(resume_id, user_id)
        if not resume:
            raise ValueError("Resume not found or access denied")
        
        # Prepare data for LLM
        resume_data = self._prepare_resume_data_for_llm(resume)
        
        # Perform deep optimization using LLM
        optimized_result = self._perform_deep_optimization(resume_data, optimization_type, job_description)
        
        if not optimized_result or "optimized_resume" not in optimized_result:
            error_msg = optimized_result.get("error") if optimized_result else "AI service returned no result"
            logger.error(f"Optimization failed for resume {resume_id}: {error_msg}")
            return {"success": False, "error": f"AI optimization failed: {error_msg}"}

        # Post-process LLM output to clean artifacts
        optimized_resume = optimized_result["optimized_resume"]
        
        # Clean experience descriptions
        if "experience" in optimized_resume:
            optimized_resume["experience"] = [
                clean_experience_entry(exp) for exp in optimized_resume["experience"]
            ]
        
        # Clean summary
        if "summary" in optimized_resume:
            optimized_resume["summary"] = clean_text(optimized_resume["summary"])
        
        # Clean other text fields
        for field in ["title", "target_role"]:
            if field in optimized_resume and optimized_resume[field]:
                optimized_resume[field] = clean_text(optimized_resume[field])

        # Prepare data for update
        optimized_resume_data = optimized_resume
        
        # Convert skills from list of strings to list of dicts with 'name' for the manager
        manager_data = optimized_resume_data.copy()
        if "skills" in manager_data and isinstance(manager_data["skills"], list):
            manager_data["skills"] = [{"name": s} for s in manager_data["skills"]]

        target_resume_id = resume_id
        
        if save_as_new:
            # Create a new resume record instead of updating
            new_title = f"{resume.title or 'Resume'} (Tailored)"
            if job_description:
                new_title = f"{resume.title or 'Resume'} - {datetime.now().strftime('%b %d')}"
            
            new_resume = self.resume_manager.create_resume(
                user=resume.user,
                resume_data={
                    **manager_data,
                    "title": new_title,
                    "target_role": manager_data.get("target_role", resume.target_role)
                }
            )
            target_resume_id = new_resume.id
            # Copy file URL if exists
            if resume.resume_file_url:
                new_resume.resume_file_url = resume.resume_file_url
                self.db.commit()
        else:
            # DO NOT update main resume immediately during optimization to allow review
            # Create new optimized version in DB for tracking
            version = self._create_optimized_version(resume, optimized_result, job_description)
        
        # ATS SCORE FOR PREVIEW
        final_ats_score = optimized_result.get("projected_ats_score", 0)
        
        return {
            "success": True,
            "resume_id": target_resume_id,
            "suggestions": optimized_result.get("optimization_summary", ""),
            "improvements": optimized_result.get("improvements_made", []),
            "ats_score": final_ats_score,
            "original_resume": resume_data,
            "optimized_resume": manager_data,
            "compatibility_score": optimized_result.get("compatibility_score", 0),
            "compatibility_feedback": optimized_result.get("compatibility_feedback", ""),
            "skill_gap": optimized_result.get("skill_gap", []),
            "matching_skills": optimized_result.get("matching_skills", []),
            "skill_recommendations": optimized_result.get("skill_recommendations", []),
            "certificate_recommendations": optimized_result.get("certificate_recommendations", [])
        }

    def _prepare_resume_data_for_llm(self, resume: Resume) -> Dict[str, Any]:
        """Convert resume model to a structured dict for LLM processing."""
        # Extract summary from parsed_data if available
        summary = ""
        if resume.parsed_data:
            try:
                pd = json.loads(resume.parsed_data)
                summary = pd.get("summary", "")
            except:
                pass

        return {
            "full_name": resume.full_name,
            "title": resume.title,
            "summary": summary,
            "target_role": resume.target_role,
            "education": [
                {
                    "school": e.school, "degree": e.degree, "major": e.major, 
                    "start_date": e.start_date, "end_date": e.end_date, "description": e.description
                } for e in resume.education
            ],
            "experience": [
                {
                    "company": e.company, "role": e.role, "location": e.location,
                    "start_date": e.start_date, "end_date": e.end_date, "current": e.current,
                    "description": e.description
                } for e in resume.experience
            ],
            "projects": [
                {
                    "project_name": p.project_name, "description": p.description, 
                    "technologies": p.technologies
                } for p in resume.projects
            ],
            "skills": [s.name for s in resume.skills]
        }

    def _perform_deep_optimization(self, resume_data: Dict[str, Any], opt_type: str, job_desc: str) -> Optional[Dict]:
        """Use LLM to perform actual optimization of content for 98% ATS accuracy."""
        try:
            if job_desc:
                mode_instruction = f"MODE: JOB-SPECIFIC TAILORING\n" \
                                   f"TARGET JOB DESCRIPTION:\n{job_desc}\n\n" \
                                   f"GOALS:\n" \
                                   f"1. Align every section with the JD's core requirements.\n" \
                                   f"2. Incorporate missing keywords from the JD naturally but prominently.\n" \
                                   f"3. Highlight most relevant experience for this specific role.\n" \
                                   f"4. Adapt the professional summary to speak directly to the job's needs."
            else:
                mode_instruction = f"MODE: GENERAL ATS SCORE OPTIMIZATION & PROFESSIONAL EXCELLENCE\n\n" \
                                   f"GOALS:\n" \
                                   f"1. Fix all formatting and structural issues identified in ATS analysis.\n" \
                                   f"2. Replace passive language with high-impact, industry-leading action verbs (e.g., 'Spearheaded', 'Engineered', 'Orchestrated').\n" \
                                   f"3. Quantify every possible achievement using hard metrics (%, $, scale, impact).\n" \
                                   f"4. Enhance the Professional Summary to be impactful, keyword-dense, and highly professional for the target role: {resume_data.get('target_role', 'Professional')}.\n" \
                                   f"5. Improve the clarity, tone, and professional language across all sections.\n" \
                                   f"6. Ensure 100% ATS readability and structural integrity."

            prompt = f"You are a world-class Resume Optimizer and ATS Algorithm Expert.\n" \
                     f"Your task is to rewrite the provided resume data to achieve a 98%+ ATS compatibility score and professional perfection.\n\n" \
                     f"{mode_instruction}\n\n" \
                     f"STRICT PRINCIPLES:\n" \
                     f"- DO NOT use generic filler text or buzzwords without context. Be specific and high-impact.\n" \
                     f"- Maintain 100% truthfulness; do not invent new roles or degrees, but you MAY rephrase existing descriptions to be more impressive and metric-focused.\n" \
                     f"- Focus on making the resume 'machine-readable' (ATS) and 'recruiter-ready' (Human).\n" \
                     f"- Every bullet point should follow the STAR (Situation, Task, Action, Result) or Google's X-Y-Z formula.\n\n" \
                     f"RESUME DATA:\n" \
                     f"{json.dumps(resume_data, indent=2)}\n\n" \
                     f"Return a structured JSON object with:\n" \
                     f"- optimized_resume: (Object matching input structure with improved content - ensure EVERY field is present)\n" \
                     f"- optimization_summary: (Comprehensive string summarizing exactly what technical improvements were made and why)\n" \
                     f"- improvements_made: (List of 5-8 specific, high-value enhancements - e.g., 'Transformed passive responsibilities into metric-driven achievements for the Senior Dev role')\n" \
                     f"- projected_ats_score: (Integer 90-100 indicating the NEW improved score)\n" \
                     f"- compatibility_score: (Integer 0-100 for JD match; or 0 if no JD)\n" \
                     f"- compatibility_feedback: (Specific, actionable feedback on how this optimization improved matching)\n" \
                     f"- skill_gap: (List of key industry skills still missing that the candidate should consider adding)\n" \
                     f"- matching_skills: (List of high-impact skills now prominently featured)\n" \
                     f"- skill_recommendations: (List of specific technical skills to learn for this career path)\n" \
                     f"- certificate_recommendations: (List of high-value certifications to increase market value)"
            
            schema = {
                "type": "object",
                "properties": {
                    "optimized_resume": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "target_role": {"type": "string"},
                            "summary": {"type": "string"},
                            "education": {"type": "array", "items": {"type": "object"}},
                            "experience": {"type": "array", "items": {"type": "object"}},
                            "projects": {"type": "array", "items": {"type": "object"}},
                            "skills": {"type": "array", "items": {"type": "string"}}
                        }
                    },
                    "optimization_summary": {"type": "string"},
                    "improvements_made": {"type": "array", "items": {"type": "string"}},
                    "projected_ats_score": {"type": "integer"},
                    "compatibility_score": {"type": "integer"},
                    "compatibility_feedback": {"type": "string"},
                    "skill_gap": {"type": "array", "items": {"type": "string"}},
                    "matching_skills": {"type": "array", "items": {"type": "string"}},
                    "skill_recommendations": {"type": "array", "items": {"type": "string"}},
                    "certificate_recommendations": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["optimized_resume", "optimization_summary", "improvements_made", "projected_ats_score"]
            }
            
            return llm_service.generate_structured_output(prompt, schema)
        except Exception as e:
            logger.error(f"Deep optimization failed: {e}")
            return None

    def _create_optimized_version(self, resume: Resume, result: Dict[str, Any], job_desc: str = "") -> ResumeVersion:
        """Create and save the optimized version in the database."""
        # Get latest version number
        version_number = len(resume.versions) + 1
        
        version = ResumeVersion(
            resume_id=resume.id,
            version_number=version_number,
            version_label=f"AI Optimized ({datetime.now().strftime('%Y-%m-%d %H:%M')})",
            optimized_flag=True,
            parsed_data=json.dumps(result["optimized_resume"]),
            ats_score=result["projected_ats_score"],
            created_at=datetime.utcnow()
        )
        
        self.db.add(version)
        
        # Also log the optimization in analyses
        analysis = ResumeAnalysis(
            resume_id=resume.id,
            analysis_type="optimization",
            score=result["projected_ats_score"],
            feedback=json.dumps({
                "summary": result["optimization_summary"],
                "improvements": result["improvements_made"],
                "compatibility_score": result.get("compatibility_score", 0),
                "compatibility_feedback": result.get("compatibility_feedback", "")
            }),
            job_description=job_desc,
            created_at=datetime.utcnow()
        )
        self.db.add(analysis)
        
        self.db.commit()
        self.db.refresh(version)
        return version
    
    def _build_resume_text(self, resume: Resume) -> str:
        """Build text representation of resume for optimization."""
        sections = []
        
        # Contact info
        if resume.full_name:
            sections.append(f"Name: {resume.full_name}")
        if resume.email:
            sections.append(f"Email: {resume.email}")
        if resume.phone:
            sections.append(f"Phone: {resume.phone}")
        if resume.linkedin_url:
            sections.append(f"LinkedIn: {resume.linkedin_url}")
        
        # Summary
        if resume.title or resume.target_role:
            sections.append(f"Title: {resume.title or resume.target_role}")
        
        # Education
        if resume.education:
            sections.append("EDUCATION:")
            for edu in resume.education:
                edu_text = f"- {edu.degree} from {edu.school}"
                if edu.major:
                    edu_text += f", Major: {edu.major}"
                if edu.gpa:
                    edu_text += f", GPA: {edu.gpa}"
                sections.append(edu_text)
        
        # Experience
        if resume.experience:
            sections.append("EXPERIENCE:")
            for exp in resume.experience:
                exp_text = f"- {exp.role} at {exp.company}"
                if exp.location:
                    exp_text += f", {exp.location}"
                if exp.start_date:
                    exp_text += f" ({exp.start_date}"
                    if exp.end_date:
                        exp_text += f" - {exp.end_date}"
                    elif exp.current:
                        exp_text += " - Present"
                    exp_text += ")"
                if exp.description:
                    exp_text += f": {exp.description}"
                sections.append(exp_text)
        
        # Projects
        if resume.projects:
            sections.append("PROJECTS:")
            for proj in resume.projects:
                proj_text = f"- {proj.project_name}"
                if proj.description:
                    proj_text += f": {proj.description}"
                if proj.technologies:
                    proj_text += f" (Tech: {proj.technologies})"
                sections.append(proj_text)
        
        # Skills
        if resume.skills:
            skill_names = [skill.name for skill in resume.skills]
            sections.append(f"SKILLS: {', '.join(skill_names)}")
        
        return "\n".join(sections)
