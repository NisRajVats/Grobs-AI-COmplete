"""
Users router for user profile and dashboard management.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.database.session import get_db
from app.models import User, Resume, JobApplication, SavedJob, UserSettings
from app.schemas.user import (
    UserProfileResponse,
    UserUpdate as UserProfileUpdate,
    DashboardStats,
    UserSettingsResponse,
    UserSettingsUpdate
)
from app.utils.dependencies import get_current_user
from app.utils.cache import cache_response

from datetime import datetime


router = APIRouter(prefix="/api/users", tags=["Users"])


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
@cache_response(ttl=300)
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


@router.get("/me/settings", response_model=UserSettingsResponse)
async def get_user_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's settings.
    """
    # Get or create settings for user
    settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    
    if not settings:
        # Create default settings
        settings = UserSettings(user_id=current_user.id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    
    return settings


@router.put("/me/settings", response_model=UserSettingsResponse)
async def update_user_settings(
    settings_data: UserSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's settings.
    """
    # Get or create settings for user
    settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    
    if not settings:
        settings = UserSettings(user_id=current_user.id)
        db.add(settings)
    
    # Update only provided fields
    update_data = settings_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(settings, field, value)
    
    db.commit()
    db.refresh(settings)
    
    return settings

