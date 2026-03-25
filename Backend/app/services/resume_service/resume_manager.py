"""
Resume manager service for CRUD operations on resumes.
Supports multi-resume management per user.
"""
import json
import logging
import os   
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.config import settings
from app.models import Resume, ResumeVersion, Education, Experience, Project, Skill, ResumeAnalysis
from app.models.user import User
from app.utils.encryption import encrypt, decrypt
from app.services.resume_service.parser import parse_resume
from app.services.resume_service.ats_analyzer import calculate_ats_score
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
        # Handle file upload if provided
        file_path = None
        resume_file_url = None
        
        if file_content and filename:
            storage_obj = storage_service.upload_resume(
                user.id, file_content, filename
            )
            file_path = storage_obj.key
            resume_file_url = storage_obj.url
        
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
        """Get all resumes for a user."""
        resumes = self.db.query(Resume).filter(
            Resume.user_id == user_id
        ).all()
        
        return resumes
    
    def get_resume(self, resume_id: int, user_id: int) -> Optional[Resume]:
        """Get a single resume by ID, ensuring ownership."""
        resume = self.db.query(Resume).filter(
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
        resume.updated_at = datetime.now().isoformat()

        # Update summary in parsed_data if provided
        if "summary" in resume_data:
            try:
                pd = json.loads(resume.parsed_data) if resume.parsed_data else {}
                pd["summary"] = resume_data["summary"]
                resume.parsed_data = json.dumps(pd)
            except:
                pass
        
        # Update nested data
        self._update_nested_data(resume, resume_data)
        
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
    
    # ==================== Resume Actions ====================
    
    def parse_resume_file(self, resume_id: int, user_id: int) -> Optional[Dict]:
        """Parse a resume PDF file and extract data."""
        resume = self.get_resume(resume_id, user_id)
        if not resume or not resume.file_path:
            return None
        
        try:
            # Get full path for local storage
            full_path = resume.file_path
            if settings.STORAGE_PROVIDER == "local" and full_path:
                # Use absolute path from project root
                base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
                full_path = os.path.join(base_dir, "uploads", full_path)
            
            parsed_data = parse_resume(full_path)
            
            # Update resume with parsed data
            resume.parsed_data = json.dumps(parsed_data)
            resume.full_name = encrypt(parsed_data.get("full_name", ""))
            resume.email = encrypt(parsed_data.get("email", ""))
            resume.phone = encrypt(parsed_data.get("phone", ""))
            resume.linkedin_url = encrypt(parsed_data.get("linkedin_url", ""))
            resume.updated_at = datetime.now().isoformat()
            
            # Populate nested tables (Education, Experience, etc.)
            self._update_nested_data(resume, parsed_data)
            
            self.db.commit()
            
            return parsed_data
        except Exception as e:
            logger.error(f"Error parsing resume: {e}")
            return None
    
    def get_ats_score(
        self,
        resume_id: int,
        user_id: int,
        job_description: str = ""
    ) -> Optional[Dict]:
        """Calculate ATS score for a resume."""
        resume = self.get_resume(resume_id, user_id)
        if not resume:
            return None
        
        ats_result = calculate_ats_score(resume, job_description)
        
        # Save analysis
        analysis = ResumeAnalysis(
            resume_id=resume.id,
            analysis_type="ats",
            score=ats_result["overall_score"],
            feedback=json.dumps(ats_result),
            created_at=datetime.now().isoformat()
        )
        self.db.add(analysis)
        
        # Update resume with score
        resume.ats_score = ats_result["overall_score"]
        self.db.commit()
        
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
                technologies=proj_data.get("technologies")
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
            created_at=datetime.now().isoformat()
        )
        self.db.add(version)
        self.db.commit()

