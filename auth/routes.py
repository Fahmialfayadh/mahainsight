"""
Authentication Routes for MahaInsight
Handles login, register, logout, token refresh, and Google OAuth.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, make_response, session
from werkzeug.security import generate_password_hash, check_password_hash
import os

from db import (
    create_user, get_user_by_email, get_user_by_id, get_user_by_google_id,
    update_user_oauth, create_refresh_token, get_refresh_token,
    revoke_refresh_token, get_supabase
)
from auth.jwt_utils import (
    generate_access_token, generate_refresh_token,
    verify_refresh_token, hash_token, TokenError
)
from auth.oauth_handler import (
    get_authorization_url, exchange_code_for_token,
    get_user_info, validate_google_profile, OAuthError
)
from auth.auth_middleware import set_auth_cookies, clear_auth_cookies
from datetime import datetime, timezone, timedelta

# Create Blueprint
auth_bp = Blueprint('auth', __name__)

# Check if we're in production (HTTPS)
IS_PRODUCTION = os.getenv("FLASK_ENV") == "production"


# ============== HELPER FUNCTIONS ==============

def create_jwt_tokens_for_user(user: dict) -> tuple:
    """Create JWT access and refresh tokens for a user."""
    access_token = generate_access_token(
        user_id=user["id"],
        email=user["email"],
        is_admin=user.get("is_admin", False)
    )
    refresh_token, token_hash = generate_refresh_token(user_id=user["id"])
    return access_token, refresh_token, token_hash


def store_refresh_token_in_db(user_id: int, token_hash: str):
    """Store refresh token in database with 30-day expiry."""
    expires_at = datetime.now(timezone.utc) + timedelta(days=30)
    create_refresh_token(user_id, token_hash, expires_at)


def update_last_login(user_id: int):
    """Update user's last login timestamp."""
    supabase = get_supabase()
    supabase.table("users_insight").update({
        "last_login_at": datetime.now(timezone.utc).isoformat()
    }).eq("id", user_id).execute()


def create_auth_response(user: dict, next_url: str = None) -> any:
    """Create response with JWT cookies and redirect."""
    # Generate tokens
    access_token, refresh_token, token_hash = create_jwt_tokens_for_user(user)
    
    # Store refresh token
    store_refresh_token_in_db(user["id"], token_hash)
    
    # Update last login
    update_last_login(user["id"])
    
    # Determine redirect
    if user.get("is_admin"):
        redirect_url = url_for("admin")
    else:
        redirect_url = next_url or url_for("index")
    
    # Create response
    response = make_response(redirect(redirect_url))
    
    # Set auth cookies
    set_auth_cookies(response, access_token, refresh_token, secure=IS_PRODUCTION)
    
    return response


# ============== ROUTES ==============

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Login page and handler with JWT token issuance."""
    if request.method == "GET":
        return render_template("auth_login.html")
    
    email = request.form.get("email")
    password = request.form.get("password")
    
    if not email or not password:
        flash("Email dan password wajib diisi", "error")
        return render_template("auth_login.html")
    
    try:
        user = get_user_by_email(email)
        
        if not user or not check_password_hash(user["password_hash"], password):
            flash("Email atau password salah", "error")
            return render_template("auth_login.html")
        
        response = create_auth_response(user, request.args.get("next"))
        flash("Login berhasil!", "success")
        return response
        
    except Exception as e:
        print(f"Login error: {e}")
        flash("Terjadi kesalahan saat login", "error")
        return render_template("auth_login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Registration page and handler."""
    if request.method == "GET":
        return render_template("auth_register.html")
    
    email = request.form.get("email")
    password = request.form.get("password")
    full_name = request.form.get("full_name")
    
    if not email or not password:
        flash("Email dan password wajib diisi", "error")
        return render_template("auth_register.html")
    
    try:
        existing = get_user_by_email(email)
        if existing:
            flash("Email sudah terdaftar", "error")
            return render_template("auth_register.html")
    except:
        pass
    
    try:
        hashed = generate_password_hash(password)
        create_user(email, hashed, full_name)
        flash("Registrasi berhasil! Silakan login.", "success")
        return redirect(url_for("auth.login"))
    except Exception as e:
        print(f"Registration error: {e}")
        flash(f"Error: {str(e)}", "error")
        return render_template("auth_register.html")


