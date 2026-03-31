"""
Resume Schemas

Pydantic models for resume endpoints.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime


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
    pass


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
    pass


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
    technologies: Optional[str] = None


class ProjectCreate(ProjectBase):
    """Schema for creating project."""
    pass


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
    pass


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
        import json
        from app.utils.encryption import decrypt
        # Convert SQLAlchemy object to dict
        data = {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
        
        # Decrypt sensitive fields for response
        if data.get('full_name'):
            data['full_name'] = decrypt(data['full_name'])
        if data.get('email'):
            data['email'] = decrypt(data['email'])
        if data.get('phone'):
            data['phone'] = decrypt(data['phone'])
        if data.get('linkedin_url'):
            data['linkedin_url'] = decrypt(data['linkedin_url'])
        
        # Add relationships or calculated fields
        data['version'] = len(obj.versions) if hasattr(obj, 'versions') else 1
        
        # Parse JSON fields if they are strings
        pd = {}
        if data.get('parsed_data') and isinstance(data['parsed_data'], str):
            try:
                pd = json.loads(data['parsed_data'])
                if not isinstance(pd, dict):
                    pd = {}
            except:
                pd = {}
        
        # Sync decrypted root fields into parsed_data for consistent preview
        pd['full_name'] = data.get('full_name')
        pd['email'] = data.get('email')
        pd['phone'] = data.get('phone')
        pd['linkedin_url'] = data.get('linkedin_url')
        pd['title'] = data.get('title')
        pd['target_role'] = data.get('target_role')
        
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
        import json
        res = super().from_orm(obj)
        data = res.dict()
        
        # Add nested relationships
        data['education'] = [EducationCreate(**{c.name: getattr(e, c.name) for c in e.__table__.columns if c.name in EducationCreate.model_fields}) for e in obj.education]
        data['experience'] = [ExperienceCreate(**{c.name: getattr(e, c.name) for c in e.__table__.columns if c.name in ExperienceCreate.model_fields}) for e in obj.experience]
        data['projects'] = [ProjectCreate(**{c.name: getattr(e, c.name) for c in e.__table__.columns if c.name in ProjectCreate.model_fields}) for e in obj.projects]
        data['skills'] = [SkillCreate(**{c.name: getattr(e, c.name) for c in e.__table__.columns if c.name in SkillCreate.model_fields}) for e in obj.skills]
        
        # Sync structured sections into parsed_data for consistent preview
        if isinstance(data['parsed_data'], dict):
            data['parsed_data']['education'] = data['education']
            data['parsed_data']['experience'] = data['experience']
            data['parsed_data']['projects'] = data['projects']
            data['parsed_data']['skills'] = data['skills']
        
        # Get latest analysis
        if hasattr(obj, 'analyses') and obj.analyses:
            latest = sorted(obj.analyses, key=lambda x: x.created_at, reverse=True)[0]
            try:
                data['latest_analysis'] = {
                    "score": latest.score,
                    "feedback": json.loads(latest.feedback) if latest.feedback else {},
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

