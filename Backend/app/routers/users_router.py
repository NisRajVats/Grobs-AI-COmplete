"""
Users router for user profile and dashboard management.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database.session import get_db
from app.models import User, Resume, JobApplication, SavedJob
from app.utils.dependencies import get_current_user

from datetime import datetime


router = APIRouter(prefix="/api/users", tags=["Users"])


# ==================== Schemas ====================

class UserProfileResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    title: Optional[str] = None
    linkedin_url: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    title: Optional[str] = None
    linkedin_url: Optional[str] = None
    avatar_url: Optional[str] = None


class DashboardStats(BaseModel):
    total_resumes: int
    avg_ats_score: float
    total_applications: int
    total_saved_jobs: int
    applications_by_status: dict


# ==================== Endpoints ====================

@router.get("/me", response_model=UserProfileResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's full profile.
    """
    return current_user


@router.put("/me", response_model=UserProfileResponse)
async def update_current_user_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's profile.
    """
    # Update only provided fields
    update_data = profile_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    
    return current_user


@router.get("/me/dashboard-stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get dashboard statistics for current user.
    """
    # Count resumes
    total_resumes = db.query(Resume).filter(
        Resume.user_id == current_user.id
    ).count()
    
    # Calculate average ATS score from resumes
    resumes = db.query(Resume).filter(
        Resume.user_id == current_user.id,
        Resume.ats_score.isnot(None)
    ).all()
    
    if resumes:
        avg_ats_score = sum(r.ats_score for r in resumes) / len(resumes)
    else:
        avg_ats_score = 0.0
    
    # Count applications
    total_applications = db.query(JobApplication).filter(
        JobApplication.user_id == current_user.id
    ).count()
    
    # Count saved jobs
    total_saved_jobs = db.query(SavedJob).filter(
        SavedJob.user_id == current_user.id
    ).count()
    
    # Get applications by status
    applications = db.query(JobApplication).filter(
        JobApplication.user_id == current_user.id
    ).all()
    
    applications_by_status = {}
    for app in applications:
        status = app.status or "unknown"
        applications_by_status[status] = applications_by_status.get(status, 0) + 1
    
    return DashboardStats(
        total_resumes=total_resumes,
        avg_ats_score=round(avg_ats_score, 1),
        total_applications=total_applications,
        total_saved_jobs=total_saved_jobs,
        applications_by_status=applications_by_status
    )

