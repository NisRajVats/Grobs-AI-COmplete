"""
Applications router for job application tracking.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.database.session import get_db
from app.models import User, JobApplication, Notification
from app.utils.dependencies import get_current_user
from datetime import datetime

router = APIRouter(prefix="/api/applications", tags=["Applications"])


# ==================== Schemas ====================

class ApplicationCreate(BaseModel):
    job_id: Optional[int] = None
    resume_id: Optional[int] = None
    job_title: str
    company: str
    status: str = "applied"
    notes: Optional[str] = None


class ApplicationUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    next_step: Optional[str] = None
    follow_up_date: Optional[str] = None


class ApplicationResponse(BaseModel):
    id: int
    user_id: int
    job_id: int
    resume_id: Optional[int]
    job_title: str
    company: str
    status: str
    applied_date: Optional[str]
    follow_up_date: Optional[str]
    notes: Optional[str]
    next_step: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


# ==================== Endpoints ====================

@router.get("", response_model=List[ApplicationResponse])
async def get_applications(
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all applications for current user."""
    query = db.query(JobApplication).filter(JobApplication.user_id == current_user.id)
    
    if status_filter:
        query = query.filter(JobApplication.status == status_filter)
    
    applications = query.order_by(JobApplication.created_at.desc()).all()
    return applications


@router.post("", response_model=ApplicationResponse)
async def create_application(
    application: ApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new job application."""
    new_application = JobApplication(
        user_id=current_user.id,
        job_id=application.job_id,
        resume_id=application.resume_id,
        job_title=application.job_title,
        company=application.company,
        status=application.status,
        notes=application.notes,
        applied_date=datetime.now().isoformat()
    )
    
    db.add(new_application)
    db.commit()
    db.refresh(new_application)
    
    # Create notification
    notif = Notification(
        user_id=current_user.id,
        title="Application Submitted",
        message=f"You applied to {application.job_title} at {application.company}",
        type="success",
        action_url="/app/applications"
    )
    db.add(notif)
    db.commit()
    
    return new_application


@router.get("/{application_id}", response_model=ApplicationResponse)
async def get_application(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific application."""
    application = db.query(JobApplication).filter(
        JobApplication.id == application_id,
        JobApplication.user_id == current_user.id
    ).first()
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    return application


@router.put("/{application_id}", response_model=ApplicationResponse)
async def update_application(
    application_id: int,
    update_data: ApplicationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an application."""
    application = db.query(JobApplication).filter(
        JobApplication.id == application_id,
        JobApplication.user_id == current_user.id
    ).first()
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Update fields
    if update_data.status is not None:
        application.status = update_data.status
    if update_data.notes is not None:
        application.notes = update_data.notes
    if update_data.next_step is not None:
        application.next_step = update_data.next_step
    if update_data.follow_up_date is not None:
        application.follow_up_date = update_data.follow_up_date
    
    application.updated_at = datetime.now().isoformat()
    
    db.commit()
    db.refresh(application)
    
    return application


@router.delete("/{application_id}")
async def delete_application(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an application."""
    application = db.query(JobApplication).filter(
        JobApplication.id == application_id,
        JobApplication.user_id == current_user.id
    ).first()
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    db.delete(application)
    db.commit()
    
    return {"message": "Application deleted successfully"}


@router.get("/stats/summary")
async def get_application_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get application statistics."""
    applications = db.query(JobApplication).filter(
        JobApplication.user_id == current_user.id
    ).all()
    
    total = len(applications)
    
    status_counts = {}
    for app in applications:
        status_counts[app.status] = status_counts.get(app.status, 0) + 1
    
    return {
        "total": total,
        "by_status": status_counts
    }

