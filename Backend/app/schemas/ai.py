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


# ==================== Interview Schemas ====================

class InterviewSessionCreate(BaseModel):
    """Schema for creating a new interview session."""
    resume_id: Optional[int] = None
    job_title: Optional[str] = None
    company: Optional[str] = None
    job_description: Optional[str] = None
    question_count: int = 5
    interview_type: str = "mixed"  # behavioral, technical, mixed


class InterviewAnswerSubmit(BaseModel):
    """Schema for submitting an interview answer."""
    question_id: int
    answer_text: Optional[str] = None
    time_taken_seconds: Optional[int] = None


class InterviewQuestionResponse(BaseModel):
    """Response schema for interview question."""
    id: int
    question_text: str
    question_type: str
    category: Optional[str] = None
    order_index: int
    tips: Optional[str] = None
    focus_areas: Optional[List[str]] = None
    answered: bool = False

    class Config:
        from_attributes = True


class InterviewSessionResponse(BaseModel):
    """Response schema for interview session."""
    id: int
    user_id: int
    resume_id: Optional[int] = None
    job_title: Optional[str] = None
    company: Optional[str] = None
    status: str
    current_question_index: int
    question_count: int
    interview_type: str
    overall_score: Optional[float] = None
    feedback_summary: Optional[str] = None
    started_at: str
    completed_at: Optional[str] = None
    questions: Optional[List[InterviewQuestionResponse]] = []

    class Config:
        from_attributes = True


class InterviewAnswerResponse(BaseModel):
    """Response schema for interview answer."""
    id: int
    question_id: int
    answer_text: Optional[str] = None
    score: Optional[float] = None
    feedback: Optional[str] = None
    strengths: Optional[List[str]] = None
    improvements: Optional[List[str]] = None
    suggested_improvements: Optional[List[str]] = None
    tone_analysis: Optional[str] = None
    filler_words_detected: Optional[List[str]] = None
    time_taken_seconds: Optional[int] = None
    created_at: str

    class Config:
        from_attributes = True


class QuestionGenerationRequest(BaseModel):
    """Request schema for generating interview questions."""
    resume_id: Optional[int] = None
    job_description: Optional[str] = ""
    job_title: Optional[str] = None
