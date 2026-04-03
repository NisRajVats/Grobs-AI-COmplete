"""
Experience model for resume entries.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database.session import Base


class Experience(Base):
    """Work experience entry model."""
    __tablename__ = "experience"
    
    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False, index=True)
    
    # Experience details
    company = Column(String, nullable=False)
    role = Column(String, nullable=False)
    location = Column(String, nullable=True)
    start_date = Column(String, nullable=True)
    end_date = Column(String, nullable=True)
    current = Column(Boolean, default=False)
    description = Column(Text, nullable=True)
    
    # Relationships
    resume = relationship("Resume", back_populates="experience")

