"""
Authentication router for user registration, login, and token management.

Endpoints:
- POST /register - Register new user
- POST /token - Login and get tokens
- POST /refresh - Refresh access token
- POST /logout - Logout (revoke token)
- POST /password-reset - Request password reset
- POST /password-reset/confirm - Confirm password reset
- GET /me - Get current user info
- PUT /password - Change password
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional

from app.database.session import get_db
from app.models import User
from app.services.auth_service import AuthService
from app.utils.dependencies import get_current_user
from app.schemas.auth import (
    UserCreate,
    UserResponse,
    TokenResponse,
    TokenRefreshRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
    PasswordChange,
    MessageResponse
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# ==================== Endpoints ====================

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user and return tokens.
    """
    auth_service = AuthService(db)
    
    # We let GrobsAIException propagate to the global exception handler
    # which will return the correct status code (e.g., 409 for AlreadyExistsError)
    result = auth_service.register_user_with_token(
        email=user_data.email, 
        password=user_data.password,
        full_name=user_data.full_name
    )
    
    return TokenResponse(
        access_token=result["tokens"].access_token,
        refresh_token=result["tokens"].refresh_token
    )


@router.post("/token", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login with email and password.
    
    Use OAuth2 form data with:
    - username: email address
    - password: password
    """
    auth_service = AuthService(db)
    
    try:
        result = auth_service.login(form_data.username, form_data.password)
        
        return TokenResponse(
            access_token=result["tokens"].access_token,
            refresh_token=result["tokens"].refresh_token
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: TokenRefreshRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    
    Request body:
    - refresh_token: The refresh token from login
    """
    auth_service = AuthService(db)
    
    try:
        result = auth_service.refresh_tokens(request.refresh_token)
        
        return TokenResponse(
            access_token=result["tokens"].access_token,
            refresh_token=result["tokens"].refresh_token
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/logout")
async def logout(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """
    Logout by revoking the refresh token.
    """
    auth_service = AuthService(db)
    
    success = auth_service.revoke_token(refresh_token)
    
    return {"message": "Logged out successfully" if success else "Token already revoked"}


@router.post("/password-reset", response_model=MessageResponse)
async def request_password_reset(
    request: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    Request password reset link.
    
    Sends a password reset email to the user.
    Note: Returns success even if email doesn't exist (prevents email enumeration).
    """
    auth_service = AuthService(db)
    
    # This triggers the background email if the user exists
    auth_service.request_password_reset(request.email)
    
    # Always return success to prevent email enumeration
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/password-reset/confirm", response_model=MessageResponse)
async def confirm_password_reset(
    request: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """
    Confirm password reset with token.
    """
    auth_service = AuthService(db)
    
    try:
        auth_service.reset_password(request.token, request.new_password)
        return {"message": "Password reset successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user info.
    """
    return current_user


@router.put("/password", response_model=MessageResponse)
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change user password (requires current password).
    """
    auth_service = AuthService(db)
    
    try:
        auth_service.change_password(
            current_user,
            password_data.old_password,
            password_data.new_password
        )
        return {"message": "Password changed successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

