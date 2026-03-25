"""
Education model for resume entries.
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database.session import Base


class Education(Base):
    """Education entry model."""
    __tablename__ = "education"
    
    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    
    # Education details
    school = Column(String, nullable=False)
    degree = Column(String, nullable=False)
    major = Column(String, nullable=True)
    gpa = Column(String, nullable=True)
    start_date = Column(String, nullable=True)
    end_date = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    
    # Relationships
    resume = relationship("Resume", back_populates="education")

