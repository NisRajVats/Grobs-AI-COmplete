"""
Job models for job listings, applications, and saved jobs.
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Float, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.session import Base


class Job(Base):
    """
    Job listing model.
    """
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Job details
    job_title = Column(String, nullable=False)
    company_name = Column(String, nullable=False)
    location = Column(String, nullable=True)
    job_type = Column(String, nullable=True)  # Full-time, Part-time, Contract, etc.
    skills_required = Column(Text, nullable=True)  # JSON array
    experience_required = Column(String, nullable=True)
    job_description = Column(Text, nullable=True)
    salary_range = Column(String, nullable=True)
    job_link = Column(String, nullable=True)
    posted_date = Column(String, nullable=True)
    source = Column(String, nullable=True)  # Greenhouse, Lever, Indeed, etc.
    
    # Embeddings for semantic search
    job_embedding = Column(Text, nullable=True)  # JSON array for vector similarity
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    applications = relationship("JobApplication", back_populates="job", cascade="all, delete-orphan")
    saved_by = relationship("SavedJob", back_populates="job", cascade="all, delete-orphan")
    # Additional relationships for scalable models
    skills = relationship("JobSkill", back_populates="job", cascade="all, delete-orphan")
    embedding = relationship("JobEmbedding", back_populates="job", uselist=False, cascade="all, delete-orphan")


class JobSkill(Base):
    """
    Normalized job skills - many-to-many relationship with jobs.
    """
    __tablename__ = "job_skills"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    skill_name = Column(String, nullable=False, index=True)
    skill_category = Column(String, nullable=True)  # technical, soft, tool, framework
    importance = Column(Integer, default=1)  # 1=optional, 2=preferred, 3=required
    
    # Timestamps
    created_at = Column(String, default=lambda: datetime.now().isoformat())
    
    # Relationships
    job = relationship("Job", back_populates="skills")


class JobEmbedding(Base):
    """
    Vector embeddings for semantic job matching.
    """
    __tablename__ = "job_embeddings"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, unique=True)
    
    # Embedding vector (stored as JSON array for portability)
    embedding_vector = Column(JSON, nullable=True)
    
    # Model info
    model_name = Column(String, default="all-MiniLM-L6-v2")
    
    # Timestamps
    created_at = Column(String, default=lambda: datetime.now().isoformat())
    updated_at = Column(String, default=lambda: datetime.now().isoformat())
    
    # Relationships
    job = relationship("Job", back_populates="embedding")


class JobApplication(Base):
    """
    Job application tracking model.
    """
    __tablename__ = "job_applications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=True)  # Resume used for application
    
    # Application details
    job_title = Column(String, nullable=True)
    company = Column(String, nullable=True)
    status = Column(String, default="applied")  # applied, interview, offer, rejected
    
    # Dates
    applied_date = Column(String, nullable=True)
    follow_up_date = Column(String, nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    next_step = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="applications")
    job = relationship("Job", back_populates="applications")
    resume = relationship("Resume")


class SavedJob(Base):
    """
    Saved jobs model.
    """
    __tablename__ = "saved_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=True)
    
    # Store job details for quick access (denormalized)
    job_title = Column(String, nullable=True)
    company = Column(String, nullable=True)
    job_description = Column(Text, nullable=True)
    
    # Match score (if calculated)
    match_score = Column(Float, nullable=True)
    
    # Timestamps
    saved_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="saved_jobs")
    job = relationship("Job", back_populates="saved_by")

