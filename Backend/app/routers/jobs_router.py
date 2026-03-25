"""
Jobs router for job listings, search, and recommendations.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.database.session import get_db
from app.models import User, Job, SavedJob
from app.utils.dependencies import get_current_user
from app.services.job_service.ingestion import (
    search_jobs as search_jobs_db,
    get_all_jobs as get_all_jobs_db,
    ingest_all_jobs
)
from app.services.job_service.ranking import JobRecommender
from app.services.resume_service.resume_manager import ResumeManager

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])


# ==================== Schemas ====================

class JobResponse(BaseModel):
    id: int
    job_title: str
    company_name: str
    location: Optional[str] = None
    job_type: Optional[str] = None
    skills_required: Optional[str] = None
    experience_required: Optional[str] = None
    job_description: Optional[str] = None
    salary_range: Optional[str] = None
    job_link: Optional[str] = None
    posted_date: Optional[str] = None
    source: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class JobSearchResponse(BaseModel):
    jobs: List[JobResponse]
    total: int

    class Config:
        from_attributes = True


class JobMatchResponse(BaseModel):
    job: JobResponse
    match_score: int
    missing_keywords: List[str]

    class Config:
        from_attributes = True


class RecommendationResponse(BaseModel):
    resume_id: int
    recommendations: List[JobMatchResponse]

    class Config:
        from_attributes = True


class SavedJobResponse(BaseModel):
    id: int
    job_id: Optional[int]
    job_title: Optional[str]
    company: Optional[str]
    job_description: Optional[str] = None
    match_score: Optional[float] = None
    saved_date: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


# ==================== Endpoints ====================

@router.get("", response_model=JobSearchResponse)
async def get_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get all jobs with pagination."""
    jobs = get_all_jobs_db(db, skip, limit)
    total = db.query(Job).count()
    
    return {"jobs": jobs, "total": total}


@router.get("/search", response_model=JobSearchResponse)
async def search_jobs(
    q: str = Query(..., min_length=1),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Search jobs by title, company, or description."""
    jobs = search_jobs_db(db, q, limit)
    
    return {"jobs": jobs, "total": len(jobs)}


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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Ingest jobs from external sources (admin/users with subscription)."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    count = ingest_all_jobs(db)
    
    return {"message": f"Successfully ingested {count} jobs"}


@router.get("/recommendations/match", response_model=RecommendationResponse)
async def get_job_recommendations(
    resume_id: int = Query(...),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get job recommendations based on a resume."""
    recommender = JobRecommender(db)
    matches = recommender.match_resume_to_jobs(resume_id, current_user.id, limit)
    
    return jsonable_encoder({
        "resume_id": resume_id,
        "recommendations": matches
    })


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

