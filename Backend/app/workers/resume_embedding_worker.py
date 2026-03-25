"""
Resume Embedding Worker - Generates vector embeddings for resumes.

This worker creates vector embeddings from parsed resume data for semantic search.
"""
import logging
from sqlalchemy.orm import Session
from datetime import datetime

from app.database.session import SessionLocal
from app.models import Resume, ResumeContent, ResumeEmbedding
from app.utils.encryption import decrypt
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


def process_resume_embedding(resume_id: int, user_id: int) -> dict:
    """
    Generate vector embedding for a parsed resume.
    
    Args:
        resume_id: ID of the resume
        user_id: ID of the user who owns the resume
        
    Returns:
        Dictionary with embedding result
    """
    db = SessionLocal()
    try:
        logger.info(f"[ResumeEmbeddingWorker] Starting embedding for resume {resume_id}")
        
        # Get resume
        resume = db.query(Resume).filter(
            Resume.id == resume_id,
            Resume.user_id == user_id
        ).first()
        
        if not resume:
            logger.error(f"[ResumeEmbeddingWorker] Resume {resume_id} not found")
            return {"success": False, "error": "Resume not found"}
        
        # Get parsed content
        content = db.query(ResumeContent).filter(
            ResumeContent.resume_id == resume_id
        ).first()
        
        if not content:
            logger.error(f"[ResumeEmbeddingWorker] Resume {resume_id} not parsed yet")
            return {"success": False, "error": "Resume not parsed yet"}
        
        # Build resume text for embedding
        resume_text = _build_resume_text(resume, content)
        
        if not resume_text.strip():
            logger.error(f"[ResumeEmbeddingWorker] No text content for resume {resume_id}")
            return {"success": False, "error": "No content to embed"}
        
        # Generate embedding
        try:
            embeddings = llm_service.generate_embeddings(resume_text)
        except Exception as e:
            logger.error(f"[ResumeEmbeddingWorker] Failed to generate embedding: {e}")
            return {"success": False, "error": f"Embedding error: {str(e)}"}
        
        if not embeddings:
            logger.error(f"[ResumeEmbeddingWorker] No embedding returned")
            return {"success": False, "error": "Failed to generate embedding"}
        
        embedding = embeddings[0]
        
        # Store or update embedding
        existing = db.query(ResumeEmbedding).filter(
            ResumeEmbedding.resume_id == resume_id
        ).first()
        
        if not existing:
            existing = ResumeEmbedding(resume_id=resume_id)
            db.add(existing)
        
        existing.embedding_vector = embedding.embedding
        existing.model_name = embedding.model
        existing.updated_at = datetime.now().isoformat()
        
        db.commit()
        
        logger.info(f"[ResumeEmbeddingWorker] Successfully embedded resume {resume_id}")
        
        return {
            "success": True,
            "resume_id": resume_id,
            "model": embedding.model,
            "embedding_dim": len(embedding.embedding)
        }
        
    except Exception as e:
        logger.error(f"[ResumeEmbeddingWorker] Error embedding resume {resume_id}: {str(e)}")
        db.rollback()
        return {"success": False, "error": str(e)}
    finally:
        db.close()


def _build_resume_text(resume: Resume, content: ResumeContent) -> str:
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
    skills = [s.name for s in resume.skills] if resume.skills else []
    if skills:
        parts.append(f"Skills: {', '.join(skills)}")
    
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


# Celery task wrapper (if Celery is available)
try:
    from celery import Celery
    celery_app = Celery('resume_embedding_worker')
    
    @celery_app.task(name='resume_embedding_worker.process')
    def celery_process_resume_embedding(resume_id: int, user_id: int):
        return process_resume_embedding(resume_id, user_id)
except ImportError:
    pass

