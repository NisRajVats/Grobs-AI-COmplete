"""
User Schemas

Pydantic models for user endpoints.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


# ==================== User Schemas ====================

class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr


class UserCreate(UserBase):
    """Schema for creating a user."""
    full_name: Optional[str] = None
    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseModel):
    """Schema for updating user information."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    title: Optional[str] = None
    linkedin_url: Optional[str] = None
    avatar_url: Optional[str] = None


class UserResponse(UserBase):
    """Response schema for user."""
    id: int
    full_name: Optional[str] = None
    is_active: bool
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserProfileResponse(UserBase):
    """Extended user profile response."""
    id: int
    is_active: bool
    is_admin: bool
    stripe_customer_id: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    title: Optional[str] = None
    linkedin_url: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Dashboard Schemas ====================

class DashboardStats(BaseModel):
    """Schema for dashboard statistics."""
    total_resumes: int
    avg_ats_score: float
    total_applications: int
    total_saved_jobs: int
    applications_by_status: dict


# ==================== Profile Schemas ====================

class ProfileCreate(BaseModel):
    """Schema for creating user profile."""
    full_name: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    bio: Optional[str] = None


class ProfileUpdate(BaseModel):
    """Schema for updating user profile."""
    full_name: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None


# ==================== Notification Schemas ====================

class NotificationCreate(BaseModel):
    """Schema for creating a notification."""
    title: str
    message: str
    type: str = "info"
    action_url: Optional[str] = None


class NotificationResponse(BaseModel):
    """Response schema for notification."""
    id: int
    user_id: int
    title: str
    message: str
    type: str
    is_read: bool
    action_url: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """Response schema for list of notifications."""
    notifications: List[NotificationResponse]
    total: int
    unread_count: int


# ==================== Settings Schemas ====================

class UserSettings(BaseModel):
    """User settings schema."""
    email_notifications: bool = True
    job_alerts: bool = True
    weekly_digest: bool = True
    marketing_emails: bool = False


class UserSettingsResponse(UserSettings):
    """Response schema for user settings."""
    user_id: int

    class Config:
        from_attributes = True

