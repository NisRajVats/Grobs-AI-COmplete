"""
Jobs router for job listings, search, and recommendations.
"""
import logging
import json
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database.session import get_db
from app.models import User, Job, SavedJob, Resume
from app.schemas.job import (
    JobResponse, 
    JobSearchResponse, 
    JobMatchResponse, 
    JobRecommendationResponse, 
    SavedJobResponse,
    LiveJobSearchResponse
)
from app.utils.dependencies import get_current_user
from app.services.job_service.ingestion import (
    search_jobs as search_jobs_db,
    get_all_jobs as get_all_jobs_db,
    ingest_all_jobs,
    JobIngestor
)
from app.services.job_service.live_job_service import live_job_service
from app.services.job_service.job_matcher import JobMatcher as JobRecommender
from app.services.resume_service.resume_manager import ResumeManager

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])


# ==================== Schemas ====================

# ==================== Endpoints ====================

@router.get("", response_model=JobSearchResponse)
async def get_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all jobs with pagination."""
    try:
        jobs = get_all_jobs_db(db, skip, limit)
        total = db.query(Job).count()
        
        return {"jobs": jobs, "total": total}
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error in get_jobs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/search", response_model=JobSearchResponse)
async def search_jobs(
    q: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    job_type: Optional[str] = Query(None),
    skills: Optional[List[str]] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Search jobs by title, company, description, and filters."""
    jobs = search_jobs_db(db, q, location, job_type, skills, limit)
    
    return {"jobs": jobs, "total": len(jobs)}


# ==================== Saved Jobs Endpoints ====================

@router.get("/saved", response_model=List[SavedJobResponse])
async def get_saved_jobs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all saved jobs for current user."""
    saved = db.query(SavedJob).filter(SavedJob.user_id == current_user.id).all()
    return jsonable_encoder(saved)


@router.post("/saved/{job_id}")
async def save_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Save a job for later."""
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check if already saved
    existing = db.query(SavedJob).filter(
        SavedJob.user_id == current_user.id,
        SavedJob.job_id == job_id
    ).first()
    
    if existing:
        return {"message": "Job already saved"}
    
    saved_job = SavedJob(
        user_id=current_user.id,
        job_id=job_id,
        job_title=job.job_title,
        company=job.company_name,
        job_description=job.job_description
    )
    
    db.add(saved_job)
    db.commit()
    
    return {"message": "Job saved successfully"}


@router.delete("/saved/{job_id}")
async def unsave_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a saved job."""
    saved = db.query(SavedJob).filter(
        SavedJob.user_id == current_user.id,
        SavedJob.job_id == job_id
    ).first()
    
    if not saved:
        raise HTTPException(status_code=404, detail="Saved job not found")
    
    db.delete(saved)
    db.commit()
    
    return {"message": "Job removed from saved"}


@router.get("/live/search", response_model=LiveJobSearchResponse)
async def get_live_jobs(
    resume_id: int = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Fetch live jobs from external APIs and calculate match scores against a resume.
    """
    try:
        # 1. Get resume details
        resume = db.query(Resume).filter(Resume.id == resume_id, Resume.user_id == current_user.id).first()
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        # 2. Extract keywords and text
        skills = [s.name for s in resume.skills[:5]]
        
        # Extract location from parsed data if possible
        location = None
        resume_text = ""
        if resume.parsed_data:
            try:
                parsed = json.loads(resume.parsed_data)
                location = parsed.get("location") or parsed.get("address")
                
                # Build text for cosine similarity
                parts = [resume.full_name or ""]
                parts.append(parsed.get("summary", ""))
                parts.append(", ".join(skills))
                resume_text = " ".join(filter(None, parts))
            except:
                pass
        
        if not resume_text:
            resume_text = f"{resume.full_name} {' '.join(skills)}"

        # 3. Fetch from live APIs via service
        jobs = await live_job_service.fetch_live_jobs(
            keywords=skills,
            location=location,
            resume_text=resume_text
        )
        
        return {
            "jobs": jobs,
            "total": len(jobs),
            "resume_id": resume_id
        }
        
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching live jobs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific job by ID."""
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job


@router.post("/ingest")
async def ingest_jobs(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Ingest jobs from external sources in the background."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    background_tasks.add_task(ingest_all_jobs, db)
    
    return {"message": "Job ingestion started in the background"}


@router.get("/recommendations/match", response_model=JobRecommendationResponse)
async def get_job_recommendations(
    resume_id: int = Query(...),
    limit: int = Query(10, ge=1, le=50),
    refresh: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get job recommendations based on a resume."""
    try:
        recommender = JobRecommender(db)
        matches = await recommender.match_resume_to_jobs(resume_id, current_user.id, limit)
        
        # If no matches or refresh requested, fetch original jobs from multiple platforms
        if not matches or refresh or len(matches) < 3:
            # 1. Get resume keywords/skills
            resume = db.query(Resume).filter(Resume.id == resume_id).first()
            if resume:
                skills = [s.name for s in resume.skills[:5]]
                
                # Extract location from parsed data if possible
                location = None
                if resume.parsed_data:
                    try:
                        parsed = json.loads(resume.parsed_data)
                        location = parsed.get("location") or parsed.get("address")
                    except:
                        pass
                
                # 2. Fetch from external sources
                ingestor = JobIngestor(db)
                raw_jobs = await ingestor.fetch_by_keywords(skills, location=location)
                
                # 3. Ingest them
                if raw_jobs:
                    await ingestor.process_and_ingest(raw_jobs)
                    # Re-match after ingestion
                    matches = await recommender.match_resume_to_jobs(resume_id, current_user.id, limit)
        
        return jsonable_encoder({
            "resume_id": resume_id,
            "recommendations": matches,
            "total": len(matches)
        })
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error in get_job_recommendations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

