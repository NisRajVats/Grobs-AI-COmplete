"""
Application Schemas

Pydantic models for job application endpoints.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ==================== Application Status Enum ====================

class ApplicationStatus:
    """Possible application statuses."""
    APPLIED = "applied"
    REVIEWING = "reviewing"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


# ==================== Application Schemas ====================

class ApplicationCreate(BaseModel):
    """Schema for creating a job application."""
    job_id: int
    resume_id: Optional[int] = None
    job_title: Optional[str] = None
    company: Optional[str] = None
    notes: Optional[str] = None


class ApplicationUpdate(BaseModel):
    """Schema for updating a job application."""
    status: Optional[str] = None
    applied_date: Optional[str] = None
    follow_up_date: Optional[str] = None
    notes: Optional[str] = None
    next_step: Optional[str] = None


class ApplicationResponse(BaseModel):
    """Response schema for job application."""
    id: int
    user_id: int
    job_id: int
    resume_id: Optional[int]
    job_title: Optional[str]
    company: Optional[str]
    status: str
    applied_date: Optional[str]
    follow_up_date: Optional[str]
    notes: Optional[str]
    next_step: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class ApplicationListResponse(BaseModel):
    """Response schema for list of applications."""
    applications: List[ApplicationResponse]
    total: int
    page: int
    page_size: int


# ==================== Application Status Update ====================

class ApplicationStatusUpdate(BaseModel):
    """Schema for updating application status."""
    status: str = Field(..., description="New status for the application")
    notes: Optional[str] = Field(None, description="Optional notes about the status change")


# ==================== Application Statistics ====================

class ApplicationStatsResponse(BaseModel):
    """Response schema for application statistics."""
    total: int
    applied: int
    reviewing: int
    interview: int
    offer: int
    rejected: int
    withdrawn: int


# ==================== Interview Schemas ====================

class InterviewCreate(BaseModel):
    """Schema for creating an interview."""
    application_id: int
    interview_date: str
    interview_type: Optional[str] = None  # phone, video, onsite
    interviewer_name: Optional[str] = None
    interviewer_email: Optional[str] = None
    notes: Optional[str] = None


class InterviewUpdate(BaseModel):
    """Schema for updating an interview."""
    interview_date: Optional[str] = None
    interview_type: Optional[str] = None
    interviewer_name: Optional[str] = None
    interviewer_email: Optional[str] = None
    notes: Optional[str] = None
    outcome: Optional[str] = None


class InterviewResponse(BaseModel):
    """Response schema for interview."""
    id: int
    application_id: int
    interview_date: str
    interview_type: Optional[str]
    interviewer_name: Optional[str]
    interviewer_email: Optional[str]
    notes: Optional[str]
    outcome: Optional[str]
    created_at: str

    class Config:
        from_attributes = True

