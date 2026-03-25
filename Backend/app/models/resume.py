"""
Resume models with multi-resume support.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.session import Base


class Resume(Base):
    """
    Resume model supporting multiple resumes per user.
    """
    __tablename__ = "resumes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Basic info (stored encrypted)
    full_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    linkedin_url = Column(String, nullable=True)
    
    # File info
    filename = Column(String, nullable=True)
    file_path = Column(String, nullable=True)
    resume_file_url = Column(String, nullable=True)  # Cloud storage URL
    
    # Resume metadata
    title = Column(String, nullable=True)  # User-defined title like "Software Engineer Resume"
    target_role = Column(String, nullable=True)  # Target job role
    template_name = Column(String, default="classic")
    status = Column(String, default="active")  # active, archived, optimized
    
    # Parsed data (JSON string)
    parsed_data = Column(Text, nullable=True)
    
    # ATS and analysis scores
    ats_score = Column(Integer, nullable=True)
    analysis_score = Column(Integer, nullable=True)
    analysis_feedback = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="resumes")
    versions = relationship("ResumeVersion", back_populates="resume", cascade="all, delete-orphan")
    education = relationship("Education", back_populates="resume", cascade="all, delete-orphan")
    experience = relationship("Experience", back_populates="resume", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="resume", cascade="all, delete-orphan")
    skills = relationship("Skill", back_populates="resume", cascade="all, delete-orphan")
    analyses = relationship("ResumeAnalysis", back_populates="resume", cascade="all, delete-orphan")
    # Additional relationships for scalable models
    content = relationship("ResumeContent", back_populates="resume", uselist=False, cascade="all, delete-orphan")
    embedding = relationship("ResumeEmbedding", back_populates="resume", uselist=False, cascade="all, delete-orphan")


class ResumeVersion(Base):
    """
    Resume version history for tracking changes and optimized versions.
    """
    __tablename__ = "resume_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    
    # Version info
    version_number = Column(Integer, default=1)
    version_label = Column(String, nullable=True)  # e.g., "Optimized v1", "ATS Version"
    
    # Whether this is an optimized version
    optimized_flag = Column(Boolean, default=False)
    
    # Version data (JSON string containing full resume data at this version)
    parsed_data = Column(Text, nullable=True)
    ats_score = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    resume = relationship("Resume", back_populates="versions")


class ResumeAnalysis(Base):
    """
    Resume analysis results (ATS, AI analysis, etc.).
    """
    __tablename__ = "resume_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    
    # Analysis type: 'ats', 'ai', 'keyword'
    analysis_type = Column(String, nullable=False)
    
    # Scores
    score = Column(Integer, nullable=True)
    
    # Detailed results (JSON string)
    feedback = Column(Text, nullable=True)
    missing_keywords = Column(Text, nullable=True)  # JSON array
    suggestions = Column(Text, nullable=True)
    
    # Job description used for analysis (if applicable)
    job_description = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    resume = relationship("Resume", back_populates="analyses")


class ResumeContent(Base):
    """
    Parsed structured resume data - separated for large JSON storage.
    """
    __tablename__ = "resume_contents"
    
    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False, unique=True)
    
    # Parsed contact info (stored encrypted)
    full_name_encrypted = Column(String, nullable=True)
    email_encrypted = Column(String, nullable=True)
    phone_encrypted = Column(String, nullable=True)
    linkedin_url_encrypted = Column(String, nullable=True)
    
    # Parsed JSON data (full parsed content)
    parsed_json = Column(JSON, nullable=True)  # Full parsed structure
    raw_text = Column(Text, nullable=True)  # Raw extracted text
    
    # Structured sections
    sections = Column(JSON, nullable=True)  # Parsed sections
    skills_list = Column(JSON, nullable=True)  # Extracted skills array
    
    # Timestamps
    parsed_at = Column(String, nullable=True)
    created_at = Column(String, default=lambda: datetime.now().isoformat())
    updated_at = Column(String, default=lambda: datetime.now().isoformat())
    
    # Relationships
    resume = relationship("Resume", back_populates="content")


class ResumeEmbedding(Base):
    """
    Vector embeddings for semantic job matching.
    """
    __tablename__ = "resume_embeddings"
    
    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False, unique=True)
    
    # Embedding vector (stored as JSON array for portability)
    embedding_vector = Column(JSON, nullable=True)
    
    # Model info
    model_name = Column(String, default="all-MiniLM-L6-v2")
    
    # Timestamps
    created_at = Column(String, default=lambda: datetime.now().isoformat())
    updated_at = Column(String, default=lambda: datetime.now().isoformat())
    
    # Relationships
    resume = relationship("Resume", back_populates="embedding")