@auth_bp.route("/logout")
def logout():
    """Logout handler - revokes refresh token and clears cookies."""
    refresh_token = request.cookies.get("refresh_token")
    
    if refresh_token:
        try:
            token_hash = hash_token(refresh_token)
            revoke_refresh_token(token_hash)
        except Exception as e:
            print(f"Logout error: {e}")
    
    response = make_response(redirect(url_for("index")))
    clear_auth_cookies(response)
    flash("Anda telah logout.", "info")
    return response


@auth_bp.route("/api/auth/refresh", methods=["POST"])
def refresh():
    """Refresh access token using refresh token (with rotation)."""
    refresh_token = request.cookies.get("refresh_token")
    
    if not refresh_token:
        return jsonify({"error": "No refresh token provided", "code": "NO_REFRESH_TOKEN"}), 401
    
    try:
        payload = verify_refresh_token(refresh_token)
        user_id = payload.get("user_id")
        
        token_hash = hash_token(refresh_token)
        db_token = get_refresh_token(token_hash)
        
        if not db_token or db_token.get("revoked"):
            return jsonify({"error": "Invalid refresh token", "code": "REVOKED_TOKEN"}), 401
        
        user = get_user_by_id(user_id)
        if not user:
            return jsonify({"error": "User not found", "code": "USER_NOT_FOUND"}), 401
        
        # Generate new tokens
        new_access_token, new_refresh_token, new_token_hash = create_jwt_tokens_for_user(user)
        
        # Revoke old & store new
        revoke_refresh_token(token_hash)
        store_refresh_token_in_db(user["id"], new_token_hash)
        
        response = make_response(jsonify({"success": True, "message": "Token refreshed"}))
        set_auth_cookies(response, new_access_token, new_refresh_token, secure=IS_PRODUCTION)
        
        return response
        
    except TokenError as e:
        return jsonify({"error": str(e), "code": "INVALID_REFRESH_TOKEN"}), 401
    except Exception as e:
        print(f"Token refresh error: {e}")
        return jsonify({"error": "Failed to refresh token", "code": "REFRESH_ERROR"}), 500


@auth_bp.route("/api/auth/google/login")
def google_login():
    """Initiate Google OAuth login flow."""
    try:
        authorization_url, state = get_authorization_url()
        session["oauth_state"] = state
        return redirect(authorization_url)
    except OAuthError as e:
        flash(f"Google OAuth error: {str(e)}", "error")
        return redirect(url_for("auth.login"))


@auth_bp.route("/api/auth/google/callback")
def google_callback():
    """Handle Google OAuth callback."""
    code = request.args.get("code")
    state = request.args.get("state")
    error = request.args.get("error")
    
    if error:
        flash(f"Google login cancelled: {error}", "error")
        return redirect(url_for("auth.login"))
    
    if not code:
        flash("No authorization code received", "error")
        return redirect(url_for("auth.login"))
    
    stored_state = session.get("oauth_state")
    if not stored_state or stored_state != state:
        flash("Invalid state parameter", "error")
        return redirect(url_for("auth.login"))
    
    try:
        token_response = exchange_code_for_token(code, state)
        access_token = token_response.get("access_token")
        
        google_profile = get_user_info(access_token)
        
        if not validate_google_profile(google_profile):
            flash("Invalid Google profile or email not verified", "error")
            return redirect(url_for("auth.login"))
        
        google_id = google_profile.get("id")
        email = google_profile.get("email")
        full_name = google_profile.get("name")
        
        # Find or create user
        user = None
        try:
            user = get_user_by_google_id(google_id)
        except:
            try:
                user = get_user_by_email(email)
                if user:
                    update_user_oauth(user["id"], google_id, google_profile)
            except:
                pass
        
        if not user:
            hashed = generate_password_hash(os.urandom(32).hex())
            user_data = create_user(email, hashed, full_name)
            user_id = user_data[0]["id"] if isinstance(user_data, list) else user_data["id"]
            update_user_oauth(user_id, google_id, google_profile)
            user = get_user_by_id(user_id)
        
        response = create_auth_response(user)
        session.pop("oauth_state", None)
        flash("Login dengan Google berhasil!", "success")
        return response
        
    except OAuthError as e:
        flash(f"Google OAuth error: {str(e)}", "error")
        return redirect(url_for("auth.login"))
    except Exception as e:
        print(f"Google callback error: {e}")  # Keep minimal error logging
        flash("Terjadi kesalahan saat login dengan Google", "error")
        return redirect(url_for("auth.login"))
