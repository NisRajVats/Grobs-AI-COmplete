"""
Resume Schemas

Pydantic models for resume endpoints.
"""
import json
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Any, Union
from datetime import datetime
from app.utils.encryption import decrypt


# ==================== Education Schemas ====================

class EducationBase(BaseModel):
    """Base education schema."""
    school: str
    degree: Optional[str] = ""
    major: Optional[str] = None
    gpa: Optional[str] = None
    start_date: Optional[str] = ""
    end_date: Optional[str] = ""
    year: Optional[str] = None  # Frontend compatibility
    description: Optional[str] = None


class EducationCreate(EducationBase):
    """Schema for creating education."""
    model_config = {"from_attributes": True}


class EducationResponse(EducationBase):
    """Response schema for education."""
    id: int
    resume_id: int

    class Config:
        from_attributes = True


# ==================== Experience Schemas ====================

class ExperienceBase(BaseModel):
    """Base experience schema."""
    company: str
    role: str
    location: Optional[str] = None
    start_date: Optional[str] = ""
    end_date: Optional[str] = None
    current: bool = False
    duration: Optional[str] = None  # Frontend compatibility
    description: Optional[str] = None
    desc: Optional[str] = None  # Frontend compatibility


class ExperienceCreate(ExperienceBase):
    """Schema for creating experience."""
    model_config = {"from_attributes": True}


class ExperienceResponse(ExperienceBase):
    """Response schema for experience."""
    id: int
    resume_id: int

    class Config:
        from_attributes = True


# ==================== Project Schemas ====================

class ProjectBase(BaseModel):
    """Base project schema."""
    project_name: str
    description: Optional[str] = None
    desc: Optional[str] = None  # Frontend compatibility
    project_url: Optional[str] = None
    github_url: Optional[str] = None
    technologies: Optional[Any] = None  # Extremely flexible
    points: Optional[List[str]] = []

    @field_validator('technologies', mode='before')
    @classmethod
    def validate_technologies(cls, v):
        """Coerce list of technologies to string if needed."""
        if isinstance(v, list):
            return ", ".join([str(item) for item in v])
        return v


class ProjectCreate(ProjectBase):
    """Schema for creating project."""
    model_config = {"from_attributes": True}


class ProjectResponse(ProjectBase):
    """Response schema for project."""
    id: int
    resume_id: int

    class Config:
        from_attributes = True


# ==================== Skill Schemas ====================

class SkillBase(BaseModel):
    """Base skill schema."""
    name: str
    category: str = "Technical"


class SkillCreate(SkillBase):
    """Schema for creating skill."""
    model_config = {"from_attributes": True}


class SkillResponse(SkillBase):
    """Response schema for skill."""
    id: int
    resume_id: int

    class Config:
        from_attributes = True


# ==================== Resume Schemas ====================

class ResumeCreate(BaseModel):
    """Schema for creating a new resume."""
    full_name: str
    email: str
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    title: Optional[str] = None
    summary: Optional[str] = None
    target_role: Optional[str] = None
    template_name: str = "classic"
    education: List[EducationCreate] = []
    experience: List[ExperienceCreate] = []
    projects: List[ProjectCreate] = []
    skills: List[SkillCreate] = []


class ResumeUpdate(BaseModel):
    """Schema for updating a resume."""
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    title: Optional[str] = None
    summary: Optional[str] = None
    target_role: Optional[str] = None
    template_name: Optional[str] = None
    parsed_data: Optional[Any] = None
    status: Optional[str] = None
    education: Optional[List[EducationCreate]] = []
    experience: Optional[List[ExperienceCreate]] = []
    projects: Optional[List[ProjectCreate]] = []
    skills: Optional[List[SkillCreate]] = []


class ResumeResponse(BaseModel):
    """Response schema for resume."""
    id: int
    user_id: int
    full_name: str
    email: str
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    title: Optional[str] = None
    target_role: Optional[str] = None
    template_name: str = "classic"
    filename: Optional[str] = None
    resume_file_url: Optional[str] = None
    ats_score: Optional[int] = None
    analysis_score: Optional[int] = None
    status: str
    version: int = 1
    created_at: datetime
    updated_at: datetime
    parsed_data: Optional[Any] = None

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, obj):
        """Optimized from_orm with lazy-load aware decryption."""
        # Use built-in dict construction which is generally faster
        data = {
            'id': obj.id,
            'user_id': obj.user_id,
            'full_name': decrypt(obj.full_name) if obj.full_name else "",
            'email': decrypt(obj.email) if obj.email else "",
            'phone': decrypt(obj.phone) if obj.phone else None,
            'linkedin_url': decrypt(obj.linkedin_url) if obj.linkedin_url else None,
            'title': obj.title,
            'target_role': obj.target_role,
            'template_name': obj.template_name,
            'filename': obj.filename,
            'resume_file_url': obj.resume_file_url,
            'ats_score': obj.ats_score,
            'analysis_score': obj.analysis_score,
            'status': obj.status,
            'created_at': obj.created_at,
            'updated_at': obj.updated_at,
        }
        
        # Add version from relationship
        data['version'] = len(obj.versions) if hasattr(obj, 'versions') else 1
        
        # Process parsed_data
        pd = {}
        if obj.parsed_data:
            if isinstance(obj.parsed_data, str):
                try:
                    pd = json.loads(obj.parsed_data)
                except:
                    pd = {}
            elif isinstance(obj.parsed_data, dict):
                pd = obj.parsed_data
        
        # Sync decrypted fields for preview consistency
        pd.update({
            'full_name': data['full_name'],
            'email': data['email'],
            'phone': data['phone'],
            'linkedin_url': data['linkedin_url'],
            'title': data['title'],
            'target_role': data['target_role']
        })
        
        data['parsed_data'] = pd
        
        return cls(**data)


