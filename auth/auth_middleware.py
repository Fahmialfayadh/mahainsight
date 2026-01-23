"""
Authentication Middleware and Decorators for MahaInsight
Provides JWT-based authentication decorators and utilities.
"""
from functools import wraps
from flask import request, jsonify, make_response
from typing import Optional, Dict, Callable
from auth.jwt_utils import verify_access_token, TokenError


def get_token_from_cookie() -> Optional[str]:
    """
    Extract access token from HttpOnly cookie.
    
    Returns:
        Token string or None if not found
    """
    return request.cookies.get("access_token")


def get_refresh_token_from_cookie() -> Optional[str]:
    """
    Extract refresh token from HttpOnly cookie.
    
    Returns:
        Token string or None if not found
    """
    return request.cookies.get("refresh_token")


def get_current_user() -> Optional[Dict]:
    """
    Get current authenticated user from JWT token.
    
    Returns:
        User payload dict with user_id, email, is_admin or None if not authenticated
    """
    token = get_token_from_cookie()
    if not token:
        return None
    
    try:
        payload = verify_access_token(token)
        return {
            "user_id": payload.get("user_id"),
            "email": payload.get("email"),
            "is_admin": payload.get("is_admin", False)
        }
    except TokenError:
        return None


def jwt_required(f: Callable) -> Callable:
    """
    Decorator to require JWT authentication for routes.
    Returns 401 if token is missing or invalid.
    Attaches current_user to flask.g for access in route.
    
    Usage:
        @app.route('/protected')
        @jwt_required
        def protected_route():
            user = get_current_user()
            return f"Hello {user['email']}"
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = get_token_from_cookie()
        
        if not token:
            return jsonify({"error": "Authentication required", "code": "NO_TOKEN"}), 401
        
        try:
            payload = verify_access_token(token)
            # Attach user info to request context
            from flask import g
            g.current_user = {
                "user_id": payload.get("user_id"),
                "email": payload.get("email"),
                "is_admin": payload.get("is_admin", False)
            }
            return f(*args, **kwargs)
            
        except TokenError as e:
            return jsonify({"error": str(e), "code": "INVALID_TOKEN"}), 401
    
    return decorated_function


def admin_required(f: Callable) -> Callable:
    """
    Decorator to require admin privileges.
    Returns 401 if not authenticated, 403 if not admin.
    
    Usage:
        @app.route('/admin/dashboard')
        @admin_required
        def admin_dashboard():
            return "Admin only area"
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = get_token_from_cookie()
        
        if not token:
            return jsonify({"error": "Authentication required", "code": "NO_TOKEN"}), 401
        
        try:
            payload = verify_access_token(token)
            
            if not payload.get("is_admin", False):
                return jsonify({"error": "Admin access required", "code": "FORBIDDEN"}), 403
            
            # Attach user info to request context
            from flask import g
            g.current_user = {
                "user_id": payload.get("user_id"),
                "email": payload.get("email"),
                "is_admin": True
            }
            return f(*args, **kwargs)
            
        except TokenError as e:
            return jsonify({"error": str(e), "code": "INVALID_TOKEN"}), 401
    
    return decorated_function


def set_auth_cookies(response, access_token: str, refresh_token: str, secure: bool = False):
    """
    Set HttpOnly authentication cookies.
    
    Args:
        response: Flask response object
        access_token: JWT access token
        refresh_token: JWT refresh token
        secure: Whether to set Secure flag (True for production/HTTPS)
    """
    # Access token cookie (15 minutes)
    response.set_cookie(
        "access_token",
        value=access_token,
        max_age=900,  # 15 minutes
        httponly=True,
        secure=secure,
        samesite="None",  # Changed from Lax to None for cross-site
        path="/"
    )
    
    # Refresh token cookie (30 days)
    response.set_cookie(
        "refresh_token",
        value=refresh_token,
        max_age=2592000,  # 30 days
        httponly=True,
        secure=secure,
        samesite="None",  # Changed from Lax to None for cross-site
        path="/"
    )


def clear_auth_cookies(response):
    """
    Clear authentication cookies on logout.
    
    Args:
        response: Flask response object
    """
    response.set_cookie("access_token", "", max_age=0, httponly=True, path="/")
    response.set_cookie("refresh_token", "", max_age=0, httponly=True, path="/")
