"""
Security Module - Enhanced Version

Security utilities for authentication and authorization.
Includes JWT with refresh token rotation support.

This is the core security module - import from here, not from utils.
"""
import os
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List
from passlib.context import CryptContext
from jose import JWTError, jwt, ExpiredSignatureError
from pydantic import BaseModel
from dataclasses import dataclass

from app.core.config import settings
from app.core.exceptions import (
    InvalidCredentialsError,
    TokenExpiredError,
    InvalidTokenError,
    RefreshTokenError
)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ==================== Password Functions ====================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


def generate_strong_password(length: int = 16) -> str:
    """
    Generate a cryptographically strong random password.
    Guarantees at least one lowercase, one uppercase, one digit, and one special character.
    
    Args:
        length: Password length (minimum 8 recommended)
        
    Returns:
        Random password string
    """
    if length < 4:
        length = 4
        
    lowercase = "abcdefghijklmnopqrstuvwxyz"
    uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    digits = "0123456789"
    special = "!@#$%^&*"
    
    # Ensure at least one of each
    password = [
        secrets.choice(lowercase),
        secrets.choice(uppercase),
        secrets.choice(digits),
        secrets.choice(special)
    ]
    
    # Fill the rest
    alphabet = lowercase + uppercase + digits + special
    password += [secrets.choice(alphabet) for _ in range(length - 4)]
    
    # Shuffle the result
    secrets.SystemRandom().shuffle(password)
    
    return ''.join(password)


# ==================== JWT Configuration ====================

# Get keys from settings, with fallbacks for development
SECRET_KEY = settings.SECRET_KEY
if not SECRET_KEY:
    if settings.ENVIRONMENT == "production":
        raise ValueError("SECRET_KEY environment variable must be set in production")
    SECRET_KEY = "dev-secret-key-change-in-production-use-environment-variable"

REFRESH_SECRET_KEY = settings.REFRESH_SECRET_KEY
if not REFRESH_SECRET_KEY:
    REFRESH_SECRET_KEY = SECRET_KEY

ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS


# ==================== Token Data Models ====================

class TokenData(BaseModel):
    """Token payload data structure."""
    email: str | None = None
    token_type: str = "access"
    user_id: int | None = None


class TokenPair(BaseModel):
    """Access and refresh token pair."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = ACCESS_TOKEN_EXPIRE_MINUTES * 60


class TokenPayload(BaseModel):
    """JWT token payload."""
    sub: str  # Subject (email)
    exp: int  # Expiration
    token_type: str  # access or refresh
    user_id: Optional[int] = None


# ==================== In-Memory Token Store ====================

# In-memory refresh token store (use Redis in production)
# Format: {token_hash: {user_id, email, created_at, expires_at}}
_refresh_tokens: Dict[str, Dict] = {}

# Blocklisted tokens (use Redis in production)
_blocklisted_tokens: set = set()


# ==================== Access Token Functions ====================

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in the token (typically {"sub": email})
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({
        "exp": expire,
        "token_type": "access",
        "jti": secrets.token_hex(16)  # Add unique ID for token uniqueness
    })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[TokenData]:
    """
    Decode an access token.
    
    Args:
        token: JWT token string
        
    Returns:
        TokenData if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        token_type: str = payload.get("token_type", "access")
        
        if email is None or token_type != "access":
            return None
            
        # Check if token is blocklisted
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        if token_hash in _blocklisted_tokens:
            return None
            
        return TokenData(email=email, token_type=token_type)
        
    except (JWTError, ExpiredSignatureError):
        return None


# ==================== Refresh Token Functions ====================

def create_refresh_token(data: dict) -> str:
    """
    Create a JWT refresh token with rotation support.
    
    Args:
        data: Data to encode (must include "sub" with user email)
        
    Returns:
        Encoded refresh token string
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({
        "exp": expire,
        "token_type": "refresh",
        "jti": secrets.token_hex(16)  # Add unique ID for token uniqueness
    })
    encoded_jwt = jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm=ALGORITHM)
    
    # Store token metadata for rotation tracking
    token_hash = hashlib.sha256(encoded_jwt.encode()).hexdigest()
    _refresh_tokens[token_hash] = {
        "user_id": data.get("user_id"),
        "email": data.get("sub"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": expire.isoformat()
    }
    
    return encoded_jwt


def decode_refresh_token(token: str) -> Optional[TokenData]:
    """
    Decode a refresh token.
    
    Args:
        token: Refresh token string
        
    Returns:
        TokenData if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        token_type: str = payload.get("token_type", "refresh")
        
        if email is None or token_type != "refresh":
            return None
            
        # Verify token exists in store
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        if token_hash not in _refresh_tokens:
            return None
            
        return TokenData(email=email, token_type=token_type)
        
    except (JWTError, ExpiredSignatureError):
        return None


