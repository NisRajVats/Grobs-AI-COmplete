"""
Encryption utilities for sensitive data.
"""
import re
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
    """Encrypt a string. Prevents double-encryption if data already looks like a token."""
    if not data or not isinstance(data, str):
        return data
        
    # Prevent double-encryption
    if data.lower().startswith("gaaaaa") and len(data) > 50:
        # Verify it actually is a valid token by trying to decrypt it
        try:
            cipher_suite.decrypt(data.encode())
            return data # Already encrypted, return as-is
        except Exception:
            pass # Not a valid token or different key, proceed to encrypt
            
    encrypted_bytes = cipher_suite.encrypt(data.encode())
    return encrypted_bytes.decode()


def decrypt(encrypted_data: str) -> str:
    """
    Decrypt an encrypted string.
    Supports multiple levels of encryption (recursive) and robust token extraction.
    Handles common artifacts like leading colons or trailing filenames.
    """
    if not encrypted_data or not isinstance(encrypted_data, str):
        return encrypted_data
    
    # 1. Basic cleanup - handle artifacts from copy-paste or corrupted DB states
    data = encrypted_data.strip()
    if data.startswith(":"):
        data = data[1:].strip()
        
    # 2. Early exit if it doesn't look like it contains a Fernet token (starts with gAAAAA)
    if "gaaaaa" not in data.lower():
        return encrypted_data

    try:
        current_val = data
        for _ in range(4): # Increased to 4 levels for safety
            # Find all potential Fernet tokens in current_val
            # Fernet tokens start with gAAAAA and use base64url alphabet
            tokens = re.findall(r'gAAAAA[A-Za-z0-9\-_]+={0,2}', current_val, re.IGNORECASE)
            
            if not tokens:
                break
                
            any_success = False
            # Sort tokens by length (descending) to try longest ones first
            for token in sorted(tokens, key=len, reverse=True):
                # Fernet is case-sensitive, but sometimes tokens get accidentally cased
                # Try original first, then a fixed version (starting with lowercase g)
                to_try = [token]
                if token.startswith("GAAAAA"):
                    to_try.append("g" + token[1:])
                
                for t in to_try:
                    # Strategy: try the token as found, then try stripping chars from the end
                    # This handles cases like "gAAAAA...SomeSuffix.pdf" where the suffix
                    # accidentally matched the base64-ish regex.
                    curr_t = t
                    # Don't strip too much; a valid token won't be shorter than 50 chars
                    while len(curr_t) >= 50:
                        try:
                            decrypted_bytes = cipher_suite.decrypt(curr_t.encode())
                            decrypted_str = decrypted_bytes.decode()
                            # Replace the EXACT substring we found (token) with decrypted string
                            # even if we only decrypted a prefix (curr_t). 
                            # If we only decrypted a prefix, we should probably only replace that prefix.
                            current_val = current_val.replace(curr_t, decrypted_str)
                            any_success = True
                            break
                        except Exception:
                            # If it didn't work and it doesn't look like it has padding, 
                            # it might be because we over-matched. Try stripping one char.
                            if len(curr_t) > 50:
                                curr_t = curr_t[:-1]
                            else:
                                break
                    if any_success:
                        break
                if any_success:
                    break
            
            if not any_success:
                break
                
        return current_val
    except Exception:
        # Fall back to original input on catastrophic failure
        return encrypted_data

