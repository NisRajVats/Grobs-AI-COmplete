from pydantic import BaseModel
from typing import List, Optional

class JobDescriptionIn(BaseModel):
    """The job description text sent from the frontend"""
    text: str

class AnalysisResult(BaseModel):
    """The structured JSON response from the AI"""
    score: float
    missing_keywords: List[str]
    suggestions: str

class ATSScoreResponse(BaseModel):
    """Response for ATS score check"""
    overall_score: int
    category_scores: dict
    issues: List[str]
    recommendations: List[str]

class CareerPathResponse(BaseModel):
    """Response for career path recommendation"""
    current_role: str
    experience_level: str
    current_skills: List[str]
    skill_categories: dict
    next_career_step: dict
    lateral_moves: List[dict]
    skills_to_develop: List[str]
    skill_gaps: List[str]
    estimated_timeline: str
    industry_trends: List[str]
    recommendations: List[str]

class InterviewQuestionsResponse(BaseModel):
    """Response for interview preparation"""
    role: str
    technologies: List[str]
    interview_structure: dict
    preparation_tips: List[str]
    estimated_duration: str

class CoverLetterRequest(BaseModel):
    """Request to generate a cover letter"""
    job_description: str
    company_name: Optional[str] = None
    position_title: Optional[str] = None

class CoverLetterResponse(BaseModel):
    """Response with generated cover letter"""
    success: bool
    cover_letter: str
    cover_letter_html: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[dict] = None

class ChatRequest(BaseModel):
    """User query for the career assistant"""
    query: str
    history: Optional[List[dict]] = []

class ChatResponse(BaseModel):
    """Response from the career assistant"""
    response: str
    success: bool = True
    error: Optional[str] = None
