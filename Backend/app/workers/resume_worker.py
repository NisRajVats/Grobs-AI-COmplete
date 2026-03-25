"""
Background worker for resume processing tasks.
Uses FastAPI's BackgroundTasks for async processing.
"""
import logging
from typing import Optional
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.services.resume_service.resume_manager import ResumeManager
from app.services.resume_service.parser import parse_resume
from app.services.resume_service.ats_analyzer import calculate_ats_score

logger = logging.getLogger(__name__)


def process_resume_parsing(resume_id: int, user_id: int):
    """
    Background task to parse a resume PDF.
    
    Args:
        resume_id: ID of the resume to parse
        user_id: ID of the user who owns the resume
    """
    db = SessionLocal()
    try:
        logger.info(f"Starting resume parsing for resume {resume_id}")
        
        manager = ResumeManager(db)
        result = manager.parse_resume_file(resume_id, user_id)
        
        if result:
            logger.info(f"Successfully parsed resume {resume_id}")
        else:
            logger.warning(f"Failed to parse resume {resume_id}")
            
    except Exception as e:
        logger.error(f"Error parsing resume {resume_id}: {str(e)}")
    finally:
        db.close()


def process_ats_analysis(resume_id: int, user_id: int, job_description: str = ""):
    """
    Background task to calculate ATS score.
    
    Args:
        resume_id: ID of the resume
        user_id: ID of the user
        job_description: Optional job description for matching
    """
    db = SessionLocal()
    try:
        logger.info(f"Starting ATS analysis for resume {resume_id}")
        
        manager = ResumeManager(db)
        result = manager.get_ats_score(resume_id, user_id, job_description)
        
        if result:
            logger.info(f"ATS score calculated for resume {resume_id}: {result.get('overall_score')}")
        else:
            logger.warning(f"Failed to calculate ATS score for resume {resume_id}")
            
    except Exception as e:
        logger.error(f"Error in ATS analysis for resume {resume_id}: {str(e)}")
    finally:
        db.close()


def process_resume_optimization(resume_id: int, user_id: int):
    """
    Background task to optimize a resume.
    
    Args:
        resume_id: ID of the resume to optimize
        user_id: ID of the user
    """
    db = SessionLocal()
    try:
        logger.info(f"Starting resume optimization for resume {resume_id}")
        
        # Get resume
        from app.models import Resume
        resume = db.query(Resume).filter(
            Resume.id == resume_id,
            Resume.user_id == user_id
        ).first()
        
        if not resume:
            logger.warning(f"Resume {resume_id} not found")
            return
        
        # TODO: Implement AI-based optimization
        # For now, just update status
        resume.status = "optimized"
        db.commit()
        
        logger.info(f"Resume {resume_id} marked as optimized")
        
    except Exception as e:
        logger.error(f"Error optimizing resume {resume_id}: {str(e)}")
    finally:
        db.close()

