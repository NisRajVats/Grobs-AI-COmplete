"""
Authentication Schemas

Pydantic models for authentication endpoints.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


# ==================== Request Schemas ====================

class UserCreate(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class TokenRefreshRequest(BaseModel):
    """Schema for token refresh."""
    refresh_token: str


class PasswordResetRequest(BaseModel):
    """Schema for requesting password reset."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Schema for confirming password reset."""
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)


class PasswordChange(BaseModel):
    """Schema for changing password."""
    old_password: str
    new_password: str = Field(..., min_length=8, max_length=100)


# ==================== Response Schemas ====================

class TokenResponse(BaseModel):
    """Response schema for authentication tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 1800  # 30 minutes in seconds


class TokenRefreshResponse(BaseModel):
    """Response schema for token refresh."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 1800


class UserResponse(BaseModel):
    """Response schema for user data."""
    id: int
    email: str
    full_name: Optional[str] = None
    title: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserProfileResponse(BaseModel):
    """Extended user profile response."""
    id: int
    email: str
    is_active: bool
    is_admin: bool
    stripe_customer_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: str
    message: str
    details: Optional[dict] = None


# ==================== Subscription Schemas ====================

class SubscriptionPlanResponse(BaseModel):
    """Response schema for subscription plan."""
    id: int
    name: str
    description: Optional[str]
    price: int
    duration_days: int
    features: Optional[str]
    stripe_price_id: Optional[str]

    class Config:
        from_attributes = True


class UserSubscriptionResponse(BaseModel):
    """Response schema for user subscription."""
    id: int
    user_id: int
    plan_id: int
    start_date: Optional[str]
    end_date: Optional[str]
    status: str
    stripe_subscription_id: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

