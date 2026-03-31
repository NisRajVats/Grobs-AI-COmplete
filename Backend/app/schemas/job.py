"""
Job Schemas

Pydantic models for job endpoints.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ==================== Job Skill Schemas ====================

class JobSkillBase(BaseModel):
    """Base job skill schema."""
    skill_name: str
    skill_category: Optional[str] = None
    importance: int = 1


class JobSkillCreate(JobSkillBase):
    """Schema for creating job skill."""
    pass


class JobSkillResponse(JobSkillBase):
    """Response schema for job skill."""
    id: int
    job_id: int

    class Config:
        from_attributes = True


# ==================== Job Schemas ====================

class JobCreate(BaseModel):
    """Schema for creating a job."""
    job_title: str = Field(..., min_length=1)
    company_name: str = Field(..., min_length=1)
    location: Optional[str] = None
    job_type: Optional[str] = None
    job_description: Optional[str] = None
    experience_required: Optional[str] = None
    salary_range: Optional[str] = None
    job_link: Optional[str] = None
    skills: List[JobSkillCreate] = []


class JobUpdate(BaseModel):
    """Schema for updating a job."""
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[str] = None
    job_description: Optional[str] = None
    experience_required: Optional[str] = None
    salary_range: Optional[str] = None
    job_link: Optional[str] = None
    skills: Optional[List[JobSkillCreate]] = None


class JobResponse(BaseModel):
    """Response schema for job."""
    id: int
    job_title: str
    company_name: str
    location: Optional[str] = None
    job_type: Optional[str] = None
    job_description: Optional[str] = None
    skills_required: Optional[str] = None
    experience_required: Optional[str] = None
    salary_range: Optional[str] = None
    job_link: Optional[str] = None
    posted_date: Optional[str] = None
    source: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class JobDetailResponse(JobResponse):
    """Detailed response schema for job with skills."""
    skills: List[JobSkillResponse] = []

    class Config:
        from_attributes = True


# ==================== Job Search Schemas ====================

class JobSearchRequest(BaseModel):
    """Schema for job search."""
    query: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[str] = None
    min_salary: Optional[int] = None
    max_salary: Optional[int] = None
    skills: Optional[List[str]] = None


class JobSearchResponse(BaseModel):
    """Response schema for job search."""
    jobs: List[JobResponse]
    total: int
    page: Optional[int] = None
    page_size: Optional[int] = None


# ==================== Job Matching Schemas ====================

class JobMatchResponse(BaseModel):
    """Response schema for job matching."""
    job: JobResponse
    match_score: float
    missing_keywords: List[str] = []

    class Config:
        from_attributes = True


# ==================== Job Embedding Schemas ====================

class JobEmbeddingResponse(BaseModel):
    """Response schema for job embedding."""
    id: int
    job_id: int
    model_name: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


# ==================== Saved Job Schemas ====================

class SavedJobResponse(BaseModel):
    """Response schema for saved job."""
    id: int
    job_id: int
    user_id: int
    job_title: Optional[str] = None
    company: Optional[str] = None
    job_description: Optional[str] = None
    match_score: Optional[float] = None
    saved_date: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SaveJobRequest(BaseModel):
    """Schema for saving a job."""
    match_score: Optional[float] = None


# ==================== Job Recommendation Schemas ====================

class JobRecommendationRequest(BaseModel):
    """Schema for job recommendations."""
    resume_id: int
    limit: int = Field(default=10, ge=1, le=50)
    min_score: float = Field(default=0.3, ge=0.0, le=1.0)


class JobRecommendationResponse(BaseModel):
    """Response schema for job recommendations."""
    resume_id: int
    recommendations: List[JobMatchResponse]
    total: int = 0

