"""
Resume manager service for CRUD operations on resumes.
Supports multi-resume management per user.
"""
import json
import logging
import os   
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload, selectinload
from datetime import datetime

from app.core.config import settings
from app.models import Resume, ResumeVersion, Education, Experience, Project, Skill, ResumeAnalysis
from app.models.user import User
from app.utils.encryption import encrypt, decrypt
from app.services.resume_service.parser import parse_resume_async
from app.services.resume_service.ats_analyzer import calculate_ats_score as calculate_ats_score
from app.integrations.cloud_storage import cloud_storage_service as storage_service

logger = logging.getLogger(__name__)


class ResumeManager:
    """Manager for resume CRUD operations with multi-resume support."""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== CRUD Operations ====================
    
    def create_resume(
        self,
        user: User,
        resume_data: Dict[str, Any],
        file_content: Optional[bytes] = None,
        filename: Optional[str] = None
    ) -> Resume:
        """
        Create a new resume for a user.
        
        Args:
            user: User creating the resume
            resume_data: Resume data dictionary
            file_content: Optional PDF file content
            filename: Optional filename
            
        Returns:
            Created Resume object
        """
        logger.info(f"create_resume called: user_id={user.id}, filename={filename}, file_size={len(file_content) if file_content else 0}")
        
        # Handle file upload if provided
        file_path = None
        resume_file_url = None
        
        if file_content and filename:
            try:
                logger.info(f"Uploading file to storage: {filename}")
                storage_obj = storage_service.upload_resume(
                    user.id, file_content, filename
                )
                file_path = storage_obj.key
                resume_file_url = storage_obj.url
                logger.info(f"File uploaded successfully: key={file_path}")
            except Exception as e:
                logger.error(f"Storage upload failed: {e}")
                raise
        
        # Create main resume record
        db_resume = Resume(
            user_id=user.id,
            full_name=encrypt(resume_data.get("full_name", "")),
            email=encrypt(resume_data.get("email", "")),
            phone=encrypt(resume_data.get("phone", "")),
            linkedin_url=encrypt(resume_data.get("linkedin_url", "")),
            filename=filename,
            file_path=file_path,
            resume_file_url=resume_file_url,
            title=resume_data.get("title"),
            target_role=resume_data.get("target_role"),
            template_name=resume_data.get("template_name", "classic"),
            parsed_data=json.dumps({"summary": resume_data.get("summary", "")}) if resume_data.get("summary") else None,
            status="active"
        )
        
        self.db.add(db_resume)
        self.db.commit()
        self.db.refresh(db_resume)
        
        # Add nested data (education, experience, projects, skills)
        self._add_nested_data(db_resume, resume_data)
        
        # Create initial version
        self._create_version(db_resume)
        
        return db_resume
    
    def get_user_resumes(self, user_id: int) -> List[Resume]:
        """Get all resumes for a user with optimized loading."""
        resumes = self.db.query(Resume).options(
            selectinload(Resume.versions),
            selectinload(Resume.analyses)
        ).filter(
            Resume.user_id == user_id
        ).all()
        
        return resumes
    
    def get_resume(self, resume_id: int, user_id: int) -> Optional[Resume]:
        """Get a single resume by ID with eager loading for performance."""
        resume = self.db.query(Resume).options(
            selectinload(Resume.education),
            selectinload(Resume.experience),
            selectinload(Resume.projects),
            selectinload(Resume.skills),
            selectinload(Resume.versions),
            selectinload(Resume.analyses)
        ).filter(
            Resume.id == resume_id,
            Resume.user_id == user_id
        ).first()
        
        return resume
    
    def update_resume(
        self,
        resume_id: int,
        user_id: int,
        resume_data: Dict[str, Any]
    ) -> Optional[Resume]:
        """Update an existing resume."""
        resume = self.get_resume(resume_id, user_id)
        if not resume:
            return None
        
        # Update main fields
        if "full_name" in resume_data:
            resume.full_name = encrypt(resume_data.get("full_name", ""))
        if "email" in resume_data:
            resume.email = encrypt(resume_data.get("email", ""))
        if "phone" in resume_data:
            resume.phone = encrypt(resume_data.get("phone", ""))
        if "linkedin_url" in resume_data:
            resume.linkedin_url = encrypt(resume_data.get("linkedin_url", ""))
        
        resume.title = resume_data.get("title", resume.title)
        resume.target_role = resume_data.get("target_role", resume.target_role)
        resume.template_name = resume_data.get("template_name", resume.template_name)
        
        # Update scores if provided (important for optimization sync)
        if "ats_score" in resume_data:
            resume.ats_score = resume_data["ats_score"]
        if "analysis_score" in resume_data:
            resume.analysis_score = resume_data["analysis_score"]
            
        resume.updated_at = datetime.now()

        # Update parsed_data - merge existing, provided, and root fields
        pd = {}
        if resume.parsed_data:
            try:
                pd = json.loads(resume.parsed_data)
                if not isinstance(pd, dict):
                    pd = {}
            except:
                pd = {}

        # 1. Merge with provided parsed_data
        if "parsed_data" in resume_data and resume_data["parsed_data"]:
            new_pd = resume_data["parsed_data"]
            if isinstance(new_pd, str):
                try:
                    new_pd = json.loads(new_pd)
                except:
                    new_pd = {}
            if isinstance(new_pd, dict):
                pd.update(new_pd)

        # 2. Sync root-level fields into parsed_data
        if "full_name" in resume_data:
            pd["full_name"] = resume_data["full_name"]
        if "email" in resume_data:
            pd["email"] = resume_data["email"]
        if "phone" in resume_data:
            pd["phone"] = resume_data["phone"]
        if "linkedin_url" in resume_data:
            pd["linkedin_url"] = resume_data["linkedin_url"]
        if "summary" in resume_data:
            pd["summary"] = resume_data["summary"]
        if "title" in resume_data:
            pd["title"] = resume_data["title"]
        if "target_role" in resume_data:
            pd["target_role"] = resume_data["target_role"]
        
        # 3. Sync nested fields into parsed_data to keep everything in sync
        for field in ["education", "experience", "projects", "skills"]:
            if field in resume_data and resume_data[field] is not None:
                pd[field] = resume_data[field]

        resume.parsed_data = json.dumps(pd)
        
        # Update nested data in structured tables
        self._update_nested_data(resume, resume_data)
        
        # Recalculate ATS score if resume content was updated and score not explicitly provided
        if "ats_score" not in resume_data and any(k in resume_data for k in ["summary", "experience", "education", "projects", "skills"]):
            # Run this in the background or just call it here since it's an update
            # We can't easily await here as this is a sync method, but we can call the calculator
            # For now, we rely on the frontend calling ats-check or the explicit ats_score provided during optimization apply
            pass

        # Create new version
        self._create_version(resume)
        
        self.db.commit()
        self.db.refresh(resume)
        
        return resume
    
    def delete_resume(self, resume_id: int, user_id: int) -> bool:
        """Delete a resume and its associated data."""
        resume = self.db.query(Resume).filter(
            Resume.id == resume_id,
            Resume.user_id == user_id
        ).first()
        
        if not resume:
            return False
        
        # Delete associated file if exists
        if resume.file_path:
            storage_service.delete_file(resume.file_path)
        
        self.db.delete(resume)
        self.db.commit()
        
        return True

    def bulk_delete(self, resume_ids: List[int], user_id: int) -> Dict[str, int]:
        """
        Bulk delete multiple resumes for a user.
        Handles cascading deletes safely (files, versions, analyses, nested data).
        
        Returns:
            Dict with 'deleted' count and 'failed' count
        """
        deleted_count = 0
        failed_count = 0
        
        for resume_id in resume_ids:
            try:
                if self.delete_resume(resume_id, user_id):
                    deleted_count += 1
                else:
                    failed_count += 1
            except Exception:
                failed_count += 1
        
        return {"deleted": deleted_count, "failed": failed_count}
    
    # ==================== Resume Actions ====================
    
    async def update_resume_analysis(
        self,
        resume_id: int,
        ml_score: int,
        parsing_result: Dict[str, Any],
        skill_analysis: Dict[str, Any],
        recommendations: List[str],
        confidence: float,
    ) -> bool:
        """Update resume analysis in the database."""
        resume = self.db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume:
            return False
        
        # Update resume scores
        resume.ats_score = ml_score
        resume.analysis_score = ml_score
        
        # Save as ResumeAnalysis record
        analysis = ResumeAnalysis(
            resume_id=resume_id,
            analysis_type="enhanced_ats",
            score=ml_score,
            feedback=json.dumps({
                "parsing_result": parsing_result,
                "skill_analysis": skill_analysis,
                "confidence": confidence,
            }),
            missing_keywords=json.dumps(skill_analysis.get("missing_skills", [])),
            suggestions=json.dumps(recommendations),
            created_at=datetime.utcnow()
        )
        self.db.add(analysis)
        self.db.commit()
        return True

    async def parse_resume_file(self, resume_id: int, user_id: int) -> Optional[Dict]:
        """Parse a resume PDF file and extract data."""
        resume = self.get_resume(resume_id, user_id)
        if not resume or not resume.file_path:
            logger.warning(f"No file_path for resume {resume_id}")
            return None
        
        # Robust path resolution for local storage
        full_path = resume.file_path
        if settings.STORAGE_PROVIDER == "local" and not os.path.isabs(full_path):
            # Candidate 1: Standardized absolute path from config
            path1 = os.path.join(settings.upload_path, full_path)
            
            # Candidate 2: Direct join with settings.UPLOAD_DIR (relative to CWD)
            path2 = os.path.join(settings.UPLOAD_DIR, full_path)
            
            # Candidate 3: Project root uploads
            path3 = os.path.join(settings.BASE_DIR, "uploads", full_path)
            
            if os.path.exists(path1):
                full_path = path1
            elif os.path.exists(path2):
                full_path = os.path.abspath(path2)
            elif os.path.exists(path3):
                full_path = path3
        
        logger.info(f"Parsing resume {resume_id} from final resolved path: {full_path}")
        
        if not os.path.exists(full_path):
            logger.error(f"File not found: {full_path}")
            raise ValueError(f"Resume file not found at {full_path}. Upload failed.")
        
        try:
            parsed_data = await parse_resume_async(full_path)
            
            if not parsed_data:
                logger.error(f"Resume parsing returned empty data for {resume_id}")
                raise ValueError("Resume parsing failed to extract any data.")
            
            logger.info(f"Updating resume {resume_id} with parsed data")
            # Update resume with parsed data
            resume.parsed_data = json.dumps(parsed_data)
            resume.full_name = encrypt(parsed_data.get("full_name", ""))
            resume.email = encrypt(parsed_data.get("email", ""))
            resume.phone = encrypt(parsed_data.get("phone", ""))
            resume.linkedin_url = encrypt(parsed_data.get("linkedin_url", ""))
            resume.updated_at = datetime.now()
            
            # Populate nested tables (Education, Experience, etc.)
            self._update_nested_data(resume, parsed_data)
            
            self.db.commit()
            self.db.refresh(resume)
            
            logger.info(f"Successfully parsed resume {resume_id}")
            return parsed_data
        except Exception as e:
            logger.error(f"Error parsing resume {resume_id}: {e}")
            if isinstance(e, ValueError):
                raise e
            raise ValueError(f"Failed to parse resume: {str(e)}")
    
    async def get_ats_score(
        self,
        resume_id: int,
        user_id: int,
        job_description: str = ""
    ) -> Optional[Dict]:
        """Calculate enhanced ATS score for a resume."""
        resume = self.get_resume(resume_id, user_id)
        if not resume:
            return None
        
        # Use Enhanced ATS analyzer (ML + Semantic)
        ats_result = await calculate_ats_score(resume, job_description=job_description, db=self.db)
        
        return ats_result
    
    def get_resume_versions(self, resume_id: int, user_id: int) -> List[ResumeVersion]:
        """Get all versions of a resume."""
        resume = self.get_resume(resume_id, user_id)
        if not resume:
            return []
        
        return resume.versions
    
    # ==================== Helper Methods ====================
    
    def _add_nested_data(self, resume: Resume, data: Dict[str, Any], commit: bool = True):
        """Add education, experience, projects, and skills."""
        # Education
        for edu_data in data.get("education", []):
            edu = Education(
                resume_id=resume.id,
                school=edu_data.get("school", ""),
                degree=edu_data.get("degree", ""),
                major=edu_data.get("major"),
                gpa=edu_data.get("gpa"),
                start_date=edu_data.get("start_date") or edu_data.get("year", ""),
                end_date=edu_data.get("end_date") or edu_data.get("year", ""),
                description=edu_data.get("description")
            )
            self.db.add(edu)
        
        # Experience
        for exp_data in data.get("experience", []):
            exp = Experience(
                resume_id=resume.id,
                company=exp_data.get("company", ""),
                role=exp_data.get("role", ""),
                location=exp_data.get("location"),
                start_date=exp_data.get("start_date") or exp_data.get("duration", "").split(" - ")[0] if exp_data.get("duration") else "",
                end_date=exp_data.get("end_date") or exp_data.get("duration", "").split(" - ")[1] if (exp_data.get("duration") and " - " in exp_data.get("duration")) else None,
                current=exp_data.get("current", False),
                description=exp_data.get("description") or exp_data.get("desc")
            )
            self.db.add(exp)
        
        # Projects
        for proj_data in data.get("projects", []):
            proj = Project(
                resume_id=resume.id,
                project_name=proj_data.get("project_name", ""),
                description=proj_data.get("description") or proj_data.get("desc"),
                project_url=proj_data.get("project_url"),
                github_url=proj_data.get("github_url"),
                technologies=proj_data.get("technologies"),
                points=proj_data.get("points", [])
            )
            self.db.add(proj)
        
        # Skills
        for skill_data in data.get("skills", []):
            skill_name = ""
            skill_category = "Technical"
            
            if isinstance(skill_data, dict):
                skill_name = skill_data.get("name", "")
                skill_category = skill_data.get("category", "Technical")
            else:
                skill_name = str(skill_data)
                
            skill = Skill(
                resume_id=resume.id,
                name=skill_name,
                category=skill_category
            )
            self.db.add(skill)
        
        if commit:
            self.db.commit()
    
    def _update_nested_data(self, resume: Resume, data: Dict[str, Any]):
        """Update nested data by replacing all entries."""
        # Clear existing
        self.db.query(Education).filter(Education.resume_id == resume.id).delete()
        self.db.query(Experience).filter(Experience.resume_id == resume.id).delete()
        self.db.query(Project).filter(Project.resume_id == resume.id).delete()
        self.db.query(Skill).filter(Skill.resume_id == resume.id).delete()
        
        # Add new data without intermediate commit to ensure atomicity
        self._add_nested_data(resume, data, commit=False)
    
    def _create_version(self, resume: Resume):
        """Create a new version of the resume."""
        version_number = len(resume.versions) + 1
        
        version = ResumeVersion(
            resume_id=resume.id,
            version_number=version_number,
            parsed_data=resume.parsed_data,
            ats_score=resume.ats_score,
            created_at=datetime.now()
        )
        self.db.add(version)
        self.db.commit()

