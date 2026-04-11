"""
Job Ingestion Worker - Ingests and processes jobs from external sources.

This worker fetches jobs from external APIs, normalizes data, and generates embeddings.
"""
import logging
import asyncio
from sqlalchemy.orm import Session
from datetime import datetime

from app.database.session import SessionLocal
from app.models import Job, JobSkill, JobEmbedding

logger = logging.getLogger(__name__)


def process_job_ingestion(job_id: int) -> dict:
    """
    Process a single job - normalize skills and generate embedding.
    
    Args:
        job_id: ID of the job to process
        
    Returns:
        Dictionary with ingestion result
    """
    db = SessionLocal()
    try:
        logger.info(f"[JobIngestionWorker] Processing job {job_id}")
        
        # Get job
        job = db.query(Job).filter(Job.id == job_id).first()
        
        if not job:
            logger.error(f"[JobIngestionWorker] Job {job_id} not found")
            return {"success": False, "error": "Job not found"}
        
        # Step 1: Extract and normalize skills
        skills_result = _extract_and_store_skills(job, db)
        
        # Step 2: Generate embedding
        embedding_result = asyncio.run(_generate_job_embedding(job, db))
        
        # Update job timestamp
        job.updated_at = datetime.now()
        db.commit()
        
        logger.info(f"[JobIngestionWorker] Successfully processed job {job_id}")
        
        return {
            "success": True,
            "job_id": job_id,
            "skills_extracted": skills_result.get("count", 0),
            "embedding_generated": embedding_result.get("success", False)
        }
        
    except Exception as e:
        logger.error(f"[JobIngestionWorker] Error processing job {job_id}: {str(e)}")
        db.rollback()
        return {"success": False, "error": str(e)}
    finally:
        db.close()


def process_batch_job_ingestion(job_ids: list) -> dict:
    """
    Process a batch of jobs.
    
    Args:
        job_ids: List of job IDs to process
        
    Returns:
        Summary of processing results
    """
    results = {
        "total": len(job_ids),
        "successful": 0,
        "failed": 0,
        "errors": []
    }
    
    for job_id in job_ids:
        result = process_job_ingestion(job_id)
        if result.get("success"):
            results["successful"] += 1
        else:
            results["failed"] += 1
            results["errors"].append({"job_id": job_id, "error": result.get("error")})
    
    return results


def _extract_and_store_skills(job: Job, db: Session) -> dict:
    """Extract skills from job description and store in normalized table."""
    import re
    import json
    
    skills = set()
    
    # Common tech skills to look for
    skill_keywords = [
        "Python", "Java", "JavaScript", "TypeScript", "Go", "Rust", "C++", "C#",
        "React", "Vue", "Angular", "Svelte", "Node.js", "Django", "FastAPI", "Flask",
        "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch",
        "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform",
        "Git", "Jira", "CI/CD", "DevOps", "Machine Learning", "Data Science",
        "REST", "GraphQL", "gRPC", "Microservices", "Agile", "Scrum"
    ]
    
    # Search in job description and skills
    search_text = (job.job_description or "").lower()
    
    # Also check legacy skills_required field
    if job.skills_required:
        try:
            if isinstance(job.skills_required, str):
                legacy_skills = json.loads(job.skills_required)
            else:
                legacy_skills = job.skills_required
            
            if legacy_skills:
                search_text += " " + " ".join(legacy_skills).lower()
        except:
            pass
    
    # Extract skills
    for skill in skill_keywords:
        if skill.lower() in search_text:
            skills.add(skill)
    
    # Categorize and store
    skill_category_map = {
        "Python": "language", "Java": "language", "JavaScript": "language",
        "TypeScript": "language", "Go": "language", "Rust": "language",
        "React": "framework", "Vue": "framework", "Angular": "framework",
        "Node.js": "framework", "Django": "framework", "FastAPI": "framework",
        "PostgreSQL": "database", "MySQL": "database", "MongoDB": "database",
        "AWS": "cloud", "Azure": "cloud", "GCP": "cloud",
        "Docker": "tool", "Kubernetes": "tool", "Git": "tool"
    }
    
    # Delete existing skills for this job
    db.query(JobSkill).filter(JobSkill.job_id == job.id).delete()
    
    # Add new skills
    for skill_name in skills:
        skill = JobSkill(
            job_id=job.id,
            skill_name=skill_name,
            skill_category=skill_category_map.get(skill_name, "technical"),
            importance=2  # Default to preferred
        )
        db.add(skill)
    
    db.commit()
    
    return {"count": len(skills)}


async def _generate_job_embedding(job: Job, db: Session) -> dict:
    """Generate vector embedding for a job."""
    try:
        from app.services.llm_service import llm_service
        
        # Build job text
        job_text = _build_job_text(job)
        
        # Generate embedding asynchronously
        embeddings = await llm_service.generate_embeddings_async(job_text)
        
        if not embeddings:
            return {"success": False, "error": "No embedding returned"}
        
        embedding = embeddings[0]
        
        # Store or update embedding
        existing = db.query(JobEmbedding).filter(
            JobEmbedding.job_id == job.id
        ).first()
        
        if not existing:
            existing = JobEmbedding(job_id=job.id)
            db.add(existing)
        
        existing.embedding_vector = embedding.embedding
        existing.model_name = embedding.model
        existing.updated_at = datetime.now().isoformat()
        
        db.commit()
        
        return {"success": True, "model": embedding.model}
        
    except Exception as e:
        logger.error(f"[JobIngestionWorker] Error generating embedding: {e}")
        return {"success": False, "error": str(e)}


def _build_job_text(job: Job) -> str:
    """Build text representation of job for embedding."""
    parts = [
        f"Job Title: {job.job_title}",
        f"Company: {job.company_name}",
        f"Location: {job.location or 'Not specified'}",
        f"Job Type: {job.job_type or 'Not specified'}",
        f"Experience Required: {job.experience_required or 'Not specified'}",
    ]
    
    if job.job_description:
        parts.append(f"Description: {job.job_description}")
    
    return "\n".join(parts)


from app.workers.celery_app import celery

# Celery task wrapper
if celery:
    @celery.task(name='job_ingestion_worker.process')
    def celery_process_job_ingestion(job_id: int):
        return process_job_ingestion(job_id)
    
    @celery.task(name='job_ingestion_worker.process_batch')
    def celery_process_batch_job_ingestion(job_ids: list):
        return process_batch_job_ingestion(job_ids)

