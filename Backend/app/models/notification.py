"""
Notification model for user notifications.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.session import Base


class Notification(Base):
    """Notification model for user notifications."""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Notification details
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String, default="info")  # info, success, warning, error
    notification_type = Column(String, nullable=True) # alternative name for type
    is_read = Column(Boolean, default=False)
    
    # Optional link/action
    action_url = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(String, default=lambda: datetime.now().isoformat())
    
    # Relationships
    user = relationship("User", back_populates="notifications")

