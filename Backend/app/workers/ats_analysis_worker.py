"""
ATS Analysis Worker - Analyzes resumes for ATS compatibility.

This worker calculates ATS scores and provides optimization suggestions.
"""
import logging
from sqlalchemy.orm import Session
from datetime import datetime

import json
from app.database.session import SessionLocal
from app.models import Resume, ResumeContent, ResumeAnalysis, User
from app.utils.encryption import decrypt
from app.services.resume_service.ats_analyzer import calculate_ats_score as calculate_ats
from app.workers.base_worker import enqueue_task

logger = logging.getLogger(__name__)


def process_ats_analysis(resume_id: int, user_id: int, job_description: str = "") -> dict:
    """
    Run ATS analysis on a parsed resume.
    
    Args:
        resume_id: ID of the resume
        user_id: ID of the user who owns the resume
        job_description: Optional job description for matching
        
    Returns:
        Dictionary with ATS analysis result
    """
    db = SessionLocal()
    try:
        logger.info(f"[ATSAnalysisWorker] Starting ATS analysis for resume {resume_id}")
        
        # Get resume with relationships
        resume = db.query(Resume).filter(
            Resume.id == resume_id,
            Resume.user_id == user_id
        ).first()
        
        if not resume:
            logger.error(f"[ATSAnalysisWorker] Resume {resume_id} not found")
            return {"success": False, "error": "Resume not found"}
        
        # Get parsed content
        content = db.query(ResumeContent).filter(
            ResumeContent.resume_id == resume_id
        ).first()
        
        if not content:
            logger.error(f"[ATSAnalysisWorker] Resume {resume_id} not parsed yet")
            return {"success": False, "error": "Resume not parsed yet"}
        
        # Build resume object for ATS analyzer
        resume_for_ats = _build_resume_for_ats(resume, content)
        
        # Calculate ATS score
        try:
            import asyncio
            ats_result = asyncio.run(calculate_ats(resume_for_ats, job_description))
        except Exception as e:
            logger.error(f"[ATSAnalysisWorker] Failed to calculate ATS score: {e}")
            return {"success": False, "error": f"ATS calculation error: {str(e)}"}
        
        # Store analysis result
        analysis = ResumeAnalysis(
            resume_id=resume_id,
            analysis_type="ats",
            score=ats_result.get("overall_score"),
            feedback=json.dumps(ats_result.get("category_scores")),
            missing_keywords=json.dumps(ats_result.get("issues", [])),
            suggestions=json.dumps(ats_result.get("recommendations", [])),
            job_description=job_description if job_description else None
        )
        
        db.add(analysis)
        
        # Update resume status
        resume.status = "analyzed"
        resume.ats_score = ats_result.get("overall_score")
        resume.updated_at = datetime.utcnow()
        
        db.commit()
        
        logger.info(f"[ATSAnalysisWorker] Successfully analyzed resume {resume_id}, score: {ats_result.get('overall_score')}")
        
        # Trigger email notification
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            enqueue_task(
                "email_worker.resume_analysis",
                recipient_email=user.email,
                user_name=user.full_name or user.email.split('@')[0],
                resume_title=resume.title or resume.filename or "My Resume",
                ats_score=ats_result.get("overall_score")
            )
        
        return {
            "success": True,
            "resume_id": resume_id,
            "ats_score": ats_result.get("overall_score"),
            "category_scores": ats_result.get("category_scores"),
            "issues": ats_result.get("issues", [])[:5],
            "recommendations": ats_result.get("recommendations", [])[:5]
        }
        
    except Exception as e:
        logger.error(f"[ATSAnalysisWorker] Error analyzing resume {resume_id}: {str(e)}")
        db.rollback()
        return {"success": False, "error": str(e)}
    finally:
        db.close()


def _build_resume_for_ats(resume: Resume, content: ResumeContent):
    """Build resume object compatible with ATS analyzer."""
    class ResumeForATS:
        def __init__(self, resume, content):
            self.full_name = decrypt(content.full_name_encrypted) if content.full_name_encrypted else ""
            self.email = decrypt(content.email_encrypted) if content.email_encrypted else ""
            self.phone = decrypt(content.phone_encrypted) if content.phone_encrypted else ""
            self.linkedin_url = decrypt(content.linkedin_url_encrypted) if content.linkedin_url_encrypted else ""
            self.education = resume.education
            self.experience = resume.experience
            self.projects = resume.projects
            self.skills = resume.skills
    
    return ResumeForATS(resume, content)


# Celery task wrapper (if Celery is available)
try:
    from celery import Celery
    celery_app = Celery('ats_analysis_worker')
    
    @celery_app.task(name='ats_analysis_worker.process')
    def celery_process_ats_analysis(resume_id: int, user_id: int, job_description: str = ""):
        return process_ats_analysis(resume_id, user_id, job_description)
except ImportError:
    pass

