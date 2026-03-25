"""
Encryption utilities for sensitive data.
"""
from cryptography.fernet import Fernet
from decouple import config

# SECURITY FIX: Require ENCRYPTION_KEY in production
# In production, always set ENCRYPTION_KEY environment variable
key_str = config("ENCRYPTION_KEY", default=None)

if key_str is None:
    import os
    if os.getenv("ENVIRONMENT", "development") == "production":
        raise ValueError("ENCRYPTION_KEY environment variable must be set in production")
    # Use a secure development key only in development mode
    # In production, set ENCRYPTION_KEY environment variable
    # This is a valid Fernet key (32 bytes, base64 encoded)
    key = b"1sivQdigt-bMFBBubkfE1HKVv1YA2JJI83yeZF3gLH4="
    cipher_suite = Fernet(key)
else:
    key = key_str.encode() if isinstance(key_str, str) else key_str
    cipher_suite = Fernet(key)


def encrypt(data: str) -> str:
    """Encrypt a string."""
    if not data:
        return data
    encrypted_bytes = cipher_suite.encrypt(data.encode())
    return encrypted_bytes.decode()


def decrypt(encrypted_data: str) -> str:
    """Decrypt an encrypted string."""
    if not encrypted_data:
        return encrypted_data
    try:
        decrypted_bytes = cipher_suite.decrypt(encrypted_data.encode())
        return decrypted_bytes.decode()
    except Exception:
        # Return original if decryption fails (for backwards compatibility)
        return encrypted_data