def create_token_pair(data: dict) -> TokenPair:
    """
    Create both access and refresh tokens.
    
    Args:
        data: Data to encode (must include "sub" and "user_id")
        
    Returns:
        TokenPair with both tokens
    """
    access_token = create_access_token(data)
    refresh_token = create_refresh_token(data)
    
    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


# ==================== Token Rotation & Revocation ====================

def rotate_refresh_token(old_token: str, data: dict) -> Optional[TokenPair]:
    """
    Rotate refresh token - invalidate old token and issue new one.
    This provides security against token theft.
    
    Args:
        old_token: The current refresh token
        data: Data for the new token
        
    Returns:
        New TokenPair if successful, None otherwise
    """
    try:
        # Verify old token
        payload = jwt.decode(old_token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
        
        # Invalidate old token
        token_hash = hashlib.sha256(old_token.encode()).hexdigest()
        if token_hash in _refresh_tokens:
            del _refresh_tokens[token_hash]
        
        # Create new token pair
        return create_token_pair(data)
        
    except (JWTError, ExpiredSignatureError):
        return None


def revoke_refresh_token(token: str) -> bool:
    """
    Manually revoke a refresh token.
    
    Args:
        token: Refresh token to revoke
        
    Returns:
        True if token was revoked, False otherwise
    """
    try:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        if token_hash in _refresh_tokens:
            del _refresh_tokens[token_hash]
            return True
        return False
    except Exception:
        return False


def revoke_access_token(token: str) -> bool:
    """
    Revoke an access token by adding it to the blocklist.
    
    Args:
        token: Access token to revoke
        
    Returns:
        True if token was revoked
    """
    try:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        _blocklisted_tokens.add(token_hash)
        return True
    except Exception:
        return False


def is_token_revoked(token: str) -> bool:
    """
    Check if a token has been revoked.
    
    Args:
        token: Token to check
        
    Returns:
        True if revoked, False otherwise
    """
    try:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        return token_hash in _blocklisted_tokens
    except Exception:
        return True  # Assume revoked on error for security


def cleanup_expired_tokens():
    """Clean up expired tokens from the store."""
    now = datetime.now(timezone.utc).isoformat()
    
    # Clean expired refresh tokens
    expired = [
        hash_val for hash_val, data in _refresh_tokens.items()
        if data.get("expires_at", "") < now
    ]
    for hash_val in expired:
        del _refresh_tokens[hash_val]


# ==================== Password Reset Tokens ====================

def create_password_reset_token(email: str) -> str:
    """
    Create a password reset token.
    
    Args:
        email: User's email address
        
    Returns:
        Password reset token
    """
    data = {
        "sub": email,
        "type": "password_reset",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)  # 1 hour expiry
    }
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)


def verify_password_reset_token(token: str) -> Optional[str]:
    """
    Verify a password reset token.
    
    Args:
        token: Password reset token
        
    Returns:
        Email if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "password_reset":
            return None
        return payload.get("sub")
    except (JWTError, ExpiredSignatureError):
        return None


# ==================== Email Verification Tokens ====================

def create_email_verification_token(email: str) -> str:
    """
    Create an email verification token.
    
    Args:
        email: User's email address
        
    Returns:
        Email verification token
    """
    data = {
        "sub": email,
        "type": "email_verification",
        "exp": datetime.now(timezone.utc) + timedelta(days=7)
    }
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)


def verify_email_verification_token(token: str) -> Optional[str]:
    """
    Verify an email verification token.
    
    Args:
        token: Email verification token
        
    Returns:
        Email if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "email_verification":
            return None
        return payload.get("sub")
    except (JWTError, ExpiredSignatureError):
        return None


# ==================== Utility Functions ====================

def get_token_expiry(token_type: str = "access") -> datetime:
    """
    Get the expiration datetime for a token type.
    
    Args:
        token_type: Type of token ("access" or "refresh")
        
    Returns:
        Expiration datetime
    """
    if token_type == "refresh":
        return datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    return datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

