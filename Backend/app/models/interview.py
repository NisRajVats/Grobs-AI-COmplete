"""
Interview models for mock interviews and practice sessions.
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Float, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.session import Base


class InterviewSession(Base):
    """
    Mock interview session model.
    Tracks an interview practice session with questions and answers.
    """
    __tablename__ = "interview_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=True)
    
    # Session details
    job_title = Column(String, nullable=True)
    company = Column(String, nullable=True)
    job_description = Column(Text, nullable=True)
    
    # Status
    status = Column(String, default="in_progress")  # in_progress, completed
    current_question_index = Column(Integer, default=0)
    
    # Configuration
    question_count = Column(Integer, default=5)
    interview_type = Column(String, default="behavioral")  # behavioral, technical, mixed
    
    # Results
    overall_score = Column(Float, nullable=True)
    feedback_summary = Column(Text, nullable=True)
    
    # Timestamps
    started_at = Column(String, default=lambda: datetime.now().isoformat())
    completed_at = Column(String, nullable=True)
    created_at = Column(String, default=lambda: datetime.now().isoformat())
    updated_at = Column(String, default=lambda: datetime.now().isoformat())
    
    # Relationships
    user = relationship("User", back_populates="interview_sessions")
    resume = relationship("Resume")
    questions = relationship("InterviewQuestion", back_populates="session", cascade="all, delete-orphan")
    answers = relationship("InterviewAnswer", back_populates="session", cascade="all, delete-orphan")


class InterviewQuestion(Base):
    """
    Interview question model within a session.
    """
    __tablename__ = "interview_questions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("interview_sessions.id"), nullable=False)
    
    # Question details
    question_text = Column(Text, nullable=False)
    question_type = Column(String, nullable=False)  # behavioral, technical, role_specific, job_specific
    category = Column(String, nullable=True)  # star, leadership, technical, etc.
    
    # Order in session
    order_index = Column(Integer, default=0)
    
    # AI-generated tips
    tips = Column(Text, nullable=True)
    focus_areas = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(String, default=lambda: datetime.now().isoformat())
    
    # Relationships
    session = relationship("InterviewSession", back_populates="questions")
    answer = relationship("InterviewAnswer", back_populates="question", uselist=False)


class InterviewAnswer(Base):
    """
    User's answer to an interview question.
    """
    __tablename__ = "interview_answers"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("interview_sessions.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("interview_questions.id"), nullable=False)
    
    # Answer content
    answer_text = Column(Text, nullable=True)
    answer_audio_url = Column(String, nullable=True)
    answer_video_url = Column(String, nullable=True)
    
    # AI Feedback
    score = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)
    strengths = Column(JSON, nullable=True)
    improvements = Column(JSON, nullable=True)
    suggested_improvements = Column(JSON, nullable=True)
    
    # Timing
    time_taken_seconds = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(String, default=lambda: datetime.now().isoformat())
    
    # Relationships
    session = relationship("InterviewSession", back_populates="answers")
    question = relationship("InterviewQuestion", back_populates="answer")

