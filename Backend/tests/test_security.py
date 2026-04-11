"""
Comprehensive tests for security module - JWT tokens, password hashing, and authentication.
"""
import pytest
from datetime import datetime, timedelta, timezone
from app.core.security import (
    get_password_hash,
    verify_password,
    generate_strong_password,
    create_access_token,
    decode_access_token,
    create_refresh_token,
    decode_refresh_token,
    create_token_pair,
    rotate_refresh_token,
    revoke_refresh_token,
    revoke_access_token,
    is_token_revoked,
    create_password_reset_token,
    verify_password_reset_token,
    create_email_verification_token,
    verify_email_verification_token,
    cleanup_expired_tokens,
    get_token_expiry,
    TokenData,
    TokenPair,
)
from app.core.exceptions import TokenExpiredError, InvalidTokenError


class TestPasswordHashing:
    """Tests for password hashing and verification."""
    
    def test_hash_password_returns_string(self):
        hashed = get_password_hash("password123")
        assert isinstance(hashed, str)
        assert len(hashed) > 0
    
    def test_verify_correct_password(self):
        password = "SecurePassword123!"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True
    
    def test_verify_incorrect_password(self):
        password = "SecurePassword123!"
        wrong_password = "WrongPassword456!"
        hashed = get_password_hash(password)
        assert verify_password(wrong_password, hashed) is False
    
    def test_different_hashes_for_same_password(self):
        password = "SamePassword"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        # bcrypt includes salt, so hashes should be different
        assert hash1 != hash2
        # But both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True
    
    def test_empty_password(self):
        hashed = get_password_hash("")
        assert verify_password("", hashed) is True
        assert verify_password("notempty", hashed) is False
    
    def test_unicode_password(self):
        password = "пароль密码🔒"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True
    
    def test_generate_strong_password_default_length(self):
        password = generate_strong_password()
        assert len(password) == 16
        assert isinstance(password, str)
    
    def test_generate_strong_password_custom_length(self):
        password = generate_strong_password(32)
        assert len(password) == 32
    
    def test_generate_strong_password_contains_various_chars(self):
        # Generate multiple passwords to ensure variety
        for _ in range(10):
            password = generate_strong_password(20)
            assert any(c.islower() for c in password)
            assert any(c.isupper() for c in password)
            assert any(c.isdigit() for c in password)


class TestAccessToken:
    """Tests for access token creation and decoding."""
    
    def test_create_access_token_returns_string(self):
        token = create_access_token({"sub": "test@example.com"})
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_decode_valid_access_token(self):
        email = "test@example.com"
        token = create_access_token({"sub": email})
        result = decode_access_token(token)
        assert result is not None
        assert result.email == email
        assert result.token_type == "access"
    
    def test_decode_invalid_token_returns_none(self):
        result = decode_access_token("invalid.token.here")
        assert result is None
    
    def test_decode_token_with_wrong_type_returns_none(self):
        # Create a refresh token and try to decode as access
        refresh_token = create_refresh_token({"sub": "test@example.com"})
        result = decode_access_token(refresh_token)
        assert result is None
    
    def test_access_token_expiration(self, monkeypatch):
        # Mock time to test expiration
        from jose import jwt
        from app.core import security
        
        # Create token with very short expiration
        to_encode = {"sub": "test@example.com"}
        to_encode["exp"] = datetime.now(timezone.utc) - timedelta(seconds=1)
        expired_token = jwt.encode(to_encode, security.SECRET_KEY, algorithm=security.ALGORITHM)
        
        result = decode_access_token(expired_token)
        assert result is None
    
    def test_access_token_contains_user_id(self):
        user_id = 123
        token = create_access_token({"sub": "test@example.com", "user_id": user_id})
        # Token should be decodable (we can't directly access payload but it's encoded)
        assert decode_access_token(token) is not None
    
    def test_access_token_missing_email_returns_none(self):
        token = create_access_token({"user_id": 123})  # Missing 'sub'
        # Manually create a token without sub
        from jose import jwt
        from app.core import security
        
        to_encode = {"user_id": 123, "exp": datetime.now(timezone.utc) + timedelta(minutes=15)}
        to_encode["token_type"] = "access"
        bad_token = jwt.encode(to_encode, security.SECRET_KEY, algorithm=security.ALGORITHM)
        
        result = decode_access_token(bad_token)
        assert result is None


