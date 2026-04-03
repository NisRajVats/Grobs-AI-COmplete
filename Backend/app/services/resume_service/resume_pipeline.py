"""
Unified Resume Processing Pipeline Service

Central orchestrator for the complete resume processing workflow:

Resume Upload
    ↓
Resume Parsing (extract text, contact info, structured data)
    ↓
Resume Content Storage (store parsed data)
    ↓
Embedding Generation (create vector embeddings)
    ↓
ATS Analysis (calculate scores, identify keywords)
    ↓
Resume Optimization (AI-powered improvements)
    ↓
Job Matching (vector similarity search)

Each step depends on the previous step completing successfully.
"""
import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.models import Resume, ResumeContent, ResumeAnalysis, ResumeEmbedding, ResumeVersion, Education, Experience, Project, Skill
from app.utils.encryption import encrypt, decrypt
from app.services.resume_service.parser import parse_resume as parse_resume_file
from app.services.resume_service.ats_analyzer import calculate_ats_score as calculate_ats
from app.services.resume_service.optimizer import ResumeOptimizer
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


class ResumePipelineService:
    """
    Unified service for orchestrating resume processing pipeline.
    Ensures proper sequencing: parsing → embedding → ATS → optimization → matching.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== Pipeline Stages ====================
    
    async def process_resume_upload(
        self,
        resume_id: int,
        file_path: str,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Process uploaded resume through the full pipeline.
        
        Args:
            resume_id: ID of the resume
            file_path: Path to the resume file
            user_id: ID of the user
            
        Returns:
            Dictionary with pipeline results
        """
        results = {
            "resume_id": resume_id,
            "stages_completed": [],
            "errors": []
        }
        
        try:
            # Stage 1: Parse Resume
            parse_result = self.parse_resume(resume_id, file_path, user_id)
            if parse_result.get("success"):
                results["stages_completed"].append("parsing")
            else:
                results["errors"].append(f"Parsing failed: {parse_result.get('error')}")
                return results
            
            # Stage 2: Generate Embeddings
            embed_result = self.generate_resume_embeddings(resume_id, user_id)
            if embed_result.get("success"):
                results["stages_completed"].append("embeddings")
            else:
                results["errors"].append(f"Embedding failed: {embed_result.get('error')}")
            
            # Stage 3: Run ATS Analysis
            ats_result = await self.run_ats_analysis(resume_id, user_id)
            if ats_result.get("success"):
                results["stages_completed"].append("ats_analysis")
            else:
                results["errors"].append(f"ATS analysis failed: {ats_result.get('error')}")
            
            results["success"] = True
            
        except Exception as e:
            logger.error(f"Pipeline error for resume {resume_id}: {e}")
            results["errors"].append(str(e))
            results["success"] = False
        
        return results
    
    def parse_resume(
        self,
        resume_id: int,
        file_path: str,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Stage 1: Parse resume PDF and extract structured data.
        
        Args:
            resume_id: ID of the resume
            file_path: Path to the resume file
            user_id: ID of the user
            
        Returns:
            Parsing result
        """
        try:
            # Resolve absolute path for local storage
            full_path = file_path
            if not full_path.startswith("http"):
                base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
                full_path = os.path.join(base_dir, "uploads", full_path)
            
            # Parse the resume file
            parsed_data = parse_resume_file(full_path)
            
            # Get or create resume content
            resume = self.db.query(Resume).filter(
                Resume.id == resume_id,
                Resume.user_id == user_id
            ).first()
            
            if not resume:
                return {"success": False, "error": "Resume not found"}
            
            # Check if content already exists
            content = self.db.query(ResumeContent).filter(
                ResumeContent.resume_id == resume_id
            ).first()
            
            if not content:
                content = ResumeContent(resume_id=resume_id)
                self.db.add(content)
            
            # Update content with parsed data
            content.full_name_encrypted = encrypt(parsed_data.get("full_name", ""))
            content.email_encrypted = encrypt(parsed_data.get("email", ""))
            content.phone_encrypted = encrypt(parsed_data.get("phone", ""))
            content.linkedin_url_encrypted = encrypt(parsed_data.get("linkedin_url", ""))
            content.raw_text = parsed_data.get("raw_text", "")
            content.parsed_json = parsed_data
            content.parsed_at = datetime.now().isoformat()
            content.updated_at = datetime.now().isoformat()
            
            # Update resume main fields for preview
            resume.full_name = encrypt(parsed_data.get("full_name", ""))
            resume.email = encrypt(parsed_data.get("email", ""))
            resume.phone = encrypt(parsed_data.get("phone", ""))
            resume.linkedin_url = encrypt(parsed_data.get("linkedin_url", ""))
            resume.parsed_data = json.dumps(parsed_data)
            
            # Populate nested tables
            self._update_nested_data(resume, parsed_data)
            
            # Update resume status
            resume.status = "parsed"
            resume.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"Successfully parsed resume {resume_id}")
            
            return {
                "success": True,
                "parsed_data": parsed_data
            }
            
        except Exception as e:
            logger.error(f"Error parsing resume {resume_id}: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    def generate_resume_embeddings(
        self,
        resume_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Stage 2: Generate vector embeddings for semantic search.
        
        Args:
            resume_id: ID of the resume
            user_id: ID of the user
            
        Returns:
            Embedding result
        """
        try:
            # Get resume content
            resume = self.db.query(Resume).filter(
                Resume.id == resume_id,
                Resume.user_id == user_id
            ).first()
            
            if not resume:
                return {"success": False, "error": "Resume not found"}
            
            content = self.db.query(ResumeContent).filter(
                ResumeContent.resume_id == resume_id
            ).first()
            
            if not content:
                return {"success": False, "error": "Resume not parsed yet"}
            
            # Build resume text for embedding
            resume_text = self._build_resume_text(resume, content)
            
            # Generate embeddings using LLM service
            embeddings = llm_service.generate_embeddings(resume_text)
            
            if not embeddings:
                return {"success": False, "error": "Failed to generate embeddings"}
            
            embedding = embeddings[0]
            
            # Store or update embedding
            existing = self.db.query(ResumeEmbedding).filter(
                ResumeEmbedding.resume_id == resume_id
            ).first()
            
            if not existing:
                existing = ResumeEmbedding(resume_id=resume_id)
                self.db.add(existing)
            
            existing.embedding_vector = embedding.embedding
            existing.model_name = embedding.model
            existing.updated_at = datetime.now().isoformat()
            
            self.db.commit()
            
            logger.info(f"Successfully generated embeddings for resume {resume_id}")
            
            return {
                "success": True,
                "model": embedding.model
            }
            
        except Exception as e:
            logger.error(f"Error generating embeddings for resume {resume_id}: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    async def run_ats_analysis(
        self,
        resume_id: int,
        user_id: int,
        job_description: str = ""
    ) -> Dict[str, Any]:
        """
        Stage 3: Run ATS analysis on parsed resume.
        
        Args:
            resume_id: ID of the resume
            user_id: ID of the user
            job_description: Optional job description for matching
            
        Returns:
            ATS analysis result
        """
        try:
            # Get resume with relationships
            resume = self.db.query(Resume).filter(
                Resume.id == resume_id,
                Resume.user_id == user_id
            ).first()
            
            if not resume:
                return {"success": False, "error": "Resume not found"}
            
            # Decrypt content for analysis
            content = self.db.query(ResumeContent).filter(
                ResumeContent.resume_id == resume_id
            ).first()
            
            if not content:
                return {"success": False, "error": "Resume not parsed yet"}
            
            # Build resume object for ATS analyzer
            resume_for_ats = self._build_resume_for_ats(resume, content)
            
            # Calculate ATS score
            ats_result = await calculate_ats(resume_for_ats, job_description=job_description)
            
            # Prepare feedback dictionary including new metrics
            feedback_dict = {
                "category_scores": ats_result.get("category_scores", {}),
                "skill_analysis": ats_result.get("skill_analysis", {}),
                "keyword_gap": ats_result.get("keyword_gap", {}),
                "industry_tips": ats_result.get("industry_tips", []),
                "llm_powered": ats_result.get("llm_powered", False)
            }
            
            # Store analysis result
            analysis = ResumeAnalysis(
                resume_id=resume_id,
                analysis_type="ats",
                score=ats_result.get("overall_score"),
                feedback=json.dumps(feedback_dict),
                missing_keywords=json.dumps(ats_result.get("issues", [])),
                suggestions=json.dumps(ats_result.get("recommendations", [])),
                job_description=job_description if job_description else None
            )
            
            self.db.add(analysis)
            
            # Update resume with score
            resume.ats_score = ats_result.get("overall_score")
            resume.analysis_score = ats_result.get("overall_score")
            resume.status = "analyzed"
            resume.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"Successfully ran ATS analysis for resume {resume_id}")
            
            return {
                "success": True,
                "ats_score": ats_result.get("overall_score")
            }
            
        except Exception as e:
            logger.error(f"Error running ATS analysis for resume {resume_id}: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    async def optimize_resume(
        self,
        resume_id: int,
        user_id: int,
        job_description: str = ""
    ) -> Dict[str, Any]:
        """
        Stage 4: AI-powered resume optimization.
        
        Args:
            resume_id: ID of the resume
            user_id: ID of the user
            job_description: Optional job description for tailoring
            
        Returns:
            Optimization result
        """
        try:
            # Use the specialized ResumeOptimizer for Stage 4
            optimizer = ResumeOptimizer(self.db)
            result = await optimizer.optimize_resume(
                resume_id=resume_id,
                user_id=user_id,
                job_description=job_description,
                optimization_type="comprehensive"
            )
            
            if not result.get("success"):
                return {"success": False, "error": result.get("error")}
            
            # Update resume status to optimized
            resume = self.db.query(Resume).filter(Resume.id == resume_id).first()
            if resume:
                resume.status = "optimized"
                self.db.commit()
            
            logger.info(f"Successfully optimized resume {resume_id} through pipeline")
            
            return {
                "success": True,
                "optimization": result.get("optimized_resume"),
                "suggestions": result.get("suggestions"),
                "ats_score": result.get("ats_score")
            }
            
        except Exception as e:
            logger.error(f"Error in pipeline resume optimization {resume_id}: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    def match_jobs(
        self,
        resume_id: int,
        user_id: int,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Stage 5: Match resume to jobs using vector similarity.
        
        Args:
            resume_id: ID of the resume
            user_id: ID of the user
            limit: Maximum number of job matches
            
        Returns:
            Job matching results
        """
        from app.services.job_service.job_matcher import JobMatcher
        
        try:
            matcher = JobMatcher(self.db)
            matches = matcher.match_resume_to_jobs(resume_id, user_id, limit)
            
            return {
                "success": True,
                "matches": matches,
                "count": len(matches)
            }
            
        except Exception as e:
            logger.error(f"Error matching jobs for resume {resume_id}: {e}")
            return {"success": False, "error": str(e)}
    
    # ==================== Helper Methods ====================
    
    def _build_resume_text(self, resume: Resume, content: ResumeContent) -> str:
        """Build text representation of resume for embedding."""
        parts = []
        
        # Contact info
        full_name = decrypt(content.full_name_encrypted) if content.full_name_encrypted else ""
        if full_name:
            parts.append(f"Name: {full_name}")
        
        email = decrypt(content.email_encrypted) if content.email_encrypted else ""
        if email:
            parts.append(f"Email: {email}")
        
        # Skills
        if content.skills_list:
            parts.append(f"Skills: {', '.join(content.skills_list)}")
        
        # Experience
        for exp in resume.experience:
            parts.append(f"Role: {exp.role} at {exp.company}. {exp.description or ''}")
        
        # Education
        for edu in resume.education:
            parts.append(f"Education: {edu.degree} from {edu.school}")
        
        # Projects
        for proj in resume.projects:
            parts.append(f"Project: {proj.project_name}. {proj.description or ''}")
        
        return "\n".join(parts)
    
    def _build_resume_for_ats(self, resume: Resume, content: ResumeContent) -> Any:
        """Build resume object compatible with ATS analyzer."""
        # Extract summary from parsed_json
        summary = ""
        if content.parsed_json and isinstance(content.parsed_json, dict):
            summary = content.parsed_json.get("summary", "")
        elif resume.parsed_data:
            try:
                pd = json.loads(resume.parsed_data)
                summary = pd.get("summary", "")
            except:
                pass
                
        # Create a simple object with required attributes
        class ResumeForATS:
            def __init__(self, resume, content, summary):
                self.full_name = decrypt(content.full_name_encrypted) if content.full_name_encrypted else ""
                self.email = decrypt(content.email_encrypted) if content.email_encrypted else ""
                self.phone = decrypt(content.phone_encrypted) if content.phone_encrypted else ""
                self.linkedin_url = decrypt(content.linkedin_url_encrypted) if content.linkedin_url_encrypted else ""
                self.title = resume.title
                self.target_role = resume.target_role
                self.summary = summary
                self.education = resume.education
                self.experience = resume.experience
                self.projects = resume.projects
                self.skills = resume.skills
        
        return ResumeForATS(resume, content, summary)
    
    def _build_optimization_prompt(
        self,
        resume: Resume,
        content: ResumeContent,
        job_description: str
    ) -> str:
        """Build prompt for resume optimization."""
        prompt = f"""Analyze and optimize this resume.

Resume:
{decrypt(content.raw_text) if content.raw_text else ''}

Skills: {', '.join([s.name for s in resume.skills])}
Experience: {len(resume.experience)} positions
Education: {len(resume.education)} entries

"""
        if job_description:
            prompt += f"""
Target Job Description:
{job_description}

Tailor the resume to better match this job.
"""
        
        prompt += """
Provide:
1. An improved professional summary
2. Key skills that should be highlighted
3. Specific suggestions for improvement
"""
        return prompt
    
    def _get_next_version_number(self, resume_id: int) -> int:
        """Get next version number for a resume."""
        latest = self.db.query(ResumeVersion).filter(
            ResumeVersion.resume_id == resume_id
        ).order_by(ResumeVersion.version_number.desc()).first()
        
        return (latest.version_number + 1) if latest else 1
    
    def _update_nested_data(self, resume: Resume, data: Dict[str, Any]):
        """Update nested data (education, experience, etc.) for a resume."""
        # Clear existing
        self.db.query(Education).filter(Education.resume_id == resume.id).delete()
        self.db.query(Experience).filter(Experience.resume_id == resume.id).delete()
        self.db.query(Project).filter(Project.resume_id == resume.id).delete()
        self.db.query(Skill).filter(Skill.resume_id == resume.id).delete()
        
        # Education
        for edu_data in data.get("education", []):
            edu = Education(
                resume_id=resume.id,
                school=edu_data.get("school", ""),
                degree=edu_data.get("degree", ""),
                major=edu_data.get("major"),
                gpa=edu_data.get("gpa"),
                start_date=edu_data.get("start_date", ""),
                end_date=edu_data.get("end_date", ""),
                description=edu_data.get("description")
            )
            self.db.add(edu)
        
        # Experience
        for exp_data in data.get("experience", []):
            description = exp_data.get("description")
            if not description and exp_data.get("points"):
                description = "\n".join(exp_data.get("points", []))
            
            exp = Experience(
                resume_id=resume.id,
                company=exp_data.get("company", ""),
                role=exp_data.get("role", ""),
                location=exp_data.get("location"),
                start_date=exp_data.get("start_date", ""),
                end_date=exp_data.get("end_date"),
                current=exp_data.get("current", False),
                description=description
            )
            self.db.add(exp)
        
        # Projects
        for proj_data in data.get("projects", []):
            description = proj_data.get("description")
            if not description and proj_data.get("points"):
                description = "\n".join(proj_data.get("points", []))
            
            technologies = proj_data.get("technologies")
            if isinstance(technologies, list):
                technologies = ", ".join(technologies)
            
            proj = Project(
                resume_id=resume.id,
                project_name=proj_data.get("project_name", ""),
                description=description,
                project_url=proj_data.get("project_url"),
                github_url=proj_data.get("github_url"),
                technologies=technologies
            )
            self.db.add(proj)
        
        # Skills
        for skill_data in data.get("skills", []):
            skill = Skill(
                resume_id=resume.id,
                name=skill_data.get("name", ""),
                category=skill_data.get("category", "Technical")
            )
            self.db.add(skill)
        
        self.db.commit()
    
    # ==================== Pipeline Status ====================
    
    def get_pipeline_status(self, resume_id: int, user_id: int) -> Dict[str, Any]:
        """Get current status of pipeline for a resume."""
        resume = self.db.query(Resume).filter(
            Resume.id == resume_id,
            Resume.user_id == user_id
        ).first()
        
        if not resume:
            return {"error": "Resume not found"}
        
        status = {
            "resume_id": resume_id,
            "current_status": resume.status,
            "stages": {
                "uploaded": True,
                "parsed": resume.status in ["parsed", "analyzed", "optimized"],
                "embedded": self._has_embeddings(resume_id),
                "analyzed": self._has_analysis(resume_id),
                "optimized": self._has_optimization(resume_id)
            }
        }
        
        return status
    
    def _has_embeddings(self, resume_id: int) -> bool:
        """Check if resume has embeddings."""
        return self.db.query(ResumeEmbedding).filter(
            ResumeEmbedding.resume_id == resume_id
        ).first() is not None
    
    def _has_analysis(self, resume_id: int) -> bool:
        """Check if resume has ATS analysis."""
        return self.db.query(ResumeAnalysis).filter(
            ResumeAnalysis.resume_id == resume_id,
            ResumeAnalysis.analysis_type == "ats"
        ).first() is not None
    
    def _has_optimization(self, resume_id: int) -> bool:
        """Check if resume has optimized version."""
        return self.db.query(ResumeVersion).filter(
            ResumeVersion.resume_id == resume_id,
            ResumeVersion.version_type == "optimized"
        ).first() is not None

