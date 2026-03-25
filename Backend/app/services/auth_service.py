"""
Authentication Service

Handles all authentication-related business logic:
- User registration
- Login / token generation
- Token refresh
- Password reset
- Email verification
"""
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.models import User
from app.core.security import (
    verify_password,
    get_password_hash,
    create_token_pair,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    rotate_refresh_token,
    revoke_refresh_token,
    create_password_reset_token,
    verify_password_reset_token,
    create_email_verification_token,
    verify_email_verification_token,
    TokenPair
)
from app.core.exceptions import (
    InvalidCredentialsError,
    TokenExpiredError,
    InvalidTokenError,
    AlreadyExistsError,
    NotFoundError
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class AuthService:
    """
    Authentication service for user management and token operations.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== User Registration ====================
    
    def register_user(
        self,
        email: str,
        password: str,
        **extra_fields
    ) -> User:
        """
        Register a new user.
        
        Args:
            email: User's email address
            password: User's password
            **extra_fields: Additional user fields
            
        Returns:
            Created User object
            
        Raises:
            AlreadyExistsError: If email already registered
        """
        # Check if user exists
        existing_user = self.db.query(User).filter(User.email == email).first()
        if existing_user:
            raise AlreadyExistsError("User", email)
        
        # Hash password and create user
        hashed_password = get_password_hash(password)
        
        # Explicitly extract full_name from extra_fields if present
        full_name = extra_fields.pop('full_name', None)
        
        user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            **extra_fields
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        logger.info(f"New user registered: {email}")
        
        return user
    
    def register_user_with_token(
        self,
        email: str,
        password: str,
        **extra_fields
    ) -> Dict[str, Any]:
        """
        Register a new user and return tokens.
        
        Args:
            email: User's email address
            password: User's password
            **extra_fields: Additional user fields
            
        Returns:
            Dictionary with user and tokens
        """
        user = self.register_user(email, password, **extra_fields)
        
        # Create tokens
        tokens = self.generate_tokens(user)
        
        return {
            "user": user,
            "tokens": tokens
        }
    
    # ==================== Login ====================
    
    def authenticate_user(
        self,
        email: str,
        password: str
    ) -> User:
        """
        Authenticate a user with email and password.
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            Authenticated User object
            
        Raises:
            InvalidCredentialsError: If authentication fails
        """
        user = self.db.query(User).filter(User.email == email).first()
        
        if not user:
            raise InvalidCredentialsError()
        
        if not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError()
        
        if not user.is_active:
            raise InvalidCredentialsError("User account is inactive")
        
        return user
    
    def login(
        self,
        email: str,
        password: str
    ) -> Dict[str, Any]:
        """
        Login user and generate tokens.
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            Dictionary with user and tokens
        """
        user = self.authenticate_user(email, password)
        
        # Generate tokens
        tokens = self.generate_tokens(user)
        
        logger.info(f"User logged in: {email}")
        
        return {
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "is_admin": user.is_admin
            },
            "tokens": tokens
        }
    
    # ==================== Token Management ====================
    
    def generate_tokens(self, user: User) -> TokenPair:
        """
        Generate access and refresh tokens for a user.
        
        Args:
            user: User object
            
        Returns:
            TokenPair with both tokens
        """
        data = {
            "sub": user.email,
            "user_id": user.id
        }
        return create_token_pair(data)
    
    def refresh_tokens(
        self,
        refresh_token: str
    ) -> Dict[str, Any]:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            Dictionary with new tokens
            
        Raises:
            InvalidTokenError: If refresh token is invalid
        """
        # Decode refresh token
        token_data = decode_refresh_token(refresh_token)
        
        if not token_data or not token_data.email:
            raise InvalidTokenError("Invalid or expired refresh token")
        
        # Get user
        user = self.db.query(User).filter(User.email == token_data.email).first()
        
        if not user or not user.is_active:
            raise InvalidTokenError("User not found or inactive")
        
        # Rotate token (invalidate old, create new)
        data = {
            "sub": user.email,
            "user_id": user.id
        }
        
        new_tokens = rotate_refresh_token(refresh_token, data)
        
        if not new_tokens:
            raise InvalidTokenError("Failed to refresh token")
        
        logger.info(f"Tokens refreshed for user: {user.email}")
        
        return {
            "tokens": new_tokens
        }
    
    def revoke_token(self, refresh_token: str) -> bool:
        """
        Revoke a refresh token.
        
        Args:
            refresh_token: Token to revoke
            
        Returns:
            True if revoked successfully
        """
        return revoke_refresh_token(refresh_token)
    
    # ==================== Password Management ====================
    
    def request_password_reset(
        self,
        email: str
    ) -> Optional[str]:
        """
        Request password reset for a user.
        
        Args:
            email: User's email address
            
        Returns:
            Password reset token if user exists (to prevent email enumeration)
        """
        user = self.db.query(User).filter(User.email == email).first()
        
        if user:
            token = create_password_reset_token(email)
            logger.info(f"Password reset requested for: {email}")
            return token
        
        # Don't reveal if email exists
        logger.warning(f"Password reset requested for unknown email: {email}")
        return None
    
    def reset_password(
        self,
        reset_token: str,
        new_password: str
    ) -> bool:
        """
        Reset user's password using reset token.
        
        Args:
            reset_token: Password reset token
            new_password: New password
            
        Returns:
            True if password was reset
            
        Raises:
            InvalidTokenError: If token is invalid
        """
        email = verify_password_reset_token(reset_token)
        
        if not email:
            raise InvalidTokenError("Invalid or expired reset token")
        
        user = self.db.query(User).filter(User.email == email).first()
        
        if not user:
            raise NotFoundError("User", email)
        
        # Update password
        user.hashed_password = get_password_hash(new_password)
        self.db.commit()
        
        logger.info(f"Password reset completed for: {email}")
        
        return True
    
    def change_password(
        self,
        user: User,
        old_password: str,
        new_password: str
    ) -> bool:
        """
        Change user's password (requires old password).
        
        Args:
            user: Current user
            old_password: Current password
            new_password: New password
            
        Returns:
            True if password was changed
            
        Raises:
            InvalidCredentialsError: If old password is wrong
        """
        if not verify_password(old_password, user.hashed_password):
            raise InvalidCredentialsError("Current password is incorrect")
        
        user.hashed_password = get_password_hash(new_password)
        self.db.commit()
        
        logger.info(f"Password changed for user: {user.email}")
        
        return True
    
    # ==================== Email Verification ====================
    
    def request_email_verification(
        self,
        email: str
    ) -> Optional[str]:
        """
        Request email verification.
        
        Args:
            email: User's email address
            
        Returns:
            Verification token if user exists
        """
        user = self.db.query(User).filter(User.email == email).first()
        
        if user:
            token = create_email_verification_token(email)
            logger.info(f"Email verification requested for: {email}")
            return token
        
        return None
    
    def verify_email(
        self,
        verification_token: str
    ) -> bool:
        """
        Verify user's email address.
        
        Args:
            verification_token: Email verification token
            
        Returns:
            True if email was verified
        """
        email = verify_email_verification_token(verification_token)
        
        if not email:
            raise InvalidTokenError("Invalid or expired verification token")
        
        user = self.db.query(User).filter(User.email == email).first()
        
        if not user:
            raise NotFoundError("User", email)
        
        logger.info(f"Email verified for: {email}")
        
        return True
    
    # ==================== User Management ====================
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address.
        
        Args:
            email: User's email address
            
        Returns:
            User object or None
        """
        return self.db.query(User).filter(User.email == email).first()
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id: User's ID
            
        Returns:
            User object or None
        """
        return self.db.query(User).filter(User.id == user_id).first()
    
    def update_user(
        self,
        user: User,
        **update_data
    ) -> User:
        """
        Update user fields.
        
        Args:
            user: User to update
            **update_data: Fields to update
            
        Returns:
            Updated User object
        """
        for field, value in update_data.items():
            if hasattr(user, field) and value is not None:
                setattr(user, field, value)
        
        user.updated_at = datetime.now().isoformat()
        
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def deactivate_user(self, user: User) -> bool:
        """
        Deactivate a user account.
        
        Args:
            user: User to deactivate
            
        Returns:
            True if deactivated
        """
        user.is_active = False
        self.db.commit()
        
        logger.info(f"User deactivated: {user.email}")
        
        return True
    
    def activate_user(self, user: User) -> bool:
        """
        Activate a user account.
        
        Args:
            user: User to activate
            
        Returns:
            True if activated
        """
        user.is_active = True
        self.db.commit()
        
        logger.info(f"User activated: {user.email}")
        
        return True