class ResumeDetailResponse(ResumeResponse):
    """Detailed response schema for resume with all sections."""
    education: List[EducationCreate] = []
    experience: List[ExperienceCreate] = []
    projects: List[ProjectCreate] = []
    skills: List[SkillCreate] = []
    latest_analysis: Optional[dict] = None

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, obj):
        """Optimized from_orm for detailed resume response."""
        # Use our own logic instead of super().from_orm + res.dict()
        res = ResumeResponse.from_orm(obj)
        data = res.model_dump()
        
        # Add nested relationships efficiently
        data['education'] = [EducationCreate.model_validate(e) for e in obj.education]
        data['experience'] = [ExperienceCreate.model_validate(e) for e in obj.experience]
        data['projects'] = [ProjectCreate.model_validate(e) for e in obj.projects]
        data['skills'] = [SkillCreate.model_validate(e) for e in obj.skills]
        
        # Sync structured sections into parsed_data
        pd = data.get('parsed_data')
        if not isinstance(pd, dict):
            pd = {}
        
        pd.update({
            'education': [e.model_dump() for e in data['education']],
            'experience': [e.model_dump() for e in data['experience']],
            'projects': [e.model_dump() for e in data['projects']],
            'skills': [e.model_dump() for e in data['skills']]
        })
        data['parsed_data'] = pd
        
        # Latest analysis
        if hasattr(obj, 'analyses') and obj.analyses:
            # We already have analyses eager loaded
            sorted_analyses = sorted(obj.analyses, key=lambda x: x.created_at, reverse=True)
            if sorted_analyses:
                latest = sorted_analyses[0]
                try:
                    data['latest_analysis'] = {
                        "score": latest.score,
                        "feedback": json.loads(latest.feedback) if latest.feedback and isinstance(latest.feedback, str) else latest.feedback or {},
                        "created_at": latest.created_at
                    }
                except:
                    data['latest_analysis'] = {"score": latest.score, "created_at": latest.created_at}
                
        return cls(**data)


# ==================== Resume Content Schemas ====================

class ResumeContentResponse(BaseModel):
    """Response schema for parsed resume content."""
    id: int
    resume_id: int
    full_name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    linkedin_url: Optional[str]
    raw_text: Optional[str]
    skills_list: Optional[List[str]]
    parsed_at: Optional[datetime]

    class Config:
        from_attributes = True


# ==================== Resume Analysis Schemas ====================

class ResumeAnalysisResponse(BaseModel):
    """Response schema for resume analysis."""
    id: int
    resume_id: int
    analysis_type: str
    ats_score: Optional[int]
    keyword_score: Optional[int]
    overall_score: Optional[int]
    analysis_feedback: Optional[dict]
    missing_keywords: Optional[List[str]]
    suggestions: Optional[List[str]]
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Resume Version Schemas ====================

class ResumeVersionResponse(BaseModel):
    """Response schema for resume version."""
    id: int
    resume_id: int
    version_number: int
    version_label: Optional[str] = None
    optimized_flag: bool = False
    ats_score: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Resume Upload Schemas ====================

class ResumeUploadResponse(BaseModel):
    """Response schema for uploaded resume."""
    resume_id: int
    message: str
    status: str = "uploaded"


# ==================== ATS Score Schemas ====================

class ATSScoreRequest(BaseModel):
    """Request schema for ATS score."""
    job_description: Optional[str] = ""


class ATSScoreResponse(BaseModel):
    """Response schema for ATS score."""
    resume_id: int
    ats_score: int
    overall_score: int
    category_scores: dict
    issues: List[str]
    recommendations: List[str]
    skill_analysis: Optional[dict] = None
    keyword_gap: Optional[dict] = None
    industry_tips: Optional[List[str]] = None


# ==================== Job Match Schemas ====================

class JobMatchResponse(BaseModel):
    """Response schema for job matching."""
    resume_id: int
    job_id: int
    job_title: str
    company_name: str
    location: Optional[str]
    match_score: int
    missing_keywords: List[str] = []


class JobMatchListResponse(BaseModel):
    """Response schema for list of job matches."""
    resume_id: int
    matches: List[JobMatchResponse]
    total: int


# ==================== Resume Optimization Schemas ====================

class OptimizeResumeRequest(BaseModel):
    """Request schema for resume optimization."""
    optimization_type: str = "comprehensive"
    job_description: Optional[str] = ""
    job_id: Optional[int] = None
    save_as_new: bool = False


class OptimizeResumeResponse(BaseModel):
    """Response schema for resume optimization."""
    success: bool
    resume_id: int
    suggestions: str
    improvements: List[str]
    ats_score: int
    original_resume: Optional[Any] = None
    optimized_resume: Optional[Any] = None
    compatibility_score: int
    compatibility_feedback: str
    skill_gap: Optional[List[str]] = []
    matching_skills: Optional[List[str]] = []
    skill_recommendations: Optional[List[str]] = []
    certificate_recommendations: Optional[List[str]] = []


class BulkDeleteRequest(BaseModel):
    """Request schema for bulk deleting resumes."""
    ids: List[int]


class BulkDeleteResponse(BaseModel):
    """Response schema for bulk delete operation."""
    deleted: int
    failed: int
    message: str

