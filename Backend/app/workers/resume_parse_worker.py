"""
Resume Parse Worker - Handles resume PDF parsing.

This worker extracts text and structured data from uploaded resumes.
"""
import logging
import os
import json
from sqlalchemy.orm import Session
from datetime import datetime

from app.database.session import SessionLocal

logger = logging.getLogger(__name__)
from app.models import Resume, ResumeContent, Education, Experience, Project, Skill
from app.utils.encryption import encrypt
from app.services.resume_service.parser import parse_resume as parse_resume_file


def _update_nested_data(db: Session, resume: Resume, data: dict):
    """Update nested data (education, experience, etc.) for a resume."""
    # Clear existing
    db.query(Education).filter(Education.resume_id == resume.id).delete()
    db.query(Experience).filter(Experience.resume_id == resume.id).delete()
    db.query(Project).filter(Project.resume_id == resume.id).delete()
    db.query(Skill).filter(Skill.resume_id == resume.id).delete()
    
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
        db.add(edu)
    
    # Experience
    for exp_data in data.get("experience", []):
        exp = Experience(
            resume_id=resume.id,
            company=exp_data.get("company", ""),
            role=exp_data.get("role", ""),
            location=exp_data.get("location"),
            start_date=exp_data.get("start_date", ""),
            end_date=exp_data.get("end_date"),
            current=exp_data.get("current", False),
            description=exp_data.get("description")
        )
        db.add(exp)
    
    # Projects
    for proj_data in data.get("projects", []):
        proj = Project(
            resume_id=resume.id,
            project_name=proj_data.get("project_name", ""),
            description=proj_data.get("description"),
            project_url=proj_data.get("project_url"),
            github_url=proj_data.get("github_url"),
            technologies=proj_data.get("technologies")
        )
        db.add(proj)
    
    # Skills
    for skill_data in data.get("skills", []):
        skill = Skill(
            resume_id=resume.id,
            name=skill_data.get("name", ""),
            category=skill_data.get("category", "Technical")
        )
        db.add(skill)
    
    db.commit()


def process_resume_parsing(resume_id: int, user_id: int) -> dict:
    """
    Parse a resume PDF file and extract structured data.
    """
    db = SessionLocal()
    try:
        logger.info(f"[ResumeParseWorker] Starting parsing for resume {resume_id}")
        
        # Get resume
        resume = db.query(Resume).filter(
            Resume.id == resume_id,
            Resume.user_id == user_id
        ).first()
        
        if not resume:
            logger.error(f"[ResumeParseWorker] Resume {resume_id} not found")
            return {"success": False, "error": "Resume not found"}
        
        # Use resume_file_url if file_path is not available
        file_path = resume.file_path or resume.resume_file_url
        if not file_path:
            logger.error(f"[ResumeParseWorker] No file path for resume {resume_id}")
            return {"success": False, "error": "No file to parse"}
        
        # Resolve absolute path for local storage
        if not file_path.startswith("http"):
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            file_path = os.path.join(base_dir, "uploads", file_path)
        
        # Parse the resume file
        try:
            parsed_data = parse_resume_file(file_path)
        except Exception as e:
            logger.error(f"[ResumeParseWorker] Failed to parse file: {e}")
            return {"success": False, "error": f"Parse error: {str(e)}"}
        
        # Update main resume fields
        resume.full_name = encrypt(parsed_data.get("full_name", ""))
        resume.email = encrypt(parsed_data.get("email", ""))
        resume.phone = encrypt(parsed_data.get("phone", ""))
        resume.linkedin_url = encrypt(parsed_data.get("linkedin_url", ""))
        resume.parsed_data = json.dumps(parsed_data)
        
        # Get or create content
        content = db.query(ResumeContent).filter(
            ResumeContent.resume_id == resume_id
        ).first()
        
        if not content:
            content = ResumeContent(resume_id=resume_id)
            db.add(content)
        
        # Update content with parsed data
        content.full_name_encrypted = encrypt(parsed_data.get("full_name", ""))
        content.email_encrypted = encrypt(parsed_data.get("email", ""))
        content.phone_encrypted = encrypt(parsed_data.get("phone", ""))
        content.linkedin_url_encrypted = encrypt(parsed_data.get("linkedin_url", ""))
        content.raw_text = parsed_data.get("raw_text", "")
        content.parsed_json = parsed_data
        content.parsed_at = datetime.now().isoformat()
        content.updated_at = datetime.now().isoformat()
        
        # Populate nested tables
        _update_nested_data(db, resume, parsed_data)
        
        # Update resume status
        resume.status = "parsed"
        resume.updated_at = datetime.now()
        
        db.commit()
        
        logger.info(f"[ResumeParseWorker] Successfully parsed resume {resume_id}")
        
        return {
            "success": True,
            "resume_id": resume_id,
            "parsed": {
                "full_name": parsed_data.get("full_name"),
                "email": parsed_data.get("email")
            }
        }
        
    except Exception as e:
        logger.error(f"[ResumeParseWorker] Error parsing resume {resume_id}: {str(e)}")
        db.rollback()
        return {"success": False, "error": str(e)}
    finally:
        db.close()


# Celery task (if Celery is available)
try:
    from celery import Celery
    celery_app = Celery('resume_parse_worker')
    
    @celery_app.task(name='resume_parse_worker.process')
    def celery_process_resume_parsing(resume_id: int, user_id: int):
        return process_resume_parsing(resume_id, user_id)
except ImportError:
    # Celery not available, use as regular function
    pass