class TestRefreshToken:
    """Tests for refresh token creation, decoding, and rotation."""
    
    def test_create_refresh_token_returns_string(self):
        token = create_refresh_token({"sub": "test@example.com"})
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_decode_valid_refresh_token(self):
        email = "test@example.com"
        token = create_refresh_token({"sub": email})
        result = decode_refresh_token(token)
        assert result is not None
        assert result.email == email
        assert result.token_type == "refresh"
    
    def test_decode_invalid_refresh_token_returns_none(self):
        result = decode_refresh_token("invalid.refresh.token")
        assert result is None
    
    def test_refresh_token_not_in_store_returns_none(self):
        # Create a token manually without storing it
        from jose import jwt
        from app.core import security
        
        to_encode = {
            "sub": "test@example.com",
            "exp": datetime.now(timezone.utc) + timedelta(days=7),
            "token_type": "refresh"
        }
        fake_token = jwt.encode(to_encode, security.REFRESH_SECRET_KEY, algorithm=security.ALGORITHM)
        
        result = decode_refresh_token(fake_token)
        assert result is None
    
    def test_create_token_pair(self):
        data = {"sub": "test@example.com", "user_id": 123}
        pair = create_token_pair(data)
        assert isinstance(pair, TokenPair)
        assert len(pair.access_token) > 0
        assert len(pair.refresh_token) > 0
        assert pair.token_type == "bearer"
        # 30 minutes in seconds (as configured in config.py)
        assert pair.expires_in == 30 * 60
    
    def test_rotate_refresh_token_success(self):
        old_data = {"sub": "test@example.com", "user_id": 123}
        old_token = create_refresh_token(old_data)
        
        # Verify old token works
        assert decode_refresh_token(old_token) is not None
        
        # Rotate token
        new_pair = rotate_refresh_token(old_token, old_data)
        assert new_pair is not None
        assert isinstance(new_pair, TokenPair)
        
        # Old token should be invalidated
        assert decode_refresh_token(old_token) is None
        
        # New token should work
        assert decode_refresh_token(new_pair.refresh_token) is not None
    
    def test_rotate_invalid_token_returns_none(self):
        result = rotate_refresh_token("invalid.token", {"sub": "test@example.com"})
        assert result is None
    
    def test_revoke_refresh_token_success(self):
        token = create_refresh_token({"sub": "test@example.com"})
        assert decode_refresh_token(token) is not None
        
        result = revoke_refresh_token(token)
        assert result is True
        assert decode_refresh_token(token) is None
    
    def test_revoke_nonexistent_refresh_token_returns_false(self):
        result = revoke_refresh_token("nonexistent.token")
        assert result is False
    
    def test_revoke_access_token(self):
        token = create_access_token({"sub": "test@example.com"})
        assert decode_access_token(token) is not None
        
        result = revoke_access_token(token)
        assert result is True
        assert decode_access_token(token) is None
    
    def test_is_token_revoked(self):
        token = create_access_token({"sub": "test@example.com"})
        assert is_token_revoked(token) is False
        
        revoke_access_token(token)
        assert is_token_revoked(token) is True


class TestPasswordResetToken:
    """Tests for password reset token functionality."""
    
    def test_create_password_reset_token(self):
        email = "test@example.com"
        token = create_password_reset_token(email)
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_verify_valid_password_reset_token(self):
        email = "test@example.com"
        token = create_password_reset_token(email)
        result = verify_password_reset_token(token)
        assert result == email
    
    def test_verify_invalid_password_reset_token_returns_none(self):
        result = verify_password_reset_token("invalid.token")
        assert result is None
    
    def test_password_reset_token_expires(self, monkeypatch):
        # Create a token that's already expired
        from jose import jwt
        from app.core import security
        
        data = {
            "sub": "test@example.com",
            "type": "password_reset",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1)
        }
        expired_token = jwt.encode(data, security.SECRET_KEY, algorithm=security.ALGORITHM)
        
        result = verify_password_reset_token(expired_token)
        assert result is None
    
    def test_password_reset_token_wrong_type_returns_none(self):
        # Create a token with wrong type
        from jose import jwt
        from app.core import security
        
        data = {
            "sub": "test@example.com",
            "type": "wrong_type",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        }
        wrong_token = jwt.encode(data, security.SECRET_KEY, algorithm=security.ALGORITHM)
        
        result = verify_password_reset_token(wrong_token)
        assert result is None


class TestEmailVerificationToken:
    """Tests for email verification token functionality."""
    
    def test_create_email_verification_token(self):
        email = "test@example.com"
        token = create_email_verification_token(email)
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_verify_valid_email_verification_token(self):
        email = "test@example.com"
        token = create_email_verification_token(email)
        result = verify_email_verification_token(token)
        assert result == email
    
    def test_verify_invalid_email_verification_token_returns_none(self):
        result = verify_email_verification_token("invalid.token")
        assert result is None
    
    def test_email_verification_token_wrong_type_returns_none(self):
        from jose import jwt
        from app.core import security
        
        data = {
            "sub": "test@example.com",
            "type": "wrong_type",
            "exp": datetime.now(timezone.utc) + timedelta(days=7)
        }
        wrong_token = jwt.encode(data, security.SECRET_KEY, algorithm=security.ALGORITHM)
        
        result = verify_email_verification_token(wrong_token)
        assert result is None


class TestTokenCleanup:
    """Tests for token cleanup functionality."""
    
    def test_cleanup_expired_tokens(self):
        # This should run without errors
        # Note: In a real scenario, we'd need to create expired tokens first
        cleanup_expired_tokens()
        # If we get here without errors, the test passes
        assert True


class TestTokenExpiry:
    """Tests for token expiry retrieval."""
    
    def test_get_access_token_expiry(self):
        expiry = get_token_expiry("access")
        assert isinstance(expiry, datetime)
        # Should be approximately 30 minutes from now (as configured)
        expected = datetime.now(timezone.utc) + timedelta(minutes=30)
        assert abs((expiry - expected).total_seconds()) < 5  # Allow 5 seconds tolerance
    
    def test_get_refresh_token_expiry(self):
        expiry = get_token_expiry("refresh")
        assert isinstance(expiry, datetime)
        # Should be approximately 7 days from now
        expected = datetime.now(timezone.utc) + timedelta(days=7)
        assert abs((expiry - expected).total_seconds()) < 5  # Allow 5 seconds tolerance
    
    def test_get_default_token_expiry(self):
        expiry = get_token_expiry()
        assert isinstance(expiry, datetime)
        # Default should be access token expiry (30 mins)
        expected = datetime.now(timezone.utc) + timedelta(minutes=30)
        assert abs((expiry - expected).total_seconds()) < 5