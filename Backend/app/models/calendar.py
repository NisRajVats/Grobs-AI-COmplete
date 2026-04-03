from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.session import Base

class CalendarEvent(Base):
    __tablename__ = "calendar_events"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    date = Column(String, nullable=False) # Store as YYYY-MM-DD
    time = Column(String, nullable=False) # Store as HH:MM
    platform = Column(String, default="Google Meet")
    type = Column(String, default="interview") # interview, networking, preparation
    status = Column(String, default="scheduled") # scheduled, completed, cancelled
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", backref="calendar_events")
