"""
Projects model for resume entries.
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database.session import Base


class Project(Base):
    """Project entry model."""
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    
    # Project details
    project_name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    project_url = Column(String, nullable=True)
    github_url = Column(String, nullable=True)
    technologies = Column(Text, nullable=True)  # Comma-separated or JSON
    
    # Relationships
    resume = relationship("Resume", back_populates="projects")

