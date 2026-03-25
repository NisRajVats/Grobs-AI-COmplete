"""
Skills model for resume entries.
"""
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database.session import Base


class Skill(Base):
    """Skill entry model."""
    __tablename__ = "skills"
    
    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    
    # Skill details
    name = Column(String, nullable=False)
    category = Column(String, default="Technical")  # Technical, Soft, Domain, etc.
    
    # Relationships
    resume = relationship("Resume", back_populates="skills")

