"""
Google OAuth Handler for MahaInsight
Manages Google OAuth flow for login and registration.
"""
import os
from typing import Dict, Optional
from authlib.integrations.requests_client import OAuth2Session
from dotenv import load_dotenv

load_dotenv()

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:5000/api/auth/google/callback")

# Google OAuth endpoints
GOOGLE_AUTHORIZATION_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_ENDPOINT = "https://www.googleapis.com/oauth2/v2/userinfo"

# Scopes
GOOGLE_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile"
]


class OAuthError(Exception):
    """Custom exception for OAuth-related errors."""
    pass


def get_oauth_session() -> OAuth2Session:
    """
    Create and return OAuth2 session for Google.
    
    Returns:
        Configured OAuth2Session instance
        
    Raises:
        OAuthError: If credentials are not configured
    """
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise OAuthError("Google OAuth credentials not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env")
    
    return OAuth2Session(
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        redirect_uri=GOOGLE_REDIRECT_URI,
        scope=GOOGLE_SCOPES
    )


def get_authorization_url() -> tuple[str, str]:
    """
    Generate Google OAuth authorization URL.
    
    Returns:
        Tuple of (authorization_url, state)
    """
    session = get_oauth_session()
    authorization_url, state = session.create_authorization_url(
        GOOGLE_AUTHORIZATION_ENDPOINT
    )
    return authorization_url, state


def exchange_code_for_token(code: str, state: str) -> Dict:
    """
    Exchange authorization code for access token.
    
    Args:
        code: Authorization code from Google callback
        state: State parameter for CSRF protection
        
    Returns:
        Token response dictionary
        
    Raises:
        OAuthError: If token exchange fails
    """
    try:
        session = get_oauth_session()
        token = session.fetch_token(
            GOOGLE_TOKEN_ENDPOINT,
            authorization_response=f"{GOOGLE_REDIRECT_URI}?code={code}&state={state}"
        )
        return token
    except Exception as e:
        raise OAuthError(f"Failed to exchange code for token: {str(e)}")


def get_user_info(access_token: str) -> Dict:
    """
    Fetch user profile information from Google.
    
    Args:
        access_token: Google access token
        
    Returns:
        User profile dictionary containing:
            - id: Google user ID
            - email: User's email
            - verified_email: Whether email is verified
            - name: Full name
            - given_name: First name
            - family_name: Last name
            - picture: Profile picture URL
            - locale: User's locale
            
    Raises:
        OAuthError: If user info fetch fails
    """
    try:
        session = get_oauth_session()
        session.token = {"access_token": access_token, "token_type": "Bearer"}
        
        response = session.get(GOOGLE_USERINFO_ENDPOINT)
        response.raise_for_status()
        
        return response.json()
    except Exception as e:
        raise OAuthError(f"Failed to fetch user info: {str(e)}")


def validate_google_profile(profile: Dict) -> bool:
    """
    Validate that Google profile has required fields.
    
    Args:
        profile: Google user profile dictionary
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = ["id", "email", "verified_email"]
    return all(field in profile for field in required_fields) and profile.get("verified_email") is True
