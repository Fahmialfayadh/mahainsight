"""
JWT Token Utilities for MahaInsight Authentication
Handles access and refresh token generation, validation, and rotation.
"""
import os
import jwt
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Tuple
from dotenv import load_dotenv

load_dotenv()

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", os.getenv("SECRET_KEY"))
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", 900))  # 15 minutes
REFRESH_TOKEN_EXPIRES = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES", 2592000))  # 30 days


class TokenError(Exception):
    """Custom exception for token-related errors."""
    pass


def generate_access_token(user_id: int, email: str, is_admin: bool = False) -> str:
    """
    Generate JWT access token with 15 minute expiry.
    
    Args:
        user_id: User's database ID
        email: User's email address
        is_admin: Whether user has admin privileges
        
    Returns:
        Encoded JWT access token
    """
    now = datetime.now(timezone.utc)
    payload = {
        "user_id": user_id,
        "email": email,
        "is_admin": is_admin,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(seconds=ACCESS_TOKEN_EXPIRES)
    }
    
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token


def generate_refresh_token(user_id: int) -> Tuple[str, str]:
    """
    Generate JWT refresh token with 30 day expiry.
    
    Args:
        user_id: User's database ID
        
    Returns:
        Tuple of (encoded token, token hash for storage)
    """
    now = datetime.now(timezone.utc)
    payload = {
        "user_id": user_id,
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(seconds=REFRESH_TOKEN_EXPIRES)
    }
    
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    return token, token_hash


def verify_access_token(token: str) -> Dict:
    """
    Verify and decode access token.
    
    Args:
        token: JWT access token string
        
    Returns:
        Decoded payload dictionary
        
    Raises:
        TokenError: If token is invalid, expired, or not an access token
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        if payload.get("type") != "access":
            raise TokenError("Invalid token type")
            
        return payload
        
    except jwt.ExpiredSignatureError:
        raise TokenError("Access token has expired")
    except jwt.InvalidTokenError as e:
        raise TokenError(f"Invalid access token: {str(e)}")


def verify_refresh_token(token: str) -> Dict:
    """
    Verify and decode refresh token.
    
    Args:
        token: JWT refresh token string
        
    Returns:
        Decoded payload dictionary
        
    Raises:
        TokenError: If token is invalid, expired, or not a refresh token
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        if payload.get("type") != "refresh":
            raise TokenError("Invalid token type")
            
        return payload
        
    except jwt.ExpiredSignatureError:
        raise TokenError("Refresh token has expired")
    except jwt.InvalidTokenError as e:
        raise TokenError(f"Invalid refresh token: {str(e)}")


def hash_token(token: str) -> str:
    """
    Create SHA-256 hash of token for secure storage.
    
    Args:
        token: Token string to hash
        
    Returns:
        Hexadecimal hash string
    """
    return hashlib.sha256(token.encode()).hexdigest()


def get_token_expiry(token: str) -> Optional[datetime]:
    """
    Extract expiry time from token without full validation.
    
    Args:
        token: JWT token string
        
    Returns:
        Expiry datetime or None if invalid
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM], options={"verify_exp": False})
        exp_timestamp = payload.get("exp")
        if exp_timestamp:
            return datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
    except:
        pass
    return None
