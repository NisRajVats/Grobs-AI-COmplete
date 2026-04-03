"""
Projects model for resume entries.
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON
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
    points = Column(JSON, nullable=True)  # Store as array of strings
    project_url = Column(String, nullable=True)
    github_url = Column(String, nullable=True)
    technologies = Column(JSON, nullable=True)  # Store as array of strings
    
    # Relationships
    resume = relationship("Resume", back_populates="projects")

